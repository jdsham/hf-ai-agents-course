# Infrastructure and Utility Components

## JSON Response Enforcement

### Component name:
enforce_json_response

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Enforce that the LLM response is either a dictionary or a JSON string. If it is a string, try to parse it as JSON.
- **Responsibilities**: 
  - Validates response type and structure
  - Converts string responses to JSON dictionaries
  - Provides error handling for invalid responses
  - Ensures consistent dictionary output format

### Component interface:
#### Inputs:
- response: Any // The response from the LLM
- component: string // The component that generated the response

#### Outputs:
- dict // The response as a dictionary

#### Validations:
- Handled by Python type checking and JSON parsing validation

### Direct Dependencies with Other Components
None

### Internal Logic
1. Check if the response is already a dictionary using isinstance(response, dict)
2. If the response is a dictionary, return it directly
3. If the response is not a dictionary, attempt to parse it as JSON using json.loads(response)
4. If JSON parsing succeeds, return the parsed data as a dictionary
5. If JSON parsing fails (raises an exception), raise a ValueError with component context and response details

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles data validation

### External Dependencies
- **Python json module**: Library for JSON parsing and validation

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
- Raises ValueError if the response is not a dictionary or a valid JSON string
- Error message includes the component name and the invalid response for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Output Schema Validation

### Component name:
validate_output_matches_json_schema

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Check if the LLM response has all the expected fields. Assumes the response is a dictionary when evaluating
- **Responsibilities**: 
  - Validates that all required output schema keys are present in the response
  - Provides boolean validation result for response completeness
  - Supports schema validation for LLM responses
  - Enables response structure validation

### Component interface:
#### Inputs:
- response: Any // The response from the LLM
- output_schema_keys: list[string] // The expected fields that should be present in the response

#### Outputs:
- bool // True if the response has all the expected fields, False otherwise

#### Validations:
- Handled by Python all() function and dictionary key checking

### Direct Dependencies with Other Components
None

### Internal Logic
1. Check if every key in output_schema_keys exists in the response dictionary. Could use Python's all() function in implementation. 
2. Return True if all keys are present, False if any key is missing

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles data validation

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---


## LLM Response Validation

### Component name:
validate_llm_response

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Validate LLM response has expected structure and fields
- **Responsibilities**: 
  - Enforces JSON response format using enforce_json_response function
  - Validates response schema using validate_output_matches_json_schema function
  - Provides comprehensive LLM response validation
  - Returns validated response as dictionary or raises appropriate errors

### Component interface:
#### Inputs:
- response: Any // The response from the LLM
- expected_fields: List[string] // The expected fields that should be present in the response
- component: string // The component that generated the response

#### Outputs:
- dict // The response as a validated dictionary

#### Validations:
- Handled by enforce_json_response and validate_output_matches_json_schema functions

### Direct Dependencies with Other Components
- enforce_json_response function
- validate_output_matches_json_schema function

### Internal Logic
1. Call enforce_json_response function to ensure response is a dictionary
2. Check if the response matches the expected schema using validate_output_matches_json_schema function
3. If schema validation fails, raise KeyError with component context and field details
4. Return the validated response dictionary

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles data validation

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
- Raises KeyError if the response does not contain all the expected fields
- Error message includes the component name, expected fields, and actual response for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Agent Message Composer

### Component name:
compose_agent_message

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Composes an agent message using the AgentMessage protocol and data structure
- **Responsibilities**: Handles agent message composition to be compliant with the AgentMessage protocol


### Component interface:
#### Inputs:
- sender: string  // The entity sending the message, either an agent or the orchestrator
- receiver: string  // The entity receiving the message, either an agent or the orchestrator
- message_type: string  // The type of message that is being sent: instruction, respense, feedback
- content: string  // The message content / message body
- step_id: integer = none // Optional. The specific research step id associated with message being composed

#### Outputs:
- agent_message: AgentMessage // The composed message as an AgentMessage

#### Validations:
- Handled by Pydantic + Typing in LangGraph

### Direct Dependencies with Other Components
None

### Internal Logic
1. Get the current timestamp
2. Take the inputs and current timestamp, and use them to compose an AgentMessage type variable that follows the AgentMessage data structure. Variable must be explicitly typed as AgentMessage.
3. Return the composed message

### Workflow Control
None

### State Management
Does not access any graph states.


### Communication Patterns
None. This component does not communicate, rather it handles communication

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) at the end of the logical steps.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---


## Agent Message Sending

### Component name:
send_message

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Adds a message to the agent_messages field in the main graph state
- **Responsibilities**: Message storage in main graph sate

### Component interface:
#### Inputs:
- state: GraphState // The main graph state
- message: AgentMessage // The agent message

#### Outputs:
- state: GraphState // The main graph state

#### Validations:
- Handled by Pydantic + Typing in LangGraph

### Direct Dependencies with Other Components
None

### Internal Logic
1. Update the state (GraphState) and append the message to the agent_messages field
2. Return the state

### Workflow Control
None

### State Management
Accesses the agent_messages field in the state input variable (GraphState) and appends the input message to the agent_messages field (list).

### Communication Patterns
None. This component does not communicate, rather it handles communication

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) at the end of the logical steps.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Agent Conversation Retrieval

### Component name:
get_agent_conversation

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Get the conversation between the orchestrator and the agent
- **Responsibilities**: 
  - Retrieves messages between orchestrator and specific agent
  - Filters messages by message types when specified
  - Filters messages by step ID when specified
  - Provides filtered conversation history for agent communication

### Component interface:
#### Inputs:
- state: GraphState // The current state of the graph
- agent_name: string // The name of the agent
- types: Optional[List[string]] = none // Optional. The types of messages to get
- step_id: Optional[integer] = none // Optional. The step id to get messages for

#### Outputs:
- List[AgentMessage] // The list of AgentMessages between the agent and orchestrator

#### Validations:
- Handled by Pydantic + Typing in LangGraph

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create initial inbox by filtering all agent_messages from state based on sender/receiver logic:
   - Include messages where sender = agent_name and receiver = "orchestrator"
   - Include messages where sender = "orchestrator" and receiver = agent_name
2. If step_id is not None, filter inbox to only include messages with matching step_id
3. If types is not None, filter inbox to only include messages where message type is in the types list
4. Return the filtered inbox list

### Workflow Control
None

### State Management
Accesses the agent_messages field in the state input variable (GraphState) to retrieve specified messages.
Does not alter the state in any way.

### Communication Patterns
None. This component does not communicate, rather it handles communication retrieval

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

## Agent Message to LangChain Conversion

### Component name:
convert_agent_messages_to_langchain

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Convert a list of AgentMessages to a list of LangChain BaseMessages
- **Responsibilities**: 
  - Converts AgentMessage protocol to LangChain message format
  - Maps sender types to appropriate LangChain message types
  - Provides protocol translation for LLM integration
  - Enables communication between agent system and LangChain components

### Component interface:
#### Inputs:
- messages: List[AgentMessage] // The list of AgentMessages to convert

#### Outputs:
- List[BaseMessage] // The list of LangChain BaseMessages

#### Validations:
- Handled by Pydantic + Typing in LangGraph

### Direct Dependencies with Other Components
None

### Internal Logic
1. Initialize an empty list called converted_messages
2. Iterate through each message in the input messages list
3. For each message, check if the sender is "orchestrator"
4. If sender is "orchestrator", create a HumanMessage with the message content
5. If sender is not "orchestrator", create an AIMessage with the message content
6. Append the created message to the converted_messages list
7. Return the converted_messages list

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles protocol conversion

### External Dependencies
- **LangChain BaseMessage**: Library for LangChain message types
- **HumanMessage**: LangChain message type for human/orchestrator messages
- **AIMessage**: LangChain message type for agent messages

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

# Researcher SubGraph Components

## YouTube Video Transcribing Tool

### Component name:
youtube_transcript_tool

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Extracts transcript from a YouTube video URL. Use this when you need to get the content/transcript from a specific YouTube video.
- **Responsibilities**: 
  - Loads YouTube video transcript using LangChain YoutubeLoader
  - Extracts transcript content and video metadata
  - Handles video information processing and formatting
  - Provides formatted transcript with video metadata

### Component interface:
#### Inputs:
- url: string  // The YouTube video URL to extract transcript from

#### Outputs:
- transcript: string  // The transcript text from the video with metadata

#### Validations:
- Handled by LangChain YoutubeLoader validation
- URL format validation handled by YoutubeLoader

### Direct Dependencies with Other Components
None

### Internal Logic
1. Log the beginning of processing with the URL
2. Create YoutubeLoader instance with the provided URL and add_video_info=True
3. Load documents using the loader
4. Check if documents list is empty
5. If no documents found, log info and return "No transcript found" message
6. Extract transcript content from the first document's page_content
7. Extract metadata from the first document
8. Format video information string with title, author, and duration from metadata
9. Log successful completion
10. Return concatenated video info and transcript content

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles external API communication

