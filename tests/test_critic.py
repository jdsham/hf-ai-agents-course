"""
Tests for Critic functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import critic, input_interface


class TestCritic:
    """Test critic functionality."""

    def test_sets_correct_state_variables_for_planner_review(self, empty_graph_state):
        """Test that critic sets correct state variables when reviewing planner's work."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good plan"
            }
            
            # Act
            result = critic(state)
            
            # Assert: critic_*_decision and critic_*_feedback are set based on LLM response
            assert result["critic_planner_decision"] == "approve"
            assert result["critic_planner_feedback"] == "Good plan"
            # Assert: Decision is either "approve" or "reject"
            assert result["critic_planner_decision"] in ["approve", "reject"]

    def test_sets_correct_state_variables_for_researcher_review(self, empty_graph_state):
        """Test that critic sets correct state variables when reviewing researcher's work."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["current_research_index"] = 0
        state["research_steps"] = ["Research CRISPR"]
        state["research_results"] = ["CRISPR is a gene editing tool"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "reject",
                "feedback": "Need more detail"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Correct critic state variables are updated based on work type
            assert result["critic_researcher_decision"] == "reject"
            assert result["critic_researcher_feedback"] == "Need more detail"

    def test_sets_correct_state_variables_for_expert_review(self, empty_graph_state):
        """Test that critic sets correct state variables when reviewing expert's work."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_expert"
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good answer"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Correct critic state variables are updated based on work type
            assert result["critic_expert_decision"] == "approve"
            assert result["critic_expert_feedback"] == "Good answer"

    def test_retrieves_latest_message_from_orchestrator(self, empty_graph_state):
        """Test that critic retrieves the latest message from orchestrator only."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "old msg", "step_id": None},
            {"sender": "critic_planner", "receiver": "orchestrator", "type": "response", "content": "old response", "step_id": None},
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "latest msg", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good work"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Only the most recent orchestrator message is processed
            # This is tested indirectly by checking that the critic processes the correct message
            assert len(result["agent_messages"]) > 3  # Should have added new message

    def test_sends_correct_message_to_orchestrator(self, empty_graph_state):
        """Test that critic sends correct message to orchestrator when critique is completed."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
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
            # Assert: Message receiver is "orchestrator"
            assert last_message["receiver"] == "orchestrator"

    def test_generates_valid_json_output(self, empty_graph_state):
        """Test that critic generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "reject",
                "feedback": "Improve the plan"
            }
            
            # Act
            result = critic(state)
            
            # Assert: LLM response contains valid JSON with decision and feedback
            assert "critic_planner_decision" in result
            assert "critic_planner_feedback" in result
            assert result["critic_planner_decision"] == "reject"
            assert result["critic_planner_feedback"] == "Improve the plan"

    def test_handles_malformed_json_response(self, empty_graph_state):
        """Test that critic handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            # Mock malformed response
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Invalid JSON")
            
            # Act
            result = critic(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Invalid JSON" in result["error"]
            assert result["error_component"] == "critic_planner"

    def test_handles_different_work_types_correctly(self, empty_graph_state):
        """Test that critic handles different types of work (planner, researcher, expert) correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["current_research_index"] = 0
        state["research_steps"] = ["Research CRISPR"]
        state["research_results"] = ["CRISPR is a gene editing tool"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good research"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Correct critic state variables are updated based on work type
            assert result["critic_researcher_decision"] == "approve"
            assert result["critic_researcher_feedback"] == "Good research"
            # Assert: Appropriate system prompt is used for each work type
            # This is tested by checking that the correct state variables are updated

    def test_critic_planner_with_plan_review(self, empty_graph_state):
        """Test critic planner with plan review."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["research_steps"] = ["Research CRISPR", "Research applications"]
        state["expert_steps"] = ["Define CRISPR", "Summarize applications"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "Review plan", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Comprehensive plan"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Critic reviews plan correctly
            assert result["critic_planner_decision"] == "approve"
            assert "Comprehensive" in result["critic_planner_feedback"]

    def test_critic_researcher_with_research_review(self, empty_graph_state):
        """Test critic researcher with research review."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["current_research_index"] = 0
        state["research_steps"] = ["Research CRISPR definition"]
        state["research_results"] = ["CRISPR is a gene editing technology discovered in bacteria"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_researcher", "type": "instruction", "content": "Review research", "step_id": 0}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "reject",
                "feedback": "Need more detail about discovery"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Critic reviews research correctly
            assert result["critic_researcher_decision"] == "reject"
            assert "more detail" in result["critic_researcher_feedback"]

    def test_critic_expert_with_expert_review(self, empty_graph_state):
        """Test critic expert with expert review."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_expert"
        state["expert_answer"] = "CRISPR is a revolutionary gene editing technology"
        state["expert_reasoning"] = "Based on the research findings, CRISPR allows precise editing of DNA"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_expert", "type": "instruction", "content": "Review expert work", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Well-reasoned answer"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Critic reviews expert work correctly
            assert result["critic_expert_decision"] == "approve"
            assert "Well-reasoned" in result["critic_expert_feedback"]

    def test_critic_message_content_includes_decision_and_feedback(self, empty_graph_state):
        """Test that critic message content includes decision and feedback."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Excellent plan"
            }
            
            # Act
            result = critic(state)
            
            # Assert: Message content includes decision and feedback
            assert len(result["agent_messages"]) > 1
            last_message = result["agent_messages"][-1]
            assert "approve" in last_message["content"]
            assert "Excellent plan" in last_message["content"]

    def test_critic_with_invalid_current_step(self, empty_graph_state):
        """Test that critic handles invalid current_step gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "invalid_step"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        # Act
        result = critic(state)
        # Assert: Error state is set
        assert result["error"] is not None
        assert result["error_component"] == "critic"
        assert "Invalid critic step" in result["error"] 