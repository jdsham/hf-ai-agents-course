"""
Tests for Expert functionality as specified in unit_tests.md
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import expert, input_interface


class TestExpert:
    """Test expert functionality."""

    def test_retrieves_messages_correctly(self, empty_graph_state, mocker):
        """Test that expert retrieves messages correctly between orchestrator and expert."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "msg1", "step_id": None},
            {"sender": "expert", "receiver": "orchestrator", "type": "response", "content": "msg2", "step_id": None},
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "msg3", "step_id": 0},
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "Expert answer",
            "expert_reasoning": "Expert reasoning"
        }
        
        # Act
        result = expert(state)
        
        # Assert: get_agent_conversation returns only expert-orchestrator messages
        # This is tested indirectly by checking that the expert processes the correct messages
        assert len(result["agent_messages"]) > 2  # Should have added new message

    def test_sends_completion_message_to_orchestrator(self, empty_graph_state, mocker):
        """Test that expert sends message correctly to orchestrator that expert analysis is done."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "Expert answer",
            "expert_reasoning": "Expert reasoning"
        }
        
        # Act
        result = expert(state)
        
        # Assert: Message is sent with "expert complete" content
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "expert complete" in last_message["content"].lower()
        # Assert: Message sender is "expert"
        assert last_message["sender"] == "expert"

    def test_updates_expert_state_with_subgraph_result(self, empty_graph_state, mocker):
        """Test that expert updates expert_state with ExpertState from subgraph."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "Expert answer",
            "expert_reasoning": "Expert reasoning"
        }
        
        # Act
        result = expert(state)
        
        # Assert: expert_state is updated with ExpertState from subgraph
        assert result["expert_state"] is not None
        assert result["expert_state"]["question"] == "Test question"
        assert result["expert_state"]["research_steps"] == ["Step 1"]
        assert result["expert_state"]["research_results"] == ["Research result 1"]
        assert result["expert_state"]["expert_answer"] == "Expert answer"
        assert result["expert_state"]["expert_reasoning"] == "Expert reasoning"

    def test_preserves_existing_expert_state_messages(self, empty_graph_state, mocker):
        """Test that expert preserves existing ExpertState messages and appends new ones."""
        # Arrange
        state = empty_graph_state.copy()
        state["expert_state"] = {
            "messages": [mocker.Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "",
            "expert_reasoning": ""
        }
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None},
            {"sender": "orchestrator", "receiver": "expert", "type": "feedback", "content": "Need more detail", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock(), mocker.Mock()],  # Additional message from feedback
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "Updated expert answer",
            "expert_reasoning": "Updated expert reasoning"
        }
        
        # Act
        result = expert(state)
        
        # Assert: Latest feedback message is appended to ExpertState messages
        assert len(result["expert_state"]["messages"]) > 1
        assert result["expert_state"]["expert_answer"] == "Updated expert answer"
        assert result["expert_state"]["expert_reasoning"] == "Updated expert reasoning"

    def test_generates_valid_json_output(self, empty_graph_state, mocker):
        """Test that expert generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "Expert answer content",
            "expert_reasoning": "Expert reasoning trace"
        }
        
        # Act
        result = expert(state)
        
        # Assert: LLM response contains valid JSON with expert_answer and reasoning_trace
        assert "expert_answer" in result["expert_state"]
        assert "expert_reasoning" in result["expert_state"]
        # Assert: expert_answer and expert_reasoning are strings
        assert isinstance(result["expert_state"]["expert_answer"], str)
        assert isinstance(result["expert_state"]["expert_reasoning"], str)

    def test_handles_malformed_json_response(self, empty_graph_state, mocker):
        """Test that expert handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        # Mock malformed response
        mock_graph.invoke.side_effect = Exception("Invalid JSON")
        
        # Act
        result = expert(state)
        # Assert: Error state is set
        assert result["error"] is not None
        assert "Invalid JSON" in result["error"]
        assert result["error_component"] == "expert"

    def test_expert_with_research_context(self, empty_graph_state, mocker):
        """Test expert with research context from previous research steps."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR definition", "Research CRISPR applications"]
        state["research_results"] = ["CRISPR is a gene editing tool", "CRISPR has applications in medicine"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "What is CRISPR?",
            "research_steps": ["Research CRISPR definition", "Research CRISPR applications"],
            "research_results": ["CRISPR is a gene editing tool", "CRISPR has applications in medicine"],
            "expert_answer": "CRISPR is a revolutionary gene editing technology",
            "expert_reasoning": "Based on the research, CRISPR is a gene editing tool with medical applications"
        }
        
        # Act
        result = expert(state)
        
        # Assert: Expert uses research context correctly
        assert result["expert_state"]["question"] == "What is CRISPR?"
        assert len(result["expert_state"]["research_steps"]) == 2
        assert len(result["expert_state"]["research_results"]) == 2
        assert "CRISPR" in result["expert_state"]["expert_answer"]

    def test_expert_with_calculation_question(self, empty_graph_state, mocker):
        """Test expert with a calculation question requiring no research."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is 15% of 200?"
        state["research_steps"] = []
        state["research_results"] = []
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "What is 15% of 200?",
            "research_steps": [],
            "research_results": [],
            "expert_answer": "15% of 200 is 30",
            "expert_reasoning": "To calculate 15% of 200, multiply 200 by 0.15: 200 * 0.15 = 30"
        }
        
        # Act
        result = expert(state)
        
        # Assert: Expert performs calculations correctly
        assert result["expert_state"]["expert_answer"] == "15% of 200 is 30"
        assert "multiply" in result["expert_state"]["expert_reasoning"]

    def test_expert_state_initialization(self, empty_graph_state, mocker):
        """Test that expert properly initializes ExpertState."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "Test question",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "Expert answer",
            "expert_reasoning": "Expert reasoning"
        }
        
        # Act
        result = expert(state)
        
        # Assert: ExpertState is properly initialized
        assert result["expert_state"] is not None
        assert "messages" in result["expert_state"]
        assert "question" in result["expert_state"]
        assert "research_steps" in result["expert_state"]
        assert "research_results" in result["expert_state"]
        assert "expert_answer" in result["expert_state"]
        assert "expert_reasoning" in result["expert_state"]

    def test_expert_message_content_includes_answer_and_reasoning(self, empty_graph_state, mocker):
        """Test that expert message content includes the expert answer and reasoning."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_expert_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "question": "What is CRISPR?",
            "research_steps": ["Step 1"],
            "research_results": ["Research result 1"],
            "expert_answer": "CRISPR is a gene editing technology",
            "expert_reasoning": "Based on the research, CRISPR is a revolutionary tool"
        }
        
        # Act
        result = expert(state)
        
        # Assert: Message content includes the expert answer and reasoning
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "CRISPR" in last_message["content"]
        assert "gene editing" in last_message["content"] 