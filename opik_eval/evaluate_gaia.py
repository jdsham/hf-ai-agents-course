#!/usr/bin/env python3
"""
Opik Evaluation Framework for Multi-Agent System

This script uses Opik's evaluate() function to evaluate a multi-agent system 
against the GAIA Level 1 dataset, while maintaining individual question tracing 
and saving outputs to a JSONL file.
"""

import json
import uuid
import logging
import sys
import time
from pathlib import Path
from opik import Opik, configure
from opik.evaluation import evaluate
from opik.evaluation.metrics import base_metric, score_result

# Add src to path for multi-agent system imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from multi_agent_system import create_multi_agent_graph
from main import load_baseline_prompts, make_agent_configs, parse_agent_output
from scorer import question_scorer

# Global variables for task function access
graph = None
opik_tracer = None




def evaluate_question(dataset_item):
    """
    Task function that evaluates a single question using the multi-agent system.
    
    Args:
        dataset_item: Dataset item containing Question, Final answer, file_name fields
        
    Returns:
        Dictionary with model_answer, expected_answer, question for scoring
    """
    global graph, opik_tracer
    
    # Extract question and file info
    question = dataset_item["Question"]
    file_name = dataset_item.get("file_name", "")
    
    # Log processing like main.py
    logging.getLogger(__name__).info(f"Processing question: {question}")
    
    # Construct file path (exactly like main.py)
    if file_name != "":
        file_path = f"/home/joe/datum/gaia_level1/{file_name}"
    else:
        file_path = ""
    
    # Generate unique thread_id
    thread_id = str(uuid.uuid4())
    
    # Configure with opik_tracer (exactly like main.py)
    config = {
        "callbacks": [opik_tracer],
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 100
    }
    
    # Invoke graph
    result = graph.invoke({"question": question, "file": file_path}, config=config)
    
    model_answer, reasoning_trace = parse_agent_output(result)
    
    # Flush traces
    opik_tracer.flush()
    
    # Write response to JSONL file immediately (exactly like main.py format)
    response = {
        "task_id": dataset_item["task_id"], 
        "model_answer": model_answer, 
        "reasoning_trace": reasoning_trace, 
        "thread_id": thread_id
    }
    
    # Write this single response to the JSONL file immediately
    output_file = "/home/joe/python-proj/hf-ai-agents-course/opik_eval/gaia_evaluation_responses.jsonl"
    with open(output_file, "a") as f:
        json.dump(response, f)
        f.write("\n")
    
    # Log completion like main.py
    logging.getLogger(__name__).info(f"Completed question: {question}")
    
    # Create the complete JSON output for Opik to record
    complete_json_output = json.dumps({
        "final_answer": model_answer,
        "reasoning_trace": reasoning_trace
    })
    
    # Return for scoring (include complete JSON output and reference)
    return {
        "output": complete_json_output,
        "reference": dataset_item["Final answer"]
    }


class CustomMetric(base_metric.BaseMetric):
    """
    Custom evaluation metric that uses the question_scorer function.
    """
    
    def __init__(self, name: str = "custom_question_scorer", track: bool = True):
        super().__init__(name=name, track=track)
    
    def score(self, reference: str, output: str, **ignored_kwargs):
        """
        Score the model output against the reference answer.
        
        Args:
            reference: The ground truth answer (expected answer)
            output: The model's output/answer (JSON string containing final_answer and reasoning_trace)
            **ignored_kwargs: Additional keyword arguments (ignored)
            
        Returns:
            ScoreResult with the evaluation score
        """
        try:
            # Extract final_answer from the JSON output
            try:
                output_json = json.loads(output)
                actual_answer = output_json.get("final_answer", "")
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, use the output as-is
                actual_answer = output
            
            # Use the question_scorer to evaluate the answer
            is_correct = question_scorer(actual_answer, reference)
            
            # Convert boolean to float score (1.0 for correct, 0.0 for incorrect)
            score_value = 1.0 if is_correct else 0.0
            
            # Create reason message
            reason = f"Answer {'correct' if is_correct else 'incorrect'}. Expected: '{reference}', Got: '{actual_answer}'"
            
            return score_result.ScoreResult(
                value=score_value,
                name=self.name,
                reason=reason
            )
            
        except Exception as e:
            # Handle any errors in scoring
            return score_result.ScoreResult(
                value=0.0,
                name=self.name,
                reason=f"Error during scoring: {str(e)}"
            )


def main():
    """
    Main function to run the evaluation.
    """
    global graph, opik_tracer, responses
    
    # Configure Opik
    configure(use_local=True)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Get dataset
        client = Opik(project_name="gaia-evaluation-project")
        dataset = client.get_dataset(name="GAIA Level 1 Dataset")
        
        # Check if dataset is empty
        if not dataset.get_items():
            logger.error("Dataset is empty")
            return
        
        # Clear the output file to start fresh
        output_file = "/home/joe/python-proj/hf-ai-agents-course/opik_eval/gaia_evaluation_responses.jsonl"
        with open(output_file, "w") as f:
            pass  # Create empty file
        
        # Load prompts and create graph (exactly like main.py)
        prompts = load_baseline_prompts()
        agent_configs = make_agent_configs(prompts)
        graph, opik_tracer = create_multi_agent_graph(agent_configs)
        
        # Run evaluation
        result = evaluate(
            dataset=dataset,
            task=evaluate_question,
            scoring_metrics=[CustomMetric()],
            experiment_name="multi-agent-gaia-evaluation",
            project_name="gaia-evaluation-project",
            experiment_config={
                "model": "o4-mini",
                "agent_type": "multi-agent-system",
                "evaluation_type": "gaia-level1"
            },
            scoring_key_mapping={
                "reference": "Final answer",  # Map dataset's "Final answer" to metric's "reference" parameter
                "output": "output"  # Map task output's "output" key to metric's "output" parameter
            },
            task_threads=1,
            verbose=1
        )
        
        # Log results (exactly like main.py)
        logger.info("Evaluation finished successfully")
        output_file = "/home/joe/python-proj/hf-ai-agents-course/opik_eval/gaia_evaluation_responses.jsonl"
        logger.info(f"Results saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise


if __name__ == "__main__":
    main()
