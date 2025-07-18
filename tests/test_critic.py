"""
Tests for Critic functionality as specified in unit_tests.md
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import critic, input_interface


class TestCritic:
    """Test critic functionality."""

    def test_sets_critic_decision_and_feedback(self, empty_graph_state, mocker):
        """Test that critic sets critic_*_decision and critic_*_feedback based on LLM response."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Good work"
        }
        
        # Act
        result = critic(state)
        
        # Assert: critic_*_decision and critic_*_feedback are set based on LLM response
        assert result["critic_planner_decision"] == "approve"
        assert result["critic_planner_feedback"] == "Good work"

    def test_updates_correct_critic_state_based_on_work_type(self, empty_graph_state, mocker):
        """Test that critic updates correct critic state variables based on work type."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "reject",
            "feedback": "Need more detail"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Correct critic state variables are updated based on work type
        assert result["critic_researcher_decision"] == "reject"
        assert result["critic_researcher_feedback"] == "Need more detail"

    def test_handles_expert_criticism(self, empty_graph_state, mocker):
        """Test that critic handles expert criticism correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Excellent analysis"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Correct critic state variables are updated based on work type
        assert result["critic_expert_decision"] == "approve"
        assert result["critic_expert_feedback"] == "Excellent analysis"

    def test_processes_only_latest_orchestrator_message(self, empty_graph_state, mocker):
        """Test that critic processes only the most recent orchestrator message."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "old", "step_id": None},
            {"sender": "critic_planner", "receiver": "orchestrator", "type": "response", "content": "old response", "step_id": None},
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "latest", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Good work"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Only the most recent orchestrator message is processed
        assert result["critic_planner_decision"] == "approve"
        assert result["critic_planner_feedback"] == "Good work"

    def test_sends_completion_message_to_orchestrator(self, empty_graph_state, mocker):
        """Test that critic sends message correctly to orchestrator that criticism is done."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Good work"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Message sender matches critic type (critic_planner, critic_researcher, critic_expert)
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert last_message["sender"] == "critic_planner"

    def test_generates_valid_json_output(self, empty_graph_state, mocker):
        """Test that critic generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "reject",
            "feedback": "Need improvement"
        }
        
        # Act
        result = critic(state)
        
        # Assert: LLM response contains valid JSON with decision and feedback
        assert "decision" in result
        assert "feedback" in result
        assert result["critic_planner_decision"] == "reject"
        assert result["critic_planner_feedback"] == "Need improvement"

    def test_handles_malformed_json_response(self, empty_graph_state, mocker):
        """Test that critic handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        # Mock malformed response
        mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Invalid JSON")
        
        # Act
        result = critic(state)
        # Assert: Error state is set
        assert result["error"] is not None
        assert "Invalid JSON" in result["error"]
        assert result["error_component"] == "critic"

    def test_critic_planner_reviews_plan(self, empty_graph_state, mocker):
        """Test that critic_planner reviews plan correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["research_steps"] = ["Step 1", "Step 2"]
        state["expert_steps"] = ["Expert 1", "Expert 2"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Good plan"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Critic reviews plan correctly
        assert result["critic_planner_decision"] == "approve"
        assert result["critic_planner_feedback"] == "Good plan"

    def test_critic_researcher_reviews_research(self, empty_graph_state, mocker):
        """Test that critic_researcher reviews research correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["research_results"] = ["Research result 1", "Research result 2"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "reject",
            "feedback": "Need more research"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Critic reviews research correctly
        assert result["critic_researcher_decision"] == "reject"
        assert result["critic_researcher_feedback"] == "Need more research"

    def test_critic_expert_reviews_expert_work(self, empty_graph_state, mocker):
        """Test that critic_expert reviews expert work correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["expert_answer"] = "Expert answer"
        state["expert_reasoning"] = "Expert reasoning"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Excellent analysis"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Critic reviews expert work correctly
        assert result["critic_expert_decision"] == "approve"
        assert result["critic_expert_feedback"] == "Excellent analysis"

    def test_critic_message_content_includes_decision_and_feedback(self, empty_graph_state, mocker):
        """Test that critic message content includes the decision and feedback."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "decision": "approve",
            "feedback": "Good work"
        }
        
        # Act
        result = critic(state)
        
        # Assert: Message content includes decision and feedback
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "approve" in last_message["content"]
        assert "Good work" in last_message["content"]

    def test_critic_handles_llm_failure(self, empty_graph_state, mocker):
        """Test that critic handles LLM failures gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_critic')
        mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("LLM failure")
        
        # Act
        result = critic(state)
        # Assert: Error state is set
        assert result["error"] is not None
        assert "LLM failure" in result["error"]
        assert result["error_component"] == "critic" 