### External Dependencies
- **YouTube API**: Access to YouTube video data and transcripts
- **LangChain YoutubeLoader**: Library for YouTube video processing
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

### Logging
- Append logging (INFO) at the beginning of processing with URL
- Append logging (INFO) at the end of successful processing
- Append logging (INFO) if no transcript is found

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

## Unstructured Excel Tool

### Component name:
unstructured_excel_tool

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Loads an Excel file and returns the content as documents
- **Responsibilities**: 
  - Loads Excel files using LangChain UnstructuredExcelLoader
  - Extracts content from Excel files
  - Returns structured document format for processing
  - Handles Excel file parsing and content extraction

### Component interface:
#### Inputs:
- file_path: string  // The path to the Excel file to load

#### Outputs:
- documents: list[Document]  // The Excel file content as a list of Document objects

#### Validations:
- Handled by LangChain UnstructuredExcelLoader validation
- File path validation handled by UnstructuredExcelLoader

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create UnstructuredExcelLoader instance with the provided file path
2. Load the Excel file content using the loader
3. Return the loaded documents as a list of Document objects

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file processing

### External Dependencies
- **LangChain UnstructuredExcelLoader**: Library for Excel file processing
- **File System**: Access to Excel files on the local file system
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

### Logging
- Append logging (INFO) at the beginning of processing with file path
- Append logging (INFO) at the end of successful processing
- Append logging (ERROR) if file loading fails

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Unstructured PowerPoint Tool

### Component name:
unstructured_powerpoint_tool

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Loads a PowerPoint file and returns the content as documents
- **Responsibilities**: 
  - Loads PowerPoint files using LangChain UnstructuredExcelLoader
  - Extracts content from PowerPoint files
  - Returns structured document format for processing
  - Handles PowerPoint file parsing and content extraction

### Component interface:
#### Inputs:
- file_path: string  // The path to the PowerPoint file to load

#### Outputs:
- documents: list[Document]  // The PowerPoint file content as a list of Document objects

#### Validations:
- Handled by LangChain UnstructuredPowerPointLoader validation
- File path validation handled by UnstructuredPowerPointLoader

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create UnstructuredPowerPointLoader instance with the provided file path
2. Load the PowerPoint file content using the loader
3. Return the loaded documents as a list of Document objects

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file processing

### External Dependencies
- **LangChain UnstructuredPowerPointLoader**: Library for PowerPoint file processing
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool
- **File System**: Access to PowerPoint files on the local file system

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

### Logging
- Append logging (INFO) at the beginning of processing with file path
- Append logging (INFO) at the end of successful processing
- Append logging (ERROR) if file loading fails

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Unstructured PDF Tool

### Component name:
unstructured_pdf_tool

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Loads a PDF file and returns the content as documents
- **Responsibilities**: 
  - Loads PDF files using LangChain UnstructuredExcelLoader
  - Extracts content from PDF files
  - Returns structured document format for processing
  - Handles PDF file parsing and content extraction

### Component interface:
#### Inputs:
- file_path: string  // The path to the PDF file to load

#### Outputs:
- documents: list[Document]  // The PDF file content as a list of Document objects

#### Validations:
- Handled by LangChain UnstructuredPDFLoader validation
- File path validation handled by UnstructuredPDFLoader

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create UnstructuredPDFLoader instance with the provided file path
2. Load the PDF file content using the loader
3. Return the loaded documents as a list of Document objects

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file processing

### External Dependencies
- **LangChain UnstructuredPDFLoader**: Library forPDF file processing
- **File System**: Access to PDF files on the local file system
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool


### Logging
- Append logging (INFO) at the beginning of processing with file path
- Append logging (INFO) at the end of successful processing
- Append logging (ERROR) if file loading fails

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Text File Tool

### Component name:
text_file_tool

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Load a text file and return the content as a string
- **Responsibilities**: 
  - Loads text files using LangChain TextLoader
  - Extracts text content from loaded documents
  - Returns file content as a string for processing
  - Provides text file reading capabilities for research operations

### Component interface:
#### Inputs:
- file_path: string // The path to the text file to load

#### Outputs:
- string // The content of the text file as a string

#### Validations:
- Handled by LangChain TextLoader validation
- File existence and accessibility validation handled by TextLoader

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create a TextLoader instance with the provided file_path parameter
2. Call the load() method on the TextLoader instance to load the text file
3. The load() method returns a list of Document objects containing the file content
4. Check if the documents list is not empty
5. If documents exist, extract the page_content from the first (and typically only) Document in the list
6. If no documents are found, return an empty string
7. Return the extracted text content as a string

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file loading operations

### External Dependencies
- **LangChain TextLoader**: Library for loading text files and creating Document objects

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Get Browser MCP Tools

### Component name:
get_browser_mcp_tools

### Component type:
async function

### Component purpose and responsibilities:
- **Purpose**: Get the browser MCP tools from the given URL
- **Responsibilities**: 
  - Establishes connection to MCP server using streamablehttp_client
  - Initializes MCP session with the server
  - Loads MCP tools from the session
  - Returns list of available MCP tools for browser operations

### Component interface:
#### Inputs:
- mcp_url: string  // The URL of the browser MCP

#### Outputs:
- list  // The list of MCP tools

#### Validations:
- Handled by MCP client session validation
- URL format validation handled by streamablehttp_client

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create async context manager for streamablehttp_client with the MCP URL, unpacking read, write, and unused streams
2. Create async context manager for ClientSession with read and write streams
3. Initialize the MCP session using await session.initialize()
4. Load MCP tools from the session using await load_mcp_tools(session)
5. Return the list of MCP tools

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
- **MCP Protocol**: Communicates with Model Context Protocol server
- **HTTP Streaming**: Uses streamable HTTP client for connection
- **Session Management**: Manages MCP session lifecycle

### External Dependencies
- **MCP Server**: Model Context Protocol server for tool access
- **streamablehttp_client**: HTTP client for MCP server communication
- **ClientSession**: MCP client session management
- **load_mcp_tools**: Function to load tools from MCP session from LangChain community

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Get Research Tools

### Component name:
get_research_tools

### Component type:
async function

### Component purpose and responsibilities:
- **Purpose**: Get the research tools
- **Responsibilities**: 
  - Creates Wikipedia tool with API wrapper
  - Creates Tavily search tool
  - Retrieves browser MCP tools from MCP server
  - Compiles and returns comprehensive list of research tools
  - Combines built-in tools with external MCP tools

### Component interface:
#### Inputs:
None

#### Outputs:
- list  // The list of research tools

#### Validations:
- Handled by individual tool creation validation
- MCP tools validation handled by get_browser_mcp_tools function

### Direct Dependencies with Other Components
- get_browser_mcp_tools function
- youtube_transcript_tool function
- unstructured_excel_tool function
- unstructured_powerpoint_tool function
- unstructured_pdf_tool function
- text_file_tool function

### Internal Logic
1. Create Wikipedia tool with WikipediaAPIWrapper(wiki_client=None)
2. Create Tavily search tool
3. Define browser MCP URL as "http://0.0.0.0:3000/mcp"
4. Retrieve MCP tools using await get_browser_mcp_tools(browser_mcp_url)
5. Return list containing:
   - youtube_transcript_tool
   - tavily_tool
   - wikipedia_tool
   - unstructured_excel_tool
   - unstructured_powerpoint_tool
   - unstructured_pdf_tool
   - text_file_tool
   - all mcp_tools (unpacked using *mcp_tools)

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
- **MCP Communication**: Uses get_browser_mcp_tools to communicate with MCP server
- **Tool Integration**: Combines multiple tool types into unified list

### External Dependencies
- **WikipediaQueryRun**: LangChain Wikipedia tool for knowledge base access
- **WikipediaAPIWrapper**: API wrapper for Wikipedia queries
- **TavilySearch**: LangChain Tavily search tool for web search

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Researcher LLM Node Factory

### Component name:
create_researcher_llm_node

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create a researcher LLM node function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a researcher LLM node
  - Injects configuration and LLM dependencies into the node function
  - Handles LLM invocation with system prompt and state messages
  - Validates LLM response against output schema
  - Returns appropriate response format based on validation result

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing system prompt and output schema
- llm_researcher: ChatOpenAI // The LLM instance for researcher operations

#### Outputs:
- Callable[[ResearcherState], ResearcherState] // The researcher LLM node function

#### Validations:
- Handled by validate_output_matches_json_schema function

### Direct Dependencies with Other Components
- validate_output_matches_json_schema function

### Internal Logic
1. Define inner function researcher_llm_node that takes ResearcherState as parameter
2. Create system prompt using SystemMessage with config.system_prompt content
3. Invoke LLM with system prompt concatenated with state messages
4. Check if response matches output schema using validate_output_matches_json_schema
5. If validation succeeds, return messages with JSON-dumped response and result field
6. If validation fails, return messages with raw response
7. Return the inner researcher_llm_node function

### Workflow Control
None

### State Management
Accesses messages field in ResearcherState input and returns updated ResearcherState with new messages.

