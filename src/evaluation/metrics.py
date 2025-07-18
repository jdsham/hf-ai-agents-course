"""
LLM Output Evaluation Metrics

This module provides a comprehensive set of metrics for evaluating LLM outputs
against reference answers. All metrics are designed to be modular and pipeline-friendly.
"""

import re
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import numpy as np

# String similarity
from difflib import SequenceMatcher

# Cosine similarity
from sentence_transformers import SentenceTransformer, util
import torch

# BLEU, ROUGE, METEOR
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from nltk.translate.meteor_score import meteor_score
import nltk

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

@dataclass
class EvaluationResult:
    """Container for evaluation results."""
    metric_name: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class LLMEvaluator:
    """
    Comprehensive LLM output evaluator with multiple metrics.
    
    Supports:
    - String similarity (exact match, sequence matcher)
    - Cosine similarity (semantic similarity)
    - BLEU, ROUGE, METEOR (NLP metrics)
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the evaluator.
        
        Args:
            embedding_model: Sentence transformer model for cosine similarity
        """
        self.embedding_model = embedding_model
        self._sentence_model = None
        self._rouge_scorer = None
        
    @property
    def sentence_model(self):
        """Lazy load sentence transformer model."""
        if self._sentence_model is None:
            self._sentence_model = SentenceTransformer(self.embedding_model)
        return self._sentence_model
    
    @property
    def rouge_scorer(self):
        """Lazy load ROUGE scorer."""
        if self._rouge_scorer is None:
            self._rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        return self._rouge_scorer
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase and remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip().lower())
        return text
    
    def exact_match(self, prediction: str, reference: str) -> EvaluationResult:
        """
        Calculate exact match score.
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            EvaluationResult with score 1.0 if exact match, 0.0 otherwise
        """
        pred_norm = self.normalize_text(prediction)
        ref_norm = self.normalize_text(reference)
        
        score = 1.0 if pred_norm == ref_norm else 0.0
        
        return EvaluationResult(
            metric_name="exact_match",
            score=score,
            metadata={"prediction_normalized": pred_norm, "reference_normalized": ref_norm}
        )
    
    def string_similarity(self, prediction: str, reference: str) -> EvaluationResult:
        """
        Calculate string similarity using SequenceMatcher.
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            EvaluationResult with similarity score between 0.0 and 1.0
        """
        pred_norm = self.normalize_text(prediction)
        ref_norm = self.normalize_text(reference)
        
        similarity = SequenceMatcher(None, pred_norm, ref_norm).ratio()
        
        return EvaluationResult(
            metric_name="string_similarity",
            score=similarity,
            metadata={"prediction_normalized": pred_norm, "reference_normalized": ref_norm}
        )
    
    def cosine_similarity(self, prediction: str, reference: str) -> EvaluationResult:
        """
        Calculate cosine similarity using sentence embeddings.
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            EvaluationResult with cosine similarity score between -1.0 and 1.0
        """
        try:
            # Encode both texts
            pred_embedding = self.sentence_model.encode(prediction, convert_to_tensor=True)
            ref_embedding = self.sentence_model.encode(reference, convert_to_tensor=True)
            
            # Calculate cosine similarity
            similarity = util.pytorch_cos_sim(pred_embedding, ref_embedding).item()
            
            return EvaluationResult(
                metric_name="cosine_similarity",
                score=similarity,
                metadata={"embedding_model": self.embedding_model}
            )
        except Exception as e:
            # Return 0.0 if embedding fails
            return EvaluationResult(
                metric_name="cosine_similarity",
                score=0.0,
                metadata={"error": str(e), "embedding_model": self.embedding_model}
            )
    
    def bleu_score(self, prediction: str, reference: str) -> EvaluationResult:
        """
        Calculate BLEU score.
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            EvaluationResult with BLEU score between 0.0 and 1.0
        """
        try:
            # Tokenize
            pred_tokens = prediction.lower().split()
            ref_tokens = reference.lower().split()
            
            # Calculate BLEU
            smoothing = SmoothingFunction().method1
            score = sentence_bleu([ref_tokens], pred_tokens, smoothing_function=smoothing)
            
            return EvaluationResult(
                metric_name="bleu_score",
                score=score,
                metadata={"prediction_tokens": pred_tokens, "reference_tokens": ref_tokens}
            )
        except Exception as e:
            return EvaluationResult(
                metric_name="bleu_score",
                score=0.0,
                metadata={"error": str(e)}
            )
    
    def rouge_scores(self, prediction: str, reference: str) -> List[EvaluationResult]:
        """
        Calculate ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L).
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            List of EvaluationResult objects for each ROUGE metric
        """
        try:
            scores = self.rouge_scorer.score(reference, prediction)
            results = []
            
            for metric_name, score in scores.items():
                results.append(EvaluationResult(
                    metric_name=f"rouge_{metric_name}",
                    score=score.fmeasure,  # Use F1 score
                    metadata={
                        "precision": score.precision,
                        "recall": score.recall,
                        "fmeasure": score.fmeasure
                    }
                ))
            
            return results
        except Exception as e:
            # Return zero scores if ROUGE calculation fails
            return [
                EvaluationResult(
                    metric_name=f"rouge_{metric}",
                    score=0.0,
                    metadata={"error": str(e)}
                ) for metric in ["1", "2", "L"]
            ]
    
    def meteor_score(self, prediction: str, reference: str) -> EvaluationResult:
        """
        Calculate METEOR score.
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            EvaluationResult with METEOR score between 0.0 and 1.0
        """
        try:
            # Tokenize
            pred_tokens = prediction.lower().split()
            ref_tokens = reference.lower().split()
            
            # Calculate METEOR
            score = meteor_score([ref_tokens], pred_tokens)
            
            return EvaluationResult(
                metric_name="meteor_score",
                score=score,
                metadata={"prediction_tokens": pred_tokens, "reference_tokens": ref_tokens}
            )
        except Exception as e:
            return EvaluationResult(
                metric_name="meteor_score",
                score=0.0,
                metadata={"error": str(e)}
            )
    
    def evaluate_all(self, prediction: str, reference: str) -> Dict[str, EvaluationResult]:
        """
        Run all evaluation metrics on a prediction-reference pair.
        
        Args:
            prediction: Model output
            reference: Reference answer
            
        Returns:
            Dictionary mapping metric names to EvaluationResult objects
        """
        results = {}
        
        # Individual metrics
        results["exact_match"] = self.exact_match(prediction, reference)
        results["string_similarity"] = self.string_similarity(prediction, reference)
        results["cosine_similarity"] = self.cosine_similarity(prediction, reference)
        results["bleu_score"] = self.bleu_score(prediction, reference)
        results["meteor_score"] = self.meteor_score(prediction, reference)
        
        # ROUGE scores (returns multiple results)
        rouge_results = self.rouge_scores(prediction, reference)
        for rouge_result in rouge_results:
            results[rouge_result.metric_name] = rouge_result
        
        return results
    
    def evaluate_batch(self, predictions: List[str], references: List[str]) -> Dict[str, List[EvaluationResult]]:
        """
        Evaluate a batch of predictions against references.
        
        Args:
            predictions: List of model outputs
            references: List of reference answers
            
        Returns:
            Dictionary mapping metric names to lists of EvaluationResult objects
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have the same length")
        
        batch_results = {}
        
        for i, (pred, ref) in enumerate(zip(predictions, references)):
            single_results = self.evaluate_all(pred, ref)
            
            for metric_name, result in single_results.items():
                if metric_name not in batch_results:
                    batch_results[metric_name] = []
                batch_results[metric_name].append(result)
        
        return batch_results
    
    def compute_aggregate_scores(self, batch_results: Dict[str, List[EvaluationResult]]) -> Dict[str, float]:
        """
        Compute aggregate scores (mean) across a batch.
        
        Args:
            batch_results: Results from evaluate_batch()
            
        Returns:
            Dictionary mapping metric names to aggregate scores
        """
        aggregate_scores = {}
        
        for metric_name, results in batch_results.items():
            scores = [result.score for result in results]
            aggregate_scores[metric_name] = np.mean(scores)
        
        return aggregate_scores


# Convenience functions for pipeline integration
def evaluate_single(prediction: str, reference: str, embedding_model: str = "all-MiniLM-L6-v2") -> Dict[str, EvaluationResult]:
    """Evaluate a single prediction-reference pair."""
    evaluator = LLMEvaluator(embedding_model)
    return evaluator.evaluate_all(prediction, reference)

def evaluate_batch_simple(predictions: List[str], references: List[str], embedding_model: str = "all-MiniLM-L6-v2") -> Dict[str, float]:
    """Evaluate a batch and return aggregate scores."""
    evaluator = LLMEvaluator(embedding_model)
    batch_results = evaluator.evaluate_batch(predictions, references)
    return evaluator.compute_aggregate_scores(batch_results) 