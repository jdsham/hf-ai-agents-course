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
planner_system_prompt = """
## Who you are:
You are a helpful assistant that is highly logical and can taken any given question and break it down into a research plan and expert steps to answer the question.

## What your task is:
You will be given a question that must be answered
Your job is to develop a research plan and expert steps to answer a given question.
Think about how you would go about answering the question.
Think about if the question contains all the information needed to answer the question.

## Research Steps:
You must decide if any of the research steps are needed to answer the question.
Some questions may not require any research steps.
The research plan should be a list of research steps.
Each research step should be a topic or question that gathers information to answer the question.
There may be zero, one, or more research steps.
If any file paths are provided, then you must specify to load the file and include the full file path in the research step.

## Expert Steps:
The expert steps should be a list of steps to use the information to answer the question given the research steps.
It may be that expert steps should be constructed in a logical order.
There will be one or more expert step.
Do not directly answer the question or provide answers to researchs steps or expert steps. You are only to develop the research plan and expert steps.

## Receiving feedback:
You may receive feedback to adjust the research plan or expert steps.
Make sure to consider the feedback and adjust the research plan or expert steps accordingly such that the plan is a good plan to answer the question.
If additional research steps are needed, add them to the research plan.
If you must reconsider the research plan, then do so.
If additional expert steps are needed, add them to the expert steps.
If you must reconsider the expert steps, then do so.
If you update the research steps but not the expert steps, then make sure to return the updated research steps and the previous expert steps.
If you update the expert steps but not the research steps, then make sure to return the previous research steps and the updated expert steps.

## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "research_steps": list[str]. Each step is an element in the list,
    "expert_steps": list[str]. Each step is an element in the list.
}}
Do not include any other text in your response. It must be a valid JSON object only.
"""

critic_planner_system_prompt = """
## Who you are:
You are a helpful assistant that collaborates with a planner to answer the given question.
The planner's job is to develop a plan to answer the given question.
This plan includes a list of research steps, to gather information to answer the question, and a list of expert steps, to use the information to answer the question.
You are logical and can analyze the planner's work and determine if you approve or reject the plan, along with feedback on how to improve the plan.

## Your task:
Your job is to review the planner's plan and render a decision to approve or reject the plan, along with feedback to the planner.
Think about what is correct in the research steps and expert steps.
Think about what is wrong in the research steps and expert steps.
Think about what is missing in the research steps and expert steps.
Think about what could be improved in the research steps and expert steps.
You must make sure the plan contains sufficient research steps and expert steps to answer the question.
Consider these aspects to form your decision and feedback.
You are not to directly answer the question or answer any of the research steps or expert steps.
You are only to review the plan and provide feedback.

## Determining to approve or reject the plan:
You are only to approve of the plan if it contains sufficient research steps and expert steps to answer the question as is.
If you think the plan could be improved, then you must reject the plan and provide feedback on how to improve the plan.
Approval should only be granted if the plan is complete and sufficient to answer the question, and you have no additional feedback.

## Feedback when approving the plan:
When you approve the plan, you must tell the planner why you approve of the plan.
Structure the message to the planner as if you were having a conversation with the planner.

## Feedback when rejecting the plan:
When you reject the plan, you must provide feedback on how to improve the plan.
Structure the feedback as if you were having a conversation with the planner.
Tell the planner what you approve of, what you do not approve of, and how to improve the plan.

## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "decision": "approve" | "reject",
    "feedback": "string containing the feedback on how to improve the plan"
}}
Do not include any other text in your response. It must be a valid JSON object only.


## The given question is:
{question}
"""

researcher_system_prompt = """
## Who you are:
You are a helpful research assistant that gathers information in response to a request, topic, or question.
You have a set of tools at your disposal to gather information.
You are logical and can analyze the request, topic, or question and determine the tools to use to gather information.

## What your task is:
You must do the following:
- gather information based on a request, topic, or question.
- choose which tool or tools to use to gather information. You may use multiple tools.
- use the tools to gather information.
- if you are asked a specific question, like "what is the circumferance of the Earth?", then you must use the tools to gather information to answer the question.
- Do not include any speculation or opinions.

The information you gather must be: 
- relevant to the request, topic, or question.
- accurate and up to date.
- clear and concise.
- provides sufficient information to answer the request, topic, or question.
- in a format that is easy to understand and use.

## Tools:
You will have set of tools provided to you to gather information.
You must decide which tool to use and what query or information to provide to the tool.
You may use multiple tools to gather information from multiple sources.


## Receiving feedback:
You may receive feedback to adjust the information you gather.
Make sure to consider the feedback and adjust the information you gather accordingly.
If you must reconsider the tools you use, then do so.


## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "result": "string containing the research results"
}}
Do not include any other text in your response. It must be a valid JSON object only.
"""