### Communication Patterns
None. This component does not communicate, rather it creates a function for LLM processing

### External Dependencies
- **LangChain SystemMessage**: Library for creating system messages
- **LangChain AIMessage**: Library for creating AI response messages
- **ChatOpenAI**: LLM interface for researcher operations

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- llm_researcher: ChatOpenAI - LLM instance passed from outer scope

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

## Researcher Subgraph Factory

### Component name:
create_researcher_subgraph

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create and compile a researcher subgraph with the given prompt and LLM
- **Responsibilities**: 
  - Creates a StateGraph for researcher workflow
  - Adds researcher LLM node to the graph
  - Adds tools node to the graph
  - Configures graph edges and conditional routing
  - Compiles and returns the complete subgraph

### Component interface:
#### Inputs:
- researcher_llm_node: Callable // The researcher LLM node function
- research_tools: list // The list of research tools to include in the subgraph

#### Outputs:
- StateGraph // The compiled researcher subgraph

#### Validations:
- Handled by LangGraph StateGraph validation

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create StateGraph instance with ResearcherState as the state type
2. Add "researcher" node to the graph using researcher_llm_node function
3. Add "tools" node to the graph using ToolNode with research_tools
4. Add edge from START to "researcher" node
5. Add conditional edges from "researcher" node using tools_condition
6. Add edge from "tools" node back to "researcher" node
7. Compile the graph and return the compiled StateGraph

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it creates a graph structure

### External Dependencies
- **LangGraph StateGraph**: Library for creating state-based graphs
- **LangGraph ToolNode**: Library for creating tool nodes in graphs
- **LangGraph START**: Library constant for graph start node
- **tools_condition**: Function for determining tool usage conditions

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

# Expert Subgraph Components

---

## Unit Converter Tool

### Component name:
unit_converter

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Convert a quantity to a different unit
- **Responsibilities**: 
  - Parses quantity strings with units using Pint library
  - Performs unit conversions between different measurement systems
  - Handles various unit types (length, mass, temperature, etc.)
  - Returns converted values as formatted strings

### Component interface:
#### Inputs:
- quantity: string // A string like '10 meters', '5 kg', '32 fahrenheit'
- to_unit: string // The unit to convert to, e.g. 'ft', 'lbs', 'celsius'

#### Outputs:
- string // The converted value as a string

#### Validations:
- Handled by Pint UnitRegistry validation
- Unit format validation handled by Pint library

### Direct Dependencies with Other Components
None

### Internal Logic
1. Log the beginning of unit conversion with quantity and target unit
2. Create Pint UnitRegistry instance
3. Parse the input quantity string using the UnitRegistry
4. Convert the quantity to the target unit using the to() method
5. Log the conversion result
6. Return the result as a string

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it performs unit conversion calculations

### External Dependencies
- **Pint UnitRegistry**: Library for unit conversion and dimensional analysis
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

### Logging
- Append logging (INFO) at the beginning of processing with quantity and target unit
- Append logging (INFO) at the end of successful processing with result

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

## Calculator Tool

### Component name:
calculator

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Evaluate a basic math expression. Supports +, -, *, /, **, and parentheses
- **Responsibilities**: 
  - Parses mathematical expressions as strings
  - Evaluates expressions using Python's eval with restricted namespace
  - Provides access to mathematical functions from Python's math module
  - Returns calculation results as formatted strings

### Component interface:
#### Inputs:
- expression: string // A mathematical expression to evaluate

#### Outputs:
- string // The calculated result as a string

#### Validations:
- Handled by Python eval function validation
- Expression format validation handled by eval function

### Direct Dependencies with Other Components
None

### Internal Logic
1. Log the beginning of calculation with the expression
2. Import the math module
3. Create allowed_names dictionary with math functions (excluding those starting with "__")
4. Evaluate the expression using eval with restricted namespace (no builtins, only math functions)
5. Log the calculation result
6. Return the result as a string

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it performs mathematical calculations

### External Dependencies
- **Python math module**: Library for mathematical functions and constants
- **Python eval function**: Built-in function for expression evaluation
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

### Global variables
None

### Closed-over variables
None

### Decorators
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

### Logging
- Append logging (INFO) at the beginning of processing with expression
- Append logging (INFO) at the end of successful processing with result

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

## Expert Tools Factory

### Component name:
get_expert_tools

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Get the expert tools
- **Responsibilities**: 
  - Creates Python REPL tool for code execution
  - Compiles list of expert tools including unit converter and calculator
  - Provides expert-level computation and analysis tools
  - Returns comprehensive list of tools for expert reasoning

### Component interface:
#### Inputs:
None

#### Outputs:
- List[Tool] // The list of expert tools

#### Validations:
- Handled by LangChain tool creation validation

### Direct Dependencies with Other Components
- unit_converter function
- calculator function

### Internal Logic
1. Create Python REPL tool using PythonREPLTool()
2. Return list containing unit_converter, calculator, and python_repl_tool

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it creates tool instances

### External Dependencies
- **LangChain PythonREPLTool**: Library for creating Python REPL tool

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.


---

## Expert LLM Node Factory

### Component name:
create_expert_llm_node

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create an expert LLM node function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns an expert LLM node
  - Injects configuration and LLM dependencies into the node function
  - Handles LLM invocation with system prompt and state messages
  - Validates LLM response against output schema
  - Updates expert state with answer and reasoning
  - Returns appropriate response format based on validation result

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing system prompt and output schema
- llm_expert: ChatOpenAI // The LLM instance for expert operations

#### Outputs:
- Callable[[ExpertState], ExpertState] // The expert LLM node function

#### Validations:
- Handled by validate_output_matches_json_schema function

### Direct Dependencies with Other Components
- validate_output_matches_json_schema function

### Internal Logic
1. Define inner function expert_llm_node that takes ExpertState as parameter
2. Create system prompt using SystemMessage with config.system_prompt content
3. Invoke LLM with system prompt concatenated with state messages
4. Check if response matches output schema using validate_output_matches_json_schema
5. If validation succeeds:
   - Update state["expert_answer"] with response["expert_answer"]
   - Update state["expert_reasoning"] with response["reasoning_trace"]
   - Create AIMessage with formatted expert answer and reasoning content
6. Return messages with the response (either formatted or raw)
7. Return the inner expert_llm_node function

### Workflow Control
None

### State Management
Accesses messages field in ExpertState input and returns updated ExpertState with new messages.
Updates expert_answer and expert_reasoning fields in state when validation succeeds.

### Communication Patterns
None. This component does not communicate, rather it creates a function for LLM processing

### External Dependencies
- **LangChain SystemMessage**: Library for creating system messages
- **LangChain AIMessage**: Library for creating AI response messages
- **ChatOpenAI**: LLM interface for expert operations

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- llm_expert: ChatOpenAI - LLM instance passed from outer scope

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Expert Subgraph Factory

### Component name:
create_expert_subgraph

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create and compile an expert subgraph with the given prompt and LLM
- **Responsibilities**: 
  - Creates a StateGraph for expert workflow
  - Adds expert LLM node to the graph
  - Adds tools node to the graph
  - Configures graph edges and conditional routing
  - Compiles and returns the complete subgraph

### Component interface:
#### Inputs:
- expert_llm_node: Callable // The expert LLM node function
- expert_tools: list // The list of expert tools to include in the subgraph

#### Outputs:
- StateGraph // The compiled expert subgraph

#### Validations:
- Handled by LangGraph StateGraph validation

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create StateGraph instance with ExpertState as the state type
2. Add "expert" node to the graph using expert_llm_node function
3. Add "tools" node to the graph using ToolNode with expert_tools
4. Add edge from START to "expert" node
5. Add conditional edges from "expert" node using tools_condition
6. Add edge from "tools" node back to "expert" node
7. Compile the graph and return the compiled StateGraph

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it creates a graph structure

### External Dependencies
- **LangGraph StateGraph**: Library for creating state-based graphs
- **LangGraph ToolNode**: Library for creating tool nodes in graphs
- **LangGraph START**: Library constant for graph start node
- **tools_condition**: Function for determining tool usage conditions

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---


# Main Graph Components

## Input Interface Factory

### Component name:
create_input_interface

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create an input interface function with the given retry limit
- **Responsibilities**: 
  - Creates a factory function that returns an input interface node
  - Injects agent configuration dependencies into the interface function
  - Handles input validation and error checking
  - Initializes all state fields for workflow execution
  - Sets up retry limits from agent configurations
  - Provides system entry point for user interactions

### Component interface:
#### Inputs:
- agent_configs: dict[str, AgentConfig] // Dictionary containing all agent configurations

#### Outputs:
- Callable[[GraphState], GraphState] // The input interface function

#### Validations:
- Handled by input validation logic within the function

### Direct Dependencies with Other Components
None

