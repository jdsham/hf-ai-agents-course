from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from typing import Any, Literal, Optional, TypedDict, List, Annotated, Callable, Tuple
import operator
import json
import logging
from langchain_openai import ChatOpenAI


from opik.integrations.langchain import OpikTracer
from opik import track

# Create logger for this module (uses root logger configuration from main.py)
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
from langchain_community.document_loaders import TextLoader
import pint


def create_sync_wrapper_for_mcp_tool(async_tool):
    """Create a synchronous wrapper for an asynchronous MCP tool."""
    def sync_wrapper(*args, **kwargs):
        import asyncio
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we are, we need to run in a new thread to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_tool.arun(*args, **kwargs))
                return future.result()
        except RuntimeError:
            # No event loop running, we can create one
            return asyncio.run(async_tool.arun(*args, **kwargs))
    
    # Copy the tool's metadata to the wrapper
    sync_wrapper.__name__ = async_tool.name
    sync_wrapper.__doc__ = async_tool.description
    sync_wrapper.args_schema = async_tool.args_schema
    sync_wrapper.return_direct = async_tool.return_direct
    
    return sync_wrapper

########################################################
# < Graph State & Agent Messages >
########################################################
class AgentMessage(TypedDict):
    timestamp:str
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
    file: Optional[str]
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
    planner_retry_count: int
    researcher_retry_count: int
    expert_retry_count: int
    planner_retry_limit: int
    researcher_retry_limit: int
    expert_retry_limit: int
    retry_failed:bool



########################################################
# < Configuration Types >
########################################################
class AgentConfig():
    """Configuration for an agent."""

    def __init__(self, name:str, provider:str, model:str, temperature:float, output_schema:dict, system_prompt:str|dict, retry_limit:int=None):
        self.name = name
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.output_schema = output_schema
        self.system_prompt = system_prompt
        self.retry_limit = retry_limit

########################################################
# < Validation Utilities >
########################################################
def enforce_json_response(response: Any, component: str) -> dict:
    """Enforce that the LLM response is either a dictionary or a JSON string. If it is a string, try to parse it as JSON.

    Args:
        response (Any): The response from the LLM
        component (str): The component that generated the response

    Raises:
        ValueError: If the response is not a valid JSON string or a dictionary

    Returns:
        dict: The response as a dictionary
    """
    # If the response is a dictionary return it
    if isinstance(response, dict):
        return response
    # If the response is a string, try to parse it as JSON
    try:
        data = json.loads(response)
        return data
    # If the response is not a dictionary or a JSON string, return False
    except Exception:
        raise ValueError(f"{component}: Response is not a dictionary or avalid JSON string: {response}")


def validate_output_matches_json_schema(response: Any, output_schema_keys: list[str]) -> bool:
    """Check if the LLM response has all the expected fields. Assumes the response is a dictionary when evaluating.

    Args:
        response (Any): The response from the LLM
        output_schema_keys (list[str]): The expected fields

    Returns:
        bool: True if the response has all the expected fields, False otherwise
    """
    return all(key in response for key in output_schema_keys)


def validate_llm_response(response: Any, expected_fields: List[str], component: str) -> bool:
    """Validate LLM response has expected structure and fields.

    Args:
        response (Any): The response from the LLM
        expected_fields (List[str]): The expected fields
        component (str): The component that generated the response

    Returns:
        dict: The response as a dictionary

    Raises:
        KeyError: If the response does not contain all the expected fields
    """
    response = enforce_json_response(response, component)
    
    if not validate_output_matches_json_schema(response, expected_fields):
        raise KeyError(f"{component}: Response does not contain all expected fields. Expected fields: {expected_fields}, Response: {response}")
    
    return response

########################################################
# < Inter-Agent Communication >
########################################################
def compose_agent_message(sender: str, receiver: str, type: str, content: str, step_id: Optional[int] = None) -> AgentMessage:
    """
    Composes an agent message using the AgentMessage protocol and data structure.
    
    Args:
        sender: str - The entity sending the message, either an agent or the orchestrator
        receiver: str - The entity receiving the message, either an agent or the orchestrator
        type: str - The type of message that is being sent: instruction, response, feedback
        content: str - The message content / message body
        step_id: Optional[int] - Optional. The specific research step id associated with message being composed
        
    Returns:
        AgentMessage - The composed message as an AgentMessage
    """
    # Step 1: Get the current timestamp
    import datetime
    current_timestamp = datetime.datetime.now().isoformat()
    
    # Step 2: Take the inputs and current timestamp, and use them to compose an AgentMessage type variable that follows the AgentMessage data structure
    agent_message: AgentMessage = {
        "sender": sender,
        "receiver": receiver,
        "type": type,
        "content": content,
        "step_id": step_id,
        "timestamp": current_timestamp
    }
    
    # Step 3: Return the composed message
    logging.debug(f"Agent message composed successfully: {agent_message}")
    return agent_message

