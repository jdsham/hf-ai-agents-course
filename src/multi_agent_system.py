from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from typing import Any, Literal, Optional, TypedDict, List, Annotated, cast
from IPython.display import Image, display
import operator
import json
import logging
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Tools
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.documents import Document
from langchain_core.tools import Tool, tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_tavily import TavilySearch
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders import UnstructuredExcelLoader, UnstructuredPowerPointLoader, UnstructuredPDFLoader
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio
from langchain_experimental.tools.python.tool import PythonREPLTool
import pint



########################################################
# < LLMs >
########################################################
llm_planner = ChatOpenAI(model="gpt-4o", temperature=0)
llm_researcher = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_expert = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_critic = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_finalizer = ChatOpenAI(model="gpt-4o", temperature=0)

########################################################
# < Graph State & Agent Messages >
########################################################
class AgentMessage(TypedDict):
    sender: str        # "critic", "expert", "orchestrator"
    receiver: str      # "expert", "orchestrator", "all"
    type: str          # "instruction", "feedback", "question"
    content: str       # Natural language message
    step_id: Optional[int] # (optional) link to logical_plan step


class ResearcherState(MessagesState):
    messages: Annotated[list[BaseMessage], operator.add]
    step_index: int
    result: Optional[Any]

class ExpertState(MessagesState):
    messages: Annotated[list[BaseMessage], operator.add]
    question: str
    research_steps: list[str]
    research_results: list[Any]
    expert_answer: Any
    expert_reasoning: str


class GraphState(MessagesState):
    agent_messages: list[AgentMessage]
    question: str
    files: Optional[list[str]]
    research_steps: list[str]
    expert_steps: list[str]
    researcher_states: dict[int, ResearcherState]
    current_research_index: int
    research_results: list[Any]
    expert_state: Optional[ExpertState]
    expert_answer: Any
    expert_reasoning: str
    critic_planner_decision: str
    critic_planner_feedback: str
    critic_researcher_decision: str
    critic_researcher_feedback: str
    critic_expert_decision: str
    critic_expert_feedback: str
    final_answer: str
    final_reasoning_trace: str
    current_step: Literal["input", "planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer", ""]
    next_step: Literal["planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer", ""]
    retry_count: int
    retry_limit: int
    error: Optional[str]
    error_component: Optional[str]


########################################################
# < Error Handling & Validation Utilities >
########################################################
def log_error(component: str, error: Exception, state: Optional[Any] = None) -> None:
    """Log errors with component context and optional state information."""
    error_msg = f"Error in {component}: {str(error)}"
    if state and hasattr(state, 'get'):
        error_msg += f" | Current step: {state.get('current_step', 'unknown')}"
    logger.error(error_msg)

def set_error_state(state: GraphState, component: str, error: Exception) -> GraphState:
    """Set error state and log the error."""
    error_msg = f"{component} failed: {str(error)}"
    state["error"] = error_msg
    state["error_component"] = component
    log_error(component, error, state)
    return state

def validate_state(state: GraphState) -> bool:
    """Validate that the state has all required fields and correct types."""
    required_fields = {
        "agent_messages": list,
        "question": str,
        "research_steps": list,
        "expert_steps": list,
        "researcher_states": dict,
        "current_research_index": int,
        "research_results": list,
        "expert_reasoning": str,
        "critic_planner_decision": str,
        "critic_planner_feedback": str,
        "critic_researcher_decision": str,
        "critic_researcher_feedback": str,
        "critic_expert_decision": str,
        "critic_expert_feedback": str,
        "final_answer": str,
        "final_reasoning_trace": str,
        "next_step": str,
        "retry_count": int,
        "retry_limit": int
    }
    
    for field, expected_type in required_fields.items():
        if field not in state:
            logger.error(f"Missing required field: {field}")
            return False
        if expected_type != Any and not isinstance(state[field], expected_type):
            logger.error(f"Invalid type for {field}: expected {expected_type}, got {type(state[field])}")
            return False
    
    return True

def validate_llm_response(response: Any, expected_fields: List[str], component: str) -> bool:
    """Validate LLM response has expected structure and fields."""
    if not isinstance(response, dict):
        logger.error(f"{component}: Response is not a dictionary")
        return False
    
    for field in expected_fields:
        if field not in response:
            logger.error(f"{component}: Missing required field '{field}' in response")
            return False
    
    return True

