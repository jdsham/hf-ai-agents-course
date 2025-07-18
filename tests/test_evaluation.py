"""
Unit tests for LLM evaluation metrics.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from evaluation.metrics import LLMEvaluator, EvaluationResult, evaluate_single, evaluate_batch_simple


class TestLLMEvaluator:
    """Test the LLMEvaluator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = LLMEvaluator()
        
        # Test cases
        self.exact_match_case = {
            "prediction": "The capital of France is Paris.",
            "reference": "Paris is the capital of France.",
            "expected_exact_match": 0.0,  # Different phrasing
            "expected_string_similarity": 0.5,  # Rough estimate
        }
        
        self.similar_case = {
            "prediction": "Mount Kilimanjaro is the tallest mountain in Africa.",
            "reference": "Mount Kilimanjaro is Africa's highest peak.",
            "expected_exact_match": 0.0,
            "expected_string_similarity": 0.3,  # Rough estimate
        }
        
        self.identical_case = {
            "prediction": "The answer is 42.",
            "reference": "The answer is 42.",
            "expected_exact_match": 1.0,
            "expected_string_similarity": 1.0,
        }
    
    def test_normalize_text(self):
        """Test text normalization."""
        text = "  Hello   World  "
        normalized = self.evaluator.normalize_text(text)
        assert normalized == "hello world"
    
    def test_exact_match(self):
        """Test exact match scoring."""
        # Test identical case
        result = self.evaluator.exact_match(
            self.identical_case["prediction"],
            self.identical_case["reference"]
        )
        assert result.score == self.identical_case["expected_exact_match"]
        assert result.metric_name == "exact_match"
        
        # Test different case
        result = self.evaluator.exact_match(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        assert result.score == self.exact_match_case["expected_exact_match"]
    
    def test_string_similarity(self):
        """Test string similarity scoring."""
        result = self.evaluator.string_similarity(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        assert 0.0 <= result.score <= 1.0
        assert result.metric_name == "string_similarity"
        assert result.metadata is not None
        assert "prediction_normalized" in result.metadata
        assert "reference_normalized" in result.metadata
    
    def test_cosine_similarity(self):
        """Test cosine similarity scoring."""
        result = self.evaluator.cosine_similarity(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        assert -1.0 <= result.score <= 1.0
        assert result.metric_name == "cosine_similarity"
        assert result.metadata is not None
        assert "embedding_model" in result.metadata
    
    def test_bleu_score(self):
        """Test BLEU score calculation."""
        result = self.evaluator.bleu_score(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        assert 0.0 <= result.score <= 1.0
        assert result.metric_name == "bleu_score"
        assert result.metadata is not None
        assert "prediction_tokens" in result.metadata
        assert "reference_tokens" in result.metadata
    
    def test_rouge_scores(self):
        """Test ROUGE score calculation."""
        results = self.evaluator.rouge_scores(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        
        # Should return 3 ROUGE metrics
        assert len(results) == 3
        
        for result in results:
            assert result.metric_name.startswith("rouge_")
            assert 0.0 <= result.score <= 1.0
            assert result.metadata is not None
            assert "precision" in result.metadata
            assert "recall" in result.metadata
            assert "fmeasure" in result.metadata
    
    def test_meteor_score(self):
        """Test METEOR score calculation."""
        result = self.evaluator.meteor_score(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        assert 0.0 <= result.score <= 1.0
        assert result.metric_name == "meteor_score"
        assert result.metadata is not None
        assert "prediction_tokens" in result.metadata
        assert "reference_tokens" in result.metadata
    
    def test_evaluate_all(self):
        """Test running all metrics at once."""
        results = self.evaluator.evaluate_all(
            self.exact_match_case["prediction"],
            self.exact_match_case["reference"]
        )
        
        # Should have all metrics
        expected_metrics = [
            "exact_match", "string_similarity", "cosine_similarity",
            "bleu_score", "meteor_score", "rouge_1", "rouge_2", "rouge_L"
        ]
        
        for metric in expected_metrics:
            assert metric in results
            assert isinstance(results[metric], EvaluationResult)
            assert results[metric].metric_name == metric
    
    def test_evaluate_batch(self):
        """Test batch evaluation."""
        predictions = [
            self.exact_match_case["prediction"],
            self.similar_case["prediction"],
            self.identical_case["prediction"]
        ]
        references = [
            self.exact_match_case["reference"],
            self.similar_case["reference"],
            self.identical_case["reference"]
        ]
        
        batch_results = self.evaluator.evaluate_batch(predictions, references)
        
        # Should have results for each metric
        expected_metrics = [
            "exact_match", "string_similarity", "cosine_similarity",
            "bleu_score", "meteor_score", "rouge_1", "rouge_2", "rouge_L"
        ]
        
        for metric in expected_metrics:
            assert metric in batch_results
            assert len(batch_results[metric]) == 3  # One result per prediction
    
    def test_compute_aggregate_scores(self):
        """Test aggregate score computation."""
        predictions = [
            self.exact_match_case["prediction"],
            self.similar_case["prediction"],
            self.identical_case["prediction"]
        ]
        references = [
            self.exact_match_case["reference"],
            self.similar_case["reference"],
            self.identical_case["reference"]
        ]
        
        batch_results = self.evaluator.evaluate_batch(predictions, references)
        aggregate_scores = self.evaluator.compute_aggregate_scores(batch_results)
        
        # Should have aggregate scores for each metric
        expected_metrics = [
            "exact_match", "string_similarity", "cosine_similarity",
            "bleu_score", "meteor_score", "rouge_1", "rouge_2", "rouge_L"
        ]
        
        for metric in expected_metrics:
            assert metric in aggregate_scores
            assert isinstance(aggregate_scores[metric], float)
            assert 0.0 <= aggregate_scores[metric] <= 1.0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_evaluate_single(self):
        """Test single evaluation convenience function."""
        prediction = "The capital of France is Paris."
        reference = "Paris is the capital of France."
        
        results = evaluate_single(prediction, reference)
        
        # Should return all metrics
        expected_metrics = [
            "exact_match", "string_similarity", "cosine_similarity",
            "bleu_score", "meteor_score", "rouge_1", "rouge_2", "rouge_L"
        ]
        
        for metric in expected_metrics:
            assert metric in results
            assert isinstance(results[metric], EvaluationResult)
    
    def test_evaluate_batch_simple(self):
        """Test batch evaluation convenience function."""
        predictions = [
            "The capital of France is Paris.",
            "Mount Kilimanjaro is the tallest mountain in Africa."
        ]
        references = [
            "Paris is the capital of France.",
            "Mount Kilimanjaro is Africa's highest peak."
        ]
        
        aggregate_scores = evaluate_batch_simple(predictions, references)
        
        # Should return aggregate scores
        expected_metrics = [
            "exact_match", "string_similarity", "cosine_similarity",
            "bleu_score", "meteor_score", "rouge_1", "rouge_2", "rouge_L"
        ]
        
        for metric in expected_metrics:
            assert metric in aggregate_scores
            assert isinstance(aggregate_scores[metric], float)
            assert 0.0 <= aggregate_scores[metric] <= 1.0


class TestErrorHandling:
    """Test error handling in evaluation metrics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = LLMEvaluator()
    
    def test_empty_strings(self):
        """Test handling of empty strings."""
        result = self.evaluator.exact_match("", "")
        assert result.score == 1.0  # Empty strings should match
        
        result = self.evaluator.string_similarity("", "")
        assert result.score == 1.0  # Empty strings should be similar
    
    def test_very_different_texts(self):
        """Test handling of very different texts."""
        result = self.evaluator.string_similarity(
            "This is completely different text.",
            "This is another completely different text."
        )
        assert 0.0 <= result.score <= 1.0  # Should still return a valid score


if __name__ == "__main__":
    pytest.main([__file__]) 