def send_message(state: GraphState, message: AgentMessage) -> GraphState:
    """Send a message to the agent.

    Args:
        state (GraphState): The current state of the graph
        message (AgentMessage): The message to send

    Returns:
        GraphState: The updated state of the graph
    """
    state["agent_messages"].append(message)
    return state

def get_agent_conversation(state: GraphState, agent_name: str, types: Optional[List[str]] = None, step_id: Optional[int] = None) -> List[AgentMessage]:
    """Get the conversation between the orchestrator and the agent.

    Args:
        state (GraphState): The current state of the graph
        agent_name (str): The name of the agent
        types (Optional[List[str]]): The types of messages to get
        step_id (Optional[int]): The step id to get messages for

    Returns:
        List[AgentMessage]: The list of AgentMessages
    """
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
    """Convert a list of AgentMessages to a list of LangChain BaseMessages.

    Args:
        messages (List[AgentMessage]): The list of AgentMessages to convert

    Returns:
        List[BaseMessage]: The list of LangChain BaseMessages
    """
    converted_messages = []
    for m in messages:
        if m["sender"] == "orchestrator":
            message = HumanMessage(content=m["content"])
        else:
            message = AIMessage(content=m["content"])
        converted_messages.append(message)
    return converted_messages

########################################################
# < Researcher SubGraph >
########################################################
@tool
def youtube_transcript_tool(url: str) -> str:
    """
    Extract transcript from a YouTube video URL.
    Use this when you need to get the content/transcript from a specific YouTube video.
    
    Args:
        url: The YouTube video URL to extract transcript from
        
    Returns:
        The transcript text from the video
    """
    logger.info(f"YouTube transcript tool processing URL: {url}")
    
    # Load the YouTube video transcript
    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
    documents = loader.load()
    
    if not documents:
        logger.info("No transcript found for YouTube video")
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

@tool
def unstructured_excel_tool(file_path: str) -> list[Document]:
    """
    Load an Excel file and return the content.
    """
    logger.info(f"Loading Excel file: {file_path}")
    loader = UnstructuredExcelLoader(file_path)
    return loader.load()

@tool
def unstructured_powerpoint_tool(file_path: str) -> list[Document]:
    """
    Load a PowerPoint file and return the content.
    """
    logger.info(f"Loading PowerPoint file: {file_path}")
    loader = UnstructuredPowerPointLoader(file_path)
    return loader.load()


@tool
def unstructured_pdf_tool(file_path: str) -> list[Document]:
    """
    Load a PDF file and return the content.
    """
    logger.info(f"Loading PDF file: {file_path}")
    loader = UnstructuredPDFLoader(file_path)
    return loader.load()


@tool
def text_file_tool(file_path: str) -> str:
    """
    Load a text file and return the content.
    """
    logger.info(f"Loading text file: {file_path}")
    loader = TextLoader(file_path)
    documents = loader.load()
    if documents:
        return documents[0].page_content
    else:
        return ""


async def get_browser_mcp_tools(mcp_url: str) -> list:
    """Get the browser MCP tools from the given URL.

    Args:
        mcp_url (str): The URL of the browser MCP

    Returns:
        list: The list of MCP tools with sync wrappers
    """
    async with streamablehttp_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = await load_mcp_tools(session)
            
            # Create sync wrappers for each MCP tool
            sync_mcp_tools = []
            for mcp_tool in mcp_tools:
                sync_tool = create_sync_wrapper_for_mcp_tool(mcp_tool)
                # Convert the sync wrapper back to a LangChain Tool
                from langchain_core.tools import tool
                wrapped_tool = tool(sync_tool)
                sync_mcp_tools.append(wrapped_tool)
            
            return sync_mcp_tools


@tool
def wikipedia_tool(query: str) -> str:
    """
    Search for information on Wikipedia.
    """
    logger.info(f"Wikipedia tool searching for: {query}")
    wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(wiki_client=None))
    return wikipedia_tool.invoke(query)


@tool
def tavily_tool(query: str) -> str:
    """
    Search for information on the web.
    """
    logger.info(f"Tavily tool searching for: {query}")
    tavily_tool = TavilySearch()
    return tavily_tool.invoke(query)
    

