"""
Tests for Orchestrator functionality as specified in unit_tests.md
Updated to reflect the new simplified 4-step orchestrator design
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import orchestrator, determine_next_step, check_retry_limit, execute_next_step, input_interface


class TestOrchestrator:
    """Test orchestrator functionality following the 4-step process."""

    def test_orchestrator_follows_4_step_process(self, empty_graph_state):
        """Test that orchestrator follows the 4-step process: determine, check, execute, return."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = orchestrator(state)
        
        # Assert: Step 1 - next_step is determined
        assert result["next_step"] == "critic_planner"
        # Assert: Step 3 - current_step is set to next_step
        assert result["current_step"] == "critic_planner"
        # Assert: Step 3 - message is sent
        assert len(result["agent_messages"]) > 0
        # Assert: Step 4 - state is returned
        assert result is not None

    def test_step1_determine_next_step_function(self, empty_graph_state):
        """Test Step 1: Determine the next step based on current step and critic decisions."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        
        # Act
        result = determine_next_step(state)
        
        # Assert: next_step is determined based on critic decision
        assert result["next_step"] == "planner"
        assert result["retry_count"] == 1

    def test_step2_check_retry_limit_function(self, empty_graph_state):
        """Test Step 2: Check retry count and handle limit exceeded."""
        # Arrange
        state = empty_graph_state.copy()
        state["retry_count"] = 5
        state["retry_limit"] = 5
        state["next_step"] = "planner"
        
        # Act
        result = check_retry_limit(state)
        
        # Assert: retry limit exceeded sets finalizer
        assert result["next_step"] == "finalizer"
        assert result["final_answer"] == "The question could not be answered."
        assert result["final_reasoning_trace"] == "The question could not be answered."

    def test_step2_check_retry_limit_below_limit(self, empty_graph_state):
        """Test Step 2: Check retry count when below limit."""
        # Arrange
        state = empty_graph_state.copy()
        state["retry_count"] = 3
        state["retry_limit"] = 5
        state["next_step"] = "planner"
        
        # Act
        result = check_retry_limit(state)
        
        # Assert: next_step remains unchanged when retry_count < retry_limit
        assert result["next_step"] == "planner"

    def test_step3_execute_next_step_function(self, empty_graph_state):
        """Test Step 3: Execute the next step by setting current_step and sending message."""
        # Arrange
        state = empty_graph_state.copy()
        state["next_step"] = "planner"
        
        # Act
        result = execute_next_step(state)
        
        # Assert: current_step is updated to match next_step
        assert result["current_step"] == "planner"
        # Assert: message is sent
        assert len(result["agent_messages"]) > 0
        message = result["agent_messages"][-1]
        assert message["receiver"] == "planner"
        assert message["sender"] == "orchestrator"

    def test_critic_rejection_sets_agent_as_next_step(self, empty_graph_state):
        """Test that when critic rejects, next_step is set to the rejected agent."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["critic_planner_feedback"] = "Plan needs improvement"
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to the rejected agent's name
        assert result["next_step"] == "planner"
        # Assert: retry_count is incremented by 1
        assert result["retry_count"] == 1

    def test_critic_approval_sets_next_agent_in_workflow(self, empty_graph_state):
        """Test that when critic accepts, next_step is set to next agent in workflow."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "approve"
        state["research_steps"] = ["Research step 1", "Research step 2"]
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to the next agent in workflow sequence
        assert result["next_step"] == "researcher"

    def test_research_next_step_remains_researcher_if_more_steps(self, empty_graph_state):
        """Test that for research, next_step remains 'researcher' if more research steps exist."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["critic_researcher_decision"] = "approve"
        state["research_steps"] = ["Step 1", "Step 2", "Step 3"]
        state["current_research_index"] = 0  # Only completed first step
        
        # Act
        result = orchestrator(state)
        
        # Assert: For research, next_step remains "researcher" if more research steps exist
        assert result["next_step"] == "researcher"

    def test_research_next_step_becomes_expert_if_all_complete(self, empty_graph_state):
        """Test that for research, next_step becomes 'expert' if all research steps complete."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["critic_researcher_decision"] = "approve"
        state["research_steps"] = ["Step 1", "Step 2"]
        state["current_research_index"] = 1  # Completed all steps
        
        # Act
        result = orchestrator(state)
        
        # Assert: For research, next_step becomes "expert" if all research steps complete
        assert result["next_step"] == "expert"

    def test_no_research_steps_skip_researcher_and_critic(self, empty_graph_state):
        """Test that if no research steps present, skip researcher and critic_researcher."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "approve"
        state["research_steps"] = []  # No research steps
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step goes directly from "planner" to "expert" when research_steps is empty
        assert result["next_step"] == "expert"

    def test_planner_current_step_sets_critic_planner_next(self, empty_graph_state):
        """Test that when planner is current_step, critic_planner is set as next_step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to "critic_planner" when current_step is "planner"
        assert result["next_step"] == "critic_planner"

    def test_researcher_current_step_sets_critic_researcher_next(self, empty_graph_state):
        """Test that when researcher is current_step, critic_researcher is set as next_step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "researcher"
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to "critic_researcher" when current_step is "researcher"
        assert result["next_step"] == "critic_researcher"

    def test_expert_current_step_sets_critic_expert_next(self, empty_graph_state):
        """Test that when expert is current_step, critic_expert is set as next_step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "expert"
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to "critic_expert" when current_step is "expert"
        assert result["next_step"] == "critic_expert"

    def test_critic_planner_approval_resets_research_state(self, empty_graph_state):
        """Test that critic planner approval resets research_results and researcher_states."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "approve"
        state["research_steps"] = ["Research step 1", "Research step 2"]
        state["research_results"] = ["old result"]
        state["researcher_states"] = {"old": "state"}
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to "researcher" when research steps exist
        assert result["next_step"] == "researcher"
        # Assert: research state is reset
        assert result["research_results"] == []
        assert result["researcher_states"] == {}

    def test_orchestrator_sends_message_to_current_step_agent(self, empty_graph_state):
        """Test that orchestrator sends message to agent set in current_step."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "planner"
        
        # Act
        result = orchestrator(state)
        
        # Assert: Message is added to agent_messages with correct receiver matching current_step
        assert len(result["agent_messages"]) > 0
        message = result["agent_messages"][-1]
        assert message["receiver"] == "critic_planner"  # orchestrator routes to critic after planner

    def test_critic_rejection_sends_feedback_message(self, empty_graph_state):
        """Test that critic rejection sends feedback message to criticized agent."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["critic_planner_feedback"] = "Plan needs improvement"
        
        # Act
        result = orchestrator(state)
        
        # Assert: Message content contains the critic feedback
        assert len(result["agent_messages"]) > 0
        message = result["agent_messages"][-1]
        assert "Plan needs improvement" in message["content"]
        # Assert: Message receiver is the agent that was criticized
        assert message["receiver"] == "planner"

    def test_researcher_message_step_id_matches_current_index(self, empty_graph_state):
        """Test that researcher message step_id matches current_research_index."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "researcher"
        state["current_research_index"] = 2
        state["research_steps"] = ["Step 1", "Step 2", "Step 3"]
        
        # Act
        result = orchestrator(state)
        
        # Assert: Message step_id matches current_research_index
        assert len(result["agent_messages"]) > 0
        message = result["agent_messages"][-1]
        assert message["step_id"] == 2

    def test_researcher_message_content_references_correct_step(self, empty_graph_state):
        """Test that researcher message content references the correct research step."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "researcher"
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1", "Research CRISPR", "Step 3"]

        # Act
        result = orchestrator(state)

        # Assert: Message content references the correct research step
        assert len(result["agent_messages"]) > 0
        message = result["agent_messages"][-1]
        # When current_step is researcher, it should send a message to critic_researcher
        assert message["receiver"] == "critic_researcher"
        assert "research results" in message["content"].lower()

    def test_message_contains_all_required_fields(self, empty_graph_state):
        """Test that messages contain all required fields."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = orchestrator(state)
        
        # Assert: All required fields are present and have correct types
        assert len(result["agent_messages"]) > 0
        message = result["agent_messages"][-1]
        assert "sender" in message
        assert "receiver" in message
        assert "type" in message
        assert "content" in message
        assert "step_id" in message
        # Assert: step_id is None for non-research messages
        assert message["step_id"] is None

    def test_research_index_increments_on_critic_approval(self, empty_graph_state):
        """Test that current_research_index increments by 1 when critic approves."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["critic_researcher_decision"] = "approve"
        state["current_research_index"] = 0
        state["research_steps"] = ["Step 1", "Step 2"]
        
        # Act
        result = orchestrator(state)
        
        # Assert: current_research_index increments by 1 when critic approves
        assert result["current_research_index"] == 1

    def test_research_index_remains_same_on_critic_rejection(self, empty_graph_state):
        """Test that current_research_index remains same when critic rejects."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["critic_researcher_decision"] = "reject"
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1", "Step 2"]
        
        # Act
        result = orchestrator(state)
        
        # Assert: current_research_index remains same when critic rejects
        assert result["current_research_index"] == 1

    def test_research_index_unchanged_for_non_researcher(self, empty_graph_state):
        """Test that current_research_index remains unchanged when not calling researcher."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        state["current_research_index"] = 2
        
        # Act
        result = orchestrator(state)
        
        # Assert: current_research_index remains unchanged when current_step is not "researcher"
        assert result["current_research_index"] == 2

    def test_all_research_steps_completed_handling(self, empty_graph_state):
        """Test handling when all research steps are completed."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["critic_researcher_decision"] = "approve"
        state["research_steps"] = ["Step 1", "Step 2"]
        state["current_research_index"] = 1  # Completed all steps
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to "expert" when current_research_index >= len(research_steps)
        assert result["next_step"] == "expert"

    def test_retry_count_increments_on_critic_rejection(self, empty_graph_state):
        """Test that retry_count increases by 1 after critic rejection."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 2
        
        # Act
        result = orchestrator(state)
        
        # Assert: retry_count increases by 1 after critic rejection
        assert result["retry_count"] == 3

    def test_retry_limit_exceeded_sets_finalizer(self, empty_graph_state):
        """Test that retry limit exceeded sets finalizer as next step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 5  # At retry limit
        
        # Act
        result = orchestrator(state)
        
        # Assert: next_step is set to "finalizer" when retry_count >= retry_limit
        assert result["next_step"] == "finalizer"

    def test_retry_limit_exceeded_sets_failure_answer(self, empty_graph_state):
        """Test that retry limit exceeded sets failure answer."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 5  # At retry limit
        
        # Act
        result = orchestrator(state)
        
        # Assert: final_answer is set to "The question could not be answered." when retry limit exceeded
        assert result["final_answer"] == "The question could not be answered."

    def test_retry_count_tracking_per_agent(self, empty_graph_state):
        """Test that retry count tracking works correctly for each agent type."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 0
        
        # Act
        result = orchestrator(state)
        
        # Assert: Retry count tracking works correctly for each agent type
        assert result["retry_count"] == 1

    def test_orchestrator_detects_error_state_and_routes_to_finalizer(self, empty_graph_state):
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

    def test_orchestrator_validates_state_after_steps(self, empty_graph_state, mocker):
        """Test that orchestrator validates state after each step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        mock_validate = mocker.patch('multi_agent_system.validate_state')
        mock_validate.return_value = False  # Simulate validation failure
        
        mock_logger = mocker.patch('multi_agent_system.logger')
        
        # Act
        orchestrator(state)
        
        # Assert: State validation is called and warning is logged
        mock_validate.assert_called()
        mock_logger.warning.assert_called_with("State validation failed in orchestrator")

    def test_orchestrator_logs_start_and_completion(self, empty_graph_state, mocker):
        """Test that orchestrator logs appropriate messages for start and completion."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        mock_logger = mocker.patch('multi_agent_system.logger')
        
        # Act
        orchestrator(state)
        
        # Assert: Appropriate log messages are generated
        mock_logger.info.assert_any_call("Orchestrator starting execution. Current step: planner")
        mock_logger.info.assert_any_call("Orchestrator completed successfully. Next step: critic_planner")

    def test_orchestrator_handles_exceptions_gracefully(self, empty_graph_state, mocker):
        """Test that orchestrator handles exceptions gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "planner"
        
        mock_determine = mocker.patch('multi_agent_system.determine_next_step')
        mock_determine.side_effect = Exception("Test exception")
        
        mock_logger = mocker.patch('multi_agent_system.logger')
        
        # Act
        result = orchestrator(state)
        
        # Assert: Exception is caught and logged
        mock_logger.error.assert_called_with("Error in orchestrator: Test exception | Current step: planner")
        assert result["error"] == "orchestrator failed: Test exception"
        assert result["error_component"] == "orchestrator" 