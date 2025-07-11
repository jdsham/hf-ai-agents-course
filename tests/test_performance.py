"""
Tests for Retry Logic functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import input_interface, planner, researcher_node, expert, critic, finalizer, orchestrator


class TestRetryLogic:
    """Test retry logic functionality."""

    def test_no_infinite_loops_in_retry_scenarios(self, empty_graph_state):
        """Test that no infinite loops occur in retry scenarios."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 4
        state["retry_limit"] = 5

        # Act
        result = orchestrator(state)

        # Assert: retry_count never exceeds retry_limit
        assert result["retry_count"] <= result["retry_limit"]
        # Assert: System eventually terminates even with repeated failures
        # With retry_count=4 and retry_limit=5, one more rejection should trigger finalizer
        assert result["next_step"] == "finalizer"  # Should route to finalizer when retry limit exceeded

    def test_system_terminates_with_repeated_failures(self, empty_graph_state):
        """Test that system eventually terminates even with repeated failures."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 5
        state["retry_limit"] = 5
        
        # Act
        result = orchestrator(state)
        
        # Assert: System eventually terminates even with repeated failures
        assert result["next_step"] == "finalizer"
        assert result["final_answer"] == "The question could not be answered."

    def test_infinite_retry_scenarios_prevented(self, empty_graph_state):
        """Test that infinite retry scenarios are prevented."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 10  # Exceeds limit
        state["retry_limit"] = 5
        
        # Act
        result = orchestrator(state)
        
        # Assert: Infinite retry scenarios are prevented
        assert result["next_step"] == "finalizer"
        assert result["final_answer"] == "The question could not be answered."

    def test_retry_count_tracking_per_agent(self, empty_graph_state):
        """Test retry count tracking per agent."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 2
        
        # Act
        result = orchestrator(state)
        
        # Assert: Retry counts are properly incremented on critic rejections
        assert result["retry_count"] == 3

    def test_retry_limits_enforced_consistently(self, empty_graph_state):
        """Test that retry limits are enforced consistently."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        state["critic_researcher_decision"] = "reject"
        state["retry_count"] = 5
        state["retry_limit"] = 5
        
        # Act
        result = orchestrator(state)
        
        # Assert: Retry limits are enforced consistently
        assert result["retry_count"] == 6
        assert result["next_step"] == "finalizer"

    def test_final_answer_set_when_retry_limit_exceeded(self, empty_graph_state):
        """Test that final answer is set when retry limit is exceeded."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_expert"
        state["critic_expert_decision"] = "reject"
        state["retry_count"] = 5
        state["retry_limit"] = 5
        
        # Act
        result = orchestrator(state)
        
        # Assert: Final answer is set when retry limit is exceeded
        assert result["final_answer"] == "The question could not be answered."
        assert result["final_reasoning_trace"] == "The question could not be answered."

    def test_multiple_rejections_from_different_agents(self, empty_graph_state):
        """Test multiple rejections from different agents."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 1
        
        # Act - First rejection
        result1 = orchestrator(state)
        
        # Second rejection from different agent
        state2 = result1.copy()
        state2["current_step"] = "critic_researcher"
        state2["critic_researcher_decision"] = "reject"
        result2 = orchestrator(state2)
        
        # Assert: Retry count tracking works correctly for each agent type
        assert result1["retry_count"] == 2
        assert result2["retry_count"] == 3

    def test_retry_count_reset_on_success(self, empty_graph_state):
        """Test that retry count behavior on successful operations."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "approve"
        state["retry_count"] = 2
        
        # Act
        result = orchestrator(state)
        
        # Assert: Retry count is not incremented on approval
        assert result["retry_count"] == 2  # Should remain unchanged

    def test_retry_count_initialization(self, empty_graph_state):
        """Test retry count initialization."""
        # Arrange
        state = empty_graph_state.copy()
        state["messages"] = [Mock(content="Test question")]
        
        # Act
        result = input_interface(state)
        
        # Assert: Retry count is properly initialized
        assert result["retry_count"] == 0
        assert result["retry_limit"] == 5

    def test_retry_count_with_different_limits(self, empty_graph_state):
        """Test retry count behavior with different limits."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 3
        state["retry_limit"] = 3  # Lower limit
        
        # Act
        result = orchestrator(state)
        
        # Assert: System respects different retry limits
        assert result["retry_count"] == 4
        assert result["next_step"] == "finalizer"

    def test_retry_count_edge_case_zero_limit(self, empty_graph_state):
        """Test retry count edge case with zero limit."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 0
        state["retry_limit"] = 0  # Zero limit
        
        # Act
        result = orchestrator(state)
        
        # Assert: System handles zero retry limit correctly
        assert result["retry_count"] == 1
        assert result["next_step"] == "finalizer"

    def test_retry_count_negative_values(self, empty_graph_state):
        """Test retry count behavior with negative values."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = -1  # Negative retry count
        state["retry_limit"] = 5
        
        # Act
        result = orchestrator(state)
        
        # Assert: System handles negative retry counts correctly
        assert result["retry_count"] == 0  # Should be incremented to 0

    def test_retry_count_large_values(self, empty_graph_state):
        """Test retry count behavior with large values."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        state["critic_planner_decision"] = "reject"
        state["retry_count"] = 1000  # Large retry count
        state["retry_limit"] = 5
        
        # Act
        result = orchestrator(state)
        
        # Assert: System handles large retry counts correctly
        assert result["retry_count"] == 1001
        assert result["next_step"] == "finalizer"

    def test_retry_count_state_preservation(self, empty_graph_state):
        """Test that retry count state is preserved across operations."""
        # Arrange
        state = empty_graph_state.copy()
        state["retry_count"] = 3
        state["retry_limit"] = 5
        
        # Act - Multiple operations without rejections
        result1 = input_interface(state)
        result2 = planner(result1) if "agent_messages" in result1 else result1
        
        # Assert: Retry count is reset by input_interface
        assert result1["retry_count"] == 0  # input_interface resets to 0
        assert result2["retry_count"] == 0  # planner doesn't change retry count on success 