"""
Tests for Routing functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import route_from_orchestrator


class TestRouting:
    """Test routing functionality."""

    def test_routing_planner_current_step(self, empty_graph_state):
        """Test routing logic handles planner current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for planner
        assert result == "planner"

    def test_routing_researcher_current_step(self, empty_graph_state):
        """Test routing logic handles researcher current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "researcher"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for researcher
        assert result == "researcher"

    def test_routing_expert_current_step(self, empty_graph_state):
        """Test routing logic handles expert current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "expert"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for expert
        assert result == "expert"

    def test_routing_critic_planner_current_step(self, empty_graph_state):
        """Test routing logic handles critic_planner current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for critic_planner
        assert result == "critic"

    def test_routing_critic_researcher_current_step(self, empty_graph_state):
        """Test routing logic handles critic_researcher current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for critic_researcher
        assert result == "critic"

    def test_routing_critic_expert_current_step(self, empty_graph_state):
        """Test routing logic handles critic_expert current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_expert"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for critic_expert
        assert result == "critic"

    def test_routing_finalizer_current_step(self, empty_graph_state):
        """Test routing logic handles finalizer current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "finalizer"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for finalizer
        assert result == "finalizer"

    def test_routing_all_valid_current_step_values(self, empty_graph_state):
        """Test routing logic handles all possible current_step values."""
        # Arrange
        valid_steps = ["planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer"]
        expected_routes = ["planner", "researcher", "expert", "critic", "critic", "critic", "finalizer"]
        
        # Act & Assert: All valid current_step values are handled
        for step, expected_route in zip(valid_steps, expected_routes):
            state = empty_graph_state.copy()
            state["current_step"] = step
            result = route_from_orchestrator(state)
            assert result == expected_route

    def test_routing_invalid_current_step_raises_exception(self, empty_graph_state):
        """Test routing logic handles edge cases and invalid states."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "invalid_step"
        
        # Act & Assert: Invalid current_step values raise appropriate exceptions
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_empty_current_step_raises_exception(self, empty_graph_state):
        """Test routing logic handles empty current_step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = ""
        
        # Act & Assert: Edge cases like empty current_step are handled
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_none_current_step_raises_exception(self, empty_graph_state):
        """Test routing logic handles None current_step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = None
        
        # Act & Assert: None current_step raises appropriate exception
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_unknown_step_raises_exception(self, empty_graph_state):
        """Test routing logic handles unknown step values."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "unknown_step"
        
        # Act & Assert: Unknown step values raise appropriate exceptions
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_case_sensitive(self, empty_graph_state):
        """Test routing logic is case sensitive."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "PLANNER"  # Uppercase
        
        # Act & Assert: Case sensitivity is maintained
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_with_whitespace(self, empty_graph_state):
        """Test routing logic handles whitespace in current_step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = " planner "  # With whitespace
        
        # Act & Assert: Whitespace is not handled (should raise exception)
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_critic_consolidation(self, empty_graph_state):
        """Test that all critic types route to the same critic node."""
        # Arrange
        critic_steps = ["critic_planner", "critic_researcher", "critic_expert"]
        
        # Act & Assert: All critic types route to "critic"
        for step in critic_steps:
            state = empty_graph_state.copy()
            state["current_step"] = step
            result = route_from_orchestrator(state)
            assert result == "critic"

    def test_routing_function_returns_string(self, empty_graph_state):
        """Test that routing function returns a string."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: Function returns a string
        assert isinstance(result, str)

    def test_routing_function_preserves_state(self, empty_graph_state):
        """Test that routing function doesn't modify the state."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        original_state = state.copy()
        
        # Act
        route_from_orchestrator(state)
        
        # Assert: State is not modified
        assert state == original_state 