### Internal Logic
1. Define inner function input_interface that takes GraphState as parameter
2. Log the beginning of input interface execution
3. Check if state has question, handle error if not provided
4. Initialize file field with existing value or None
5. Initialize planner work fields (research_steps and expert_steps as empty lists)
6. Initialize researcher work fields:
   - Set current_research_index to -1
   - Set researcher_states to empty dict
   - Set research_results to empty list
7. Initialize expert work fields:
   - Set expert_state to None
   - Set expert_answer to empty string
   - Set expert_reasoning to empty string
8. Initialize critic work fields (all decision and feedback fields to empty strings)
9. Initialize finalizer work fields (final_answer and final_reasoning_trace to empty strings)
10. Initialize orchestrator work fields:
    - Set agent_messages to empty list
    - Set current_step to "input"
    - Set next_step to "planner"
11. Initialize retry counts to 0 for all agents
12. Set retry limits from agent_configs for planner, researcher, and expert
13. Log successful completion
14. Return the updated state
15. Return the inner input_interface function

### Workflow Control
None

### State Management
Accesses and initializes all fields in GraphState input and returns updated GraphState with initialized values.

### Communication Patterns
None. This component does not communicate, rather it initializes system state

### External Dependencies
None

### Global variables
None

### Closed-over variables
- agent_configs: dict[str, AgentConfig] - Agent configurations passed from outer scope

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

### Error Handling
- Raises ValueError if no question is provided to input interface
- Error message includes context about missing question
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Next Step Determination

### Component name:
determine_next_step

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Orchestrator logic to determine the next step based on current step and critic decisions
- **Responsibilities**: 
  - Handles critic decisions and sets the next step accordingly
  - Handles initial state and non-critic steps
  - Handles retry counter incrementation
  - Manages workflow state transitions
  - Determines routing logic for multi-agent workflow

### Component interface:
#### Inputs:
- state: GraphState // The current state of the graph

#### Outputs:
- GraphState // The updated state of the graph with next_step determined

#### Validations:
- Handled by state field access validation

### Direct Dependencies with Other Components
None

### Internal Logic
1. Check if current_step equals "critic_planner"
2. If current_step is "critic_planner":
   - Check if critic_planner_decision equals "approve"
   - If critic_planner_decision is "approve":
     - Check if length of research_steps list is greater than 0
     - If research_steps has items, set next_step to "researcher"
     - If research_steps is empty, set next_step to "expert"
   - If critic_planner_decision is "reject":
     - Set next_step to "planner"
     - Increment planner_retry_count by 1
3. Check if current_step equals "critic_researcher"
4. If current_step is "critic_researcher":
   - Check if critic_researcher_decision equals "approve"
   - If critic_researcher_decision is "approve":
     - Check if current_research_index + 1 is greater than or equal to length of research_steps
     - If all research steps completed, set next_step to "expert"
     - If more research steps remain, set next_step to "researcher"
   - If critic_researcher_decision is "reject":
     - Set next_step to "researcher"
     - Increment researcher_retry_count by 1
5. Check if current_step equals "critic_expert"
6. If current_step is "critic_expert":
   - Check if critic_expert_decision equals "approve"
   - If critic_expert_decision is "approve":
     - Set next_step to "finalizer"
   - If critic_expert_decision is "reject":
     - Set next_step to "expert"
     - Increment expert_retry_count by 1
7. Handle initial state and non-critic steps:
   - Check if current_step is empty string or equals "input"
   - If current_step is empty or "input", set next_step to "planner"
   - If current_step equals "planner", set next_step to "critic_planner"
   - If current_step equals "researcher", set next_step to "critic_researcher"
   - If current_step equals "expert", set next_step to "critic_expert"
8. Return the updated state

### Workflow Control
Controls workflow state transitions by determining the next step based on current state and critic decisions.

### State Management
Reads current_step, critic decisions, and retry counts from state.
Updates next_step and retry counts in state based on decision logic.

### Communication Patterns
None. This component does not communicate, rather it determines workflow routing

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Retry Limit Check

### Component name:
check_retry_limit

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Orchestrator logic to check retry count and handle limit exceeded
- **Responsibilities**: 
  - Handles retry limit exceeded and sets the next step to finalizer
  - Handles graceful failure and sets the final answer and reasoning trace
  - Monitors retry counts for all agents (planner, researcher, expert)
  - Prevents infinite retry loops by enforcing retry limits
  - Provides graceful degradation when limits are exceeded

### Component interface:
#### Inputs:
- state: GraphState // The current state of the graph

#### Outputs:
- GraphState // The updated state of the graph

#### Validations:
- Handled by retry count comparison validation

### Direct Dependencies with Other Components
None

### Internal Logic
1. Check if any agent has exceeded its retry limit:
   - Compare planner_retry_count >= planner_retry_limit
   - Compare researcher_retry_count >= researcher_retry_limit
   - Compare expert_retry_count >= expert_retry_limit
2. If any retry limit is exceeded:
   - Log graceful failure message with next_step information
   - Set next_step to "finalizer"
   - Set final_answer to "The question could not be answered."
   - Set final_reasoning_trace to "The question could not be answered."
3. Return the updated state

### Workflow Control
Controls workflow termination by checking retry limits and routing to finalizer when limits are exceeded.

### State Management
Reads retry counts and retry limits from state.
Updates next_step, final_answer, and final_reasoning_trace in state when limits are exceeded.

### Communication Patterns
None. This component does not communicate, rather it checks retry limits

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) when retry limit is exceeded with graceful failure message

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Next Step Execution

### Component name:
execute_next_step

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Orchestrator logic to execute the next step by setting current_step and sending message
- **Responsibilities**: 
  - Handles the different steps and sends the appropriate message
  - Includes any context needed in the message
  - Sets current_step to next_step
  - Composes and sends agent messages based on current step
  - Manages message content and context for each agent type
  - Handles retry scenarios with feedback

### Component interface:
#### Inputs:
- state: GraphState // The current state of the graph

#### Outputs:
- GraphState // The updated state of the graph

#### Validations:
- Handled by state field access validation

### Direct Dependencies with Other Components
- compose_agent_message function
- send_message function

### Internal Logic
1. Set state["current_step"] to state["next_step"] value
2. Check if current_step equals "planner"
3. If current_step is "planner":
   - Check if critic_planner_decision equals "reject"
   - If critic_planner_decision is "reject":
     - Create retry message using compose_agent_message with sender="orchestrator", receiver="planner", type="instruction", and content formatted as "Use the following feedback to improve the plan:\n{state['critic_planner_feedback']}"
   - If critic_planner_decision is not "reject":
     - Initialize file_info as empty string
     - Check if state["file"] exists
     - If file exists, set file_info to "\n\nInclude using following file in any of the research steps:" + "\n".join(state["file"])
     - Create initial planning message using compose_agent_message with sender="orchestrator", receiver="planner", type="instruction", and content formatted as "Develop a logical plan to answer the following question:\n{state['question']}{file_info}"
4. Check if current_step equals "critic_planner"
5. If current_step is "critic_planner":
   - Build task context string formatted as "Use the following context to answer the User Question:\n\n## Context\n### Planner Task\nThe planner was asked to develop a logical plan to answer the following input question: {state['question']}\n\n"
   - Initialize file_info as empty string
   - Check if state["file"] exists
   - If file exists, append file_info formatted as "\n\nThe following file must be used in reference to answer the question:\n {state["file"]}"
   - Build research_steps string formatted as "### Planner's Plan\nThe planner determined the following research steps were needed to answer the question: {state['research_steps']}"
   - Build expert_steps string formatted as "\nThe planner determined the following expert steps were needed to answer the question: {state['expert_steps']}\n\n"
   - Build user_question string formatted as "## User Question:\nDoes the planner's plan have the correct and logical research and expert steps needed to answer the input question? If yes, approve. If no, reject."
   - Create critic message using compose_agent_message with sender="orchestrator", receiver="critic_planner", type="instruction", and content combining task + research_steps + expert_steps + user_question
6. Check if current_step equals "researcher"
7. If current_step is "researcher":
   - Check if critic_researcher_decision equals "reject"
   - If critic_researcher_decision is "reject":
     - Create retry message using compose_agent_message with sender="orchestrator", receiver="researcher", type="instruction", content formatted as "Use the following feedback to improve the research:\n{state["critic_researcher_feedback"]}", and step_id=state["current_research_index"]
   - If critic_researcher_decision is not "reject":
     - Increment state["current_research_index"] by 1
     - Create research instruction message using compose_agent_message with sender="orchestrator", receiver="researcher", type="instruction", content formatted as "Research the following topic or question: {state['research_steps'][state['current_research_index']]}", and step_id=state["current_research_index"]
8. Check if current_step equals "critic_researcher"
9. If current_step is "critic_researcher":
   - Build topic context string formatted as "Use the following context to answer the User Question:\n\n## Context\n### Research Topic\nThe researcher was asked to research the following topic: {state['research_steps'][state['current_research_index']]}\n\n"
   - Build results string formatted as "### Research Results\nThe researcher's results are: {state['research_results'][state['current_research_index']]}\n\n"
   - Build user_question string formatted as "## User Question:\nDoes the researcher's results contain sufficient information on the topic? If yes, approve. If no, reject."
   - Create critic message using compose_agent_message with sender="orchestrator", receiver="critic_researcher", type="instruction", and content combining topic + results + user_question
