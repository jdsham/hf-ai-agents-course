"""
Tests for Error Handling and Logging functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import (
    input_interface, planner, researcher_node, expert, critic, finalizer, orchestrator,
    validate_state, validate_llm_response, handle_agent_error, set_error_state, log_error
)


class TestErrorHandlingAndLogging:
    """Test error handling and logging functionality."""

    def test_error_state_management(self, empty_graph_state):
        """Test that error states are properly set and propagated."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        
        # Act - simulate an error
        error = Exception("Test error")
        result = set_error_state(state, "test_component", error)
        
        # Assert: Error state is set correctly
        assert result["error"] == "test_component failed: Test error"
        assert result["error_component"] == "test_component"

    def test_orchestrator_detects_error_state(self, empty_graph_state):
        """Test that orchestrator detects error states and routes to finalizer."""
        # Arrange
        state = empty_graph_state.copy()
        state["error"] = "test_component failed: Test error"
        state["error_component"] = "test_component"
        state["current_step"] = "planner"
        
        # Act
        result = orchestrator(state)
        
        # Assert: Orchestrator routes to finalizer when error state is present
        assert result["next_step"] == "finalizer"
        assert "error" in result["final_answer"]
        assert "error" in result["final_reasoning_trace"]

    def test_state_validation_passes_for_valid_state(self, empty_graph_state):
        """Test that state validation passes for valid states."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)  # Initialize all required fields
        
        # Act
        result = validate_state(state)
        
        # Assert: State validation passes
        assert result is True

    def test_state_validation_fails_for_missing_fields(self, empty_graph_state):
        """Test that state validation fails for missing required fields."""
        # Arrange
        state = empty_graph_state.copy()
        # Remove a required field
        if "research_steps" in state:
            del state["research_steps"]
        
        # Act
        result = validate_state(state)
        
        # Assert: State validation fails
        assert result is False

    def test_state_validation_fails_for_invalid_types(self, empty_graph_state):
        """Test that state validation fails for invalid field types."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)  # Initialize all required fields
        state["retry_count"] = "invalid_type"  # Should be int
        
        # Act
        result = validate_state(state)
        
        # Assert: State validation fails
        assert result is False

    def test_llm_response_validation_passes_for_valid_response(self):
        """Test that LLM response validation passes for valid responses."""
        # Arrange
        response = {"research_steps": ["step1"], "expert_steps": ["step1"]}
        expected_fields = ["research_steps", "expert_steps"]
        
        # Act
        result = validate_llm_response(response, expected_fields, "planner")
        
        # Assert: Response validation passes
        assert result is True

    def test_llm_response_validation_fails_for_missing_fields(self):
        """Test that LLM response validation fails for missing required fields."""
        # Arrange
        response = {"research_steps": ["step1"]}  # Missing expert_steps
        expected_fields = ["research_steps", "expert_steps"]
        
        # Act
        result = validate_llm_response(response, expected_fields, "planner")
        
        # Assert: Response validation fails
        assert result is False

    def test_llm_response_validation_fails_for_invalid_type(self):
        """Test that LLM response validation fails for invalid response type."""
        # Arrange
        response = "not_a_dict"
        expected_fields = ["research_steps", "expert_steps"]
        
        # Act
        result = validate_llm_response(response, expected_fields, "planner")
        
        # Assert: Response validation fails
        assert result is False

    def test_handle_agent_error_sets_error_state(self, empty_graph_state):
        """Test that handle_agent_error properly sets error state."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)  # Initialize all required fields
        error = Exception("Test error")
        
        # Act
        result = handle_agent_error(state, "test_component", error)
        
        # Assert: Error state is set
        assert result["error"] == "test_component failed: Test error"
        assert result["error_component"] == "test_component"
        assert result["retry_count"] == 1  # Should be incremented

    def test_handle_agent_error_routes_to_finalizer_on_retry_limit(self, empty_graph_state):
        """Test that handle_agent_error routes to finalizer when retry limit exceeded."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)  # Initialize all required fields
        state["retry_count"] = 5  # At retry limit
        error = Exception("Test error")
        
        # Act
        result = handle_agent_error(state, "test_component", error)
        
        # Assert: Routes to finalizer
        assert result["next_step"] == "finalizer"
        assert "error" in result["final_answer"]
        assert "error" in result["final_reasoning_trace"]

    def test_planner_logs_start_and_completion(self, empty_graph_state):
        """Test that planner logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["step1"],
                "expert_steps": ["step1"]
            }
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                planner(state)
                
                # Assert: Appropriate log messages are generated
                mock_logger.info.assert_any_call("Planner starting execution")
                mock_logger.info.assert_any_call("Planner completed successfully")

    def test_planner_handles_llm_failure(self, empty_graph_state):
        """Test that planner handles LLM failures gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("LLM failure")
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act: Should not raise exception, should handle gracefully
                result = planner(state)
                
                # Assert: Error state is set and logged
                assert result["error"] is not None
                assert "planner" in result["error"]
                assert result["error_component"] == "planner"
                mock_logger.error.assert_called()
                
                # Assert: Error is handled gracefully
                mock_logger.error.assert_called_with("Error in planner: LLM failure | Current step: input")
                assert result["error"] == "planner failed: LLM failure"
                assert result["error_component"] == "planner"

    def test_researcher_logs_start_and_completion(self, empty_graph_state):
        """Test that researcher logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["current_research_index"] = 0
        state["research_steps"] = ["Research step"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "step_index": 0,
                "result": "Research result"
            }
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                researcher_node(state)
                
                # Assert: Appropriate log messages are generated
                mock_logger.info.assert_any_call("Researcher starting execution for step 0")
                mock_logger.info.assert_any_call("Researcher completed successfully for step 0")

    def test_expert_logs_start_and_completion(self, empty_graph_state):
        """Test that expert logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                expert(state)
                
                # Assert: Appropriate log messages are generated
                mock_logger.info.assert_any_call("Expert starting execution")
                mock_logger.info.assert_any_call("Expert completed successfully")

    def test_critic_logs_start_and_completion(self, empty_graph_state):
        """Test that critic logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good plan"
            }
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                critic(state)
                
                # Assert: Appropriate log messages are generated
                mock_logger.info.assert_any_call("Critic starting execution for step: critic_planner")
                mock_logger.info.assert_any_call("Critic completed successfully for step: critic_planner")

    def test_finalizer_logs_start_and_completion(self, empty_graph_state):
        """Test that finalizer logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Final answer",
                "final_reasoning_trace": "Final reasoning"
            }
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                finalizer(state)
                
                # Assert: Appropriate log messages are generated
                mock_logger.info.assert_any_call("Finalizer starting execution")
                mock_logger.info.assert_any_call("Finalizer completed successfully")

    def test_input_interface_logs_start_and_completion(self, empty_graph_state):
        """Test that input interface logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        
        with patch('multi_agent_system.logger') as mock_logger:
            # Act
            input_interface(state)
            
            # Assert: Appropriate log messages are generated
            mock_logger.info.assert_any_call("Input interface starting execution")
            mock_logger.info.assert_any_call("Input interface completed successfully")

    def test_input_interface_initializes_error_fields(self, empty_graph_state):
        """Test that input interface initializes error fields to None."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        
        # Act
        result = input_interface(state)
        
        # Assert: Error fields are initialized to None
        assert result["error"] is None
        assert result["error_component"] is None

    def test_tool_error_logging(self):
        """Test that tool errors are properly logged."""
        with patch('multi_agent_system.logger') as mock_logger:
            # Test calculator tool error logging
            from multi_agent_system import calculator
            result = calculator("invalid_expression")

            # Assert: Error is logged - check for any calculator error message
            mock_logger.error.assert_called()
            # Get the actual call arguments to verify it's a calculator error
            call_args = mock_logger.error.call_args[0][0]
            assert "Calculator failed:" in call_args

    def test_orchestrator_validates_state_after_steps(self, empty_graph_state):
        """Test that orchestrator validates state after each step."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        state["current_step"] = "planner"
        
        with patch('multi_agent_system.validate_state') as mock_validate:
            mock_validate.return_value = False  # Simulate validation failure
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                orchestrator(state)
                
                # Assert: State validation is called and warning is logged
                mock_validate.assert_called()
                mock_logger.warning.assert_called_with("State validation failed in orchestrator")

    def test_agent_error_handling_with_network_errors(self, empty_graph_state):
        """Test that network errors are handled differently from other errors."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        network_error = Exception("Network timeout")
        
        # Act
        result = handle_agent_error(state, "test_component", network_error)
        
        # Assert: Network errors don't increment retry count
        assert result["retry_count"] == 0  # Should not increment for network errors

    def test_agent_error_handling_with_validation_errors(self, empty_graph_state):
        """Test that validation errors increment retry count."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="test question")]
        state = input_interface(state)
        validation_error = ValueError("Invalid response structure")
        
        # Act
        result = handle_agent_error(state, "test_component", validation_error)
        
        # Assert: Validation errors increment retry count
        assert result["retry_count"] == 1  # Should increment for validation errors 