async def get_research_tools() -> list[Tool]:
    """Get the research tools.

    Returns:
        list: The list of research tools
    """
    browser_mcp_url = "http://0.0.0.0:3000/mcp"
    mcp_tools = await get_browser_mcp_tools(browser_mcp_url)
    return [
        youtube_transcript_tool,
        tavily_tool,
        wikipedia_tool,
        unstructured_excel_tool,
        unstructured_powerpoint_tool,
        unstructured_pdf_tool,
        text_file_tool,
        *mcp_tools,
    ]

def create_researcher_llm_node(config: AgentConfig, llm_researcher: ChatOpenAI) -> Callable[[ResearcherState], ResearcherState]:
    """Create a researcher LLM node function with the given prompt and LLM.

    Args:
        config (AgentConfig): The configuration for the researcher agent
        llm_researcher (ChatOpenAI): The LLM for the researcher agent

    Returns:
        Callable[[ResearcherState], ResearcherState]: The researcher LLM node function
    """
    def researcher_llm_node(state: ResearcherState) -> ResearcherState:
        """Researcher LLM node function with the given prompt and LLM."""
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        response = llm_researcher.invoke(sys_prompt + state["messages"])
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"Researcher tool calls: {response.tool_calls}")
        return {"messages": [response]}
    return researcher_llm_node

def create_researcher_subgraph(researcher_llm_node: Callable, research_tools: list) -> StateGraph:
    """Create and compile a researcher subgraph with the given prompt and LLM.

    Args:
        researcher_llm_node (Callable): The researcher LLM node function
        research_tools (list): The list of research tools

    Returns:
        StateGraph: The compiled researcher subgraph
    """
    researcher_graph = StateGraph(ResearcherState)
    researcher_graph.add_node("researcher", researcher_llm_node)
    researcher_graph.add_node("tools", ToolNode(research_tools))
    researcher_graph.add_edge(START, "researcher")
    researcher_graph.add_conditional_edges("researcher", tools_condition)
    researcher_graph.add_edge("tools", "researcher")
    return researcher_graph.compile()

########################################################
# < Expert SubGraph >
########################################################
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
    logger.info(f"Unit converter converting {quantity} to {to_unit}")
    ureg = pint.UnitRegistry()
    q = ureg(quantity)
    result = q.to(to_unit)
    logger.info(f"Unit converter result: {result}")
    return str(result)


@tool
def calculator(expression: str) -> str:
    """Evaluate a basic math expression. Supports +, -, *, /, **, and parentheses.

    Args:
        expression (str): The math expression to evaluate

    Returns:
        str: The result of the expression
    """
    logger.info(f"Calculator evaluating expression: {expression}")
    import math
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    result = eval(expression, {"__builtins__": None}, allowed_names)
    logger.info(f"Calculator result: {result}")
    return str(result)


@tool
def python_repl_tool(code: str) -> str:
    """
    Use this when you need to run Python code.
    Args:
        code: The Python code to execute
    Returns:
        The result of the code execution as a string.
    """
    logger.info(f"Executing the following python code: {code}")
    python_repl_tool = PythonREPLTool()
    return python_repl_tool.invoke(code)


def get_expert_tools() -> List[Tool]:
    """Get the expert tools.

    Returns:
        list: The list of expert tools
    """
    return [unit_converter, calculator, python_repl_tool]


def create_expert_llm_node(config: AgentConfig, llm_expert: ChatOpenAI) -> Callable[[ExpertState], ExpertState]:
    """Create an expert LLM node function with the given prompt and LLM."""
    def expert_llm_node(state: ExpertState) -> ExpertState:
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        response = llm_expert.invoke(sys_prompt + state["messages"])    
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"Expert tool calls: {response.tool_calls}")
        return {"messages": [response]}
    return expert_llm_node


def create_expert_subgraph(expert_llm_node: Callable, expert_tools: list) -> StateGraph:
    """Create and compile an expert subgraph with the given prompt and LLM."""
    expert_graph = StateGraph(ExpertState)
    expert_graph.add_node("expert", expert_llm_node)
    expert_graph.add_node("tools", ToolNode(expert_tools))
    expert_graph.add_edge(START, "expert")
    expert_graph.add_conditional_edges("expert", tools_condition)
    expert_graph.add_edge("tools", "expert")
    return expert_graph.compile()