10. Check if current_step equals "expert"
11. If current_step is "expert":
    - Check if critic_expert_decision equals "reject"
    - If critic_expert_decision is "reject":
      - Create retry message using compose_agent_message with sender="orchestrator", receiver="expert", type="instruction", and content formatted as "Use the following feedback to improve your answer:\n{state["critic_expert_feedback"]}"
    - If critic_expert_decision is not "reject":
      - Build context string formatted as "Use the following context and recommended instructions to answer the question:\n ## Context:\n{state['research_results']}\n\n"
      - Build expert_steps string formatted as "## Recommended Instructions:\nIt was recommended to perform the following steps to answer the question:\n{state['expert_steps']}\n\n"
      - Build user_question string formatted as "## The Question:\nAnswer the question: {state['question']}"
      - Create expert instruction message using compose_agent_message with sender="orchestrator", receiver="expert", type="instruction", and content combining context + expert_steps + user_question
12. Check if current_step equals "critic_expert"
13. If current_step is "critic_expert":
    - Build question context string formatted as "Use the following context answer the User Question:\n ## Context:\n\n### Expert Question:\n The expert was asked to answer the following question: {state['question']}\n\n"
    - Build context string formatted as "### Researched Information:\nThe expert had the following researched information to use to answer the question:\n{state["research_results"]}\n\n"
    - Build expert_answer string formatted as "## Expert Answer:\nThe expert gave the following response and reasoning:\nExpert answer: {state['expert_answer']}\nExpert reasoning: {state['expert_reasoning']}\n\n"
    - Build user_question string formatted as "## User Question:\nDoes the expert's answer actually answer the question to a satisfactory level? If yes, approve. If no, reject."
    - Create critic message using compose_agent_message with sender="orchestrator", receiver="critic_expert", type="instruction", and content combining question + context + expert_answer + user_question
14. Check if current_step equals "finalizer"
15. If current_step is "finalizer":
    - Create finalizer instruction message using compose_agent_message with sender="orchestrator", receiver="finalizer", type="instruction", and content formatted as "Generate the final answer and reasoning trace (logical steps) to answer the question."
16. If current_step is invalid (not matching any condition):
    - Raise ValueError with message formatted as "Invalid current step: {state['current_step']}"
17. Send the composed message using send_message function with state and message parameters
18. Return the updated state

### Workflow Control
Controls workflow execution by setting current_step and sending appropriate messages to agents.

### State Management
Reads next_step and various state fields to compose messages.
Updates current_step and current_research_index in state.
Sends messages through send_message function.

### Communication Patterns
- **Agent Communication**: Sends messages to different agents based on current step
- **Message Composition**: Creates context-rich messages for each agent type
- **Feedback Integration**: Includes critic feedback in retry scenarios

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
- Raises ValueError if current_step is invalid
- Error message includes the invalid current step for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Main Orchestrator

### Component name:
orchestrator

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Orchestrator logic to coordinate the multi-agent workflow
- **Responsibilities**: 
  - Follows the 4-step process outlined in the logical design
  - Determines the next step in the workflow
  - Checks retry count and handles limit exceeded scenarios
  - Executes the next step by setting current_step and sending message
  - Coordinates all agent interactions and workflow transitions
  - Manages workflow state and progression

### Component interface:
#### Inputs:
- state: GraphState // The current state of the graph

#### Outputs:
- GraphState // The updated state of the graph

#### Validations:
- Handled by state field access validation

### Direct Dependencies with Other Components
- determine_next_step function
- check_retry_limit function
- execute_next_step function

### Internal Logic
1. Log the beginning of orchestrator execution with current step
2. Call determine_next_step function to determine next step
3. Call check_retry_limit function to check retry limits
4. Call execute_next_step function to execute the next step
5. Log successful completion with next step
6. Return the updated state

### Workflow Control
Controls the entire multi-agent workflow by coordinating the 4-step process and managing workflow state transitions.

### State Management
Reads and updates state throughout the workflow process.
Coordinates state transitions between different workflow steps.

### Communication Patterns
- **Workflow Coordination**: Coordinates all agent interactions and workflow transitions
- **State Management**: Manages workflow state and progression

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution with current step
- Append logging (INFO) at the end of successful completion with next step

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Orchestrator Routing

### Component name:
route_from_orchestrator

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Route the state to the appropriate agent based on the current step
- **Responsibilities**: 
  - Determines which agent should receive the state based on current_step
  - Maps current_step values to appropriate agent names
  - Handles routing for all agent types (planner, researcher, expert, critic, finalizer)
  - Provides conditional routing logic for workflow execution
  - Validates current_step and raises error for invalid steps

### Component interface:
#### Inputs:
- state: GraphState // The current state of the graph

#### Outputs:
- str // The name of the agent to route to

#### Validations:
- Handled by current_step validation logic

### Direct Dependencies with Other Components
None

### Internal Logic
1. Check if current_step is "planner"
2. If planner, return "planner"
3. Check if current_step is "researcher"
4. If researcher, return "researcher"
5. Check if current_step is "expert"
6. If expert, return "expert"
7. Check if current_step is "critic_planner"
8. If critic_planner, return "critic"
9. Check if current_step is "critic_researcher"
10. If critic_researcher, return "critic"
11. Check if current_step is "critic_expert"
12. If critic_expert, return "critic"
13. Check if current_step is "finalizer"
14. If finalizer, return "finalizer"
15. If current_step is invalid, raise ValueError with error message

### Workflow Control
Controls workflow routing by determining which agent should receive the state based on current_step.

### State Management
Reads current_step from state to determine routing destination.
Does not modify state, only reads for routing decision.

### Communication Patterns
None. This component does not communicate, rather it determines routing destination

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
- Raises ValueError if current_step is invalid
- Error message includes the invalid current step for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Planner Agent Factory

### Component name:
create_planner_agent

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create a planner agent function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a planner agent
  - Injects configuration and LLM dependencies into the agent function
  - Handles LLM invocation with system prompt and message history
  - Validates LLM response against output schema
  - Updates state with research_steps and expert_steps
  - Composes and sends response message to orchestrator
  - Provides planning capabilities for workflow execution

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing system prompt and output schema
- llm_planner: ChatOpenAI // The LLM instance for planner operations

#### Outputs:
- Callable[[GraphState], GraphState] // The planner agent function

#### Validations:
- Handled by validate_llm_response function

### Direct Dependencies with Other Components
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

### Internal Logic
1. Define inner function planner_agent that takes GraphState as parameter
2. Log the beginning of planner execution
3. Create system prompt using SystemMessage with config.system_prompt content
4. Get agent conversation history using get_agent_conversation function
5. Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
6. Invoke LLM with system prompt concatenated with message history
7. Validate response using validate_llm_response function
8. Update state["research_steps"] with response["research_steps"]
9. Update state["expert_steps"] with response["expert_steps"]
10. Compose agent message using compose_agent_message function with sender="planner", receiver="orchestrator", type="response", and content containing research steps and expert steps
11. Send message using send_message function
12. Log successful completion
13. Return the updated state
14. Return the inner planner_agent function

### Workflow Control
None

### State Management
Reads message history from state and updates research_steps and expert_steps fields.
Sends response message through send_message function.

### Communication Patterns
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with planning results
- **LLM Integration**: Communicates with LLM for planning operations

### External Dependencies
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for planner operations

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- llm_planner: ChatOpenAI - LLM instance passed from outer scope

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Researcher Agent Factory

### Component name:
create_researcher_agent

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create a researcher agent function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a researcher agent
  - Injects configuration and compiled researcher graph dependencies
  - Handles researcher state management for individual research steps
  - Executes research using compiled researcher subgraph
  - Validates LLM response against output schema
  - Updates state with research results and researcher states
  - Composes and sends response message to orchestrator
  - Provides research capabilities for workflow execution

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing output schema
- compiled_researcher_graph: Callable // The compiled researcher subgraph function

#### Outputs:
- Callable[[GraphState], GraphState] // The researcher agent function

#### Validations:
- Handled by validate_llm_response function

### Direct Dependencies with Other Components
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

### Internal Logic
1. Define inner function researcher_agent that takes GraphState as parameter
2. Log the beginning of researcher execution
3. Get current research index from state
4. Get agent conversation history using get_agent_conversation function with step_id = current research index
5. Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
6. Check if ResearcherState exists for current index
7. If ResearcherState doesn't exist:
   - Create new ResearcherState with messages, step_index, and result=None
8. If ResearcherState exists:
   - Get existing ResearcherState from state
   - Append latest message to ResearcherState messages
9. Execute research using compiled_researcher_graph.invoke with ResearcherState
10. Validate response using validate_llm_response function
11. Store response result in ResearcherState
12. Update ResearcherState in state
13. Store research results in state:
    - If research_results list length <= current index, append result
    - Otherwise, update result at current index
