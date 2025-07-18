"""
Tests for Routing functionality as specified in unit_tests.md
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import route_from_orchestrator, input_interface


class TestRouting:
    """Test routing functionality."""

    def test_routes_planner_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to planner correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for planner
        assert result == "planner"

    def test_routes_researcher_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to researcher correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "researcher"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for researcher
        assert result == "researcher"

    def test_routes_expert_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to expert correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "expert"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for expert
        assert result == "expert"

    def test_routes_critic_planner_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to critic_planner correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_planner"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for critic_planner
        assert result == "critic_planner"

    def test_routes_critic_researcher_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to critic_researcher correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_researcher"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for critic_researcher
        assert result == "critic_researcher"

    def test_routes_critic_expert_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to critic_expert correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "critic_expert"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for critic_expert
        assert result == "critic_expert"

    def test_routes_finalizer_correctly(self, empty_graph_state):
        """Test that route_from_orchestrator routes to finalizer correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "finalizer"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: route_from_orchestrator returns correct node name for finalizer
        assert result == "finalizer"

    def test_routing_all_valid_steps(self, empty_graph_state):
        """Test that route_from_orchestrator handles all valid step values correctly."""
        # Arrange
        valid_steps = ["planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer"]
        
        # Act & Assert: All valid steps return correct routes
        for step in valid_steps:
            state = empty_graph_state.copy()
            state["current_step"] = step
            result = route_from_orchestrator(state)
            assert result == step

    def test_routing_invalid_step_raises_exception(self, empty_graph_state):
        """Test that route_from_orchestrator raises exception for invalid step values."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "invalid_step"
        
        # Act & Assert: Invalid current_step values raise appropriate exceptions
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_empty_current_step_raises_exception(self, empty_graph_state):
        """Test that route_from_orchestrator handles empty current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = ""
        
        # Act & Assert: Edge cases like empty current_step are handled
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_none_current_step_raises_exception(self, empty_graph_state):
        """Test that route_from_orchestrator handles None current_step correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = None
        
        # Act & Assert: None current_step raises appropriate exception
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_unknown_step_raises_exception(self, empty_graph_state):
        """Test that route_from_orchestrator handles unknown step values correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "unknown_step"
        
        # Act & Assert: Unknown step values raise appropriate exceptions
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_case_sensitive(self, empty_graph_state):
        """Test that route_from_orchestrator is case sensitive."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "PLANNER"  # Wrong case
        
        # Act & Assert: Case sensitivity is maintained
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_with_whitespace(self, empty_graph_state):
        """Test that route_from_orchestrator handles whitespace correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = " planner "  # With whitespace
        
        # Act & Assert: Whitespace is not handled (should raise exception)
        with pytest.raises(ValueError):
            route_from_orchestrator(state)

    def test_routing_critic_consolidation(self, empty_graph_state):
        """Test that all critic steps route to the same critic node."""
        # Arrange
        critic_steps = ["critic_planner", "critic_researcher", "critic_expert"]
        
        # Act & Assert: All critic steps route to critic
        for step in critic_steps:
            state = empty_graph_state.copy()
            state["current_step"] = step
            result = route_from_orchestrator(state)
            assert result == "critic"

    def test_routing_returns_string(self, empty_graph_state):
        """Test that route_from_orchestrator returns a string."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        
        # Act
        result = route_from_orchestrator(state)
        
        # Assert: Function returns a string
        assert isinstance(result, str)

    def test_routing_does_not_modify_state(self, empty_graph_state):
        """Test that route_from_orchestrator does not modify the input state."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_step"] = "planner"
        original_state = state.copy()
        
        # Act
        route_from_orchestrator(state)
        
        # Assert: State is not modified
        assert state == original_state 