########################################################
# < Main Graph Nodes >
########################################################
def create_input_interface(agent_configs: dict[str, AgentConfig]):
    """Create an input interface function with the given retry limit."""
    def input_interface(state: GraphState) -> GraphState:
        """Input interface with error handling and validation."""
        logger.info("Input interface starting execution")
        
        # Handle question extraction with proper error handling
        if not state.get("question") or len(state["question"]) == 0:
            raise ValueError("No question provided to input interface")

        # Initialize all state fields first to ensure they exist for error handling
        state["file"] = state["file"] if state["file"] else None
        # Planner Work
        state["research_steps"] = []
        state["expert_steps"] = []
        # Researcher Work
        state["current_research_index"] = -1
        state["researcher_states"] = dict()
        state["research_results"] = []
        # Expert Work
        state["expert_state"] = None
        state["expert_answer"] = ""
        state["expert_reasoning"] = ""
        # Critic Work
        state["critic_planner_decision"] = ""
        state["critic_planner_feedback"] = ""
        state["critic_researcher_decision"] = ""
        state["critic_researcher_feedback"] = ""
        state["critic_expert_decision"] = ""
        state["critic_expert_feedback"] = ""
        # Finalizer Work
        state["final_answer"] = ""
        state["final_reasoning_trace"] = ""
        # Orchestrator Work
        state["agent_messages"] = []
        state["current_step"] = "input"
        state["next_step"] = "planner"
        # Retry counts and limits
        state["planner_retry_count"] = 0
        state["researcher_retry_count"] = 0
        state["expert_retry_count"] = 0
        state["planner_retry_limit"] = agent_configs["planner"].retry_limit
        state["researcher_retry_limit"] = agent_configs["researcher"].retry_limit
        state["expert_retry_limit"] = agent_configs["expert"].retry_limit
        state["retry_failed"] = False
        
        logger.info("Input interface completed successfully")
        return state
    
    return input_interface


########################################################
# < Orchestrator Helper Functions >
########################################################
def determine_next_step(state: GraphState) -> GraphState:
    """Orchestrator logic to determine the next step based on current step and critic decisions.
    Handles critic decisions and sets the next step accordingly.
    Handles initial state and non-critic steps.
    Handles retry counter incrementation.

    Args:
        state (GraphState): The current state of the graph

    Returns:
        GraphState: The updated state of the graph
    """
    
    # Handle critic decisions and set next step accordingly
    if state["current_step"] == "critic_planner":
        if state["critic_planner_decision"] == "approve":
            logger.info("Planner approved.")
            if len(state["research_steps"]) > 0:
                state["next_step"] = "researcher"
            else:
                state["next_step"] = "expert"
        elif state["critic_planner_decision"] == "reject":
            state["next_step"] = "planner"
            state["planner_retry_count"] += 1
            logger.info(f"Planner rejected. Retry count: {state['planner_retry_count']}")
    
    elif state["current_step"] == "critic_researcher":
        if state["critic_researcher_decision"] == "approve":
            logger.info("Researcher approved.")
            # Check if all research steps are completed
            if state["current_research_index"] + 1 >= len(state["research_steps"]):
                state["next_step"] = "expert"
            else:
                state["next_step"] = "researcher"
        elif state["critic_researcher_decision"] == "reject":
            state["next_step"] = "researcher"
            state["researcher_retry_count"] += 1
            logger.info(f"Researcher rejected. Retry count: {state['researcher_retry_count']}")
    
    elif state["current_step"] == "critic_expert":
        if state["critic_expert_decision"] == "approve":
            logger.info("Expert approved.")
            state["next_step"] = "finalizer"
        elif state["critic_expert_decision"] == "reject":
            state["next_step"] = "expert"
            state["expert_retry_count"] += 1
            logger.info(f"Expert rejected. Retry count: {state['expert_retry_count']}")
    
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
    """Orchestrator logic to check retry count and handle limit exceeded.
    Handles retry limit exceeded and sets the next step to finalizer.
    Handles graceful failure and sets the final answer and reasoning trace.

    Args:
        state (GraphState): The current state of the graph

    Returns:
        GraphState: The updated state of the graph
    """
    if (state["planner_retry_count"] >= state["planner_retry_limit"] 
        or state["researcher_retry_count"] >= state["researcher_retry_limit"] 
        or state["expert_retry_count"] >= state["expert_retry_limit"]):
        # Log the failure
        logger.info(f"Graceful Failure: Retry limit exceeded for {state['next_step']}")
        state["retry_failed"] = True
        state["next_step"] = "finalizer"
        state["final_answer"] = "The question could not be answered."
        state["final_reasoning_trace"] = "The question could not be answered."
    return state


orchestrator_msg_to_critic_planner = """
Use the following context to answer the User Question:

## Context:

### Planner Task
The planner was asked to develop a logical plan to answer the following input question:
{question}

### Planner Plan
The planner determined the following research steps were needed to answer the question: 
{research_steps}

The planner determined the following expert steps were needed to answer the question:
{expert_steps}

## The User Question:
Does the planner's plan have the correct and logical research and expert steps needed to answer the input question? If yes, approve. If no, reject.
If rejected, provide direct feedback on how the planner could improve their plan, to a satisfactory level.
"""