14. Compose agent message using compose_agent_message function with sender="researcher", receiver="orchestrator", type="response", step_id=current_research_index, and content containing research completion status
15. Send message using send_message function
16. Log successful completion
17. Return the updated state
18. Return the inner researcher_agent function

### Workflow Control
None

### State Management
Reads current_research_index and manages researcher_states and research_results fields.
Creates and updates ResearcherState for individual research steps.
Sends response message through send_message function.

### Communication Patterns
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with research completion status
- **Subgraph Integration**: Communicates with compiled researcher subgraph

### External Dependencies
None

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- compiled_researcher_graph: Callable - Compiled researcher subgraph passed from outer scope

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Expert Agent Factory

### Component name:
create_expert_agent

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create an expert agent function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns an expert agent
  - Injects configuration and compiled expert graph dependencies
  - Handles expert state management for reasoning operations
  - Executes expert reasoning using compiled expert subgraph
  - Validates LLM response against output schema
  - Updates state with expert answer and reasoning
  - Composes and sends response message to orchestrator
  - Provides expert reasoning capabilities for workflow execution

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing output schema
- compiled_expert_graph: Callable // The compiled expert subgraph function

#### Outputs:
- Callable[[GraphState], GraphState] // The expert agent function

#### Validations:
- Handled by validate_llm_response function

### Direct Dependencies with Other Components
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

### Internal Logic
1. Define inner function expert_agent that takes GraphState as parameter
2. Log the beginning of expert execution
3. Get agent conversation history using get_agent_conversation function
4. Convert agent messages to LangChain format and take only the last message
5. Get expert_state from state
6. Check if expert_state is None
7. If expert_state is None:
   - Create new ExpertState with messages, question, research_steps, research_results, and empty expert fields
8. If expert_state exists:
   - Extend expert_state messages with new message_in
9. Execute expert reasoning using compiled_expert_graph.invoke with expert_state
10. Validate response using validate_llm_response function
11. Store response expert_answer and expert_reasoning in expert_state
12. Update expert_state in state
13. Store expert_answer and expert_reasoning in state
14. Compose agent message using compose_agent_message function with sender="expert", receiver="orchestrator", type="response", and content containing expert answer and reasoning
15. Send message using send_message function
16. Log successful completion
17. Return the updated state
18. Return the inner expert_agent function

### Workflow Control
None

### State Management
Reads expert_state from state and manages expert_answer and expert_reasoning fields.
Creates and updates ExpertState for reasoning operations.
Sends response message through send_message function.

### Communication Patterns
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with expert answer and reasoning
- **Subgraph Integration**: Communicates with compiled expert subgraph

### External Dependencies
None

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- compiled_expert_graph: Callable - Compiled expert subgraph passed from outer scope

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Critic Agent Factory

### Component name:
create_critic_agent

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create a critic agent function with the given prompts for different critic types
- **Responsibilities**: 
  - Creates a factory function that returns a critic agent
  - Injects configuration and LLM dependencies into the agent function
  - Handles different critic types based on current_step (critic_planner, critic_researcher, critic_expert)
  - Selects appropriate system prompt based on critic type
  - Handles LLM invocation with system prompt and message history
  - Validates LLM response against output schema
  - Updates state with critic decisions and feedback
  - Composes and sends response message to orchestrator
  - Provides quality assessment capabilities for workflow execution

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing system prompts and output schema
- llm_critic: ChatOpenAI // The LLM instance for critic operations

#### Outputs:
- Callable[[GraphState], GraphState] // The critic agent function

#### Validations:
- Handled by validate_llm_response function

### Direct Dependencies with Other Components
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

### Internal Logic
1. Define inner function critic_agent that takes GraphState as parameter
2. Log the beginning of critic execution
3. Determine which critic to run based on current_step
4. If current_step is "critic_planner":
   - Get critic_prompt from config.system_prompt["critic_planner"]
5. If current_step is "critic_researcher":
   - Get critic_prompt from config.system_prompt["critic_researcher"]
6. If current_step is "critic_expert":
   - Get critic_prompt from config.system_prompt["critic_expert"]
7. If current_step is invalid, raise RuntimeError
8. Create system prompt using SystemMessage with critic_prompt content
9. Get agent conversation history using get_agent_conversation function with current_step
10. Convert agent messages to LangChain format and take only the last message
11. Invoke LLM with system prompt concatenated with message history
12. Validate response using validate_llm_response function
13. Store critic decision and feedback based on current step:
    - If critic_planner: store in critic_planner_decision and critic_planner_feedback
    - If critic_researcher: store in critic_researcher_decision and critic_researcher_feedback
    - If critic_expert: store in critic_expert_decision and critic_expert_feedback
14. Compose agent message using compose_agent_message function with sender="critic", receiver="orchestrator", type="response", and content containing decision and feedback
15. Send message using send_message function
16. Log successful completion
17. Return the updated state
18. Return the inner critic_agent function

### Workflow Control
None

### State Management
Reads current_step from state and updates critic decision and feedback fields based on critic type.
Sends response message through send_message function.

### Communication Patterns
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with critic decision and feedback
- **LLM Integration**: Communicates with LLM for quality assessment operations

### External Dependencies
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for critic operations

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- llm_critic: ChatOpenAI - LLM instance passed from outer scope

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

### Error Handling
- Raises RuntimeError if current_step is invalid for critic operations
- Error message includes the invalid current step for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Finalizer Agent Factory

### Component name:
create_finalizer_agent

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create a finalizer agent function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a finalizer agent
  - Injects configuration and LLM dependencies into the agent function
  - Handles LLM invocation with system prompt and message history
  - Validates LLM response against output schema
  - Updates state with final answer and reasoning trace
  - Composes and sends response message to orchestrator
  - Provides final answer generation capabilities for workflow execution

### Component interface:
#### Inputs:
- config: AgentConfig // The agent configuration containing system prompt and output schema
- llm_finalizer: ChatOpenAI // The LLM instance for finalizer operations

#### Outputs:
- Callable[[GraphState], GraphState] // The finalizer agent function

#### Validations:
- Handled by validate_llm_response function

### Direct Dependencies with Other Components
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

### Internal Logic
1. Define inner function finalizer_agent that takes GraphState as parameter
2. Log the beginning of finalizer execution
3. Create system prompt using SystemMessage with config.system_prompt content
4. Get agent conversation history using get_agent_conversation function
5. Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
6. Invoke LLM with system prompt concatenated with message history
7. Validate response using validate_llm_response function
8. Update state["final_answer"] with response["final_answer"]
9. Update state["final_reasoning_trace"] with response["final_reasoning_trace"]
10. Compose agent message using compose_agent_message function with sender="finalizer", receiver="orchestrator", type="response", and content containing final answer and reasoning trace
11. Send message using send_message function
12. Log successful completion
13. Return the updated state
14. Return the inner finalizer_agent function

### Workflow Control
None

### State Management
Reads message history from state and updates final_answer and final_reasoning_trace fields.
Sends response message through send_message function.

### Communication Patterns
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with final answer and reasoning trace
- **LLM Integration**: Communicates with LLM for final answer generation operations

### External Dependencies
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for finalizer operations

### Global variables
None

### Closed-over variables
- config: AgentConfig - Configuration passed from outer scope
- llm_finalizer: ChatOpenAI - LLM instance passed from outer scope

### Decorators
None

### Logging
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## OpenAI LLM Factory

### Component name:
openai_llm_factory

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Create an OpenAI LLM with the given model and temperature
- **Responsibilities**: 
  - Creates ChatOpenAI instance with specified model and temperature
  - Configures structured output with JSON mode
  - Provides factory pattern for OpenAI LLM creation
  - Enables consistent LLM configuration across the system

### Component interface:
#### Inputs:
- model: string // The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
- temperature: float // The temperature setting for the LLM (0.0 to 2.0)
- output_schema: dict // The structured output schema for JSON mode

#### Outputs:
- ChatOpenAI // The configured OpenAI LLM instance

#### Validations:
- Handled by ChatOpenAI constructor validation
- Temperature range validation handled by OpenAI API

### Direct Dependencies with Other Components
None

### Internal Logic
1. Create ChatOpenAI instance with provided model and temperature parameters
2. Configure the LLM with structured output using the provided output_schema and json_mode method
3. Return the configured ChatOpenAI instance

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it creates LLM instances

### External Dependencies
- **LangChain ChatOpenAI**: Library for OpenAI LLM interface
- **OpenAI API**: External API for LLM access

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## LLM Factory

### Component name:
llm_factory

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Get the appropriate LLM factory based on the provider
- **Responsibilities**: 
  - Routes to appropriate LLM factory based on provider configuration
  - Supports multiple LLM providers through factory pattern
  - Delegates LLM creation to provider-specific factories
  - Provides unified interface for LLM creation across different providers

### Component interface:
#### Inputs:
- config: AgentConfig // The configuration for the agent containing provider, model, temperature, and output_schema

