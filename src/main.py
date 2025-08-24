import json
import time
import os
import logging
from multi_agent_system import create_multi_agent_graph, AgentConfig
from typing import Literal
import sys
import uuid

# Configure logging at the entry point
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Create logger for main module
logger = logging.getLogger(__name__)


def load_prompt_from_file(file_path: str) -> str:
    """
    Load a prompt from a text file.
    
    Args:
        file_path (str): Path to the prompt file
        
    Returns:
        str: Content of the prompt file
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            logger.debug(f"Successfully loaded prompt from: {file_path}")
            return content
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {file_path}")
        raise FileNotFoundError(f"Prompt file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading prompt file {file_path}: {str(e)}")
        raise Exception(f"Error reading prompt file {file_path}: {str(e)}")


def load_baseline_prompts(prompts_dir: str = None) -> dict:
    """
    Load all baseline prompts from the prompts/baseline directory.
    
    Args:
        prompts_dir (str): Optional path to the prompts/baseline directory.
                          If None, will automatically find the correct path.
        
    Returns:
        dict[str, AgentPrompts]: Dictionary containing all agent prompts
    """
    if prompts_dir is None:
        # Try to find the baseline prompts directory relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level from src/ to the project root, then into prompts/baseline
        prompts_dir = os.path.join(script_dir, "..", "prompts", "baseline")
        prompts_dir = os.path.normpath(prompts_dir)
    
    logger.info(f"Loading prompts from directory: {prompts_dir}")
    
    prompt_files = {
        "executor": "executor_system_prompt.txt",
        "guard": "guard_system_prompt.txt",
        }
    
    prompts = {}
    for agent_name, filename in prompt_files.items():
        file_path = os.path.join(prompts_dir, filename)
        logger.debug(f"Loading prompt for {agent_name} from: {file_path}")
        prompts[agent_name] = load_prompt_from_file(file_path)
    
    logger.info(f"Successfully loaded {len(prompts)} prompts")
    return prompts


def read_jsonl_file(file_path:str) -> dict:
    """
    Read a JSONL file line by line and yield each parsed JSON object.
    
    Args:
        file_path (str): Path to the JSONL file
        
    Yields:
        dict: Parsed JSON object from each line
    """
    logger.debug(f"Reading JSONL file: {file_path}")
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()  # Remove whitespace and newlines
            if line:  # Skip empty lines
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON line: {e}")
                    continue


def write_jsonl_file(data_list:list[dict], output_file_path:str) -> None:
    """
    Write a list of data to a JSONL file, with each element as a separate line.
    
    Args:
        data_list (list): List of data to write (can be dicts, strings, etc.)
        output_file_path (str): Path to the output JSONL file
    
    Returns:
        None
    """
    logger.info(f"Writing {len(data_list)} items to: {output_file_path}")
    with open(output_file_path, "w") as f:
        for item in data_list:
            json_line = json.dumps(item)
            f.write(json_line + "\n")
    logger.info(f"Successfully wrote {len(data_list)} items to: {output_file_path}")



def make_agent_configs(prompts: dict) -> dict[str, AgentConfig]:
    """
    Make a dictionary of agent configs from the prompts.

    Args:
        prompts (dict): Dictionary of prompts for each agent

    Returns:
        dict[str, AgentConfig]: Dictionary of agent configs
    """
    logger.info("Creating agent configurations...")
    configs = {
        "executor": AgentConfig(name="executor", provider="openai", model="o4-mini", temperature=1.0, system_prompt=prompts["executor"], output_schema={"final_answer": str, "reasoning_trace": str}),
        "guard": AgentConfig(name="guard", provider="openai", model="o4-mini", temperature=1.0, system_prompt=prompts["guard"]),
        "web_browser": AgentConfig(name="web_browser", provider="openai", model="o4-mini", temperature=1.0, system_prompt=prompts["web_browser"]),
    }
    logger.info(f"Created {len(configs)} agent configurations")
    return configs


def parse_agent_output(result: dict) -> dict:
    """
    Parse the output of the agent.
    This function is used to parse the output of the agent and extract the model answer and the reasoning trace.
    If the agent output is not a valid JSON, it will try to extract the model answer and the reasoning trace from the last message.
    If the last message is not a valid JSON, it will use the raw response as the model answer and the reasoning trace.
    If all else fails, it will set a default model answer and reasoning trace to "I could not answer the question." and "Something went wrong." respectively.

    Args:
        result (dict): The result of the agent

    Returns:
        tuple: A tuple containing the model answer and the reasoning trace
    """
    # Parse the output state to extract final_answer and reasoning_trace
    model_answer = ""
    reasoning_trace = ""
    
    # Get the last message from the state
    if "messages" in result and result["messages"]:
        last_message = result["messages"][-1]
        last_message_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        try:
            # First try to parse the message content directly as JSON
            output_json = json.loads(last_message_content)
            if "final_answer" in output_json and "reasoning_trace" in output_json:
                model_answer = output_json["final_answer"]
                reasoning_trace = output_json["reasoning_trace"]
            else:
                raise ValueError("JSON missing required fields")
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse JSON directly: {e}")
            # Fallback: try to extract JSON from the response
            import re
            
            # Look for JSON in the response with more flexible pattern
            json_patterns = [
                r'\{[^{}]*"final_answer"[^{}]*"reasoning_trace"[^{}]*\}',
                r'\{[^{}]*"final_answer"[^{}]*\}',
                r'\{[^{}]*"reasoning_trace"[^{}]*"final_answer"[^{}]*\}'
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, last_message_content, re.DOTALL)
                if json_match:
                    try:
                        fallback_json = json.loads(json_match.group())
                        model_answer = fallback_json.get("final_answer", "")
                        reasoning_trace = fallback_json.get("reasoning_trace", "")
                        if model_answer and reasoning_trace:
                            logger.info("Successfully extracted JSON using fallback pattern")
                            break
                    except json.JSONDecodeError:
                        continue
            
            # If still no valid JSON found, use the raw response
            if not model_answer:
                model_answer = last_message_content
                reasoning_trace = "Raw response used as final answer"
                logger.warning("Using raw response as final answer")
    
    # Also try to get from state if available
    if not model_answer:
        model_answer = result.get("final_answer", "I could not answer the question.")
    if not reasoning_trace:
        reasoning_trace = result.get("reasoning_trace", "Something went wrong.")

    return model_answer, reasoning_trace


def main() -> None:
    """
    Main function to run the application.
    """
    try:
        # Configure Opik for real-time flushing
        from opik import configure
        configure(use_local=True)

        logger.info("Application started")
        
        # Load baseline prompts
        logger.info("Loading baseline prompts...")
        prompts = load_baseline_prompts()
        logger.info(f"Loaded {len(prompts)} prompts: {list(prompts.keys())}")
        agent_configs = make_agent_configs(prompts)
        
        # Create the multi-agent graph using the factory function
        logger.info("Creating multi-agent graph...")
        graph, opik_tracer = create_multi_agent_graph(agent_configs)
        logger.info("Graph created successfully!")
        
        jsonl_file_path = "/home/joe/python-proj/hf-ai-agents-course/src/gaia_lvl1.jsonl"
        
        responses = []
        logger.info("Starting to process JSONL file...")
        for item in read_jsonl_file(jsonl_file_path):
            if item["Level"] == 1:
                logger.info(f"Processing question: {item["Question"]}")
                # Generate unique thread_id for each iteration
                thread_id = str(uuid.uuid4())
                # Configure with unique thread_id
                config = {
                    "callbacks": [opik_tracer],
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": 100
                }
                
                if item["file_name"] != "":
                    file_path = f"/home/joe/datum/gaia_level1/{item['file_name']}"
                else:
                    file_path = ""
                result = graph.invoke({"question": item["Question"], "file": file_path}, config=config)
                
                model_answer, reasoning_trace = parse_agent_output(result)
                
                response = {"task_id": item["task_id"], "model_answer": model_answer, "reasoning_trace": reasoning_trace, "thread_id": thread_id}

                responses.append(response)
                logger.info(f"Completed question: {item["Question"]}")
                # Flush traces after each question
                opik_tracer.flush()
                time.sleep(5)

        logger.info("Writing responses to output file...")
        write_jsonl_file(responses, "/home/joe/python-proj/hf-ai-agents-course/src/gaia_lvl1_responses.jsonl")
        logger.info("Application finished successfully")
        # Ensure all traces are logged before exiting

    except Exception as e:
        # Ensure all traces are logged before exiting
        try:
            opik_tracer.flush()
        finally:
            logger.error(f"Application failed: {str(e)}")
            print(f"Application failed: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()