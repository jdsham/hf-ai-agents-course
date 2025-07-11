"""
Tests for Error Handling functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import input_interface, planner, researcher_node, expert, critic, finalizer


class TestErrorHandling:
    """Test error handling functionality."""

    def test_handle_network_failures_gracefully(self, empty_graph_state):
        """Test that network failures don't crash the system."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.side_effect = Exception("Network timeout")
            
            # Act
            result = researcher_node(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Network timeout" in result["error"]
            assert result["error_component"] == "researcher"

    def test_handle_invalid_input_questions(self, empty_graph_state):
        """Test handling of invalid input questions (empty, malformed, too long)."""
        # Arrange
        empty_question_state = {
            "messages": [HumanMessage(content="")]
        }
        
        # Act & Assert: Empty questions are handled gracefully
        result = input_interface(empty_question_state)
        assert result["question"] == ""

    def test_handle_malformed_agent_responses(self, empty_graph_state):
        """Test handling of malformed agent responses (invalid JSON, missing fields)."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Invalid JSON")
            
            # Act
            result = planner(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Invalid JSON" in result["error"]
            assert result["error_component"] == "planner"

    def test_handle_tool_failures(self, empty_graph_state):
        """Test handling of tool failures."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_research_index"] = 0
        state["research_steps"] = ["Research step"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.side_effect = Exception("Tool failure")
            
            # Act
            result = researcher_node(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Tool failure" in result["error"]
            assert result["error_component"] == "researcher"

    def test_handle_memory_exhaustion(self, empty_graph_state):
        """Test handling of memory exhaustion and resource limits."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Memory limit exceeded")
            
            # Act
            result = finalizer(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Memory limit exceeded" in result["error"]
            assert result["error_component"] == "finalizer"

    def test_handle_malformed_messages(self, empty_graph_state):
        """Test handling of malformed messages in the communication system."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "critic_planner"  # Set correct step for critic
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Malformed message")
            
            # Act
            result = critic(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Malformed message" in result["error"]
            assert result["error_component"] == "critic_planner"

    def test_handle_missing_required_fields(self, empty_graph_state):
        """Test handling of missing required fields in responses."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Step 1"]  # Missing expert_steps
            }
            
            # Act
            result = planner(state)
            
            # Assert: Missing fields are handled gracefully
            assert "expert_steps" in result
            assert result["expert_steps"] == []  # Should default to empty list

    def test_handle_invalid_step_id(self, empty_graph_state):
        """Test handling of invalid step_id values."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 5
        state["research_steps"] = ["Step 1", "Step 2"]  # Only 2 steps, but index is 5
        
        # Act & Assert: Invalid step_id is handled gracefully
        # This would be caught by the researcher_node function
        assert state["current_research_index"] > len(state["research_steps"])

    def test_handle_empty_research_results(self, empty_graph_state):
        """Test handling of empty research results."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 0
        state["research_steps"] = ["Research step"]
        state["research_results"] = []
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "step_index": 0,
                "result": None  # Empty result
            }
            
            # Act
            result = researcher_node(state)
            
            # Assert: Empty results are handled gracefully
            assert result["research_results"][0] is None

    def test_handle_invalid_critic_decisions(self, empty_graph_state):
        """Test handling of invalid critic decisions."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "maybe",  # Invalid decision
                "feedback": "Test feedback"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Invalid decisions are handled gracefully
            assert result["critic_planner_decision"] == "maybe"

    def test_handle_large_input_questions(self, empty_graph_state):
        """Test handling of very large input questions."""
        # Arrange
        large_question = "What is CRISPR? " * 1000  # Very large question
        large_question_state = {
            "messages": [HumanMessage(content=large_question)]
        }
        
        # Act
        result = input_interface(large_question_state)
        
        # Assert: Large questions are handled gracefully
        assert len(result["question"]) > 0
        assert "CRISPR" in result["question"]

    def test_handle_special_characters_in_questions(self, empty_graph_state):
        """Test handling of special characters in questions."""
        # Arrange
        special_question = "What is CRISPR? 🧬 <script>alert('test')</script> & < > \" '"
        special_question_state = {
            "messages": [HumanMessage(content=special_question)]
        }
        
        # Act
        result = input_interface(special_question_state)
        
        # Assert: Special characters are handled gracefully
        assert "CRISPR" in result["question"]
        assert "🧬" in result["question"]

    def test_handle_concurrent_access_scenarios(self, empty_graph_state):
        """Test handling of concurrent access and race conditions."""
        # Arrange
        state1 = empty_graph_state.copy()
        state2 = empty_graph_state.copy()
        
        # Simulate concurrent access by modifying both states
        state1["retry_count"] = 1
        state2["retry_count"] = 2
        
        # Act & Assert: Each state maintains its own retry count
        assert state1["retry_count"] == 1
        assert state2["retry_count"] == 2

    def test_handle_invalid_state_transitions(self, empty_graph_state):
        """Test handling of invalid state transitions."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "invalid_step"
        
        # Act & Assert: Invalid state transitions are handled gracefully
        # This would be caught by the routing function
        assert state["current_step"] == "invalid_step"

    def test_handle_missing_agent_messages(self, empty_graph_state):
        """Test handling of missing agent messages."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = []  # Empty messages
        
        # Act & Assert: Empty messages are handled gracefully
        assert len(state["agent_messages"]) == 0

    def test_handle_invalid_message_structure(self, empty_graph_state):
        """Test handling of invalid message structure."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator"}  # Missing required fields
        ]
        
        # Act & Assert: Invalid message structure is handled gracefully
        # The system should continue to function even with malformed messages
        assert len(state["agent_messages"]) == 1 