#### Outputs:
- ChatOpenAI // The LLM with structured output

#### Validations:
- Handled by provider validation logic
- Provider-specific factory validation

### Direct Dependencies with Other Components
- openai_llm_factory function

### Internal Logic
1. Check if config.provider equals "openai"
2. If provider is "openai":
   - Call openai_llm_factory function with config.model, config.temperature, and config.output_schema
   - Return the result from openai_llm_factory
3. If provider is not "openai":
   - Raise ValueError with invalid provider message

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it routes to appropriate LLM factories

### External Dependencies
None

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
- Raises ValueError if provider is not "openai"
- Error message includes the invalid provider for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Multi-Agent Graph Factory

### Component name:
create_multi_agent_graph

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Factory function that creates and compiles a multi-agent graph with injected prompts
- **Responsibilities**: 
  - Creates LLM instances for all agents using factory pattern
  - Creates researcher and expert subgraphs with tools
  - Creates all agent functions with injected prompts and LLMs
  - Builds complete StateGraph with all nodes and edges
  - Compiles and returns the complete multi-agent workflow graph
  - Provides unified graph creation interface for multi-agent system

### Component interface:
#### Inputs:
- agent_configs: dict[str, AgentConfig] // Dictionary containing all agent configurations

#### Outputs:
- StateGraph // Compiled graph ready for invocation

#### Validations:
- Handled by LangGraph StateGraph validation
- Agent configuration validation handled by individual factory functions

### Direct Dependencies with Other Components
- llm_factory function
- get_research_tools function
- get_expert_tools function
- create_researcher_llm_node function
- create_researcher_subgraph function
- create_expert_llm_node function
- create_expert_subgraph function
- create_planner_agent function
- create_researcher_agent function
- create_expert_agent function
- create_critic_agent function
- create_finalizer_agent function
- create_input_interface function
- orchestrator function
- route_from_orchestrator function

### Internal Logic
1. Create LLM instances dynamically for all agents:
   - Create llm_planner using llm_factory with planner config
   - Create llm_researcher using llm_factory with researcher config
   - Create llm_expert using llm_factory with expert config
   - Create llm_critic using llm_factory with critic config
   - Create llm_finalizer using llm_factory with finalizer config
2. Create Researcher Subgraphs:
   - Get research tools using asyncio.run(get_research_tools())
   - Bind research tools to llm_researcher
   - Create researcher node using create_researcher_llm_node
   - Create researcher graph using create_researcher_subgraph
3. Create Expert Subgraphs:
   - Get expert tools using get_expert_tools()
   - Bind expert tools to llm_expert
   - Create expert node using create_expert_llm_node
   - Create expert graph using create_expert_subgraph
4. Create agent functions with injected prompts and LLMs:
   - Create planner_agent using create_planner_agent
   - Create researcher_agent using create_researcher_agent
   - Create expert_agent using create_expert_agent
   - Create critic_agent using create_critic_agent
   - Create finalizer_agent using create_finalizer_agent
5. Create input interface with retry limit using create_input_interface
6. Build the graph:
   - Create StateGraph instance with GraphState
   - Add all nodes to the graph (input_interface, orchestrator, planner, researcher, expert, critic, finalizer)
7. Add edges to the graph:
   - Add edge from START to input_interface
   - Add edge from input_interface to orchestrator
   - Add edges from all agents to orchestrator
   - Add edge from finalizer to END
8. Add conditional edges from orchestrator using route_from_orchestrator function with mapping dictionary containing "planner", "researcher", "expert", "critic", and "finalizer" routes
9. Compile and return the graph using builder.compile()

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it creates graph structure

### External Dependencies
- **LangGraph StateGraph**: Library for creating state-based graphs
- **LangGraph START/END**: Library constants for graph start and end nodes
- **asyncio**: Library for asynchronous operations

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
None. This component does not perform logging operations.

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---


# Entry Point Components

---

## Prompt File Loader

### Component name:
load_prompt_from_file

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Load a prompt from a text file and return its content as a string
- **Responsibilities**: 
  - Opens and reads text files with UTF-8 encoding
  - Strips whitespace from file content
  - Handles file not found errors gracefully
  - Handles general file reading errors
  - Logs successful file loading operations
  - Logs error conditions with detailed context
  - Returns cleaned prompt content for system use

### Component interface:
#### Inputs:
- file_path: string // The path to the prompt file to load

#### Outputs:
- string // The content of the prompt file with whitespace stripped

#### Validations:
- Handled by Python file system validation
- UTF-8 encoding validation handled by file opening

### Direct Dependencies with Other Components
None

### Internal Logic
1. Enter a try block to handle potential file reading errors
2. Open the file specified by file_path parameter with UTF-8 encoding in read mode using "with" statement
3. Read the entire file content using f.read() method
4. Strip whitespace from the beginning and end of the content using strip() method
5. Log a debug message indicating successful prompt loading with the file path
6. Return the cleaned content string
7. If FileNotFoundError occurs:
   - Log an error message with the file path that was not found
   - Raise a new FileNotFoundError with the same message
8. If any other Exception occurs:
   - Log an error message with the file path and the exception details
   - Raise a new Exception with the file path and exception details

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file reading operations

### External Dependencies
- **Python file system**: Library for file reading operations
- **Python logging**: Library for debug and error logging

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (DEBUG) when prompt is successfully loaded
- Append logging (ERROR) if file is not found
- Append logging (ERROR) if any other file reading error occurs

### Error Handling
- Catches FileNotFoundError and re-raises with context
- Catches general Exception and re-raises with context
- Logs all error conditions before re-raising exceptions
- All errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## Baseline Prompts Loader

### Component name:
load_baseline_prompts

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Load all baseline prompts from the prompts/baseline directory
- **Responsibilities**: 
  - Automatically determines the correct prompts directory path if not provided
  - Loads all required prompt files for each agent type
  - Manages prompt file naming and organization
  - Coordinates loading of multiple prompt files
  - Logs loading progress and completion status
  - Returns a dictionary containing all agent prompts
  - Handles path resolution and normalization

### Component interface:
#### Inputs:
- prompts_dir: string = None // Optional path to the prompts/baseline directory. If None, will automatically find the correct path.

#### Outputs:
- dict[str, str] // Dictionary containing all agent prompts with agent names as keys and prompt content as values

#### Validations:
- Handled by load_prompt_from_file function validation
- Path existence validation handled by file system operations

### Direct Dependencies with Other Components
- load_prompt_from_file function

### Internal Logic
1. Check if prompts_dir parameter is None
2. If prompts_dir is None:
   - Get the directory of the current script using os.path.dirname(os.path.abspath(__file__))
   - Construct the prompts directory path by going up one level from src/ to project root, then into prompts/baseline using os.path.join(script_dir, "..", "prompts", "baseline")
   - Normalize the path using os.path.normpath(prompts_dir)
3. Log an info message indicating the prompts directory being loaded from
4. Define prompt_files dictionary with agent names as keys and filenames as values:
   - "planner": "planner_system_prompt.txt"
   - "critic_planner": "critic_planner_system_prompt.txt"
   - "researcher": "researcher_system_prompt.txt"
   - "critic_researcher": "critic_researcher_system_prompt.txt"
   - "expert": "expert_system_prompt.txt"
   - "critic_expert": "critic_expert_system_prompt.txt"
   - "finalizer": "finalizer_system_prompt.txt"
5. Initialize empty prompts dictionary
6. Iterate through each agent_name and filename in prompt_files.items():
   - Construct the full file path using os.path.join(prompts_dir, filename)
   - Log a debug message indicating which agent prompt is being loaded and from which file path
   - Load the prompt content using load_prompt_from_file(file_path)
   - Store the loaded prompt in prompts dictionary with agent_name as key
7. Log an info message indicating successful loading with the number of prompts loaded
8. Return the prompts dictionary

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file loading operations

### External Dependencies
- **Python os.path**: Library for path manipulation and directory operations
- **Python logging**: Library for info and debug logging

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) when starting to load prompts from directory
- Append logging (DEBUG) for each individual prompt file being loaded
- Append logging (INFO) when successfully loaded all prompts with count

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## JSONL File Reader

### Component name:
read_jsonl_file

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Read a JSONL file line by line and yield each parsed JSON object
- **Responsibilities**: 
  - Opens and reads JSONL files line by line
  - Strips whitespace and newlines from each line
  - Skips empty lines during processing
  - Parses each non-empty line as JSON
  - Handles JSON parsing errors gracefully
  - Logs file reading operations and errors
  - Yields parsed JSON objects as dictionaries
  - Provides generator-based file processing for memory efficiency

### Component interface:
#### Inputs:
- file_path: string // Path to the JSONL file to read

#### Outputs:
- Generator yielding dict // Parsed JSON object from each line

#### Validations:
- Handled by Python file system validation
- JSON parsing validation handled by json.loads()

### Direct Dependencies with Other Components
None