orchestrator_msg_to_critic_planner_with_file = """
Use the following context to answer the User Question:

## Context:

### Planner Task
The planner was asked to develop a logical plan to answer the following input question:
{question}

### File
The following file must be used in reference to answer the question:
{file}

### Planner Plan
The planner determined the following research steps were needed to answer the question: 
{research_steps}

The planner determined the following expert steps were needed to answer the question:
{expert_steps}

## The User Question:
Does the planner's plan have the correct and logical research and expert steps needed to answer the input question?
Does it also include the file in the research steps?
If yes, approve. If no, reject.
If rejected, provide direct feedback on how the planner could improve their plan, to a satisfactory level.
"""

orchestrator_msg_to_critic_researcher = """
Use the following context and recommended instructions to answer the User Question:

## Context:

### Research Topic
The researcher was asked to research the following topic: {research_topic}

### Research Results
The researcher's results are: 
{research_results}

## The User Question:
Does the researcher's results contain sufficient information on the topic? If yes, approve. If no, reject.
If rejected, provide direct feedback on how the researcher could improve their research, to a satisfactory level.
"""

orchestrator_msg_to_expert = """
Use the following context and recommended instructions to answer the User Question:

## Context:

### Researched Information:
{research_results}

### Recommended Instructions:
It was recommended to perform the following steps to answer the question:
{expert_steps}

## The User Question:
Answer the question: {question}
"""


orchestrator_msg_to_critic_expert = """
Use the following context answer the User Question:

## Context
### Expert Question
The expert was asked to answer the following question: {question}

### Researched Information:
The expert had the following researched information to use to answer the question:
{research_results}

### Expert Answer:
The expert gave the following answer and reasoning:
Expert answer: 
{expert_answer}

Expert reasoning: 
{expert_reasoning}

## User Question:
Does the expert's answer actually answer the question to a satisfactory level? If yes, approve. If no, reject.
If rejected, provide direct feedback on how the expert could improve their answer, to a satisfactory level."
"""

orchestrator_msg_to_finalizer = """
Use the following context to perform the User Task:

## Context
### The question that had to be answered:
{question}

### The research steps are:
{research_steps}

### The expert steps are:
{expert_steps}

### The expert's answer is:
{expert_answer}

### The expert's reasoning is:
{expert_reasoning} 


## User Task
Generate the final answer and reasoning trace (logical steps) to answer the question.
"""

orchestrator_msg_to_finalizer_retry_failed = """
Generate the output with the following content:
{
    "final_answer": "The question could not be answered.",
    "final_reasoning_trace": "The question could not be answered."
}
"""


