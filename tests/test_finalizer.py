"""
Tests for Finalizer functionality as specified in unit_tests.md
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import finalizer, input_interface


class TestFinalizer:
    """Test finalizer functionality."""

    def test_sets_final_answer_and_reasoning(self, empty_graph_state, mocker):
        """Test that finalizer sets final_answer and final_reasoning_trace based on LLM response."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "Final answer",
            "final_reasoning_trace": "Final reasoning trace"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: final_answer and final_reasoning_trace are set based on LLM response
        assert result["final_answer"] == "Final answer"
        assert result["final_reasoning_trace"] == "Final reasoning trace"

    def test_finalizer_with_complete_workflow(self, empty_graph_state, mocker):
        """Test finalizer with complete workflow data."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR and who invented it?"
        state["research_steps"] = ["Research CRISPR definition", "Research CRISPR inventors"]
        state["research_results"] = ["CRISPR is a gene editing tool", "CRISPR was invented by Doudna and Charpentier"]
        state["expert_answer"] = "CRISPR is a revolutionary gene editing technology"
        state["expert_reasoning"] = "Based on the research, CRISPR allows precise DNA editing"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "CRISPR is a revolutionary gene editing technology",
            "final_reasoning_trace": "Based on comprehensive research and expert analysis"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer uses all available context
        assert result["final_answer"] == "CRISPR is a revolutionary gene editing technology"
        assert "comprehensive research" in result["final_reasoning_trace"]

    def test_generates_valid_json_output(self, empty_graph_state, mocker):
        """Test that finalizer generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "Final answer content",
            "final_reasoning_trace": "Final reasoning trace content"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: LLM response contains valid JSON with required fields
        assert "final_answer" in result
        assert "final_reasoning_trace" in result
        # Assert: final_answer and final_reasoning_trace are strings
        assert isinstance(result["final_answer"], str)
        assert isinstance(result["final_reasoning_trace"], str)

    def test_finalizer_with_partial_data(self, empty_graph_state, mocker):
        """Test finalizer with partial workflow data."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["research_results"] = ["CRISPR is a gene editing tool"]
        # No expert_answer or expert_reasoning
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "Comprehensive answer",
            "final_reasoning_trace": "Based on available research"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer handles partial data gracefully
        assert result["final_answer"] == "Comprehensive answer"
        assert "available research" in result["final_reasoning_trace"]

    def test_handles_malformed_json_response(self, empty_graph_state, mocker):
        """Test that finalizer handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        # Mock malformed response
        mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Invalid JSON")
        
        # Act
        result = finalizer(state)
        # Assert: Error state is set
        assert result["error"] is not None
        assert "Invalid JSON" in result["error"]
        assert result["error_component"] == "finalizer"

    def test_finalizer_with_complex_question(self, empty_graph_state, mocker):
        """Test finalizer with a complex question requiring comprehensive analysis."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR, who invented it, and what are its applications?"
        state["research_steps"] = ["Research CRISPR definition", "Research inventors", "Research applications"]
        state["research_results"] = [
            "CRISPR is a gene editing technology",
            "CRISPR was co-invented by Doudna and Charpentier",
            "CRISPR has applications in medicine, agriculture, and research"
        ]
        state["expert_answer"] = "CRISPR (Clustered Regularly Interspaced Short Palindromic Repeats) is a revolutionary gene editing technology that allows scientists to precisely edit DNA. It was co-invented by Jennifer Doudna and Emmanuelle Charpentier, who were awarded the Nobel Prize in Chemistry in 2020 for their groundbreaking work.",
        state["expert_reasoning"] = "Based on comprehensive research, CRISPR represents a breakthrough in genetic engineering with wide-ranging applications."
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "CRISPR (Clustered Regularly Interspaced Short Palindromic Repeats) is a revolutionary gene editing technology that allows scientists to precisely edit DNA. It was co-invented by Jennifer Doudna and Emmanuelle Charpentier, who were awarded the Nobel Prize in Chemistry in 2020 for their groundbreaking work.",
            "final_reasoning_trace": "Based on comprehensive research and expert analysis, CRISPR represents a breakthrough in genetic engineering with applications across multiple fields."
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer handles complex questions correctly
        assert "CRISPR" in result["final_answer"]
        assert "Doudna" in result["final_answer"]
        assert "Charpentier" in result["final_answer"]
        assert "Nobel Prize" in result["final_answer"]

    def test_finalizer_with_simple_question(self, empty_graph_state, mocker):
        """Test finalizer with a simple question requiring minimal analysis."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is 2 + 2?"
        state["research_steps"] = []
        state["research_results"] = []
        state["expert_answer"] = "2 + 2 = 4"
        state["expert_reasoning"] = "Basic arithmetic calculation"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "2 + 2 = 4",
            "final_reasoning_trace": "Simple arithmetic calculation"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer handles simple questions correctly
        assert result["final_answer"] == "2 + 2 = 4"
        assert "arithmetic" in result["final_reasoning_trace"]

    def test_finalizer_with_error_state(self, empty_graph_state, mocker):
        """Test finalizer when system is in error state."""
        # Arrange
        state = empty_graph_state.copy()
        state["error"] = "planner failed: Test error"
        state["error_component"] = "planner"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "The question could not be answered.",
            "final_reasoning_trace": "The question could not be answered."
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer handles error states correctly
        assert result["final_answer"] == "The question could not be answered."
        assert result["final_reasoning_trace"] == "The question could not be answered."

    def test_finalizer_message_content_includes_final_answer(self, empty_graph_state, mocker):
        """Test that finalizer message content includes the final answer."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "Final answer",
            "final_reasoning_trace": "Final reasoning trace"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Message content includes the final answer
        assert len(result["agent_messages"]) > 1
        last_message = result["agent_messages"][-1]
        assert "Final answer" in last_message["content"]

    def test_finalizer_with_incomplete_expert_analysis(self, empty_graph_state, mocker):
        """Test finalizer when expert analysis is incomplete."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["research_results"] = ["CRISPR is a gene editing tool"]
        state["expert_answer"] = ""  # Incomplete expert analysis
        state["expert_reasoning"] = ""
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "Unable to provide answer due to incomplete expert analysis",
            "final_reasoning_trace": "Expert analysis was not completed"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer handles incomplete expert analysis
        assert "incomplete" in result["final_answer"]
        assert "expert analysis" in result["final_reasoning_trace"]

    def test_finalizer_with_retry_limit_exceeded(self, empty_graph_state, mocker):
        """Test finalizer when retry limit has been exceeded."""
        # Arrange
        state = empty_graph_state.copy()
        state["retry_count"] = 5
        state["retry_limit"] = 5
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        mock_llm = mocker.patch('multi_agent_system.llm_finalizer')
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            "final_answer": "Final answer",
            "final_reasoning_trace": "Final reasoning trace"
        }
        
        # Act
        result = finalizer(state)
        
        # Assert: Finalizer handles retry limit exceeded
        assert result["final_answer"] == "Final answer"
        assert result["final_reasoning_trace"] == "Final reasoning trace" 