### Internal Logic
1. Log a debug message indicating the JSONL file being read with the file path
2. Open the file specified by file_path parameter in read mode using "with" statement
3. Iterate through each line in the file using for loop
4. Strip whitespace and newlines from the current line using strip() method
5. Check if the stripped line is not empty (truthy)
6. If line is not empty:
   - Enter a try block to handle potential JSON parsing errors
   - Parse the line as JSON using json.loads(line)
   - Yield the parsed JSON object as a dictionary
   - If json.JSONDecodeError occurs:
     - Log an error message with the JSON parsing error details
     - Continue to the next line using continue statement
7. If line is empty, skip to the next line (implicit in the if condition)
8. Continue iteration until all lines in the file are processed

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file reading operations

### External Dependencies
- **Python file system**: Library for file reading operations
- **Python json**: Library for JSON parsing operations
- **Python logging**: Library for debug and error logging

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (DEBUG) when starting to read JSONL file
- Append logging (ERROR) if JSON parsing fails for any line

### Error Handling
- Catches json.JSONDecodeError and logs error with details
- Continues processing remaining lines after JSON parsing errors
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## JSONL File Writer

### Component name:
write_jsonl_file

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Write a list of data to a JSONL file, with each element as a separate line
- **Responsibilities**: 
  - Opens and writes to JSONL files in write mode
  - Converts each data item to JSON format
  - Writes each JSON object as a separate line with newline separator
  - Logs file writing operations and completion status
  - Handles file writing operations safely
  - Provides atomic file writing with proper file handling
  - Returns None to indicate completion

### Component interface:
#### Inputs:
- data_list: list[dict] // List of data to write (can be dicts, strings, etc.)
- output_file_path: string // Path to the output JSONL file

#### Outputs:
- None // Function does not return a value

#### Validations:
- Handled by Python file system validation
- JSON serialization validation handled by json.dumps()

### Direct Dependencies with Other Components
None

### Internal Logic
1. Log an info message indicating the number of items being written and the output file path
2. Open the file specified by output_file_path parameter in write mode using "with" statement
3. Iterate through each item in the data_list using for loop
4. Convert the current item to JSON format using json.dumps(item)
5. Write the JSON line to the file followed by a newline character using f.write(json_line + "\n")
6. Continue iteration until all items in data_list are processed
7. Log an info message indicating successful completion with the number of items written and the output file path

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles file writing operations

### External Dependencies
- **Python file system**: Library for file writing operations
- **Python json**: Library for JSON serialization operations
- **Python logging**: Library for info logging

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) when starting to write items to file
- Append logging (INFO) when successfully completed writing items to file

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Agent Configuration Factory

### Component name:
make_agent_configs

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Make a dictionary of agent configs from the prompts
- **Responsibilities**: 
  - Creates AgentConfig instances for all agent types
  - Configures each agent with specific parameters and settings
  - Maps prompts to appropriate agent configurations
  - Sets up output schemas for structured responses
  - Configures retry limits for each agent type
  - Logs configuration creation progress and completion
  - Returns a dictionary containing all agent configurations
  - Handles different prompt structures for different agent types

### Component interface:
#### Inputs:
- prompts: dict // Dictionary of prompts for each agent

#### Outputs:
- dict[str, AgentConfig] // Dictionary of agent configs with agent names as keys and AgentConfig instances as values

#### Validations:
- Handled by AgentConfig constructor validation
- Dictionary key access validation handled by Python

### Direct Dependencies with Other Components
- AgentConfig class from multi_agent_system module

### Internal Logic
1. Log an info message indicating the start of agent configuration creation
2. Create configs dictionary with agent configurations:
   - "planner": Create AgentConfig with name="planner", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"research_steps": list[str], "expert_steps": list[str]}, system_prompt=prompts["planner"], retry_limit=3
   - "researcher": Create AgentConfig with name="researcher", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"result": str}, system_prompt=prompts["researcher"], retry_limit=5
   - "expert": Create AgentConfig with name="expert", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"expert_answer": str, "reasoning_trace": str}, system_prompt=prompts["expert"], retry_limit=5
   - "critic": Create AgentConfig with name="critic", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"decision": Literal["approve", "reject"], "feedback": str}, system_prompt={"critic_planner":prompts["critic_planner"], "critic_researcher":prompts["critic_researcher"], "critic_expert":prompts["critic_expert"]}, retry_limit=None
   - "finalizer": Create AgentConfig with name="finalizer", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"final_answer": str, "final_reasoning_trace": str}, system_prompt=prompts["finalizer"], retry_limit=None
3. Log an info message indicating successful creation with the number of agent configurations created
4. Return the configs dictionary

### Workflow Control
None

### State Management
Does not access any graph states.

### Communication Patterns
None. This component does not communicate, rather it handles configuration creation

### External Dependencies
- **AgentConfig class**: From multi_agent_system module for agent configuration
- **Python typing**: Library for Literal type annotations
- **Python logging**: Library for info logging

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) when starting to create agent configurations
- Append logging (INFO) when successfully created agent configurations with count

### Error Handling
None. 
All errors and exceptions will be uncaught and bubble up the call stack.
This enables a global error handling design implemented in the entry point.

---

## Main Application Entry Point

### Component name:
main

### Component type:
function

### Component purpose and responsibilities:
- **Purpose**: Main function to run the application
- **Responsibilities**: 
  - Initializes and orchestrates the entire multi-agent system
  - Loads baseline prompts for all agents
  - Creates agent configurations from prompts
  - Builds the multi-agent graph
  - Processes JSONL input file containing questions
  - Invokes the graph for each question processing
  - Collects and stores responses
  - Writes results to output file
  - Handles application lifecycle and error management
  - Provides comprehensive logging throughout execution
  - Manages application startup and shutdown

### Component interface:
#### Inputs:
None // Function takes no parameters

#### Outputs:
- None // Function does not return a value

#### Validations:
- Handled by individual component validations
- File existence validation handled by file operations

### Direct Dependencies with Other Components
- load_baseline_prompts function
- make_agent_configs function
- create_multi_agent_graph function
- read_jsonl_file function
- write_jsonl_file function

### Internal Logic
1. Enter a try block to handle potential application errors
2. Log an info message indicating application start
3. Load baseline prompts:
   - Log info message indicating start of baseline prompt loading
   - Call load_baseline_prompts() function
   - Log info message with number of prompts loaded and their keys
4. Create agent configurations:
   - Call make_agent_configs(prompts) function
5. Create multi-agent graph:
   - Log info message indicating start of graph creation
   - Call create_multi_agent_graph(agent_configs) function
   - Log info message indicating successful graph creation
6. Initialize processing variables:
   - Set jsonl_file_path to "/home/joe/python-proj/hf-agents-course/src/metadata.jsonl"
   - Initialize empty responses list
   - Log info message indicating start of JSONL file processing
7. Process each item in the JSONL file:
   - Iterate through items returned by read_jsonl_file(jsonl_file_path)
   - Check if item["Level"] equals 1
   - If Level is 1:
     - Log info message with the question being processed
     - Check if item["file_name"] is not empty
     - If file_name is not empty, set file_path to "/home/joe/datum/gaia_lvl1/{item['file_name']}"
     - If file_name is empty, set file_path to empty string
     - Invoke graph with question and file_path using graph.invoke()
     - Create response dictionary with task_id, model_answer, and reasoning_trace
     - Append response to responses list
     - Log info message indicating question completion
     - Sleep for 5 seconds using time.sleep(5)
8. Write results to output file:
   - Log info message indicating start of response writing
   - Call write_jsonl_file(responses, "/home/joe/python-proj/hf-agents-course/src/gaia_lvl1_responses.jsonl")
9. Log info message indicating successful application completion
10. If any Exception occurs:
    - Log error message with exception details
    - Print error message to console
    - Exit application with exit code 1 using sys.exit(1)

### Workflow Control
Controls the entire application workflow from initialization to completion.

### State Management
Does not access any graph states directly, but orchestrates state management through graph invocation.

### Communication Patterns
- **Component Orchestration**: Coordinates all major system components
- **File Processing**: Manages input and output file operations
- **Graph Invocation**: Communicates with multi-agent graph for question processing

### External Dependencies
- **Python time**: Library for sleep operations
- **Python sys**: Library for system exit operations
- **Python logging**: Library for comprehensive logging

### Global variables
None

### Closed-over variables
None

### Decorators
None

### Logging
- Append logging (INFO) when application starts
- Append logging (INFO) when loading baseline prompts
- Append logging (INFO) with number of prompts loaded and their keys
- Append logging (INFO) when creating multi-agent graph
- Append logging (INFO) when graph creation is successful
- Append logging (INFO) when starting JSONL file processing
- Append logging (INFO) for each question being processed
- Append logging (INFO) for each question completion
- Append logging (INFO) when writing responses to output file
- Append logging (INFO) when application finishes successfully
- Append logging (ERROR) if application fails with exception details

### Error Handling
- Catches any Exception and logs error with details
- Prints error message to console
- Exits application with exit code 1 using sys.exit(1)
- All errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