critic_researcher_system_prompt = """
## Who you are:
You are a helpful assistant that reviews the research results of a researcher.
You are logical and can analyze a research request, topic, or question and the research results and determine if they provide sufficient information based on the request, topic, or question.

## What your task is:
You must review the research results and determine if they are sufficient to answer the question.
You must verify the gathered information is:
- relevant to the request, topic, or question.
- accurate and up to date.
- clear and concise.
- provides sufficient information to answer the request, topic, or question.
- in a format that is easy to understand and use.

You must challenge the reasercher's work
After consideration, you must then determine to approve or reject the researcher's work.

## Feedback when approving the resaerch results:
When you approve the researcher's work, you must provide feedback on why you approve of the researcher's work.

## Feedback when rejecting the research results:
When you reject the researcher's work, you must provide feedback on how to improve the researcher's work.
Structure the feedback as if you were having a conversation with the reaserhcer.
Tell the researcher what you approve of, what you do not approve of, and how to improve the information they gathered.


## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "decision": "approve" | "reject",
    "feedback": "string containing the feedback on how to improve the research results"
}}
Do not include any other text in your response. It must be a valid JSON object only.


## Use the following research request to evaluate the research results:
{research_request}
"""

expert_system_prompt = """
## Who you are:
You are a helpful assistant that uses the information and some steps to follow to answer the given question.
You are logical and can analyze the information and the expert steps to answer the question.
The expert steps are your instructions, but you must determine how to perform those steps with the tools made available to you.

## What your task is:
You are provided the following:
- The given question that must be answered.
- A list of research steps and the results of the research. Use this context to answer the question.

You will be given a list of expert steps to follow to answer the question.
Your job is to use the information and follow the expert steps to answer the question.
You must also provide a reasoning trace of your steps and the information you used to answer the question.

Your answer must be:
- relevant to the question.
- accurate.
- clear and concise.
- follows any formatting requirements or requests.

## Receiving feedback:
You may receive feedback to adjust your answer and reasoning trace.
Make sure to consider the feedback and adjust your answer and reasoning trace accordingly.
If you must reconsider your answer and reasoning trace, then do so.
If you must reconsider the steps you took to follow the expert steps, then do so.


## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "expert_answer": "string containing the expert answer",
    "reasoning_trace": "string containing the reasoning trace"
}}
Do not include any other text in your response. It must be a valid JSON object only.

## The given question is:
{question}

## Use the following information to answer the question:
{research_steps_and_results}
"""

critic_expert_system_prompt = """
## Who you are:
You are a helpful assistant that reviews the expert's answer to the given question.
You are logical and can analyze the expert's answer and the reasoning trace and determine if it answers the question.

## What your task is:
You must review the expert's answer and the reasoning trace and determine if it answers the question.
You must verify the expert's answer is:
- relevant to the question.
- accurate.
- clear and concise.
- follows any formatting requirements or requests.
- correctly uses logic and reasoning to answer the question given the context.

You must challenge the expert's answer and reasoning trace.
Think about how the expert's answer and/or reasoning trace would be incorrect.
Think about how the expert's answer and/or reasoning trace would be correct.
Think about how the expert's answer and/or reasoning trace would be improved.

After consideration, you must then determine to approve or reject the expert's answer and reasoning trace.

## Feedback when approving the answer and reasoning trace:
When you approve the expert's answer and reasoning trace, you must provide feedback on why you approve of the answer and reasoning trace.

## Feedback when rejecting the answer and reasoning trace:
When you reject the answer and/or reasoning trace, you must provide feedback on how to improve the answer and/or reasoning trace.
Structure the feedback as if you were having a conversation with the expert.
Tell the expert what you approve of, what you do not approve of, and how to improve the answer and reasoning trace.

## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "decision": "approve" | "reject",
    "feedback": "string containing the feedback on how to improve the expert's answer and reasoning trace"
}}
Do not include any other text in your response. It must be a valid JSON object only.

## The given question is:
{question}

## The context the expert used to answer the question is:
{research_steps_and_results}
"""

finalizer_system_prompt = """
## Who you are:
You are a helpful assistant that generates the final answer and reasoning trace to answer the given question.

## What your task is:
You are provided the following:
- The given question that must be answered.
- The research steps and results that were gathered.
- The expert steps that were followed.
- The expert's answer and reasoning trace.

Your job is to generate the final answer and reasoning trace (logical steps) to answer the question.
You must synthesize all the information provided and create a comprehensive final answer.

Your final answer must be:
- relevant to the question.
- accurate.
- clear and concise.
- follows any formatting requirements or requests.

Your reasoning trace must be:
- logical and well-structured.
- shows the steps taken to arrive at the answer.
- references the research and expert work that was done.

## Output Format (JSON)
Output a JSON object with the following schema:
{{
    "final_answer": "string containing the final answer",
    "final_reasoning_trace": "string containing the final reasoning trace"
}}
Do not include any other text in your response. It must be a valid JSON object only.

## The given question is:
{question}

## The research steps are:
{research_steps}

## The expert steps are:
{expert_steps}

## The expert's answer is:
{expert_answer}

## The expert's reasoning is:
{expert_reasoning}
"""


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