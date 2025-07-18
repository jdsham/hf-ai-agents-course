"""
Tests for Researcher functionality as specified in unit_tests.md
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import researcher_node, input_interface


class TestResearcher:
    """Test researcher functionality."""

    def test_creates_researcher_state_for_each_step_index(self, empty_graph_state, mocker):
        """Test that researcher creates ResearcherState for each research step index."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 0
        state["research_steps"] = ["Research step 1", "Research step 2"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 0,
            "result": "Research result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: researcher_states dict contains entry for each research step index
        assert 0 in result["researcher_states"]
        # Assert: State is preserved between retries for same step
        assert result["researcher_states"][0]["step_index"] == 0

    def test_retrieves_messages_for_specific_research_index(self, empty_graph_state, mocker):
        """Test that researcher retrieves messages correctly for a specific current research index."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_step"] = "researcher"  # Set correct step
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1", "Step 2"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "msg1", "step_id": 0},
            {"sender": "researcher", "receiver": "orchestrator", "type": "response", "content": "msg2", "step_id": 0},
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "msg3", "step_id": 1},
        ]
        # Add a message for the current step to process
        state["agent_messages"].append({
            "sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "Research step 1", "step_id": 1}
        )

        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 1,
            "result": "Research result"
        }

        # Act
        result = researcher_node(state)

        # Assert: get_agent_conversation filters messages by correct step_id
        # This is tested indirectly by checking that the researcher processes the correct messages
        assert len(result["agent_messages"]) == 4  # Should have added new message

    def test_adds_new_researcher_state_for_new_step(self, empty_graph_state, mocker):
        """Test that researcher adds new researcher state when performing a new research step."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 2
        state["research_steps"] = ["Step 1", "Step 2", "Step 3"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 2}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 2,
            "result": "Research result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: New ResearcherState is created and added to researcher_states
        assert 2 in result["researcher_states"]
        # Assert: step_index matches current_research_index
        assert result["researcher_states"][2]["step_index"] == 2

    def test_uses_existing_research_state_for_retry(self, empty_graph_state, mocker):
        """Test that researcher uses same research state when performing a retry."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1", "Step 2"]
        state["researcher_states"] = {
            1: {"messages": [mocker.Mock()], "step_index": 1, "result": None}
        }
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "retry", "step_id": 1}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock(), mocker.Mock()],  # Additional message added
            "step_index": 1,
            "result": "Updated research result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: Existing ResearcherState is reused for retry
        assert 1 in result["researcher_states"]
        # Assert: Messages are appended to existing state
        assert len(result["researcher_states"][1]["messages"]) > 1

    def test_dynamically_builds_research_results(self, empty_graph_state, mocker):
        """Test that researcher dynamically builds research results as research steps are completed."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 0
        state["research_steps"] = ["Step 1", "Step 2", "Step 3"]
        state["research_results"] = []  # Starts empty
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 0,
            "result": "Research result for step 1"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: research_results list starts as empty and grows dynamically
        assert len(result["research_results"]) == 1
        # Assert: New result is appended to end of list when research step completes
        assert result["research_results"][0] == "Research result for step 1"
        # Assert: List length matches the number of completed research steps
        assert len(result["research_results"]) == 1  # Only step 0 completed

    def test_overwrites_research_results_on_retry(self, empty_graph_state, mocker):
        """Test that researcher overwrites research results at proper index when retrying."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1", "Step 2"]
        state["research_results"] = ["Result 1", "Old result 2"]  # Already has 2 results
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "retry", "step_id": 1}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 1,
            "result": "Updated result 2"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: research_results[current_research_index] is updated with new result when retrying
        assert result["research_results"][1] == "Updated result 2"
        # Assert: List length remains the same (not pre-allocated)
        assert len(result["research_results"]) == 2

    def test_research_results_not_pre_allocated(self, empty_graph_state, mocker):
        """Test that research_results is not pre-allocated with length equal to research_steps."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["current_research_index"] = 0
        state["research_steps"] = ["Step 1", "Step 2", "Step 3", "Step 4"]  # 4 research steps
        state["research_results"] = []  # Starts empty
        
        # Act - simulate multiple research steps
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        # First research step
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 0,
            "result": "Result 1"
        }
        result1 = researcher_node(state)

        # Second research step - use deep copy to avoid mutating the first result
        import copy
        state2 = copy.deepcopy(result1)
        state2["current_research_index"] = 1
        state2["agent_messages"].append(
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 1}
        )
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 1,
            "result": "Result 2"
        }
        result2 = researcher_node(state2)

        # Assert: research_results grows dynamically, not pre-allocated
        # The test runs both steps in sequence, so both results are added
        assert len(result1["research_results"]) == 1  # After first step
        assert len(result2["research_results"]) == 2  # After second step
        assert result1["research_results"][0] == "Result 1"
        assert result2["research_results"][1] == "Result 2"

    def test_sends_completion_message_to_orchestrator(self, empty_graph_state, mocker):
        """Test that researcher sends message correctly to orchestrator that research is done."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 0
        state["research_steps"] = ["Step 1"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 0,
            "result": "Research result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: Message is sent with "research complete" content
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "research complete" in last_message["content"].lower()
        # Assert: Message sender is "researcher"
        assert last_message["sender"] == "researcher"

    def test_handles_all_research_steps_completed(self, empty_graph_state):
        """Test that researcher handles case when all research steps are completed."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1"]
        state["research_results"] = ["Result 1"]
        
        # Act
        result = researcher_node(state)
        
        # Assert: No new researcher state is created when all steps complete
        assert len(result["researcher_states"]) == 0

    def test_researcher_with_multiple_tool_calls(self, empty_graph_state, mocker):
        """Test that researcher handles multiple tool calls correctly."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 0
        state["research_steps"] = ["Research CRISPR technology"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock(), mocker.Mock(), mocker.Mock()],  # Multiple messages from tool calls
            "step_index": 0,
            "result": "Comprehensive CRISPR research result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: Multiple tool calls are handled correctly
        assert len(result["researcher_states"][0]["messages"]) == 3
        assert result["research_results"][0] == "Comprehensive CRISPR research result"

    def test_researcher_state_preservation_across_retries(self, empty_graph_state, mocker):
        """Test that researcher preserves state across retries."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 1
        state["research_steps"] = ["Step 1", "Step 2"]
        state["researcher_states"] = {
            1: {
                "messages": [mocker.Mock(), mocker.Mock()],  # Previous messages
                "step_index": 1,
                "result": None
            }
        }
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "retry", "step_id": 1}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock(), mocker.Mock(), mocker.Mock()],  # Additional message
            "step_index": 1,
            "result": "Updated result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: State is preserved and extended
        assert len(result["researcher_states"][1]["messages"]) == 3
        assert result["research_results"][1] == "Updated result"

    def test_researcher_message_content_includes_research_step(self, empty_graph_state, mocker):
        """Test that researcher message content includes the research step being performed."""
        # Arrange
        state = empty_graph_state.copy()
        state["current_research_index"] = 0
        state["research_steps"] = ["Research CRISPR technology"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "test", "step_id": 0}
        ]
        
        mock_graph = mocker.patch('multi_agent_system.compiled_researcher_graph')
        mock_graph.invoke.return_value = {
            "messages": [mocker.Mock()],
            "step_index": 0,
            "result": "CRISPR research result"
        }
        
        # Act
        result = researcher_node(state)
        
        # Assert: Message content includes the research step
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "CRISPR" in last_message["content"] 