def handle_agent_error(state: GraphState, component: str, error: Exception) -> GraphState:
    """Handle errors in agent nodes with appropriate state updates."""
    state = set_error_state(state, component, error)
    
    # Increment retry count for recoverable errors
    if "network" not in str(error).lower() and "timeout" not in str(error).lower():
        state["retry_count"] += 1
    
    # If retry limit exceeded, route to finalizer
    if state["retry_count"] >= state["retry_limit"]:
        state["next_step"] = "finalizer"
        state["final_answer"] = f"The question could not be answered due to an error in {component}."
        state["final_reasoning_trace"] = f"System encountered an error: {str(error)}"
        logger.warning(f"Retry limit exceeded for {component}, routing to finalizer")
    
    return state


########################################################
# < Inter-Agent Communication >
########################################################
def send_message(state: GraphState, message: AgentMessage) -> GraphState:
    state["agent_messages"].append(message)
    return state

def get_agent_conversation(state: GraphState, agent_name: str, types: Optional[List[str]] = None, step_id: Optional[int] = None) -> List[AgentMessage]:
    # Only messages between orchestrator and the agent
    inbox = [
        m for m in state["agent_messages"]
        if (m["sender"] == agent_name and m["receiver"] == "orchestrator")
        or (m["sender"] == "orchestrator" and m["receiver"] == agent_name)
    ]
    if step_id is not None:
        inbox = [m for m in inbox if m["step_id"] == step_id]
    if types:
        inbox = [m for m in inbox if m["type"] in types]
    return inbox


def convert_agent_messages_to_langchain(messages: List[AgentMessage]) -> List[BaseMessage]:
    converted_messages = []
    for m in messages:
        if m["sender"] == "orchestrator":
            message = HumanMessage(content=m["content"])
        else:
            message = AIMessage(content=m["content"])
        converted_messages.append(message)
    return converted_messages