def execute_next_step(state: GraphState) -> GraphState:
    """Orchestrator logic to execute the next step by setting current_step and sending message.
    Handles the different steps and sends the appropriate message.
    Includes any context needed in the message.

    Args:
        state (GraphState): The current state of the graph

    Returns:
        GraphState: The updated state of the graph
    """
    
    # Set current_step = next_step
    state["current_step"] = state["next_step"]
    
    # Send appropriate message based on the current step
    if state["current_step"] == "planner":
        if state["critic_planner_decision"] == "reject":
            # Retry with feedback
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "planner",
                type= "instruction",
                content= f"Use the following feedback to improve the plan:\n{state['critic_planner_feedback']}",
            )
        else:
            # Initial planning request
            file_info = ""
            if state["file"]:
                file_info = "\n\nInclude using following file in any of the research steps:" + "\n".join(state["file"])
            
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "planner",
                type= "instruction",
                content= f"Develop a logical plan to answer the following question:\n{state['question']}{file_info}",
            )
    
    elif state["current_step"] == "critic_planner":
        # Add context to the last message to the critic.

        if state["file"]:
            content = orchestrator_msg_to_critic_planner_with_file.format(question=state["question"], file=state["file"], research_steps=state["research_steps"], expert_steps=state["expert_steps"])
        else:
            content = orchestrator_msg_to_critic_planner.format(question=state["question"], research_steps=state["research_steps"], expert_steps=state["expert_steps"])
        message = compose_agent_message(
            sender= "orchestrator",
            receiver= "critic_planner",
            type= "instruction",
            content= content,
        )
    elif state["current_step"] == "researcher":
        if state["critic_researcher_decision"] == "reject":
            # Retry with feedback
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "researcher",
                type= "instruction",
                content= f"Use the following feedback to improve the research:\n{state["critic_researcher_feedback"]}",
                step_id=state["current_research_index"],
            )
        else:
            # Increment research index for new step
            state["current_research_index"] += 1
            
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "researcher",
                type= "instruction",
                content= f"Research the following topic or question: {state['research_steps'][state['current_research_index']]}",
                step_id= state["current_research_index"],
            )   
    elif state["current_step"] == "critic_researcher":
        message = compose_agent_message(
            sender= "orchestrator",
            receiver= "critic_researcher",
            type= "instruction",
            content= orchestrator_msg_to_critic_researcher.format(research_topic=state["research_steps"][state["current_research_index"]], research_results=state["research_results"][state["current_research_index"]]),
        )
    elif state["current_step"] == "expert":
        if state["critic_expert_decision"] == "reject":
            # Retry with feedback
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "expert",
                type= "instruction",
                content= f"Use the following feedback to improve your answer:\n{state["critic_expert_feedback"]}",
            )
        else:
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "expert",
                type= "instruction",
                content= orchestrator_msg_to_expert.format(research_results=state["research_results"], expert_steps=state["expert_steps"], question=state["question"]),
            )
    
    elif state["current_step"] == "critic_expert":
        message = compose_agent_message(
            sender= "orchestrator",
            receiver= "critic_expert",
            type= "instruction",
            content= orchestrator_msg_to_critic_expert.format(question=state["question"], research_results=state["research_results"], expert_answer=state["expert_answer"], expert_reasoning=state["expert_reasoning"]),
        )
    
    elif state["current_step"] == "finalizer":
        if state["retry_failed"]:
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "finalizer",
                type= "instruction",
                content= orchestrator_msg_to_finalizer_retry_failed,
            )
        else:
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "finalizer",
                type= "instruction",
                content= orchestrator_msg_to_finalizer.format(question=state["question"], research_steps=state["research_steps"], expert_steps=state["expert_steps"], expert_answer=state["expert_answer"], expert_reasoning=state["expert_reasoning"]),
            )
    
    else:
        raise ValueError(f"Invalid current step: {state['current_step']}")
    
    # Send the message
    send_message(state, message)
    return state

@track
def orchestrator(state: GraphState) -> GraphState:
    """Orchestrator logic to coordinate the multi-agent workflow.
    Follows the 4-step process outlined in the logical design:
    1. Determine the next step
    2. Check retry count and handle limit exceeded
    3. Execute the next step by setting current_step and sending message
    4. Return state

    Args:
        state (GraphState): The current state of the graph

    Returns:
        GraphState: The updated state of the graph
    """
    
    logger.info(f"Orchestrator starting execution. Current step: {state.get('current_step', 'unknown')}")
        
    # Step 1: Determine the next step
    state = determine_next_step(state)
    
    # Step 2: Check retry count
    state = check_retry_limit(state)
    
    # Step 3: Execute the next step
    state = execute_next_step(state)
    
    logger.info(f"Orchestrator completed successfully. Next step: {state.get('next_step', 'unknown')}")
    return state

########################################################
# < Conditional Edges >
########################################################
def route_from_orchestrator(state: GraphState) -> str:
    """Route the state to the appropriate agent based on the current step.

    Args:
        state (GraphState): The current state of the graph

    Returns:
        str: The name of the agent to route to
    """
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
# < Graph Factory Function >
########################################################

def create_planner_agent(config: AgentConfig, llm_planner: ChatOpenAI) -> Callable[[GraphState], GraphState]:
    """Create a planner agent function with the given prompt and LLM."""
    #@track
    def planner_agent(state: GraphState) -> GraphState:
        """Planner agent with injected prompt."""
        logger.info("Planner starting execution")
        
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        message_history = get_agent_conversation(state, "planner")
        message_in = convert_agent_messages_to_langchain(message_history)
        
        response = llm_planner.invoke(sys_prompt + message_in)
        
        # Validate response
        response = validate_llm_response(response, config.output_schema.keys(), "planner")
        
        state["research_steps"] = response["research_steps"]
        state["expert_steps"] = response["expert_steps"]
        
        agent_message = compose_agent_message(
            sender= "planner",
            receiver= "orchestrator",
            type= "response",
            content= f"Planner complete. Research steps: {response['research_steps']}, Expert steps: {response['expert_steps']}",   
        )
        state = send_message(state, agent_message)
        
        
        logger.info("Planner completed successfully")
        return state    
    return planner_agent

   
