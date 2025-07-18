"""
Example usage of LLM evaluation metrics.

This script demonstrates how to use the evaluation framework
to assess LLM outputs against reference answers.
"""

import sys
import os
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from evaluation.metrics import LLMEvaluator, evaluate_single, evaluate_batch_simple


def example_single_evaluation():
    """Example of evaluating a single prediction-reference pair."""
    print("=== Single Evaluation Example ===")
    
    # Sample prediction and reference
    prediction = "The capital of France is Paris, which is located in the north-central part of the country."
    reference = "Paris is the capital of France."
    
    # Evaluate using convenience function
    results = evaluate_single(prediction, reference)
    
    print(f"Prediction: {prediction}")
    print(f"Reference:  {reference}")
    print("\nResults:")
    for metric_name, result in results.items():
        print(f"  {metric_name}: {result.score:.4f}")
    
    return results


def example_batch_evaluation():
    """Example of evaluating multiple prediction-reference pairs."""
    print("\n=== Batch Evaluation Example ===")
    
    # Sample test cases
    test_cases = [
        {
            "prediction": "Mount Kilimanjaro is the tallest mountain in Africa.",
            "reference": "Mount Kilimanjaro is Africa's highest peak."
        },
        {
            "prediction": "The answer is 42.",
            "reference": "The answer is 42."
        },
        {
            "prediction": "The weather is sunny today.",
            "reference": "It's raining heavily."
        }
    ]
    
    predictions = [case["prediction"] for case in test_cases]
    references = [case["reference"] for case in test_cases]
    
    # Evaluate batch and get aggregate scores
    aggregate_scores = evaluate_batch_simple(predictions, references)
    
    print("Test Cases:")
    for i, case in enumerate(test_cases):
        print(f"  {i+1}. Prediction: {case['prediction']}")
        print(f"     Reference:  {case['reference']}")
    
    print("\nAggregate Scores:")
    for metric_name, score in aggregate_scores.items():
        print(f"  {metric_name}: {score:.4f}")
    
    return aggregate_scores


def example_custom_evaluator():
    """Example of using the LLMEvaluator class directly."""
    print("\n=== Custom Evaluator Example ===")
    
    # Initialize evaluator with custom embedding model
    evaluator = LLMEvaluator(embedding_model="all-MiniLM-L6-v2")
    
    prediction = "The population density of Tokyo is approximately 6,364 people per square kilometer."
    reference = "Tokyo has a population density of about 6,364 people per km²."
    
    # Run individual metrics
    exact_match = evaluator.exact_match(prediction, reference)
    string_sim = evaluator.string_similarity(prediction, reference)
    cosine_sim = evaluator.cosine_similarity(prediction, reference)
    
    print(f"Prediction: {prediction}")
    print(f"Reference:  {reference}")
    print(f"\nIndividual Metrics:")
    print(f"  Exact Match: {exact_match.score:.4f}")
    print(f"  String Similarity: {string_sim.score:.4f}")
    print(f"  Cosine Similarity: {cosine_sim.score:.4f}")
    
    return evaluator


def example_with_gaia_test_cases():
    """Example using the synthetic GAIA test cases."""
    print("\n=== GAIA Test Cases Example ===")
    
    # Load test cases
    test_cases_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'synthetic_gaia_testcases.jsonl')
    
    if not os.path.exists(test_cases_path):
        print(f"Test cases file not found: {test_cases_path}")
        return
    
    # Load a few test cases
    test_cases = []
    with open(test_cases_path, 'r') as f:
        for i, line in enumerate(f):
            if i >= 3:  # Only use first 3 cases for example
                break
            test_cases.append(json.loads(line))
    
    # Simulate LLM predictions (in practice, these would come from your model)
    predictions = [
        "Mount Kilimanjaro",  # For the first test case
        "The article discusses renewable energy impact on global electricity production.",  # For the second
        "Roger Penrose, Reinhard Genzel, and Andrea Ghez"  # For the third
    ]
    
    references = [case["answer"] for case in test_cases]
    
    # Evaluate
    aggregate_scores = evaluate_batch_simple(predictions, references)
    
    print("GAIA Test Cases Evaluation:")
    for i, (case, pred) in enumerate(zip(test_cases, predictions)):
        print(f"  {i+1}. Question: {case['question']}")
        print(f"     Prediction: {pred}")
        print(f"     Reference:  {case['answer']}")
    
    print("\nAggregate Scores:")
    for metric_name, score in aggregate_scores.items():
        print(f"  {metric_name}: {score:.4f}")
    
    return aggregate_scores


def main():
    """Run all examples."""
    print("LLM Evaluation Metrics Examples")
    print("=" * 50)
    
    # Run examples
    example_single_evaluation()
    example_batch_evaluation()
    example_custom_evaluator()
    example_with_gaia_test_cases()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main() 