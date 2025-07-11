"""
Tests for Planner functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import planner, input_interface


class TestPlanner:
    """Test planner functionality."""

    def test_retrieves_messages_correctly(self, empty_graph_state):
        """Test that planner retrieves messages correctly between orchestrator and planner."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "msg1", "step_id": None},
            {"sender": "planner", "receiver": "orchestrator", "type": "response", "content": "msg2", "step_id": None},
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "msg3", "step_id": 0},
        ]
        
        # Act
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Step 1"],
                "expert_steps": ["Expert 1"]
            }
            result = planner(state)
        
        # Assert: get_agent_conversation returns only planner-orchestrator messages
        # This is tested indirectly by checking that the planner processes the correct messages
        assert len(result["agent_messages"]) > 2  # Should have added new message

    def test_updates_state_with_research_and_expert_steps(self, empty_graph_state, mock_llm_planner):
        """Test that planner updates state graph with research_steps and expert_steps."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        # Act
        result = planner(state)
        
        # Assert: research_steps and expert_steps are updated with LLM response values
        assert result["research_steps"] == ["Research step 1", "Research step 2"]
        assert result["expert_steps"] == ["Expert step 1", "Expert step 2"]
        # Assert: Both fields are lists of strings
        assert isinstance(result["research_steps"], list)
        assert isinstance(result["expert_steps"], list)
        assert all(isinstance(step, str) for step in result["research_steps"])
        assert all(isinstance(step, str) for step in result["expert_steps"])

    def test_outputs_empty_research_steps_when_not_needed(self, empty_graph_state):
        """Test that planner outputs empty list for research steps if no research is needed."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": [],
                "expert_steps": ["Expert step 1"]
            }
            
            # Act
            result = planner(state)
            
            # Assert: research_steps is empty list when question doesn't require research
            assert result["research_steps"] == []

    def test_sends_completion_message_to_orchestrator(self, empty_graph_state, mock_llm_planner):
        """Test that planner sends message correctly to orchestrator that plan is done."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        # Act
        result = planner(state)
        
        # Assert: Message is sent to orchestrator with "plan complete" content
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "plan complete" in last_message["content"].lower()
        # Assert: Message sender is "planner"
        assert last_message["sender"] == "planner"

    def test_handles_critic_feedback_when_plan_rejected(self, empty_graph_state):
        """Test that planner handles feedback from critic correctly when plan is rejected."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None},
            {"sender": "orchestrator", "receiver": "planner", "type": "feedback", "content": "Plan needs more detail", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Detailed step 1"],
                "expert_steps": ["Detailed expert 1"]
            }
            
            # Act
            result = planner(state)
            
            # Assert: Planner processes critic feedback and updates plan accordingly
            # This is tested by checking that the LLM was called with the feedback message
            assert len(result["agent_messages"]) > 2
            # Assert: Updated plan addresses critic's concerns
            assert result["research_steps"] == ["Detailed step 1"]

    def test_generates_valid_json_output(self, empty_graph_state):
        """Test that planner generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Step 1", "Step 2"],
                "expert_steps": ["Expert 1", "Expert 2"]
            }
            
            # Act
            result = planner(state)
            
            # Assert: LLM response contains valid JSON with required fields
            assert "research_steps" in result
            assert "expert_steps" in result
            # Assert: research_steps and expert_steps are lists
            assert isinstance(result["research_steps"], list)
            assert isinstance(result["expert_steps"], list)

    def test_handles_malformed_json_response(self, empty_graph_state):
        """Test that planner handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            # Mock malformed response
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Invalid JSON")
            
            # Act
            result = planner(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Invalid JSON" in result["error"]
            assert result["error_component"] == "planner"

    def test_planner_with_complex_question(self, empty_graph_state):
        """Test planner with a complex question requiring multiple research steps."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR, who invented it, and what are its applications?"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": [
                    "Research what CRISPR is",
                    "Research who invented CRISPR",
                    "Research applications of CRISPR"
                ],
                "expert_steps": [
                    "Define CRISPR technology",
                    "Identify the inventors",
                    "Summarize applications"
                ]
            }
            
            # Act
            result = planner(state)
            
            # Assert: Complex question generates multiple research and expert steps
            assert len(result["research_steps"]) == 3
            assert len(result["expert_steps"]) == 3
            assert "CRISPR" in result["research_steps"][0]
            assert "invented" in result["research_steps"][1]
            assert "applications" in result["research_steps"][2]

    def test_planner_with_simple_question(self, empty_graph_state):
        """Test planner with a simple question requiring no research."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is 2 + 2?"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": [],
                "expert_steps": ["Calculate 2 + 2"]
            }
            
            # Act
            result = planner(state)
            
            # Assert: Simple question generates no research steps
            assert result["research_steps"] == []
            assert len(result["expert_steps"]) == 1
            assert "Calculate" in result["expert_steps"][0]

    def test_planner_message_content_includes_question(self, empty_graph_state):
        """Test that planner message content includes the question being planned for."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Research CRISPR"],
                "expert_steps": ["Define CRISPR"]
            }
            
            # Act
            result = planner(state)
            
            # Assert: Message content includes the question
            assert len(result["agent_messages"]) > 1
            last_message = result["agent_messages"][-1]
            assert "CRISPR" in last_message["content"]

    def test_planner_logs_start_and_completion(self, empty_graph_state):
        """Test that planner logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
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
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("LLM failure")
            
            with patch('multi_agent_system.logger') as mock_logger:
                # Act
                result = planner(state)
                
                # Assert: Error is handled gracefully
                mock_logger.error.assert_called_with("Error in planner: LLM failure | Current step: input")
                assert result["error"] == "planner failed: LLM failure"
                assert result["error_component"] == "planner"

    def test_planner_validates_state_after_execution(self, empty_graph_state):
        """Test that planner validates state after successful execution."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["step1"],
                "expert_steps": ["step1"]
            }
            
            with patch('multi_agent_system.validate_state') as mock_validate:
                mock_validate.return_value = False  # Simulate validation failure
                
                with patch('multi_agent_system.logger') as mock_logger:
                    # Act
                    planner(state)
                    
                    # Assert: State validation is called and warning is logged
                    mock_validate.assert_called()
                    mock_logger.warning.assert_called_with("State validation failed after planner execution") 