def create_researcher_agent(config: AgentConfig, compiled_researcher_graph:Callable) -> Callable[[GraphState], GraphState]:
    """Create a researcher agent function with the given prompt and LLM."""
    #@track
    def researcher_agent(state: GraphState) -> GraphState:
        """Researcher agent with injected prompt."""
        logger.info("Researcher starting execution")
        
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

        # Execute research using subgraph
        researcher_state = compiled_researcher_graph.invoke(researcher_state)
        
        # Validate response
        response = validate_llm_response(researcher_state["messages"][-1].content, config.output_schema.keys(), f"researcher step {state['current_research_index']}")
        # Store response in ResearcherState in case of text JSON response
        researcher_state["result"] = response["result"]

        # Update ResearcherState in state
        state["researcher_states"][idx] = researcher_state

        # Store results
        if len(state["research_results"]) <= idx:
            state["research_results"].append(response["result"])
        else:
            state["research_results"][idx] = response["result"]

        # Send response to orchestrator
        agent_message = compose_agent_message(
            sender= "researcher",
            receiver= "orchestrator",
            type= "response",
            content= f"Researcher complete for step {state['current_research_index']}",
            step_id= state["current_research_index"],
        )
        state = send_message(state, agent_message)
        

        logger.info("Researcher completed successfully")
        return state
    return researcher_agent


def create_expert_agent(config: AgentConfig, compiled_expert_graph:Callable) -> Callable[[GraphState], GraphState]:
    """Create an expert agent function with the given prompt and LLM."""

    #@track
    def expert_agent(state: GraphState) -> GraphState:
        """Expert agent with injected prompt."""
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

        # Execute expert reasoning using subgraph
        expert_state = compiled_expert_graph.invoke(expert_state)

        # Validate response
        response = validate_llm_response(expert_state["messages"][-1].content, config.output_schema.keys(), "expert")
        
        # Store response in ExpertState in case of text JSON response
        expert_state["expert_answer"] = response["expert_answer"]
        expert_state["expert_reasoning"] = response["reasoning_trace"]

        # Update ExpertState in state
        state["expert_state"] = expert_state

        # Store results
        state["expert_answer"] = response["expert_answer"]
        state["expert_reasoning"] = response["reasoning_trace"]
        
        agent_message = compose_agent_message(
            sender= "expert",
            receiver= "orchestrator",
            type= "response",
            content= f"Expert complete. Answer: {expert_state['expert_answer']}, Reasoning: {expert_state['expert_reasoning']}",
        )
        state = send_message(state, agent_message)
        
        
        logger.info("Expert completed successfully")
        return state
    
    return expert_agent


def create_critic_agent(config: AgentConfig, llm_critic: ChatOpenAI) -> Callable[[GraphState], GraphState]:
    """Create a critic agent function with the given prompts for different critic types."""
    #@track
    def critic_agent(state: GraphState) -> GraphState:
        """Critic agent with injected prompts for different critic types."""
        logger.info(f"Critic starting execution - {state['current_step']}")


        # Determine which critic to run and get the appropriate prompt
        if state["current_step"] == "critic_planner":
            critic_prompt = config.system_prompt["critic_planner"]
        elif state["current_step"] == "critic_researcher":
            critic_prompt = config.system_prompt["critic_researcher"]
        elif state["current_step"] == "critic_expert":
            critic_prompt = config.system_prompt["critic_expert"]
        else:
            raise RuntimeError(f"Invalid critic step: {state['current_step']}")
        
        sys_prompt = [SystemMessage(content=critic_prompt)]
        message_history = get_agent_conversation(state, state["current_step"])
        message_in = [convert_agent_messages_to_langchain(message_history)[-1]]

        response = llm_critic.invoke(sys_prompt + message_in)
        
        # Validate response
        response = validate_llm_response(response, config.output_schema.keys(), "critic")
        
        # Store critic decision and feedback based on current step
        if state["current_step"] == "critic_planner":
            state["critic_planner_decision"] = response["decision"]
            state["critic_planner_feedback"] = response["feedback"]
        elif state["current_step"] == "critic_researcher":
            state["critic_researcher_decision"] = response["decision"]
            state["critic_researcher_feedback"] = response["feedback"]
        elif state["current_step"] == "critic_expert":
            state["critic_expert_decision"] = response["decision"]
            state["critic_expert_feedback"] = response["feedback"]
        
        message = compose_agent_message(
            sender= "critic",
            receiver= "orchestrator",
            type= "response",
            content= f"Critic complete. Decision: {response['decision']}, Feedback: {response['feedback']}",
        )
        state = send_message(state, message)
        
        
        logger.info("Critic completed successfully")
        return state
    
    return critic_agent


