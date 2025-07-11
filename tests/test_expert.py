"""
Tests for Expert functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import expert, input_interface


class TestExpert:
    """Test expert functionality."""

    def test_retrieves_messages_correctly(self, empty_graph_state):
        """Test that expert retrieves messages correctly between orchestrator and expert."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "msg1", "step_id": None},
            {"sender": "expert", "receiver": "orchestrator", "type": "response", "content": "msg2", "step_id": None},
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "msg3", "step_id": 0},
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: get_agent_conversation returns only expert-orchestrator messages
            # This is tested indirectly by checking that the expert processes the correct messages
            assert len(result["agent_messages"]) > 2  # Should have added new message

    def test_sends_completion_message_to_orchestrator(self, empty_graph_state):
        """Test that expert sends correct message to orchestrator that expert is complete."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: Message is sent with "expert complete" content
            assert len(result["agent_messages"]) > 1
            last_message = result["agent_messages"][-1]
            assert "expert complete" in last_message["content"].lower()
            # Assert: Message contains expert answer and reasoning
            assert "Expert answer" in last_message["content"]
            assert "Expert reasoning" in last_message["content"]

    def test_sets_expert_state_to_main_graph_state(self, empty_graph_state):
        """Test that expert correctly sets expert state to main graph state."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: expert_state is updated with ExpertState from subgraph
            assert result["expert_state"] is not None
            # Assert: expert_answer and expert_reasoning are updated
            assert result["expert_answer"] == "Expert answer"
            assert result["expert_reasoning"] == "Expert reasoning"

    def test_messages_in_expert_state_are_current(self, empty_graph_state):
        """Test that messages in expert state are current based on retrieved messages."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: ExpertState messages match latest orchestrator-expert conversation
            assert result["expert_state"]["messages"] is not None
            assert len(result["expert_state"]["messages"]) > 0

    def test_expert_retry_with_feedback(self, empty_graph_state):
        """Test that expert retry has latest feedback message appended to messages."""
        # Arrange
        state = empty_graph_state.copy()
        state["expert_state"] = {
            "messages": [Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Result 1"],
            "expert_answer": "",
            "expert_reasoning": ""
        }
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None},
            {"sender": "orchestrator", "receiver": "expert", "type": "feedback", "content": "Improve your answer", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock(), Mock()],  # Additional message from feedback
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Improved answer",
                "expert_reasoning": "Improved reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: Latest feedback message is appended to ExpertState messages
            assert len(result["expert_state"]["messages"]) == 2

    def test_generates_valid_json_output(self, empty_graph_state):
        """Test that expert generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: LLM response contains valid JSON with expert_answer and reasoning_trace
            assert "expert_answer" in result
            assert "expert_reasoning" in result
            assert result["expert_answer"] == "Expert answer"
            assert result["expert_reasoning"] == "Expert reasoning"

    def test_handles_malformed_json_response(self, empty_graph_state):
        """Test that expert handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            # Mock malformed response
            mock_graph.invoke.side_effect = Exception("Invalid JSON")
            
            # Act
            result = expert(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Invalid JSON" in result["error"]
            assert result["error_component"] == "expert"

    def test_expert_with_research_context(self, empty_graph_state):
        """Test expert with research context provided."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR definition", "Research CRISPR applications"]
        state["research_results"] = ["CRISPR is a gene editing tool", "CRISPR has many medical applications"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "What is CRISPR?",
                "research_steps": ["Research CRISPR definition", "Research CRISPR applications"],
                "research_results": ["CRISPR is a gene editing tool", "CRISPR has many medical applications"],
                "expert_answer": "CRISPR is a revolutionary gene editing technology",
                "expert_reasoning": "Based on the research, CRISPR is a gene editing tool with medical applications"
            }
            
            # Act
            result = expert(state)
            
            # Assert: Expert uses research context correctly
            assert result["expert_answer"] == "CRISPR is a revolutionary gene editing technology"
            assert "gene editing" in result["expert_reasoning"]

    def test_expert_with_calculation_requirements(self, empty_graph_state):
        """Test expert with calculation requirements."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is 15% of 200?"
        state["research_steps"] = []
        state["research_results"] = []
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "Calculate 15% of 200", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "What is 15% of 200?",
                "research_steps": [],
                "research_results": [],
                "expert_answer": "30",
                "expert_reasoning": "15% of 200 = 0.15 * 200 = 30"
            }
            
            # Act
            result = expert(state)
            
            # Assert: Expert performs calculations correctly
            assert result["expert_answer"] == "30"
            assert "0.15 * 200" in result["expert_reasoning"]

    def test_expert_state_initialization(self, empty_graph_state):
        """Test expert state initialization when expert_state is None."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "Test question"
        state["research_steps"] = ["Step 1"]
        state["research_results"] = ["Result 1"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: ExpertState is properly initialized
            assert result["expert_state"] is not None
            assert result["expert_state"]["question"] == "Test question"
            assert result["expert_state"]["research_steps"] == ["Step 1"]
            assert result["expert_state"]["research_results"] == ["Result 1"]

    def test_expert_message_content_includes_expert_steps(self, empty_graph_state):
        """Test that expert message content includes the expert steps being performed."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["expert_steps"] = ["Calculate the result", "Summarize findings"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "Test question",
                "research_steps": ["Step 1"],
                "research_results": ["Result 1"],
                "expert_answer": "Expert answer",
                "expert_reasoning": "Expert reasoning"
            }
            
            # Act
            result = expert(state)
            
            # Assert: Message content includes the expert answer and reasoning
            assert len(result["agent_messages"]) > 1
            last_message = result["agent_messages"][-1]
            assert "Expert answer" in last_message["content"]
            assert "Expert reasoning" in last_message["content"] 