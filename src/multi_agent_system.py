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
from langchain_core.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_tavily import TavilySearch
from langchain_community.document_loaders import YoutubeLoader
from langchain_community.document_loaders import UnstructuredExcelLoader, UnstructuredPowerPointLoader, UnstructuredPDFLoader
from langchain_experimental.tools.python.tool import PythonREPLTool
from langchain_community.document_loaders import TextLoader
import pint



########################################################
# < Graph State & Agent Messages >
########################################################

class GraphState(MessagesState):
    question: str
    file: Optional[str]

########################################################
# < Configuration Types >
########################################################
class AgentConfig():
    """Configuration for an agent."""

    def __init__(self, name:str, provider:str, model:str, temperature:float, system_prompt:str, output_schema:dict=None):
        self.name = name
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.output_schema = output_schema
        self.system_prompt = system_prompt


########################################################
# < Information Gathering Tools >
########################################################
@tool
def wikipedia_tool(query: str) -> str:
    """
    Search for and retrieve the full content of a Wikipedia page.
    
    This tool will:
    1. Search for the Wikipedia page matching your query
    2. Retrieve the complete page content (not just a summary)
    3. Return the full text including all sections and subsections
    4. Use Beautiful Soup as fallback if content is missing
    
    Args:
        query: The search term or page title to look up on Wikipedia
        
    Returns:
        The complete Wikipedia page content as a string
    """
    logger.info(f"Wikipedia tool searching for: {query}")
    
    try:
        import wikipedia
        
        # Set the language to English
        wikipedia.set_lang("en")
        
        # Try to get the page directly first
        try:
            page = wikipedia.page(query)
            logger.info(f"Found page: {page.title}")
        except wikipedia.exceptions.DisambiguationError as e:
            # If there are multiple pages with similar names, use the first option
            page = wikipedia.page(e.options[0])
            logger.info(f"Found page (disambiguation): {page.title}")
        except wikipedia.exceptions.PageError:
            # If page doesn't exist, search for it
            search_results = wikipedia.search(query, results=5)
            if search_results:
                page = wikipedia.page(search_results[0])
                logger.info(f"Found page via search: {page.title}")
            else:
                return f"No Wikipedia page found for '{query}'"
        
        # Get the full page content from wikipedia library
        full_content = page.content
        
        # Check if content seems incomplete (missing key sections)
        content_looks_complete = True
        if len(full_content) < 10000:  # Very short content
            content_looks_complete = False
        elif "recipients" in query.lower() and "recipients" not in full_content.lower():
            content_looks_complete = False
        elif "list" in query.lower() and len(full_content.split('\n')) < 50:
            content_looks_complete = False
        
        # If content seems incomplete, try Beautiful Soup as fallback
        if not content_looks_complete:
            logger.info("Content seems incomplete, trying Beautiful Soup fallback...")
            try:
                import requests
                from bs4 import BeautifulSoup
                
                # Get the raw HTML content
                response = requests.get(page.url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract the main content
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    # Remove unwanted elements but keep tables and lists
                    for element in content_div.find_all(['script', 'style', 'sup']):
                        element.decompose()
                    
                    # Get text content with better formatting
                    raw_content = content_div.get_text(separator='\n', strip=True)
                    
                    # If raw content is significantly longer, use it
                    if len(raw_content) > len(full_content) * 1.5:
                        full_content = raw_content
                        logger.info("Using Beautiful Soup content for more complete data")
                    else:
                        logger.info("Beautiful Soup content not significantly better, keeping original")
                else:
                    logger.warning("Could not find main content div in HTML")
            except Exception as e:
                logger.warning(f"Beautiful Soup fallback failed: {e}")
        
        # Add page metadata
        page_info = f"Page Title: {page.title}\n"
        page_info += f"URL: {page.url}\n"
        page_info += f"Summary: {page.summary}\n"
        page_info += f"Content Length: {len(full_content)} characters\n"
        page_info += f"Method: {'Beautiful Soup' if not content_looks_complete else 'Wikipedia Library'}\n\n"
        page_info += "=" * 50 + "\n"
        page_info += "FULL PAGE CONTENT:\n"
        page_info += "=" * 50 + "\n\n"
        
        logger.info(f"Successfully retrieved content from Wikipedia page: {page.title} ({len(full_content)} characters)")
        return page_info + full_content
        
    except Exception as e:
        logger.error(f"Error retrieving Wikipedia content: {e}")
        return f"Error retrieving Wikipedia content: {str(e)}"


@tool
def tavily_tool(query: str) -> str:
    """
    Search for information on the web.
    """
    logger.info(f"Tavily tool searching for: {query}")
    tavily_tool = TavilySearch()
    return tavily_tool.invoke(query)


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
    

########################################################
# < Information Synthesis Tools >
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
    
    IMPORTANT: To capture the results of your code, you MUST use print() statements.
    The tool only captures standard output (print statements), not variable assignments.
    
    Examples:
    - WRONG: filtered_winners = [winner for winner in winners if check_nationality(winner)]
    - CORRECT: print(filtered_winners)
    - CORRECT: print(f"Result: {result}")
    - CORRECT: print([winner for winner in winners if check_nationality(winner)])
    
    Always end your code with a print() statement to see the results.
    
    Args:
        code: The Python code to execute
    Returns:
        The result of the code execution as a string.
    """
    logger.info(f"Executing the following python code: {code}")
    python_repl_tool = PythonREPLTool()
    return python_repl_tool.invoke(code)


########################################################
# < Guard Agent as a Tool >
########################################################
def create_guard_agent_tool(config: AgentConfig) -> Callable[[str], str]:
    """Create a guard agent function with the given prompts for different critic types."""
    llm_guard = llm_factory(config)

    @tool
    def guard_agent_tool(question_for_guard:str, original_task:str, context:str) -> str:
        """Use this tool when you need to review your thinking process or you need to review your final answer and reasoning to seek key suggestions proactively or in review.
        
        Args:
            question_for_guard: What you want to ask the guard agent to help review your reasoning process or review your final answer and reasoning.
            original_task: The original task
            context: Any relevant information that may be useful to the guard agent to answer the query correctly

        Returns:
            The response from the guard agent
        """
        logger.info(f"Guard starting execution")
        
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        message_in = f"""## Original Task\n{original_task}\n\n## Context\n{context}\n\n## Question for Guard\n{question_for_guard}"""

        response = llm_guard.invoke(sys_prompt + [HumanMessage(content=message_in)])     
        
        logger.info("Guard completed successfully")
        return response.content
    
    return guard_agent_tool

########################################################
# < Main Graph Nodes >
########################################################

def input_interface(state: GraphState) -> GraphState:
    """Input interface with error handling and validation."""
    logger.info("Input interface starting execution")
    
    # Handle question extraction with proper error handling
    if not state.get("question") or len(state["question"]) == 0:
        raise ValueError("No question provided to input interface")

    # Initialize all state fields first to ensure they exist for error handling
    state["file"] = state["file"] if state["file"] else None

    if state["file"]:
        state["messages"] = [HumanMessage(content=f"## Task\n{state['question']}\n\n## File\nUse the following file to help you solve the task: {state['file']}")]
    else:
        state["messages"] = [HumanMessage(content=f"## Task\n{state['question']}")]
        
    logger.info("Input interface completed successfully")
    return state


def create_executor_agent(config: AgentConfig, llm_executor: ChatOpenAI) -> Callable[[GraphState], GraphState]:
    """Create an executor agent function with the given prompt and LLM."""
    def executor_agent(state: GraphState) -> GraphState:
        """Executor agent with injected prompt."""
        logger.info("Executor starting execution")
        
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        response = llm_executor.invoke(sys_prompt + state["messages"])

        # If the Executor has tool calls, it is still working on the task
        if hasattr(response, 'tool_calls') and response.tool_calls:
            logger.info(f"Executor tool calls: {response.tool_calls}")
        return {"messages": [response]}
    
    return executor_agent



########################################################
# < Graph Factory Function >
########################################################
def openai_llm_factory(model: str, temperature: float, tools: list = None) -> ChatOpenAI:
    """Create an OpenAI LLM with the given model and temperature.

    Args:
        model (str): The model to use
        temperature (float): The temperature to use
        output_schema (dict): The output schema to use (JSON schema)
    """
    llm = ChatOpenAI(model=model, temperature=temperature)
    if tools:
        llm = llm.bind_tools(tools)
    return llm


def llm_factory(config:AgentConfig, tools: list = None) -> ChatOpenAI:
    """Get the appropriate LLM factory based on the provider.

    Args:
        config (AgentConfig): The configuration for the agent

    Returns:
        ChatOpenAI: The LLM with structured output
    """
    if config.provider == "openai":
        return openai_llm_factory(config.model, config.temperature, tools)
    else:
        raise ValueError(f"Invalid provider: {config.provider}")


def assemble_tools(agent_configs: dict[str, AgentConfig]) -> list:
    guard_agent_tool = create_guard_agent_tool(agent_configs["guard"])
    return [guard_agent_tool, youtube_transcript_tool, tavily_tool, wikipedia_tool, unstructured_excel_tool, unstructured_powerpoint_tool, unstructured_pdf_tool, text_file_tool, unit_converter, calculator, python_repl_tool]


def create_multi_agent_graph(agent_configs: dict[str, AgentConfig]) -> Tuple[StateGraph, OpikTracer]:
    """
    Factory function that creates and compiles a multi-agent graph with injected prompts.
    
    Args:
        agent_configs (dict[str, AgentConfig]): Dictionary containing all agent configs
        
    Returns:
        Compiled graph ready for invocation
    """
    # Define Agent Tools
    tools = assemble_tools(agent_configs)

    # Create Executor Agent
    llm_executor = llm_factory(agent_configs["executor"], tools)
    executor_agent = create_executor_agent(agent_configs["executor"], llm_executor)


    # Build the graph
    builder = StateGraph(GraphState)
    
    builder.add_node("input_interface", input_interface)
    builder.add_node("executor", executor_agent)
    builder.add_node("tools", ToolNode(tools))
    
    builder.add_edge(START, "input_interface")
    builder.add_edge("input_interface", "executor")
    builder.add_conditional_edges("executor", tools_condition)
    builder.add_edge("tools", "executor")
        
    # Compile and return the graph
    app = builder.compile()

    # Create the OpikTracer for LangGraph
    opik_tracer = OpikTracer(graph=app.get_graph(xray=True))
    
    return app, opik_tracer