def create_finalizer_agent(config: AgentConfig, llm_finalizer: ChatOpenAI) -> Callable[[GraphState], GraphState]:
    """Create a finalizer agent function with the given prompt and LLM."""
    #@track
    def finalizer_agent(state: GraphState) -> GraphState:
        """Finalizer agent with injected prompt."""
        logger.info("Finalizer starting execution")
        
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        message_history = get_agent_conversation(state, "finalizer")
        message_in = convert_agent_messages_to_langchain(message_history)
        
        response = llm_finalizer.invoke(sys_prompt + message_in)
        
        # Validate response
        response = validate_llm_response(response, config.output_schema.keys(), "finalizer")
        
        state["final_answer"] = response["final_answer"]
        state["final_reasoning_trace"] = response["final_reasoning_trace"]
        
        message = compose_agent_message(
            sender= "finalizer",
            receiver= "orchestrator",
            type= "response",
            content= f"Finalizer complete. The final answer is:\n{response['final_answer']}\n\n## The final reasoning trace is:\n{response['final_reasoning_trace']}",
        )
        state = send_message(state, message)
        
        logger.info("Finalizer completed successfully")
        return state    
    return finalizer_agent


def openai_llm_factory(name:str, model: str, temperature: float, output_schema: dict = None, tools: list = None) -> ChatOpenAI:
    """Create an OpenAI LLM with the given model and temperature.

    Args:
        model (str): The model to use
        temperature (float): The temperature to use
        output_schema (dict): The output schema to use (JSON schema)
    """
    llm = ChatOpenAI(model=model, temperature=temperature)
    if tools:
        llm = llm.bind_tools(tools)
    if output_schema and name not in ("researcher", "expert"):
        llm = llm.with_structured_output(output_schema, method="json_mode")
    return llm


def llm_factory(config:AgentConfig, tools: list = None) -> ChatOpenAI:
    """Get the appropriate LLM factory based on the provider.

    Args:
        config (AgentConfig): The configuration for the agent

    Returns:
        ChatOpenAI: The LLM with structured output
    """
    if config.provider == "openai":
        return openai_llm_factory(config.name, config.model, config.temperature, config.output_schema, tools)
    else:
        raise ValueError(f"Invalid provider: {config.provider}")


def create_multi_agent_graph(agent_configs: dict[str, AgentConfig]) -> Tuple[StateGraph, OpikTracer]:
    """
    Factory function that creates and compiles a multi-agent graph with injected prompts.
    
    Args:
        agent_configs (dict[str, AgentConfig]): Dictionary containing all agent configs
        
    Returns:
        Compiled graph ready for invocation
    """
    # Define Agent Tools
    research_tools = asyncio.run(get_research_tools())
    expert_tools = get_expert_tools()

    # Create LLMs dynamically
    llm_planner = llm_factory(agent_configs["planner"])
    llm_researcher = llm_factory(agent_configs["researcher"], research_tools)
    llm_expert = llm_factory(agent_configs["expert"], expert_tools)
    llm_critic = llm_factory(agent_configs["critic"])
    llm_finalizer = llm_factory(agent_configs["finalizer"])   
   
    # Create Researcher Subgraphs    
    researcher_node = create_researcher_llm_node(agent_configs["researcher"], llm_researcher)
    researcher_graph = create_researcher_subgraph(researcher_node, research_tools)
    
    # Create Expert Subgraphs
    expert_node = create_expert_llm_node(agent_configs["expert"], llm_expert)
    expert_graph = create_expert_subgraph(expert_node, expert_tools)

    # Create agent functions with injected prompts and LLMs
    planner_agent = create_planner_agent(agent_configs["planner"], llm_planner)
    researcher_agent = create_researcher_agent(agent_configs["researcher"], researcher_graph)
    expert_agent = create_expert_agent(agent_configs["expert"], expert_graph)
    critic_agent = create_critic_agent(agent_configs["critic"], llm_critic)
    finalizer_agent = create_finalizer_agent(agent_configs["finalizer"], llm_finalizer)
    
    # Create input interface with retry limit
    input_interface = create_input_interface(agent_configs)
    
    # Build the graph
    builder = StateGraph(GraphState)
    
    builder.add_node("input_interface", input_interface)
    builder.add_node("orchestrator", orchestrator)
    builder.add_node("planner", planner_agent)
    builder.add_node("researcher", researcher_agent)
    builder.add_node("expert", expert_agent)
    builder.add_node("critic", critic_agent)
    builder.add_node("finalizer", finalizer_agent)
    
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
    
    # Compile and return the graph
    app = builder.compile()

    # Create the OpikTracer for LangGraph
    opik_tracer = OpikTracer(graph=app.get_graph(xray=True))
    
    return app, opik_tracer