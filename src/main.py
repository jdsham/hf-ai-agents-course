import json
import time
import os
import logging
from multi_agent_system import create_multi_agent_graph, AgentConfig
from langchain_core.messages import HumanMessage
from typing import Literal
import sys

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
        "planner": "planner_system_prompt.txt",
        "critic_planner": "critic_planner_system_prompt.txt",
        "researcher": "researcher_system_prompt.txt",
        "critic_researcher": "critic_researcher_system_prompt.txt",
        "expert": "expert_system_prompt.txt",
        "critic_expert": "critic_expert_system_prompt.txt",
        "finalizer": "finalizer_system_prompt.txt"
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
        "planner": AgentConfig(name="planner", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"research_steps": list[str], "expert_steps": list[str]}, system_prompt=prompts["planner"], retry_limit=3),
        "researcher": AgentConfig(name="researcher", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"result": str}, system_prompt=prompts["researcher"], retry_limit=5),
        "expert": AgentConfig(name="expert", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"expert_answer": str, "reasoning_trace": str}, system_prompt=prompts["expert"], retry_limit=5),
        "critic": AgentConfig(name="critic", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"decision": Literal["approve", "reject"], "feedback": str}, system_prompt={"critic_planner":prompts["critic_planner"], "critic_researcher":prompts["critic_researcher"], "critic_expert":prompts["critic_expert"]}, retry_limit=None),
        "finalizer": AgentConfig(name="finalizer", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"final_answer": str, "final_reasoning_trace": str}, system_prompt=prompts["finalizer"], retry_limit=None),
    }
    logger.info(f"Created {len(configs)} agent configurations")
    return configs


def main() -> None:
    """
    Main function to run the application.
    """
    try:
        logger.info("Application started")
        
        # Load baseline prompts
        logger.info("Loading baseline prompts...")
        prompts = load_baseline_prompts()
        logger.info(f"Loaded {len(prompts)} prompts: {list(prompts.keys())}")
        agent_configs = make_agent_configs(prompts)
        
        # Create the multi-agent graph using the factory function
        logger.info("Creating multi-agent graph...")
        graph = create_multi_agent_graph(agent_configs)
        logger.info("Graph created successfully!")
        
        jsonl_file_path = "/home/joe/python-proj/hf-agents-course/src/metadata.jsonl"
        
        responses = []
        logger.info("Starting to process JSONL file...")

        for item in read_jsonl_file(jsonl_file_path):
            if item["Level"] == 1:
                logger.info(f"Processing question: {item["Question"]}")
                if item["file_name"] != "":
                    file_path = f"/home/joe/datum/gaia_lvl1/{item['file_name']}"
                else:
                    file_path = ""
                result = graph.invoke({"question": item["Question"], "file_path": file_path})
                response = {"task_id": item["task_id"], "model_answer": result["final_answer"], "reasoning_trace": result["reasoning_trace"]}

                responses.append(response)
                logger.info(f"Completed question: {item["Question"]}")
                time.sleep(5)

        logger.info("Writing responses to output file...")
        write_jsonl_file(responses, "/home/joe/python-proj/hf-agents-course/src/gaia_lvl1_responses.jsonl")
        logger.info("Application finished successfully")
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        print(f"Application failed: {str(e)}")
        sys.exit(1)

# Example usage:
if __name__ == "__main__":
    main()