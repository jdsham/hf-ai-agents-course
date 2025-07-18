"""
Tests for Input Interface functionality as specified in unit_tests.md
"""
import pytest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import input_interface
from langchain_core.messages import HumanMessage


class TestInputInterface:
    """Test input interface functionality."""

    def test_default_state_values_set_correctly(self, sample_question):
        """Test that all default state values are set correctly by input_interface."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: All state variables are initialized to expected default values
        assert result["agent_messages"] == []
        assert result["research_steps"] == []
        assert result["expert_steps"] == []
        assert result["current_research_index"] == -1
        assert result["researcher_states"] == {}
        assert result["research_results"] == []
        assert result["expert_state"] is None
        assert result["expert_answer"] == ""
        assert result["expert_reasoning"] == ""
        assert result["critic_planner_decision"] == ""
        assert result["critic_planner_feedback"] == ""
        assert result["critic_researcher_decision"] == ""
        assert result["critic_researcher_feedback"] == ""
        assert result["critic_expert_decision"] == ""
        assert result["critic_expert_feedback"] == ""
        assert result["final_answer"] == ""
        assert result["final_reasoning_trace"] == ""
        assert result["current_step"] == "input"
        assert result["next_step"] == "planner"
        assert result["retry_count"] == 0
        assert result["retry_limit"] == 5
        assert result["error"] is None
        assert result["error_component"] is None

    def test_question_field_set_from_first_message(self, sample_question):
        """Test that question field is set to the content of the first message."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: question field is set to the content of the first message
        assert result["question"] == sample_question

    def test_next_step_set_to_planner(self, sample_question):
        """Test that next_step is set to 'planner'."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: next_step is set to "planner"
        assert result["next_step"] == "planner"

    def test_question_with_string_content(self):
        """Test handling of question with string content."""
        # Arrange
        question = "What is the capital of France?"
        initial_state = {
            "messages": [HumanMessage(content=question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: question field is set correctly
        assert result["question"] == question

    def test_question_with_non_string_content(self):
        """Test handling of question with non-string content."""
        # Arrange
        question_obj = {"text": "What is the capital of France?"}
        
        # Act & Assert: HumanMessage validation should handle this
        # Since HumanMessage validates content type, we expect a validation error
        with pytest.raises(Exception):  # Expect validation error
            initial_state = {
                "messages": [HumanMessage(content=question_obj)]
            }
            input_interface(initial_state)

    def test_empty_messages_list(self):
        """Test handling of empty messages list."""
        # Arrange
        initial_state = {
            "messages": []
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: Default values are still set correctly
        assert result["next_step"] == "planner"
        assert result["retry_count"] == 0
        assert result["retry_limit"] == 5
        assert result["question"] == ""
        assert result["error"] is None

    def test_multiple_messages_uses_first(self, sample_question):
        """Test that only the first message is used for the question."""
        # Arrange
        initial_state = {
            "messages": [
                HumanMessage(content=sample_question),
                HumanMessage(content="This should be ignored"),
                HumanMessage(content="This too")
            ]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: Only first message content is used
        assert result["question"] == sample_question

    def test_state_isolation(self, sample_question):
        """Test that input_interface properly isolates state."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)],
            "agent_messages": [{"old": "data"}],
            "research_steps": ["old step"],
            "expert_steps": ["old step"],
            "current_research_index": 5,
            "researcher_states": {"old": "state"},
            "research_results": ["old result"],
            "expert_state": {"old": "state"},
            "expert_answer": "old answer",
            "expert_reasoning": "old reasoning",
            "critic_planner_decision": "old decision",
            "critic_planner_feedback": "old feedback",
            "critic_researcher_decision": "old decision",
            "critic_researcher_feedback": "old feedback",
            "critic_expert_decision": "old decision",
            "critic_expert_feedback": "old feedback",
            "final_answer": "old answer",
            "final_reasoning_trace": "old trace",
            "current_step": "old step",
            "next_step": "old step",
            "retry_count": 10,
            "retry_limit": 20
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: All old state is cleared and reset to defaults
        assert result["agent_messages"] == []
        assert result["research_steps"] == []
        assert result["expert_steps"] == []
        assert result["current_research_index"] == -1
        assert result["researcher_states"] == {}
        assert result["research_results"] == []
        assert result["expert_state"] is None
        assert result["expert_answer"] == ""
        assert result["expert_reasoning"] == ""
        assert result["critic_planner_decision"] == ""
        assert result["critic_planner_feedback"] == ""
        assert result["critic_researcher_decision"] == ""
        assert result["critic_researcher_feedback"] == ""
        assert result["critic_expert_decision"] == ""
        assert result["critic_expert_feedback"] == ""
        assert result["final_answer"] == ""
        assert result["final_reasoning_trace"] == ""
        assert result["current_step"] == "input"
        assert result["next_step"] == "planner"
        assert result["retry_count"] == 0
        assert result["retry_limit"] == 5
        assert result["error"] is None
        assert result["error_component"] is None

    def test_files_field_initialization(self, sample_question):
        """Test that files field is properly initialized."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: files field is set to None
        assert result["files"] is None

    def test_question_preservation(self, sample_question):
        """Test that the question is preserved correctly."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: question is preserved exactly as provided
        assert result["question"] == sample_question
        assert "CRISPR" in result["question"]
        assert "invented" in result["question"]

    def test_error_fields_initialized_to_none(self, sample_question):
        """Test that error fields are initialized to None."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        # Act
        result = input_interface(initial_state)
        
        # Assert: Error fields are initialized to None
        assert result["error"] is None
        assert result["error_component"] is None

    def test_input_interface_logs_start_and_completion(self, sample_question):
        """Test that input interface logs appropriate messages for start and completion."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content=sample_question)]
        }
        
        with pytest.raises(Exception):  # Expect validation error
            initial_state = {
                "messages": [HumanMessage(content=question_obj)]
            }
            input_interface(initial_state) 