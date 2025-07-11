"""
Tests for Edge Cases functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import input_interface, planner, researcher_node, expert, critic, finalizer


class TestEdgeCases:
    """Test edge cases functionality."""

    def test_verify_system_behavior_with_various_question_types(self):
        """Test system behavior with various question types."""
        # Arrange
        question_types = [
            "What is 2 + 2?",  # Simple calculation
            "What is CRISPR?",  # Scientific concept
            "Who won the 2020 US presidential election?",  # Factual question
            "What are the ethical implications of AI?",  # Philosophical question
            "How do I make a cake?",  # How-to question
            "What is the meaning of life?",  # Abstract question
            "What is the weather like?",  # Current information
            "Can you help me with my homework?",  # Request for help
        ]
        
        # Act & Assert: System handles various question types
        for question in question_types:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question
            assert result["next_step"] == "planner"

    def test_handle_empty_questions(self):
        """Test handling of empty questions."""
        # Arrange
        empty_questions = [
            "",
            "   ",
            "\n\t",
            "?",
        ]
        
        # Act & Assert: Empty questions are handled gracefully
        for question in empty_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_very_long_questions(self):
        """Test handling of very long questions."""
        # Arrange
        long_question = "What is CRISPR technology, who invented it, what are its applications in medicine, what are the ethical implications, how does it work at the molecular level, what are the current limitations, what are the future prospects, and what are the regulatory considerations?" * 10
        
        # Act
        initial_state = {
            "messages": [HumanMessage(content=long_question)]
        }
        result = input_interface(initial_state)
        
        # Assert: Very long questions are handled
        assert len(result["question"]) > 0
        assert "CRISPR" in result["question"]

    def test_handle_questions_with_special_characters(self):
        """Test handling of questions with special characters."""
        # Arrange
        special_questions = [
            "What is CRISPR? 🧬",
            "What is 2 + 2? <script>alert('test')</script>",
            "What is AI? & < > \" '",
            "What is DNA? \n\t\r",
            "What is ML? \u00a0\u200b",  # Non-breaking space and zero-width space
        ]
        
        # Act & Assert: Special characters are handled
        for question in special_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_unicode(self):
        """Test handling of questions with unicode characters."""
        # Arrange
        unicode_questions = [
            "What is CRISPR? 🧬🧪🔬",
            "What is DNA? 脱氧核糖核酸",
            "What is AI? 인공지능",
            "What is ML? машинное обучение",
            "What is NLP? معالجة اللغة الطبيعية",
        ]
        
        # Act & Assert: Unicode characters are handled
        for question in unicode_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_html_tags(self):
        """Test handling of questions with HTML tags."""
        # Arrange
        html_questions = [
            "What is CRISPR? <b>bold</b>",
            "What is DNA? <i>italic</i>",
            "What is AI? <a href='#'>link</a>",
            "What is ML? <div>div</div>",
            "What is NLP? <script>alert('xss')</script>",
        ]
        
        # Act & Assert: HTML tags are handled
        for question in html_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_sql_injection(self):
        """Test handling of questions with SQL injection attempts."""
        # Arrange
        sql_questions = [
            "What is CRISPR?'; DROP TABLE users; --",
            "What is DNA? UNION SELECT * FROM users",
            "What is AI? OR 1=1",
            "What is ML? INSERT INTO users VALUES ('hacker')",
            "What is NLP? UPDATE users SET password='hacked'",
        ]
        
        # Act & Assert: SQL injection attempts are handled
        for question in sql_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_xss_attempts(self):
        """Test handling of questions with XSS attempts."""
        # Arrange
        xss_questions = [
            "What is CRISPR? <script>alert('xss')</script>",
            "What is DNA? <img src=x onerror=alert('xss')>",
            "What is AI? <svg onload=alert('xss')>",
            "What is ML? javascript:alert('xss')",
            "What is NLP? <iframe src=javascript:alert('xss')>",
        ]
        
        # Act & Assert: XSS attempts are handled
        for question in xss_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_command_injection(self):
        """Test handling of questions with command injection attempts."""
        # Arrange
        command_questions = [
            "What is CRISPR? && rm -rf /",
            "What is DNA? | cat /etc/passwd",
            "What is AI? ; ls -la",
            "What is ML? `whoami`",
            "What is NLP? $(id)",
        ]
        
        # Act & Assert: Command injection attempts are handled
        for question in command_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_path_traversal(self):
        """Test handling of questions with path traversal attempts."""
        # Arrange
        path_questions = [
            "What is CRISPR? ../../../etc/passwd",
            "What is DNA? ..\\..\\..\\windows\\system32\\config\\sam",
            "What is AI? %2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "What is ML? ..%252f..%252f..%252fetc%252fpasswd",
            "What is NLP? ..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        ]
        
        # Act & Assert: Path traversal attempts are handled
        for question in path_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_null_bytes(self):
        """Test handling of questions with null bytes."""
        # Arrange
        null_questions = [
            "What is CRISPR?\x00",
            "What is DNA?\x00\x00",
            "What is AI?\x00test\x00",
            "What is ML?\x00\x00\x00",
            "What is NLP?\x00\x00\x00\x00",
        ]
        
        # Act & Assert: Null bytes are handled
        for question in null_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_control_characters(self):
        """Test handling of questions with control characters."""
        # Arrange
        control_questions = [
            "What is CRISPR?\x01\x02\x03",
            "What is DNA?\x04\x05\x06",
            "What is AI?\x07\x08\x09",
            "What is ML?\x0a\x0b\x0c",
            "What is NLP?\x0d\x0e\x0f",
        ]
        
        # Act & Assert: Control characters are handled
        for question in control_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_very_large_numbers(self):
        """Test handling of questions with very large numbers."""
        # Arrange
        large_number_questions = [
            f"What is {2**1000}?",
            f"What is {10**1000}?",
            f"What is {9999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999}?",
            "What is 1" + "0" * 1000 + "?",
            "What is 9" + "9" * 1000 + "?",
        ]
        
        # Act & Assert: Very large numbers are handled
        for question in large_number_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_repeated_characters(self):
        """Test handling of questions with repeated characters."""
        # Arrange
        repeated_questions = [
            "What is CRISPR?" + "A" * 1000,
            "What is DNA?" + "B" * 1000,
            "What is AI?" + "C" * 1000,
            "What is ML?" + "D" * 1000,
            "What is NLP?" + "E" * 1000,
        ]
        
        # Act & Assert: Repeated characters are handled
        for question in repeated_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_malformed_utf8(self):
        """Test handling of questions with malformed UTF-8."""
        # Arrange
        malformed_utf8_questions = [
            "What is CRISPR?\xff\xfe",
            "What is DNA?\xfe\xff",
            "What is AI?\xff\xff\xff",
            "What is ML?\xfe\xfe\xfe",
            "What is NLP?\xff\xfe\xff\xfe",
        ]
        
        # Act & Assert: Malformed UTF-8 is handled
        for question in malformed_utf8_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_whitespace_only(self):
        """Test handling of questions with only whitespace."""
        # Arrange
        whitespace_questions = [
            " ",
            "\t",
            "\n",
            "\r",
            "\f",
            "\v",
            " \t\n\r\f\v ",
        ]
        
        # Act & Assert: Whitespace-only questions are handled
        for question in whitespace_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_only_punctuation(self):
        """Test handling of questions with only punctuation."""
        # Arrange
        punctuation_questions = [
            "?",
            "!",
            ".",
            ",",
            ";",
            ":",
            "?!.,;:",
        ]
        
        # Act & Assert: Punctuation-only questions are handled
        for question in punctuation_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_only_numbers(self):
        """Test handling of questions with only numbers."""
        # Arrange
        number_questions = [
            "123",
            "456789",
            "0",
            "999999999",
            "12345678901234567890",
        ]
        
        # Act & Assert: Number-only questions are handled
        for question in number_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_only_symbols(self):
        """Test handling of questions with only symbols."""
        # Arrange
        symbol_questions = [
            "@#$%",
            "&*()",
            "+-*/",
            "=<>",
            "[]{}",
            "|\\",
            "~`",
        ]
        
        # Act & Assert: Symbol-only questions are handled
        for question in symbol_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question

    def test_handle_questions_with_mixed_content(self):
        """Test handling of questions with mixed content."""
        # Arrange
        mixed_questions = [
            "What is CRISPR? 🧬 <script>alert('test')</script> && rm -rf / ../../../etc/passwd \x00\x01\x02",
            "What is DNA? 脱氧核糖核酸 UNION SELECT * FROM users <img src=x onerror=alert('xss')> \xff\xfe",
            "What is AI? 인공지능 | cat /etc/passwd javascript:alert('xss') \x00\x00\x00",
            "What is ML? машинное обучение OR 1=1 <svg onload=alert('xss')> \xfe\xff",
            "What is NLP? معالجة اللغة الطبيعية INSERT INTO users VALUES ('hacker') <iframe src=javascript:alert('xss')> \xff\xff\xff",
        ]
        
        # Act & Assert: Mixed content is handled
        for question in mixed_questions:
            initial_state = {
                "messages": [HumanMessage(content=question)]
            }
            result = input_interface(initial_state)
            assert result["question"] == question 