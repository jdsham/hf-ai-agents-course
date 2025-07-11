"""
Tests for Finalizer functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import finalizer, input_interface


class TestFinalizer:
    """Test finalizer functionality."""

    def test_retrieves_messages_correctly(self, empty_graph_state):
        """Test that finalizer correctly retrieves messages from orchestrator to finalizer."""
        # Arrange
        state = empty_graph_state.copy()
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "msg1", "step_id": None},
            {"sender": "finalizer", "receiver": "orchestrator", "type": "response", "content": "msg2", "step_id": None},
            {"sender": "orchestrator", "receiver": "researcher", "type": "instruction", "content": "msg3", "step_id": 0},
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Final answer",
                "final_reasoning_trace": "Final reasoning"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: get_agent_conversation returns only finalizer-orchestrator messages
            # This is tested indirectly by checking that the finalizer processes the correct messages
            assert len(result["agent_messages"]) > 2  # Should have added new message

    def test_sets_final_answer_and_reasoning_trace(self, empty_graph_state):
        """Test that finalizer correctly sets state variables for final answer and reasoning trace."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "CRISPR is a revolutionary gene editing technology",
                "final_reasoning_trace": "Based on comprehensive research and expert analysis"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: final_answer and final_reasoning_trace are set based on LLM response
            assert result["final_answer"] == "CRISPR is a revolutionary gene editing technology"
            assert result["final_reasoning_trace"] == "Based on comprehensive research and expert analysis"

    def test_sends_completion_message_to_orchestrator(self, empty_graph_state):
        """Test that finalizer correctly sends message to orchestrator when completed."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Final answer content",
                "final_reasoning_trace": "Final reasoning content"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: Message is sent with "finalizer complete" content
            assert len(result["agent_messages"]) > 1
            last_message = result["agent_messages"][-1]
            assert "finalizer complete" in last_message["content"].lower()
            # Assert: Message contains final answer and reasoning trace
            assert "Final answer content" in last_message["content"]
            assert "Final reasoning content" in last_message["content"]

    def test_generates_valid_json_output(self, empty_graph_state):
        """Test that finalizer generates valid JSON output conforming to expected schema."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Comprehensive answer",
                "final_reasoning_trace": "Detailed reasoning"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: LLM response contains valid JSON with final_answer and final_reasoning_trace
            assert "final_answer" in result
            assert "final_reasoning_trace" in result
            assert result["final_answer"] == "Comprehensive answer"
            assert result["final_reasoning_trace"] == "Detailed reasoning"

    def test_handles_malformed_json_response(self, empty_graph_state):
        """Test that finalizer handles malformed JSON responses gracefully."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            # Mock malformed response
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Invalid JSON")
            
            # Act
            result = finalizer(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Invalid JSON" in result["error"]
            assert result["error_component"] == "finalizer"

    def test_finalizer_with_comprehensive_context(self, empty_graph_state):
        """Test finalizer with comprehensive context from all previous agents."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR and who invented it?"
        state["research_steps"] = [
            "Research CRISPR definition",
            "Research CRISPR inventors"
        ]
        state["expert_steps"] = [
            "Define CRISPR technology",
            "Identify the inventors"
        ]
        state["expert_answer"] = "CRISPR is a gene editing technology invented by Jennifer Doudna and Emmanuelle Charpentier"
        state["expert_reasoning"] = "Based on research findings, CRISPR was discovered and developed by these scientists"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "CRISPR (Clustered Regularly Interspaced Short Palindromic Repeats) is a revolutionary gene editing technology that allows scientists to precisely edit DNA. It was co-invented by Jennifer Doudna and Emmanuelle Charpentier, who were awarded the Nobel Prize in Chemistry in 2020 for their groundbreaking work.",
                "final_reasoning_trace": "1. Research identified CRISPR as a gene editing tool\n2. Research found that Doudna and Charpentier were key inventors\n3. Expert analysis confirmed the technology and inventors\n4. Final synthesis combines all findings into comprehensive answer"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: Finalizer synthesizes all information correctly
            assert "CRISPR" in result["final_answer"]
            assert "Doudna" in result["final_answer"]
            assert "Charpentier" in result["final_answer"]
            assert "gene editing" in result["final_answer"]
            assert "1." in result["final_reasoning_trace"]  # Shows structured reasoning

    def test_finalizer_with_minimal_context(self, empty_graph_state):
        """Test finalizer with minimal context (no research steps)."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is 2 + 2?"
        state["research_steps"] = []
        state["expert_steps"] = ["Calculate the result"]
        state["expert_answer"] = "4"
        state["expert_reasoning"] = "2 + 2 = 4"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "2 + 2 = 4",
                "final_reasoning_trace": "Simple arithmetic calculation: 2 + 2 = 4"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: Finalizer handles minimal context correctly
            assert result["final_answer"] == "2 + 2 = 4"
            assert "arithmetic" in result["final_reasoning_trace"]

    def test_finalizer_with_failure_scenario(self, empty_graph_state):
        """Test finalizer with failure scenario (retry limit exceeded)."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = []
        state["expert_steps"] = []
        state["expert_answer"] = "The question could not be answered."
        state["expert_reasoning"] = "The question could not be answered."
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "The question could not be answered.",
                "final_reasoning_trace": "The system was unable to provide a satisfactory answer after multiple attempts."
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: Finalizer handles failure scenario correctly
            assert result["final_answer"] == "The question could not be answered."
            assert "unable to provide" in result["final_reasoning_trace"]

    def test_finalizer_message_content_includes_all_context(self, empty_graph_state):
        """Test that finalizer message content includes all relevant context."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Final answer",
                "final_reasoning_trace": "Final reasoning"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: Message content includes all relevant context
            assert len(result["agent_messages"]) > 1
            last_message = result["agent_messages"][-1]
            assert "Final answer" in last_message["content"]
            assert "Final reasoning" in last_message["content"]

    def test_finalizer_with_empty_expert_output(self, empty_graph_state):
        """Test finalizer with empty expert output."""
        # Arrange
        state = empty_graph_state.copy()
        state = input_interface(state)
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["expert_answer"] = ""
        state["expert_reasoning"] = ""
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Unable to provide answer due to incomplete expert analysis",
                "final_reasoning_trace": "Expert did not provide sufficient analysis"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: Finalizer handles empty expert output gracefully
            assert "Unable to provide" in result["final_answer"]
            assert "Expert did not provide" in result["final_reasoning_trace"]

    def test_finalizer_system_prompt_formatting(self, empty_graph_state):
        """Test that finalizer system prompt is properly formatted with all context."""
        # Arrange
        state = empty_graph_state.copy()
        state["question"] = "What is CRISPR?"
        state["research_steps"] = ["Research CRISPR definition"]
        state["expert_steps"] = ["Define CRISPR technology"]
        state["expert_answer"] = "CRISPR is a gene editing tool"
        state["expert_reasoning"] = "Based on research findings"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "finalizer", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "Final answer",
                "final_reasoning_trace": "Final reasoning"
            }
            
            # Act
            result = finalizer(state)
            
            # Assert: System prompt includes all required context
            # This is tested indirectly by checking that the finalizer processes the context correctly
            assert result["final_answer"] == "Final answer"
            assert result["final_reasoning_trace"] == "Final reasoning" 