########################################################
# < Agent System Prompts >
########################################################
import os
PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")
def load_prompt(filename):
    with open(os.path.join(PROMPT_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()

planner_system_prompt = load_prompt("planner_system_prompt.txt")
critic_planner_system_prompt = load_prompt("critic_planner_system_prompt.txt")
researcher_system_prompt = load_prompt("researcher_system_prompt.txt")
critic_researcher_system_prompt = load_prompt("critic_researcher_system_prompt.txt")
expert_system_prompt = load_prompt("expert_system_prompt.txt")
critic_expert_system_prompt = load_prompt("critic_expert_system_prompt.txt")
finalizer_system_prompt = load_prompt("finalizer_system_prompt.txt")


def make_research_steps_and_results(prompt, question: str, research_steps: list[str], research_results: list[str]) -> str:
    research_steps_and_results = ""
    for i, (step, result) in enumerate(zip(research_steps, research_results)):
        research_steps_and_results += f"## The research step {i} is:\n{step}\n## The research result {i} is:\n{result}\n"
    return prompt.format(question=question, research_steps_and_results=research_steps_and_results)


########################################################
# < Researcher Tools >
########################################################
def youtube_transcript_tool(url: str) -> str:
    """
    Extract transcript from a YouTube video URL.
    
    Args:
        url: The YouTube video URL to extract transcript from
        
    Returns:
        The transcript text from the video
    """
    try:
        logger.info(f"YouTube transcript tool processing URL: {url}")
        
        # Load the YouTube video transcript
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
        documents = loader.load()
        
        if not documents:
            logger.warning("No transcript found for YouTube video")
            return "No transcript found for this YouTube video."
        
        # Extract transcript content
        transcript = documents[0].page_content
        
        # Add video metadata if available
        metadata = documents[0].metadata
        video_info = f"Video Title: {metadata.get('title', 'Unknown')}\n"
        video_info += f"Channel: {metadata.get('author', 'Unknown')}\n"
        video_info += f"Duration: {metadata.get('length', 'Unknown')} seconds\n\n"
        
        logger.info(f"YouTube transcript tool completed successfully")
        return video_info + transcript
        
    except Exception as e:
        error_msg = f"Error extracting transcript: {str(e)}"
        logger.error(f"YouTube transcript tool failed: {error_msg}")
        return error_msg

@tool
def unstructured_excel_tool(file_path: str) -> list[Document]:
    """
    Load an Excel file and return the content.
    """
    loader = UnstructuredExcelLoader(file_path)
    return loader.load()

@tool
def unstructured_powerpoint_tool(file_path: str) -> list[Document]:
    """
    Load a PowerPoint file and return the content.
    """
    loader = UnstructuredPowerPointLoader(file_path)
    return loader.load()

@tool
def unstructured_pdf_tool(file_path: str) -> list[Document]:
    """
    Load a PDF file and return the content.
    """
    loader = UnstructuredPDFLoader(file_path)
    return loader.load()


wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(wiki_client=None))

tavily_tool = TavilySearch()

youtube_tool = Tool(
    name="youtube_transcript",
    description="Extract transcript from a YouTube video URL. Use this when you need to get the content/transcript from a specific YouTube video.",
    func=youtube_transcript_tool,
)


async def get_browser_mcp_tools(mcp_url: str) -> list:
    async with streamablehttp_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await load_mcp_tools(session)
            return mcp_tools

async def get_research_tools():
    browser_mcp_url = "http://0.0.0.0:3000/mcp"
    mcp_tools = await get_browser_mcp_tools(browser_mcp_url)
    return [
        youtube_tool,
        tavily_tool,
        unstructured_excel_tool,
        unstructured_powerpoint_tool,
        unstructured_pdf_tool,
        *mcp_tools,
    ]

research_tools = asyncio.run(get_research_tools())
#research_tools = await get_research_tools()

########################################################
# < Researcher Graph >
########################################################
llm_researcher = llm_researcher.bind_tools(research_tools)

def researcher_llm_node(state: ResearcherState) -> ResearcherState:
    output_schema = {"result": str}
    llm_researcher_structured = llm_researcher.with_structured_output(output_schema, method="json_mode")
    sys_prompt = [SystemMessage(content=researcher_system_prompt)]
    response = llm_researcher_structured.invoke(sys_prompt + state["messages"])
    if isinstance(response, dict):
        return {"messages": [AIMessage(content=json.dumps(response))], "result": response["result"]}
    else:
        return {"messages": [response]}

researcher_graph = StateGraph(ResearcherState)
researcher_graph.add_node("researcher", researcher_llm_node)
researcher_graph.add_node("tools", ToolNode(research_tools))
researcher_graph.add_edge(START, "researcher")
researcher_graph.add_conditional_edges(
    "researcher",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
researcher_graph.add_edge("tools", "researcher")
compiled_researcher_graph = researcher_graph.compile()


########################################################
# < Expert Tools >
########################################################
python_repl_tool = PythonREPLTool()
ureg = pint.UnitRegistry()

@tool
def unit_converter(quantity: str, to_unit: str) -> str:
    """
    Convert a quantity to a different unit.
    Args:
        quantity: A string like '10 meters', '5 kg', '32 fahrenheit'
        to_unit: The unit to convert to, e.g. 'ft', 'lbs', 'celsius'
    Returns:
        The converted value as a string.
    """
    try:
        logger.info(f"Unit converter converting {quantity} to {to_unit}")
        q = ureg(quantity)
        result = q.to(to_unit)
        logger.info(f"Unit converter result: {result}")
        return str(result)
    except Exception as e:
        error_msg = f"Error: {e}"
        logger.error(f"Unit converter failed: {error_msg}")
        return error_msg


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic math expression. Supports +, -, *, /, **, and parentheses."""
    import math
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }

    try:
        logger.info(f"Calculator evaluating expression: {expression}")
        result = eval(expression, {"__builtins__": None}, allowed_names)
        logger.info(f"Calculator result: {result}")
        return str(result)
    except Exception as e:
        error_msg = f"Error evaluating expression: {e}"
        logger.error(f"Calculator failed: {error_msg}")
        return error_msg

expert_tools = [python_repl_tool, unit_converter, calculator]

########################################################
# < Expert Graph >
########################################################
llm_expert_with_tools = llm_expert.bind_tools(expert_tools)

def is_final_output(response, output_schema_keys):
    if isinstance(response, dict):
        return all(key in response for key in output_schema_keys)
    try:
        data = json.loads(response)
        return all(key in data for key in output_schema_keys)
    except Exception:
        return False


def expert_llm_node(state: ExpertState) -> ExpertState:
    output_schema = {"expert_answer": str, "reasoning_trace": str}
    llm_expert_structured = llm_expert.with_structured_output(output_schema, method="json_mode")
    sys_prompt = make_research_steps_and_results(expert_system_prompt, state["question"], state["research_steps"], state["research_results"])
    sys_prompt = [SystemMessage(content=sys_prompt)]
    response = llm_expert_structured.invoke(sys_prompt + state["messages"])    
    if is_final_output(response, output_schema.keys()):
        state["expert_answer"] = response["expert_answer"]
        state["expert_reasoning"] = response["reasoning_trace"]
        response = AIMessage(content=f"Expert answer: {state['expert_answer']}\nExpert reasoning: {state['expert_reasoning']}")
    return {"messages": [response]}

expert_graph = StateGraph(ExpertState)
expert_graph.add_node("expert", expert_llm_node)
expert_graph.add_node("tools", ToolNode(expert_tools))
expert_graph.add_edge(START, "expert")
expert_graph.add_conditional_edges(
    "expert",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
expert_graph.add_edge("tools", "expert")
compiled_expert_graph = expert_graph.compile()

########################################################
# < Main Graph Nodes >
########################################################
def input_interface(state: GraphState) -> GraphState:
    """Input interface with error handling and validation."""
    try:
        logger.info("Input interface starting execution")
        
        # Initialize all state fields first to ensure they exist for error handling
        state["agent_messages"] = []
        state["files"] = None
        state["research_steps"] = []
        state["expert_steps"] = []
        state["current_research_index"] = -1
        state["researcher_states"] = dict()
        state["research_results"] = []
        state["expert_state"] = None
        state["expert_answer"] = ""
        state["expert_reasoning"] = ""
        state["critic_planner_decision"] = ""
        state["critic_planner_feedback"] = ""
        state["critic_researcher_decision"] = ""
        state["critic_researcher_feedback"] = ""
        state["critic_expert_decision"] = ""
        state["critic_expert_feedback"] = ""
        state["final_answer"] = ""
        state["final_reasoning_trace"] = ""
        state["current_step"] = "input"
        state["next_step"] = "planner"
        state["retry_count"] = 0
        state["retry_limit"] = 5
        state["error"] = None
        state["error_component"] = None
        
        # Handle question extraction with proper error handling
        if not state.get("messages") or len(state["messages"]) == 0:
            state["question"] = ""
            logger.warning("No messages provided to input interface")
        else:
            question = state["messages"][0].content
            if isinstance(question, str):
                state["question"] = question
            else:
                state["question"] = str(question)
        
        # Validate state after initialization
        if not validate_state(state):
            logger.warning("State validation failed after input interface initialization")
        
        logger.info("Input interface completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Input interface failed: {str(e)}")
        return handle_agent_error(state, "input_interface", e)


########################################################
# < Orchestrator Helper Functions >
########################################################
def determine_next_step(state: GraphState) -> GraphState:
    """Step 1: Determine the next step based on current step and critic decisions"""
    
    # Handle critic decisions and set next step accordingly
    if state["current_step"] == "critic_planner":
        if state["critic_planner_decision"] == "approve":
            if len(state["research_steps"]) > 0:
                state["next_step"] = "researcher"
                # Reset research state for new research phase
                state["current_research_index"] = -1
                state["research_results"] = []
                state["researcher_states"] = dict()
            else:
                state["next_step"] = "expert"
        elif state["critic_planner_decision"] == "reject":
            state["next_step"] = "planner"
            state["retry_count"] += 1
    
    elif state["current_step"] == "critic_researcher":
        if state["critic_researcher_decision"] == "approve":
            # Check if all research steps are completed
            if state["current_research_index"] >= len(state["research_steps"]) - 1:
                state["next_step"] = "expert"
            else:
                state["next_step"] = "researcher"
        elif state["critic_researcher_decision"] == "reject":
            state["next_step"] = "researcher"
            state["retry_count"] += 1
    
    elif state["current_step"] == "critic_expert":
        if state["critic_expert_decision"] == "approve":
            state["next_step"] = "finalizer"
        elif state["critic_expert_decision"] == "reject":
            state["next_step"] = "expert"
            state["retry_count"] += 1
    
    # Handle initial state and non-critic steps
    elif state["current_step"] == "" or state["current_step"] == "input":
        state["next_step"] = "planner"
    elif state["current_step"] == "planner":
        state["next_step"] = "critic_planner"
    elif state["current_step"] == "researcher":
        state["next_step"] = "critic_researcher"
    elif state["current_step"] == "expert":
        state["next_step"] = "critic_expert"
    
    return state


def check_retry_limit(state: GraphState) -> GraphState:
    """Step 2: Check retry count and handle limit exceeded"""
    if state["retry_count"] >= state["retry_limit"]:
        state["next_step"] = "finalizer"
        state["final_answer"] = "The question could not be answered."
        state["final_reasoning_trace"] = "The question could not be answered."
    return state


def execute_next_step(state: GraphState) -> GraphState:
    """Step 3: Execute the next step by setting current_step and sending message"""
    
    # Set current_step = next_step
    state["current_step"] = state["next_step"]
    
    # Send appropriate message based on the current step
    if state["current_step"] == "planner":
        if state["critic_planner_decision"] == "reject":
            # Retry with feedback
            message = {
                "sender": "orchestrator",
                "receiver": "planner",
                "type": "instruction",
                "content": state["critic_planner_feedback"],
                "step_id": None,
            }
        else:
            # Initial planning request
            files_info = ""
            if state["files"]:
                files_info = "\nInclude using following files in the research steps: " + "\n".join(state["files"])
            
            message = {
                "sender": "orchestrator",
                "receiver": "planner",
                "type": "instruction",
                "content": f"Develop a logical plan to answer the following question: {state['question']}{files_info}",
                "step_id": None,
            }
    
    elif state["current_step"] == "critic_planner":
        logical_plan = "\n".join(state["research_steps"]) + "\n" + "\n".join(state["expert_steps"])
        message = {
            "sender": "orchestrator",
            "receiver": "critic_planner",
            "type": "instruction",
            "content": f"Review the following plan to make sure it is a good plan to answer the question. The plan: {logical_plan}",
            "step_id": None,
        }
    
    elif state["current_step"] == "researcher":
        if state["critic_researcher_decision"] == "reject":
            # Retry with feedback
            message = {
                "sender": "orchestrator",
                "receiver": "researcher",
                "type": "instruction",
                "content": state["critic_researcher_feedback"],
                "step_id": state["current_research_index"],
            }
        else:
            # Increment research index for new step
            state["current_research_index"] += 1
            
            if state["current_research_index"] < len(state["research_steps"]):
                message = {
                    "sender": "orchestrator",
                    "receiver": "researcher",
                    "type": "instruction",
                    "content": f"Research the following topic or question: {state['research_steps'][state['current_research_index']]}",
                    "step_id": state["current_research_index"],
                }
            else:
                # All research steps completed
                message = {
                    "sender": "orchestrator",
                    "receiver": "researcher",
                    "type": "instruction",
                    "content": "All research steps completed.",
                    "step_id": state["current_research_index"] - 1,
                }
    
    elif state["current_step"] == "critic_researcher":
        research_result = ""
        if state["current_research_index"] < len(state["research_results"]):
            research_result = state["research_results"][state["current_research_index"]]
        
        message = {
            "sender": "orchestrator",
            "receiver": "critic_researcher",
            "type": "instruction",
            "content": f"Review the following research results to make sure it satisfies the request.\n## The research results: {research_result}",
            "step_id": state["current_research_index"],
        }
    
    elif state["current_step"] == "expert":
        if state["critic_expert_decision"] == "reject":
            # Retry with feedback
            message = {
                "sender": "orchestrator",
                "receiver": "expert",
                "type": "instruction",
                "content": state["critic_expert_feedback"],
                "step_id": None,
            }
        else:
            message = {
                "sender": "orchestrator",
                "receiver": "expert",
                "type": "instruction",
                "content": f"Perform the following step(s) to answer the question: {' '.join(state['expert_steps'])}",
                "step_id": None,
            }
    
    elif state["current_step"] == "critic_expert":
        message = {
            "sender": "orchestrator",
            "receiver": "critic_expert",
            "type": "instruction",
            "content": f"Review the following expert's answer to make sure it answers the question.\n## The expert's answer: {state['expert_answer']}",
            "step_id": None,
        }
    
    elif state["current_step"] == "finalizer":
        message = {
            "sender": "orchestrator",
            "receiver": "finalizer",
            "type": "instruction",
            "content": "Generate the final answer and reasoning trace (logical steps) to answer the question.",
            "step_id": None,
        }
    
    else:
        raise ValueError(f"Invalid current step: {state['current_step']}")
    
    # Send the message
    return send_message(state, cast(AgentMessage, message))


def orchestrator(state: GraphState) -> GraphState:
    """
    Main orchestrator function that coordinates the multi-agent workflow.
    Follows the 4-step process outlined in the logical design:
    1. Determine the next step
    2. Check retry count
    3. Execute the next step
    4. Return state
    """
    try:
        logger.info(f"Orchestrator starting execution. Current step: {state.get('current_step', 'unknown')}")
        
        # Check for error state first
        if state.get("error"):
            logger.warning(f"Error state detected: {state['error']} from {state.get('error_component', 'unknown')}")
            # Route to finalizer if there's an error
            state["next_step"] = "finalizer"
            if not state.get("final_answer"):
                state["final_answer"] = f"The question could not be answered due to an error: {state['error']}"
            if not state.get("final_reasoning_trace"):
                state["final_reasoning_trace"] = f"System encountered an error in {state.get('error_component', 'unknown component')}: {state['error']}"
            return state
        
        # Step 1: Determine the next step
        state = determine_next_step(state)
        
        # Step 2: Check retry count
        state = check_retry_limit(state)
        
        # Step 3: Execute the next step
        state = execute_next_step(state)
        
        # Step 4: Validate state and return
        if not validate_state(state):
            logger.warning("State validation failed in orchestrator")
        
        logger.info(f"Orchestrator completed successfully. Next step: {state.get('next_step', 'unknown')}")
        return state
        
    except Exception as e:
        logger.error(f"Orchestrator failed: {str(e)}")
        return handle_agent_error(state, "orchestrator", e)


def planner(state: GraphState) -> GraphState:
    """Planner agent with error handling and validation."""
    try:
        logger.info("Planner starting execution")
        
        output_schema = {"research_steps": list[str], "expert_steps": list[str]}
        # Accesses messages between the orchestrator and the planner only.
        sys_prompt = [SystemMessage(content=planner_system_prompt)]
        message_history = get_agent_conversation(state, "planner")
        message_in = convert_agent_messages_to_langchain(message_history)
        
        # LLM call with error handling
        response = llm_planner.with_structured_output(output_schema, method="json_mode").invoke(sys_prompt + message_in)
        
        # Validate response
        if not validate_llm_response(response, ["research_steps", "expert_steps"], "planner"):
            raise ValueError("Invalid LLM response structure")
        
        state["research_steps"] = response.get("research_steps", [])
        state["expert_steps"] = response.get("expert_steps", [])

        agent_message: AgentMessage = {
            "sender": "planner",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Plan complete.\n## The research steps are:\n{state['research_steps']}\n\n## And the expert steps are:\n{state['expert_steps']}",
            "step_id": None,
        }
        state = send_message(state, agent_message)
        
        # Validate state after execution
        if not validate_state(state):
            logger.warning("State validation failed after planner execution")
        
        logger.info("Planner completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Planner failed: {str(e)}")
        return handle_agent_error(state, "planner", e)


def researcher_node(state: GraphState) -> GraphState:
    """Researcher agent with error handling and validation."""
    try:
        logger.info(f"Researcher starting execution for step {state['current_research_index']}")
        
        idx = state["current_research_index"]
        message_history = get_agent_conversation(state, "researcher", step_id=idx)
        message_in = convert_agent_messages_to_langchain(message_history)
        
        # Get or create ResearcherState for this step
        if idx not in state["researcher_states"]:
            researcher_state = ResearcherState(
                messages=message_in,
                step_index=idx,
                result=None
            )
        else:
            researcher_state = state["researcher_states"][idx]
            researcher_state["messages"].append(message_in[-1])

        # Pass to subgraph with error handling
        try:
            researcher_state = cast(ResearcherState, compiled_researcher_graph.invoke(researcher_state))
        except Exception as subgraph_error:
            logger.error(f"Researcher subgraph failed: {str(subgraph_error)}")
            raise subgraph_error
            
        state["researcher_states"][idx] = researcher_state
        
        # If complete, store result
        if len(state["research_results"]) <= idx:
            state["research_results"].append(researcher_state["result"])
        else:
            state["research_results"][idx] = researcher_state["result"]

        # Generates a message to the orchestrator agent that the research is complete
        agent_message: AgentMessage = {
            "sender": "researcher",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Research complete. The research results are:\n{state['research_results'][idx]}",
            "step_id": idx,
        }
        state = send_message(state, agent_message)
        
        # Validate state after execution
        if not validate_state(state):
            logger.warning("State validation failed after researcher execution")
        
        logger.info(f"Researcher completed successfully for step {idx}")
        return state
        
    except Exception as e:
        logger.error(f"Researcher failed: {str(e)}")
        return handle_agent_error(state, "researcher", e)



def expert(state: GraphState) -> GraphState:
    """Expert agent with error handling and validation."""
    try:
        logger.info("Expert starting execution")
        
        message_history = get_agent_conversation(state, "expert")
        message_in = [convert_agent_messages_to_langchain(message_history)[-1]]
        
        expert_state = state["expert_state"]
        if expert_state is None:
            expert_state = ExpertState(
                messages=message_in,
                question=state["question"],
                research_steps=state["research_steps"],
                research_results=state["research_results"],
                expert_answer="",
                expert_reasoning="",
            )
        else:
            expert_state["messages"].extend(message_in)
            
        # Pass to subgraph with error handling
        try:
            expert_state = cast(ExpertState, compiled_expert_graph.invoke(expert_state))
        except Exception as subgraph_error:
            logger.error(f"Expert subgraph failed: {str(subgraph_error)}")
            raise subgraph_error
            
        state["expert_state"] = expert_state
        state["expert_answer"] = expert_state["expert_answer"]
        state["expert_reasoning"] = expert_state["expert_reasoning"]

        agent_message: AgentMessage = {
            "sender": "expert",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Expert complete. The expert answer is:\n{expert_state['expert_answer']}\n\n## The reasoning trace is:\n{expert_state['expert_reasoning']}",
            "step_id": None,
        }
        state = send_message(state, cast(AgentMessage, agent_message))
        
        # Validate state after execution
        if not validate_state(state):
            logger.warning("State validation failed after expert execution")
        
        logger.info("Expert completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Expert failed: {str(e)}")
        return handle_agent_error(state, "expert", e)


########################################################
# < Critic Helper Functions >
########################################################
def handle_critic_planner_review(state: GraphState) -> GraphState:
    """Handle critic review of planner's work with error handling"""
    try:
        logger.info("Critic planner review starting")
        
        output_schema = {"decision": Literal["approve", "reject"], "feedback": str}
        
        sys_prompt = [SystemMessage(content=critic_planner_system_prompt.format(question=state["question"]))]
        message_history = [get_agent_conversation(state, "critic_planner")[-1]]
        message_in = convert_agent_messages_to_langchain(message_history)
        
        response = llm_critic.with_structured_output(output_schema, method="json_mode").invoke(sys_prompt + message_in)
        
        # Validate response
        if not validate_llm_response(response, ["decision", "feedback"], "critic_planner"):
            raise ValueError("Invalid critic response structure")
        
        state["critic_planner_decision"] = response["decision"]
        state["critic_planner_feedback"] = response["feedback"]
        
        planner_message: AgentMessage = {
            "sender": "critic_planner",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Critic of the planner's plan complete. The decision is:\n{response['decision']}\n\n## The feedback is:\n{response['feedback']}",
            "step_id": None,
        }
        
        logger.info(f"Critic planner review completed with decision: {response['decision']}")
        return send_message(state, planner_message)
        
    except Exception as e:
        logger.error(f"Critic planner review failed: {str(e)}")
        return handle_agent_error(state, "critic_planner", e)


def handle_critic_researcher_review(state: GraphState) -> GraphState:
    """Handle critic review of researcher's work with error handling"""
    try:
        logger.info(f"Critic researcher review starting for step {state['current_research_index']}")
        
        output_schema = {"decision": Literal["approve", "reject"], "feedback": str}
        
        sys_prompt = [SystemMessage(content=critic_researcher_system_prompt.format(research_request=state["research_steps"][state["current_research_index"]]))]
        message_history = [get_agent_conversation(state, "critic_researcher", step_id=state["current_research_index"])[-1]]
        message_in = convert_agent_messages_to_langchain(message_history)
        
        response = llm_critic.with_structured_output(output_schema, method="json_mode").invoke(sys_prompt + message_in)
        
        # Validate response
        if not validate_llm_response(response, ["decision", "feedback"], "critic_researcher"):
            raise ValueError("Invalid critic response structure")
        
        state["critic_researcher_decision"] = response["decision"]
        state["critic_researcher_feedback"] = response["feedback"]
        
        researcher_message: AgentMessage = {
            "sender": "critic_researcher",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Critic of the researcher's work complete. The decision is:\n{response['decision']}\n\n## The feedback is:\n{response['feedback']}",
            "step_id": state["current_research_index"],
        }
        
        logger.info(f"Critic researcher review completed with decision: {response['decision']}")
        return send_message(state, researcher_message)
        
    except Exception as e:
        logger.error(f"Critic researcher review failed: {str(e)}")
        return handle_agent_error(state, "critic_researcher", e)


def handle_critic_expert_review(state: GraphState) -> GraphState:
    """Handle critic review of expert's work with error handling"""
    try:
        logger.info("Critic expert review starting")
        
        output_schema = {"decision": Literal["approve", "reject"], "feedback": str}
        
        sys_prompt = [SystemMessage(content=make_research_steps_and_results(critic_expert_system_prompt, state["question"], state["research_steps"], state["research_results"]))]
        message_history = [get_agent_conversation(state, "critic_expert")[-1]]
        message_in = convert_agent_messages_to_langchain(message_history)
        
        response = llm_critic.with_structured_output(output_schema, method="json_mode").invoke(sys_prompt + message_in)
        
        # Validate response
        if not validate_llm_response(response, ["decision", "feedback"], "critic_expert"):
            raise ValueError("Invalid critic response structure")
        
        state["critic_expert_decision"] = response["decision"]
        state["critic_expert_feedback"] = response["feedback"]
        
        expert_message: AgentMessage = {
            "sender": "critic_expert",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Critic of the expert's work complete. The decision is:\n{response['decision']}\n\n## The feedback is:\n{response['feedback']}",
            "step_id": None,
        }
        
        logger.info(f"Critic expert review completed with decision: {response['decision']}")
        return send_message(state, expert_message)
        
    except Exception as e:
        logger.error(f"Critic expert review failed: {str(e)}")
        return handle_agent_error(state, "critic_expert", e)


def critic(state: GraphState) -> GraphState:
    """Main critic function that routes to appropriate critic type based on current_step"""
    try:
        logger.info(f"Critic starting execution for step: {state['current_step']}")
        
        if state["current_step"] == "critic_planner":
            result = handle_critic_planner_review(state)
        elif state["current_step"] == "critic_researcher":
            result = handle_critic_researcher_review(state)
        elif state["current_step"] == "critic_expert":
            result = handle_critic_expert_review(state)
        else:
            raise ValueError(f"Invalid critic step: {state['current_step']}")
        
        logger.info(f"Critic completed successfully for step: {state['current_step']}")
        return result
        
    except Exception as e:
        logger.error(f"Critic failed: {str(e)}")
        return handle_agent_error(state, "critic", e)


def finalizer(state: GraphState) -> GraphState:
    """Finalizer agent with error handling and validation."""
    try:
        logger.info("Finalizer starting execution")
        
        output_schema = {"final_answer": str, "final_reasoning_trace": str}
        sys_prompt = [SystemMessage(content=finalizer_system_prompt.format(question=state["question"], research_steps=state["research_steps"], expert_steps=state["expert_steps"], expert_answer=state["expert_answer"], expert_reasoning=state["expert_reasoning"]))]
        message_history = get_agent_conversation(state, "finalizer")
        message_in = convert_agent_messages_to_langchain(message_history)
        
        response = llm_finalizer.with_structured_output(output_schema, method="json_mode").invoke(sys_prompt + message_in)
        
        # Validate response
        if not validate_llm_response(response, ["final_answer", "final_reasoning_trace"], "finalizer"):
            raise ValueError("Invalid finalizer response structure")
        
        state["final_answer"] = response["final_answer"]
        state["final_reasoning_trace"] = response["final_reasoning_trace"]
        
        agent_message: AgentMessage = {
            "sender": "finalizer",
            "receiver": "orchestrator",
            "type": "response",
            "content": f"Finalizer complete. The final answer is:\n{response['final_answer']}\n\n## The final reasoning trace is:\n{response['final_reasoning_trace']}",
            "step_id": None,
        }
        state = send_message(state, agent_message)
        
        # Validate state after execution
        if not validate_state(state):
            logger.warning("State validation failed after finalizer execution")
        
        logger.info("Finalizer completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Finalizer failed: {str(e)}")
        return handle_agent_error(state, "finalizer", e)

########################################################
# < Conditional Edges >
########################################################
def route_from_orchestrator(state: GraphState) -> str:
    if state["current_step"] == "planner":
        return "planner"
    elif state["current_step"] == "researcher":
        return "researcher"
    elif state["current_step"] == "expert":
        return "expert"
    elif state["current_step"] == "critic_planner":
        return "critic"
    elif state["current_step"] == "critic_researcher":
        return "critic"
    elif state["current_step"] == "critic_expert":
        return "critic"
    elif state["current_step"] == "finalizer":
        return "finalizer"
    else:
        raise ValueError(f"Invalid current step: {state['current_step']}")

########################################################
# < Graph Construction >
########################################################

builder = StateGraph(GraphState)

builder.add_node("input_interface", input_interface)
builder.add_node("orchestrator", orchestrator)
builder.add_node("planner", planner)
builder.add_node("researcher", researcher_node)
builder.add_node("expert", expert)
builder.add_node("critic", critic)
builder.add_node("finalizer", finalizer)

builder.add_edge(START, "input_interface")
builder.add_edge("input_interface", "orchestrator")
builder.add_edge("planner", "orchestrator")
builder.add_edge("researcher", "orchestrator")
builder.add_edge("expert", "orchestrator")
builder.add_edge("critic", "orchestrator")
builder.add_edge("finalizer", END)

builder.add_conditional_edges("orchestrator", route_from_orchestrator, {
        "planner": "planner",
        "researcher": "researcher",
        "expert": "expert",
        "critic": "critic",
        "finalizer": "finalizer"
        }
    )

graph = builder.compile()


#state = graph.invoke({"messages": [HumanMessage(content="What is CRISPR? And who invented it?")]}, {"recursion_limit": 100})
#print(state)