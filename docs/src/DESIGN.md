# Multi-Agent System Design Document

## Table of Contents

1. [Summary](#1-summary)
2. [Data Structures](#2-data-structures)
   - [Core System Data Structures](#core-system-data-structures)
   - [Message State Management](#message-state-management)
   - [Entry Point Data Structures](#entry-point-data-structures)
3. [Component Specifications](#3-component-specifications)
   - [Core Graph Components](#core-graph-components)
   - [Factory Functions](#factory-functions)
   - [Tool Suite](#tool-suite)
   - [Entry Point Components](#entry-point-components)
4. [System Workflow](#4-system-workflow)
   - [Main Execution Flow](#main-execution-flow)
   - [Graph Execution Pattern](#graph-execution-pattern)
5. [External Dependencies](#5-external-dependencies)
   - [LLM Services](#llm-services)
   - [Tool Dependencies](#tool-dependencies)
6. [Configuration Management](#6-configuration-management)
   - [Environment Variables](#environment-variables)
   - [Prompt Management](#prompt-management)
7. [Logging and Observability](#7-logging-and-observability)
   - [Logging Configuration](#logging-configuration)
   - [Opik Tracing](#opik-tracing)
8. [Error Handling](#8-error-handling)
   - [Global Error Strategy](#global-error-strategy)
   - [Component Error Handling](#component-error-handling)
9. [File Operations](#9-file-operations)
   - [Input Processing](#input-processing)
   - [Output Generation](#output-generation)

---

## 1. Summary

The system implements a streamlined **executor-guard architecture** for answering GAIA Level 1 questions through intelligent problem-solving and dynamic supervision. Built on LangGraph, the system employs a **2-agent approach** that combines an executor agent as the main brain with a guard agent embedded as a tool for quality control.

### Core Architecture

**Executor Agent**: The primary intelligence that analyzes tasks, orchestrates problem-solving, and coordinates tool usage. It receives user questions, breaks down complex problems, and systematically works through solutions using a comprehensive tool suite.

**Guard Agent**: Embedded as a tool within the executor's workflow, providing dynamic supervision, course correction, and quality control. The guard agent reviews reasoning processes, validates intermediate steps, and ensures answer quality throughout problem-solving.

### LangGraph Workflow

The system uses LangGraph for workflow orchestration with a streamlined graph structure:
- **Input Interface**: Processes user questions and optional file attachments
- **Executor Node**: Main agent that analyzes and solves problems
- **Tools Node**: Comprehensive tool suite including search, document processing, computation, and the guard agent
- **Conditional Edges**: Dynamic routing based on tool execution results

### Tool Integration

The executor agent has access to a comprehensive tool suite:
- **Search Tools**: Tavily web search, Wikipedia queries, YouTube transcript extraction
- **Document Processing**: PDF, Excel, PowerPoint, and text file parsing
- **Computation Tools**: Calculator, Python REPL, unit conversion
- **Guard Tool**: Embedded quality control and supervision

### Factory Pattern & Configuration

The system employs a factory pattern for dynamic graph creation and prompt injection:
- **Agent Configuration**: Centralized configuration for model selection, temperature, and system prompts
- **LLM Factory**: Dynamic LLM instantiation with configurable parameters
- **Prompt Management**: External prompt files loaded at runtime for flexibility

### Entry Point & Batch Processing

The main entry point script (`main.py`) orchestrates batch processing of GAIA questions:
- **Opik Integration**: Real-time tracing and observability for each question
- **JSONL Processing**: Batch processing of GAIA Level 1 questions from structured files
- **Thread Management**: Unique thread IDs for each question to maintain isolation
- **Result Extraction**: Structured output parsing with fallback mechanisms

### Graph Compilation & Execution

The system compiles a single graph per session and invokes it for each question:
- **Graph Compilation**: Single compilation with OpikTracer integration
- **Per-Question Invocation**: Each question runs as a separate graph execution
- **State Management**: Clean state reset between questions via unique thread IDs
- **Error Handling**: Robust error handling with logging and fallback mechanisms

This streamlined architecture provides efficient problem-solving capabilities while maintaining quality through embedded supervision, making it well-suited for batch processing of complex reasoning tasks.

---

## 2. Data Structures

### Core System Data Structures

#### Graph State

**Purpose**: Central state container for the executor-guard workflow orchestration

**Usage**: Used by the main LangGraph to manage workflow state, coordinate between executor and guard agents, and track progress through the question-answering process

**Validation**: Validated via LangGraph (Pydantic + typing)

**Inheritance**: Extends `MessagesState` from LangGraph for message management

**Definition**:
```
DATA_STRUCTURE GraphState
    Fields:
    // Input related fields
    question: string // User's question to be answered
    file: Optional[string] // Optional field, contains the path to the file associated with the question if specified
    
    // Message state (inherited from MessagesState)
    messages: list[BaseMessage] // LangChain BaseMessage objects for conversation history
        // Implementation type: messages: Annotated[list[BaseMessage], operator.add]
END DATA_STRUCTURE
```

#### Agent Configuration

**Purpose**: Configuration container for agent instantiation and behavior

**Usage**: Used by the factory pattern to create and configure agents with specific models, prompts, and parameters

**Validation**: Validated via Python type hints and constructor validation

**Definition**:
```
DATA_STRUCTURE AgentConfig
    Fields:
    name: string // Name identifier for the agent
    provider: string // LLM provider (e.g., "openai")
    model: string // Specific model name (e.g., "o4-mini")
    temperature: float // Temperature setting for LLM generation
    system_prompt: string // System prompt content loaded from external file
    output_schema: dict = none // Optional JSON schema for structured output validation
END DATA_STRUCTURE
```

### Message State Management

#### MessagesState Inheritance

**Purpose**: Provides message management capabilities through LangGraph's built-in message state

**Usage**: Inherited by GraphState to enable automatic message accumulation and conversation history

**Features**:
- **Automatic Message Accumulation**: Messages are automatically added to the conversation history
- **Type Safety**: Uses LangChain's `BaseMessage` types (SystemMessage, HumanMessage, AIMessage)
- **Operator Integration**: Uses `operator.add` for message concatenation

**Message Types**:
- **SystemMessage**: System instructions and prompts
- **HumanMessage**: User input and questions
- **AIMessage**: Agent responses and tool calls

### Entry Point Data Structures

#### Question Item

**Purpose**: Represents a single question from the GAIA dataset

**Usage**: Used by the entry point script to process individual questions from the JSONL file

**Validation**: Validated via JSON parsing

**Definition**:
```
DATA_STRUCTURE QuestionItem
    Fields:
    Question: string // The question text to be answered
    Level: integer // The difficulty level (1, 2, or 3)
    Answer: string // The ground truth answer
    Reasoning: string // The ground truth reasoning
    Category: string // The question category
    Subcategory: string // The question subcategory
    Source: string // The source of the question
    Year: integer // The year the question was created
    Month: integer // The month the question was created
    Day: integer // The day the question was created
    Hour: integer // The hour the question was created
    Minute: integer // The minute the question was created
    Second: integer // The second the question was created
    Microsecond: integer // The microsecond the question was created
    Timezone: string // The timezone of the question
    ID: string // Unique identifier for the question
END DATA_STRUCTURE
```

#### Response Item

**Purpose**: Represents the system's response to a question

**Usage**: Used by the entry point script to store and output the system's answers

**Validation**: Validated via JSON parsing

**Definition**:
```
DATA_STRUCTURE ResponseItem
    Fields:
    question: string // The original question
    model_answer: string // The model's answer to the question
    reasoning_trace: string // The model's reasoning process
    ground_truth_answer: string // The ground truth answer from the dataset
    ground_truth_reasoning: string // The ground truth reasoning from the dataset
    level: integer // The difficulty level of the question
    category: string // The question category
    subcategory: string // The question subcategory
    source: string // The source of the question
    id: string // Unique identifier for the question
END DATA_STRUCTURE
```

---

## 3. Component Specifications

This section documents the core components of the executor-guard system, including the main graph nodes, factory functions, tool suite, and entry point components. The system employs a streamlined architecture with an executor agent as the primary intelligence and a guard agent embedded as a tool for quality control.

### Component Categories
- **Core Graph Components**: Main workflow nodes (input_interface, executor_agent, ToolNode)
- **Factory Functions**: Dynamic creation and configuration (create_multi_agent_graph, llm_factory, create_executor_agent)
- **Tool Suite**: Comprehensive tool collection (guard_agent_tool, information gathering, file processing, computation)
- **Entry Point Components**: Batch processing and orchestration (load_prompt_from_file, load_baseline_prompts, read_jsonl_file)

### Core Graph Components

#### Input Interface

**Component name**: input_interface

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Process and validate user input, initialize message state
- **Responsibilities**: 
  - Validate question input and ensure it exists
  - Handle optional file attachments and format them appropriately
  - Initialize message state with HumanMessage containing task and file information
  - Provide error handling for missing or invalid inputs
  - Set up initial conversation context for the executor agent

**Component interface**:
- **Inputs**:
  - state: GraphState // The current graph state containing question and optional file
- **Outputs**:
  - GraphState // Updated state with initialized messages
- **Validations**:
  - Question must exist and not be empty
  - File path is optional but validated if provided

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Validate that question exists and is not empty
2. Set file field to None if not provided
3. Create HumanMessage with task description
4. Include file information in message if file is provided
5. Initialize messages list with the HumanMessage
6. Return updated state

**Pseudocode**:
```
FUNCTION input_interface(state: GraphState) -> GraphState
    /*
    Purpose: Process and validate user input, initialize message state
    
    BEHAVIOR:
    - Accepts: state (GraphState) - Current graph state with question and optional file
    - Produces: GraphState - Updated state with initialized messages
    - Handles: Input validation and message initialization
    
    DEPENDENCIES:
    - HumanMessage from langchain_core.messages
    - GraphState data structure
    
    IMPLEMENTATION NOTES:
    - Must validate question input before processing
    - Should handle optional file attachments gracefully
    - Must initialize messages for conversation context
    */
    
    // Validate question input
    IF NOT state.get("question") OR len(state["question"]) == 0 THEN
        RAISE ValueError("No question provided to input interface")
    END IF
    
    // Handle optional file attachment
    state["file"] = state["file"] IF state["file"] ELSE None
    
    // Create message content based on file presence
    IF state["file"] THEN
        message_content = f"## Task\n{state['question']}\n\n## File\nUse the following file to help you solve the task: {state['file']}"
    ELSE
        message_content = f"## Task\n{state['question']}"
    END IF
    
    // Initialize messages with HumanMessage
    state["messages"] = [HumanMessage(content=message_content)]
    
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Entry point for graph execution

**State Management**: Initializes message state for conversation context

**Communication Patterns**: Sets up initial communication context for executor agent

**External Dependencies**:
- **HumanMessage**: From langchain_core.messages for message creation
- **GraphState**: Data structure for state management

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: Logs execution start and completion

**Error Handling**:
- Raises ValueError for missing or empty questions
- Validates file path if provided
- All other errors bubble up to global error handling

#### Executor Agent

**Component name**: executor_agent (created by create_executor_agent)

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Main problem-solving agent with injected prompts and tool access
- **Responsibilities**: 
  - Analyze tasks and determine required tools for problem-solving
  - Execute problem-solving steps using available tools
  - Coordinate with guard agent for quality control and supervision
  - Return responses with tool calls or final answers
  - Maintain conversation context through message state

**Component interface**:
- **Inputs**:
  - state: GraphState // Current graph state with messages and context
- **Outputs**:
  - GraphState // Updated state with agent response
- **Validations**:
  - Messages must exist in state
  - System prompt must be injected via closure

**Direct Dependencies with Other Components**:
- **LLM**: OpenAI ChatOpenAI instance with bound tools
- **System Prompt**: Injected via AgentConfig closure
- **Tools**: All available tools bound to LLM

**Internal Logic**:
1. Create system prompt from injected configuration
2. Combine system prompt with current messages
3. Invoke LLM with prompt and message context
4. Check for tool calls in response
5. Log tool calls if present
6. Return response in messages format

**Pseudocode**:
```
FUNCTION executor_agent(state: GraphState) -> GraphState
    /*
    Purpose: Main problem-solving agent with injected prompts and tool access
    
    BEHAVIOR:
    - Accepts: state (GraphState) - Current state with messages and context
    - Produces: GraphState - Updated state with agent response
    - Handles: Task analysis, tool selection, and problem-solving execution
    
    DEPENDENCIES:
    - SystemMessage from langchain_core.messages
    - OpenAI ChatOpenAI with bound tools
    - AgentConfig for system prompt injection
    
    IMPLEMENTATION NOTES:
    - Uses closure to access injected system prompt and LLM
    - Must handle tool calls and final responses
    - Should maintain conversation context
    */
    
    // Create system prompt from injected configuration
    sys_prompt = [SystemMessage(content=config.system_prompt)]
    
    // Combine system prompt with current messages
    full_context = sys_prompt + state["messages"]
    
    // Invoke LLM with context
    response = llm_executor.invoke(full_context)
    
    // Check for tool calls (agent still working)
    IF hasattr(response, 'tool_calls') AND response.tool_calls THEN
        LOG("Executor tool calls: {response.tool_calls}")
        END IF
    
    // Return response in messages format
    RETURN {"messages": [response]}
    
END FUNCTION
```

**Workflow Control**: Main decision point for tool execution or completion

**State Management**: Updates message state with agent responses

**Communication Patterns**: Communicates with LLM and coordinates tool usage

**External Dependencies**:
- **SystemMessage**: From langchain_core.messages for system prompts
- **ChatOpenAI**: OpenAI LLM with bound tools
- **AgentConfig**: Configuration for system prompt injection

**Global variables**: None

**Closed-over variables**: 
- config: AgentConfig // Injected configuration
- llm_executor: ChatOpenAI // Injected LLM instance

**Decorators**: None

**Logging**: Logs execution start and tool calls

**Error Handling**:
- Handles LLM invocation errors
- Validates response structure
- All errors bubble up to global error handling

#### Tool Node

**Component name**: ToolNode

**Component type**: LangGraph node

**Component purpose and responsibilities**:
- **Purpose**: Execute all available tools based on executor agent requests
- **Responsibilities**: 
  - Route tool execution requests from executor agent
  - Execute guard agent tool for supervision and quality control
  - Execute information gathering tools (search, Wikipedia, YouTube)
  - Execute file processing tools (PDF, Excel, PowerPoint, text)
  - Execute computation tools (calculator, unit conversion, Python REPL)
  - Return tool results to executor agent

**Component interface**:
- **Inputs**:
  - state: GraphState // Current state with tool execution requests
- **Outputs**:
  - GraphState // Updated state with tool results
- **Validations**:
  - Tool calls must be valid and supported
  - Tool parameters must match expected schemas

**Direct Dependencies with Other Components**:
- **Guard Agent Tool**: For quality control and supervision
- **Information Gathering Tools**: wikipedia_tool, tavily_tool, youtube_transcript_tool
- **File Processing Tools**: unstructured_excel_tool, unstructured_powerpoint_tool, unstructured_pdf_tool, text_file_tool
- **Computation Tools**: calculator, unit_converter, python_repl_tool

**Internal Logic**:
1. Receive tool execution requests from executor agent
2. Route requests to appropriate tools based on tool names
3. Execute tools with provided parameters
4. Handle tool execution errors and exceptions
5. Return tool results in standardized format
6. Update state with tool outputs

**Pseudocode**:
```
NODE ToolNode(tools: list)
    /*
    Purpose: Execute all available tools based on executor agent requests
    
    BEHAVIOR:
    - Accepts: state (GraphState) - State with tool execution requests
    - Produces: GraphState - Updated state with tool results
    - Handles: Tool routing, execution, and result formatting
    
    DEPENDENCIES:
    - All available tools in tools list
    - LangGraph ToolNode implementation
    
    IMPLEMENTATION NOTES:
    - Uses LangGraph's built-in ToolNode for execution
    - Must handle all tool types and their specific requirements
    - Should provide consistent error handling across tools
    */
    
    // Tool execution handled by LangGraph ToolNode
    // Routes requests to appropriate tools based on tool names
    // Executes tools with provided parameters
    // Returns results in standardized format
    
END NODE
```

**Workflow Control**: Executes tools and returns results to executor

**State Management**: Updates state with tool execution results

**Communication Patterns**: Receives tool requests and returns results

**External Dependencies**:
- **LangGraph ToolNode**: Built-in tool execution node
- **All Tool Functions**: Guard agent, information gathering, file processing, computation tools

**Global variables**: None

**Closed-over variables**: 
- tools: list // List of all available tools

**Decorators**: None

**Logging**: Individual tools handle their own logging

**Error Handling**:
- Individual tools handle their own error cases
- ToolNode provides consistent error propagation
- All errors bubble up to global error handling

### Factory Functions

#### Multi-Agent Graph Factory

**Component name**: create_multi_agent_graph

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Main factory for creating and compiling the executor-guard graph
- **Responsibilities**: 
  - Assemble all tools using assemble_tools() function
  - Create executor agent with injected prompts and LLM
  - Build StateGraph with input_interface, executor, and tools nodes
  - Add conditional edges for tool execution routing
  - Compile graph and create OpikTracer for observability
  - Return compiled graph and tracer for execution

**Component interface**:
- **Inputs**:
  - agent_configs: dict[str, AgentConfig] // Dictionary containing all agent configurations
- **Outputs**:
  - Tuple[StateGraph, OpikTracer] // Compiled graph and Opik tracer
- **Validations**:
  - Agent configs must contain "executor" and "guard" configurations
  - All required configurations must be valid

**Direct Dependencies with Other Components**:
- **assemble_tools()**: For tool suite creation
- **llm_factory()**: For LLM creation with tool binding
- **create_executor_agent()**: For executor agent creation
- **StateGraph**: LangGraph graph builder
- **OpikTracer**: For observability and tracing

**Internal Logic**:
1. Assemble comprehensive tool suite using assemble_tools()
2. Create LLM instance with bound tools using llm_factory()
3. Create executor agent with injected configuration using create_executor_agent()
4. Build StateGraph with GraphState as the state type
5. Add nodes: input_interface, executor, and tools (ToolNode)
6. Add edges: START → input_interface → executor → conditional edges → tools → executor
7. Compile the graph
8. Create OpikTracer for observability
9. Return compiled graph and tracer

**Pseudocode**:
```
FUNCTION create_multi_agent_graph(agent_configs: dict[str, AgentConfig]) -> Tuple[StateGraph, OpikTracer]
    /*
    Purpose: Main factory for creating and compiling the executor-guard graph
    
    BEHAVIOR:
    - Accepts: agent_configs (dict[str, AgentConfig]) - Agent configurations
    - Produces: Tuple[StateGraph, OpikTracer] - Compiled graph and tracer
    - Handles: Graph creation, tool assembly, and compilation
    
    DEPENDENCIES:
    - assemble_tools() for tool suite creation
    - llm_factory() for LLM creation
    - create_executor_agent() for agent creation
    - StateGraph for graph building
    - OpikTracer for observability
    
    IMPLEMENTATION NOTES:
    - Must assemble tools before creating LLM
    - Must bind tools to LLM for executor agent
    - Must create proper graph structure with conditional edges
    - Must compile graph and create tracer for execution
    */
    
    // Assemble comprehensive tool suite
    tools = assemble_tools(agent_configs)
    
    // Create LLM with bound tools
    llm_executor = llm_factory(agent_configs["executor"], tools)
    
    // Create executor agent with injected configuration
    executor_agent = create_executor_agent(agent_configs["executor"], llm_executor)
    
    // Build the graph
    builder = StateGraph(GraphState)
    
    // Add nodes
    builder.add_node("input_interface", input_interface)
    builder.add_node("executor", executor_agent)
    builder.add_node("tools", ToolNode(tools))
    
    // Add edges
    builder.add_edge(START, "input_interface")
    builder.add_edge("input_interface", "executor")
    builder.add_conditional_edges("executor", tools_condition)
    builder.add_edge("tools", "executor")
    
    // Compile graph
    app = builder.compile()
    
    // Create OpikTracer for observability
    opik_tracer = OpikTracer(graph=app.get_graph(xray=True))
    
    RETURN (app, opik_tracer)
    
END FUNCTION
```

**Workflow Control**: Creates the complete workflow graph

**State Management**: Sets up GraphState as the state type

**Communication Patterns**: Establishes communication flow between nodes

**External Dependencies**:
- **StateGraph**: LangGraph graph builder
- **OpikTracer**: For observability and tracing
- **tools_condition**: LangGraph conditional edge logic

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: Logs graph creation process

**Error Handling**:
- Validates agent configurations
- Handles graph compilation errors
- All errors bubble up to global error handling

#### LLM Factory

**Component name**: llm_factory

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create LLM instances with tool binding
- **Responsibilities**: 
  - Route to appropriate provider factory (openai_llm_factory)
  - Handle tool binding for executor agent
  - Support multiple LLM providers (currently OpenAI only)
  - Validate provider configuration

**Component interface**:
- **Inputs**:
  - config: AgentConfig // Agent configuration with provider and model details
  - tools: list = None // Optional list of tools to bind to LLM
- **Outputs**:
  - ChatOpenAI // Configured LLM instance with bound tools
- **Validations**:
  - Provider must be supported (currently "openai")
  - Configuration must contain valid model and temperature

**Direct Dependencies with Other Components**:
- **openai_llm_factory()**: For OpenAI LLM creation
- **AgentConfig**: For configuration parameters

**Internal Logic**:
1. Check if provider is "openai"
2. Call openai_llm_factory with model, temperature, and tools
3. Return configured LLM instance
4. Raise ValueError for unsupported providers

**Pseudocode**:
```
FUNCTION llm_factory(config: AgentConfig, tools: list = None) -> ChatOpenAI
    /*
    Purpose: Create LLM instances with tool binding
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - Agent configuration
    - Accepts: tools (list) - Optional tools to bind
    - Produces: ChatOpenAI - Configured LLM instance
    - Handles: Provider routing and tool binding
    
    DEPENDENCIES:
    - openai_llm_factory() for OpenAI LLM creation
    - AgentConfig for configuration parameters
    
    IMPLEMENTATION NOTES:
    - Currently supports only OpenAI provider
    - Must handle tool binding if tools provided
    - Should validate provider before routing
    */
    
    // Route to appropriate provider factory
    IF config.provider == "openai" THEN
        RETURN openai_llm_factory(config.model, config.temperature, tools)
    ELSE
        RAISE ValueError(f"Invalid provider: {config.provider}")
    END IF
    
END FUNCTION
```

**Workflow Control**: None (factory function)

**State Management**: None (factory function)

**Communication Patterns**: None (factory function)

**External Dependencies**:
- **openai_llm_factory()**: For OpenAI LLM creation

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None

**Error Handling**:
- Raises ValueError for unsupported providers
- All other errors bubble up from provider factories

#### OpenAI LLM Factory

**Component name**: openai_llm_factory

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create OpenAI ChatOpenAI instances with configuration
- **Responsibilities**: 
  - Create ChatOpenAI with specified model and temperature
  - Bind tools to LLM if provided
  - Return configured LLM instance ready for use

**Component interface**:
- **Inputs**:
  - model: str // OpenAI model name (e.g., "o4-mini")
  - temperature: float // Temperature setting for generation
  - tools: list = None // Optional list of tools to bind
- **Outputs**:
  - ChatOpenAI // Configured OpenAI LLM instance
- **Validations**:
  - Model must be valid OpenAI model
  - Temperature must be between 0 and 2
  - Tools must be valid tool objects if provided

**Direct Dependencies with Other Components**:
- **ChatOpenAI**: OpenAI LLM class
- **Tool objects**: For binding to LLM

**Internal Logic**:
1. Create ChatOpenAI instance with model and temperature
2. Bind tools to LLM if tools list is provided
3. Return configured LLM instance

**Pseudocode**:
```
FUNCTION openai_llm_factory(model: str, temperature: float, tools: list = None) -> ChatOpenAI
    /*
    Purpose: Create OpenAI ChatOpenAI instances with configuration
    
    BEHAVIOR:
    - Accepts: model (str) - OpenAI model name
    - Accepts: temperature (float) - Temperature setting
    - Accepts: tools (list) - Optional tools to bind
    - Produces: ChatOpenAI - Configured LLM instance
    - Handles: LLM creation and tool binding
    
    DEPENDENCIES:
    - ChatOpenAI from langchain_openai
    - Tool objects for binding
    
    IMPLEMENTATION NOTES:
    - Must create LLM with proper model and temperature
    - Must bind tools if provided
    - Should return ready-to-use LLM instance
    */
    
    // Create ChatOpenAI instance
    llm = ChatOpenAI(model=model, temperature=temperature)
    
    // Bind tools if provided
    IF tools THEN
        llm = llm.bind_tools(tools)
    END IF
    
    RETURN llm
    
END FUNCTION
```

**Workflow Control**: None (factory function)

**State Management**: None (factory function)

**Communication Patterns**: None (factory function)

**External Dependencies**:
- **ChatOpenAI**: From langchain_openai for LLM creation

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None

**Error Handling**:
- Handles ChatOpenAI creation errors
- Handles tool binding errors
- All errors bubble up to calling functions

#### Executor Agent Factory

**Component name**: create_executor_agent

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create executor agent function with injected prompts
- **Responsibilities**: 
  - Create executor_agent function with closure over config and LLM
  - Inject system prompt from AgentConfig
  - Handle tool calls and response processing
  - Return callable executor agent function

**Component interface**:
- **Inputs**:
  - config: AgentConfig // Agent configuration with system prompt
  - llm_executor: ChatOpenAI // LLM instance with bound tools
- **Outputs**:
  - Callable[[GraphState], GraphState] // Executor agent function
- **Validations**:
  - Config must contain valid system prompt
  - LLM must be properly configured with tools

**Direct Dependencies with Other Components**:
- **SystemMessage**: For system prompt creation
- **GraphState**: For state management

**Internal Logic**:
1. Define inner executor_agent function with closure over config and LLM
2. Create system prompt from injected configuration
3. Combine system prompt with current messages
4. Invoke LLM with full context
5. Handle tool calls and response processing
6. Return response in messages format

**Pseudocode**:
```
FUNCTION create_executor_agent(config: AgentConfig, llm_executor: ChatOpenAI) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create executor agent function with injected prompts
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - Agent configuration
    - Accepts: llm_executor (ChatOpenAI) - LLM with bound tools
    - Produces: Callable - Executor agent function
    - Handles: Function creation with injected configuration
    
    DEPENDENCIES:
    - SystemMessage for system prompt creation
    - GraphState for state management
    
    IMPLEMENTATION NOTES:
    - Uses closure to inject configuration and LLM
    - Must create callable function for graph execution
    - Should handle tool calls and responses properly
    */
    
    // Define inner executor agent function
    FUNCTION executor_agent(state: GraphState) -> GraphState
        // Create system prompt from injected configuration
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        
        // Combine system prompt with current messages
        response = llm_executor.invoke(sys_prompt + state["messages"])
        
        // Handle tool calls if present
        IF hasattr(response, 'tool_calls') AND response.tool_calls THEN
            LOG("Executor tool calls: {response.tool_calls}")
        END IF
        
        // Return response in messages format
        RETURN {"messages": [response]}
END FUNCTION
    
    RETURN executor_agent
    
END FUNCTION
```

**Workflow Control**: Creates the main workflow decision point

**State Management**: Creates function that manages message state

**Communication Patterns**: Creates function that communicates with LLM

**External Dependencies**:
- **SystemMessage**: From langchain_core.messages for system prompts

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig // Injected configuration
- llm_executor: ChatOpenAI // Injected LLM instance

**Decorators**: None

**Logging**: Logs tool calls in created function

**Error Handling**:
- Handles LLM invocation errors in created function
- All errors bubble up to global error handling

#### Guard Agent Tool Factory

**Component name**: create_guard_agent_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create a guard agent tool function for quality control and supervision
- **Responsibilities**: 
  - Create guard agent tool with closure over guard configuration
  - Inject system prompt from AgentConfig
  - Handle quality control and supervision requests
  - Return callable guard agent tool function
  - Provide embedded supervision capabilities

**Component interface**:
- **Inputs**:
  - config: AgentConfig // Guard agent configuration with system prompt
- **Outputs**:
  - Callable[[str, str, str], str] // Guard agent tool function
- **Validations**:
  - Config must contain valid system prompt
  - Guard configuration must be properly set up

**Direct Dependencies with Other Components**:
- **llm_factory()**: For LLM creation with guard configuration
- **SystemMessage**: For system prompt creation
- **HumanMessage**: For message formatting

**Internal Logic**:
1. Create LLM instance using llm_factory with guard configuration
2. Define inner guard_agent_tool function with closure over LLM
3. Format input message with original task, context, and question
4. Invoke LLM with system prompt and formatted message
5. Return guard agent's response as feedback or validation

**Pseudocode**:
```
FUNCTION create_guard_agent_tool(config: AgentConfig) -> Callable[[str, str, str], str]
    /*
    Purpose: Create a guard agent tool function for quality control and supervision
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - Guard agent configuration
    - Produces: Callable - Guard agent tool function
    - Handles: Quality control and supervision requests
    
    DEPENDENCIES:
    - llm_factory() for LLM creation
    - SystemMessage for system prompt creation
    - HumanMessage for message formatting
    
    IMPLEMENTATION NOTES:
    - Uses closure to inject guard configuration and LLM
    - Must create callable tool function for executor use
    - Should handle quality control requests effectively
    - Must format messages properly for guard agent
    */
    
    // Create LLM for guard agent
    llm_guard = llm_factory(config)
    
    // Define inner guard agent tool function
    FUNCTION guard_agent_tool(question_for_guard: str, original_task: str, context: str) -> str
        // Create system prompt from injected configuration
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        
        // Format input message with structured sections
        message_in = f"""## Original Task\n{original_task}\n\n## Context\n{context}\n\n## Question for Guard\n{question_for_guard}"""
        
        // Invoke LLM with system prompt and formatted message
        response = llm_guard.invoke(sys_prompt + [HumanMessage(content=message_in)])
        
        // Log successful completion
        LOG("Guard completed successfully")
        
        // Return guard agent's response
        RETURN response.content
END FUNCTION
    
    RETURN guard_agent_tool
    
END FUNCTION
```

**Workflow Control**: Provides supervision and quality control capabilities

**State Management**: Does not directly manage state, provides feedback

**Communication Patterns**: Creates function that communicates with guard LLM

**External Dependencies**:
- **llm_factory()**: For LLM creation with guard configuration
- **SystemMessage**: From langchain_core.messages for system prompts
- **HumanMessage**: From langchain_core.messages for message creation

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig // Injected guard configuration
- llm_guard: ChatOpenAI // Injected LLM instance

**Decorators**:
- @tool: LangChain tool decorator for guard agent tool

**Logging**:
- Logs guard execution start and completion

**Error Handling**:
- Handles LLM creation errors
- All errors bubble up to calling functions

#### Tool Assembly

**Component name**: assemble_tools

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Assemble comprehensive tool suite for executor agent
- **Responsibilities**: 
  - Create guard agent tool using create_guard_agent_tool()
  - Return list of all available tools (guard, search, file processing, computation)
  - Ensure all tools are properly configured and available

**Component interface**:
- **Inputs**:
  - agent_configs: dict[str, AgentConfig] // Dictionary containing agent configurations
- **Outputs**:
  - list // List of all available tools
- **Validations**:
  - Agent configs must contain "guard" configuration
  - All tool functions must be available

**Direct Dependencies with Other Components**:
- **create_guard_agent_tool()**: For guard agent tool creation
- **All tool functions**: wikipedia_tool, tavily_tool, youtube_transcript_tool, etc.

**Internal Logic**:
1. Create guard agent tool using create_guard_agent_tool()
2. Return comprehensive list of all available tools
3. Include guard agent, information gathering, file processing, and computation tools

**Pseudocode**:
```
FUNCTION assemble_tools(agent_configs: dict[str, AgentConfig]) -> list
    /*
    Purpose: Assemble comprehensive tool suite for executor agent
    
    BEHAVIOR:
    - Accepts: agent_configs (dict[str, AgentConfig]) - Agent configurations
    - Produces: list - List of all available tools
    - Handles: Tool creation and assembly
    
    DEPENDENCIES:
    - create_guard_agent_tool() for guard agent tool
    - All available tool functions
    
    IMPLEMENTATION NOTES:
    - Must create guard agent tool first
    - Must include all available tool types
    - Should return complete tool suite
    */
    
    // Create guard agent tool
    guard_agent_tool = create_guard_agent_tool(agent_configs["guard"])
    
    // Return comprehensive tool list
    RETURN [
        guard_agent_tool,
        youtube_transcript_tool,
        tavily_tool,
        wikipedia_tool,
        unstructured_excel_tool,
        unstructured_powerpoint_tool,
        unstructured_pdf_tool,
        text_file_tool,
        unit_converter,
        calculator,
        python_repl_tool
    ]
    
END FUNCTION
```

**Workflow Control**: None (assembly function)

**State Management**: None (assembly function)

**Communication Patterns**: None (assembly function)

**External Dependencies**:
- **create_guard_agent_tool()**: For guard agent tool creation
- **All tool functions**: For comprehensive tool suite

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None

**Error Handling**:
- Handles guard agent tool creation errors
- All other errors bubble up from tool functions

### Tool Suite

#### Guard Agent Tool

**Component name**: guard_agent_tool (created by create_guard_agent_tool)

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Embedded quality control and supervision
- **Responsibilities**: 
  - Review reasoning processes and final answers for quality and completeness
  - Provide course correction and improvement suggestions during problem-solving
  - Validate answer quality and ensure reasoning is sound
  - Support both proactive and reactive supervision throughout the workflow
  - Offer critical feedback to improve the executor agent's performance

**Component interface**:
- **Inputs**:
  - question_for_guard: str // Specific question or request for the guard agent
  - original_task: str // The original task/question being solved
  - context: str // Relevant information and context for the guard's review
- **Outputs**:
  - str // Guard agent's feedback, suggestions, or validation results
- **Validations**:
  - All input parameters must be non-empty strings
  - Context should contain relevant information for meaningful review

**Direct Dependencies with Other Components**:
- **llm_factory()**: For LLM creation with guard configuration
- **AgentConfig**: For guard agent configuration and system prompt

**Internal Logic**:
1. Create LLM instance using llm_factory with guard configuration
2. Format input message with original task, context, and specific question
3. Invoke LLM with system prompt and formatted message
4. Return guard agent's response as feedback or validation

**Pseudocode**:
```    
// Define guard agent tool function
FUNCTION guard_agent_tool(question_for_guard: str, original_task: str, context: str) -> str
    // Format input message
    message_in = f"""## Original Task\n{original_task}\n\n## Context\n{context}\n\n## Question for Guard\n{question_for_guard}"""
    
    // Invoke LLM with system prompt and message
    response = llm_guard.invoke(sys_prompt + [HumanMessage(content=message_in)])
    
    RETURN response.content
END FUNCTION

END FUNCTION
```

**Workflow Control**: Provides supervision and quality control feedback

**State Management**: Does not directly manage state, provides feedback

**Communication Patterns**: Receives review requests and returns feedback

**External Dependencies**:
- **llm_factory()**: For LLM creation
- **HumanMessage**: From langchain_core.messages for message creation

**Global variables**: None

**Closed-over variables**:
- llm_guard: ChatOpenAI // Guard agent LLM instance
- sys_prompt: list // System prompt for guard agent

**Decorators**: @tool

**Logging**: Logs guard execution start and completion

**Error Handling**:
- Handles LLM invocation errors
- Validates input parameters
- All errors bubble up to global error handling

#### Information Gathering Tools

**Component category**: Information gathering and research tools

**Component purpose and responsibilities**:
- **Purpose**: External information retrieval and research capabilities
- **Responsibilities**: 
  - Provide access to current and historical information
  - Support research and fact-checking activities
  - Enable comprehensive information gathering for problem-solving
  - Handle various information sources and formats

##### Wikipedia Tool

**Component name**: wikipedia_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Full page content retrieval from Wikipedia with fallback methods
- **Responsibilities**: 
  - Search for Wikipedia pages matching query terms
  - Retrieve complete page content including all sections
  - Use multiple retrieval methods (Wikipedia Library, Beautiful Soup)
  - Provide comprehensive page information with metadata
  - Handle cases where content is incomplete or missing

**Component interface**:
- **Inputs**:
  - query: str // Search term or page title to look up
- **Outputs**:
  - str // Full Wikipedia page content with metadata
- **Validations**:
  - Query must be non-empty string
  - Query should be relevant search term

**Direct Dependencies with Other Components**:
- **WikipediaQueryRun**: LangChain Wikipedia query tool
- **WikipediaAPIWrapper**: LangChain Wikipedia API wrapper

**Internal Logic**:
1. Search for Wikipedia page using WikipediaQueryRun
2. Retrieve page content using Wikipedia API wrapper
3. Check content completeness and use fallback if needed
4. Format response with page metadata and full content
5. Return comprehensive page information

**Pseudocode**:
```
FUNCTION wikipedia_tool(query: str) -> str
    /*
    Purpose: Retrieve full Wikipedia page content with fallback methods
    
    BEHAVIOR:
    - Accepts: query (str) - Search term or page title
    - Produces: str - Full page content with metadata
    - Handles: Page retrieval with multiple fallback methods
    
    DEPENDENCIES:
    - WikipediaQueryRun for page search
    - WikipediaAPIWrapper for content retrieval
    
    IMPLEMENTATION NOTES:
    - Uses multiple retrieval methods for reliability
    - Provides comprehensive page information
    - Handles incomplete content gracefully
    */
    
    // Search for Wikipedia page
    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    page_info = wiki_tool.run(query)
    
    // Retrieve full page content
    page = wiki_tool.api_wrapper.page(page_info)
    full_content = page.content
    
    // Check content completeness and use fallback if needed
    IF content_looks_complete THEN
        method = "Wikipedia Library"
    ELSE
        method = "Beautiful Soup"
        // Use Beautiful Soup fallback method
    END IF
    
    // Format response with metadata
    response = f"Page Title: {page.title}\n"
    response += f"Method: {method}\n"
    response += f"FULL PAGE CONTENT:\n{full_content}"
    
    RETURN response
    
END FUNCTION
```

**Workflow Control**: Provides information retrieval capabilities

**State Management**: Does not manage state, provides information

**Communication Patterns**: Receives search queries and returns content

**External Dependencies**:
- **WikipediaQueryRun**: LangChain Wikipedia query tool
- **WikipediaAPIWrapper**: LangChain Wikipedia API wrapper

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs search queries and successful retrievals

**Error Handling**:
- Handles page not found errors
- Handles API errors gracefully
- Returns error messages for failed retrievals

##### Tavily Tool

**Component name**: tavily_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Web search for current information using Tavily search engine
- **Responsibilities**: 
  - Perform web searches for current and up-to-date information
  - Provide search results from multiple web sources
  - Support real-time information gathering
  - Handle various search queries and topics

**Component interface**:
- **Inputs**:
  - query: str // Search query for web search
- **Outputs**:
  - str // Search results from Tavily
- **Validations**:
  - Query must be non-empty string
  - Query should be searchable terms

**Direct Dependencies with Other Components**:
- **TavilySearch**: LangChain Tavily search tool

**Internal Logic**:
1. Create TavilySearch instance
2. Execute search with provided query
3. Return search results

**Pseudocode**:
```
FUNCTION tavily_tool(query: str) -> str
    /*
    Purpose: Perform web search using Tavily search engine
    
    BEHAVIOR:
    - Accepts: query (str) - Search query
    - Produces: str - Search results
    - Handles: Web search for current information
    
    DEPENDENCIES:
    - TavilySearch from langchain_tavily
    
    IMPLEMENTATION NOTES:
    - Provides current web search results
    - Supports various search topics
    */
    
    // Create Tavily search tool
    tavily_tool = TavilySearch()
    
    // Execute search
    results = tavily_tool.invoke(query)
    
    RETURN results
    
END FUNCTION
```

**Workflow Control**: Provides current information retrieval

**State Management**: Does not manage state

**Communication Patterns**: Receives search queries and returns results

**External Dependencies**:
- **TavilySearch**: From langchain_tavily for web search

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs search queries

**Error Handling**:
- Handles search API errors
- Returns error messages for failed searches

##### YouTube Transcript Tool

**Component name**: youtube_transcript_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Extract transcript from YouTube videos with video metadata
- **Responsibilities**: 
  - Extract full transcript from YouTube video URLs
  - Provide video metadata (title, channel, duration)
  - Handle various video formats and languages
  - Support content analysis from video sources

**Component interface**:
- **Inputs**:
  - url: str // YouTube video URL
- **Outputs**:
  - str // Video transcript with metadata
- **Validations**:
  - URL must be valid YouTube URL
  - Video must have available transcript

**Direct Dependencies with Other Components**:
- **YoutubeLoader**: LangChain YouTube loader

**Internal Logic**:
1. Load YouTube video using YoutubeLoader
2. Extract transcript content
3. Gather video metadata (title, channel, duration)
4. Format response with metadata and transcript
5. Return comprehensive video information

**Pseudocode**:
```
FUNCTION youtube_transcript_tool(url: str) -> str
    /*
    Purpose: Extract transcript from YouTube video with metadata
    
    BEHAVIOR:
    - Accepts: url (str) - YouTube video URL
    - Produces: str - Video transcript with metadata
    - Handles: Video transcript extraction
    
    DEPENDENCIES:
    - YoutubeLoader from langchain_community.document_loaders
    
    IMPLEMENTATION NOTES:
    - Extracts full transcript content
    - Provides comprehensive video metadata
    - Handles various video formats
    */
    
    // Load YouTube video
    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
    documents = loader.load()
    
    // Extract transcript and metadata
    transcript = documents[0].page_content
    metadata = documents[0].metadata
    
    // Format response with metadata
    video_info = f"Video Title: {metadata.get('title', 'Unknown')}\n"
    video_info += f"Channel: {metadata.get('author', 'Unknown')}\n"
    video_info += f"Duration: {metadata.get('length', 'Unknown')} seconds\n\n"
    
    RETURN video_info + transcript
    
END FUNCTION
```

**Workflow Control**: Provides video content extraction

**State Management**: Does not manage state

**Communication Patterns**: Receives video URLs and returns transcripts

**External Dependencies**:
- **YoutubeLoader**: From langchain_community.document_loaders

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs video processing and successful extractions

**Error Handling**:
- Handles invalid URLs
- Handles videos without transcripts
- Returns error messages for failed extractions

#### File Processing Tools

**Component category**: Document content extraction and processing tools

**Component purpose and responsibilities**:
- **Purpose**: Extract and process content from various file formats
- **Responsibilities**: 
  - Load and parse different file formats
  - Extract text content from structured documents
  - Handle various document types and structures
  - Provide content for analysis and processing

##### Excel File Tool

**Component name**: unstructured_excel_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Load and extract content from Excel files
- **Responsibilities**: 
  - Parse Excel files (.xlsx, .xls formats)
  - Extract text content from cells and sheets
  - Handle multiple worksheets
  - Provide structured document output

**Component interface**:
- **Inputs**:
  - file_path: str // Path to Excel file
- **Outputs**:
  - list[Document] // List of document objects with extracted content
- **Validations**:
  - File path must be valid and accessible
  - File must be valid Excel format

**Direct Dependencies with Other Components**:
- **UnstructuredExcelLoader**: LangChain Excel loader

**Internal Logic**:
1. Create UnstructuredExcelLoader instance
2. Load Excel file from specified path
3. Extract content from all worksheets
4. Return list of document objects

**Pseudocode**:
```
FUNCTION unstructured_excel_tool(file_path: str) -> list[Document]
    /*
    Purpose: Load and extract content from Excel files
    
    BEHAVIOR:
    - Accepts: file_path (str) - Path to Excel file
    - Produces: list[Document] - Extracted content documents
    - Handles: Excel file parsing and content extraction
    
    DEPENDENCIES:
    - UnstructuredExcelLoader from langchain_community.document_loaders
    
    IMPLEMENTATION NOTES:
    - Handles multiple worksheets
    - Extracts text from cells
    - Returns structured document objects
    */
    
    // Create Excel loader
    loader = UnstructuredExcelLoader(file_path)
    
    // Load and extract content
    documents = loader.load()
    
    RETURN documents
    
END FUNCTION
```

**Workflow Control**: Provides Excel content extraction

**State Management**: Does not manage state

**Communication Patterns**: Receives file paths and returns content

**External Dependencies**:
- **UnstructuredExcelLoader**: From langchain_community.document_loaders

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs file loading operations

**Error Handling**:
- Handles file not found errors
- Handles invalid Excel format errors
- Returns empty list for failed loads

##### PowerPoint Tool

**Component name**: unstructured_powerpoint_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Load and extract content from PowerPoint files
- **Responsibilities**: 
  - Parse PowerPoint files (.pptx, .ppt formats)
  - Extract text content from slides
  - Handle slide notes and metadata
  - Provide structured document output

**Component interface**:
- **Inputs**:
  - file_path: str // Path to PowerPoint file
- **Outputs**:
  - list[Document] // List of document objects with extracted content
- **Validations**:
  - File path must be valid and accessible
  - File must be valid PowerPoint format

**Direct Dependencies with Other Components**:
- **UnstructuredPowerPointLoader**: LangChain PowerPoint loader

**Internal Logic**:
1. Create UnstructuredPowerPointLoader instance
2. Load PowerPoint file from specified path
3. Extract content from all slides
4. Return list of document objects

**Pseudocode**:
```
FUNCTION unstructured_powerpoint_tool(file_path: str) -> list[Document]
    /*
    Purpose: Load and extract content from PowerPoint files
    
    BEHAVIOR:
    - Accepts: file_path (str) - Path to PowerPoint file
    - Produces: list[Document] - Extracted content documents
    - Handles: PowerPoint file parsing and content extraction
    
    DEPENDENCIES:
    - UnstructuredPowerPointLoader from langchain_community.document_loaders
    
    IMPLEMENTATION NOTES:
    - Handles multiple slides
    - Extracts text from slide content
    - Returns structured document objects
    */
    
    // Create PowerPoint loader
    loader = UnstructuredPowerPointLoader(file_path)
    
    // Load and extract content
    documents = loader.load()
    
    RETURN documents
    
END FUNCTION
```

**Workflow Control**: Provides PowerPoint content extraction

**State Management**: Does not manage state

**Communication Patterns**: Receives file paths and returns content

**External Dependencies**:
- **UnstructuredPowerPointLoader**: From langchain_community.document_loaders

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs file loading operations

**Error Handling**:
- Handles file not found errors
- Handles invalid PowerPoint format errors
- Returns empty list for failed loads

##### PDF Tool

**Component name**: unstructured_pdf_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Load and extract content from PDF files
- **Responsibilities**: 
  - Parse PDF files (.pdf format)
  - Extract text content from pages
  - Handle text and image-based PDFs
  - Provide structured document output

**Component interface**:
- **Inputs**:
  - file_path: str // Path to PDF file
- **Outputs**:
  - list[Document] // List of document objects with extracted content
- **Validations**:
  - File path must be valid and accessible
  - File must be valid PDF format

**Direct Dependencies with Other Components**:
- **UnstructuredPDFLoader**: LangChain PDF loader

**Internal Logic**:
1. Create UnstructuredPDFLoader instance
2. Load PDF file from specified path
3. Extract content from all pages
4. Return list of document objects

**Pseudocode**:
```
FUNCTION unstructured_pdf_tool(file_path: str) -> list[Document]
    /*
    Purpose: Load and extract content from PDF files
    
    BEHAVIOR:
    - Accepts: file_path (str) - Path to PDF file
    - Produces: list[Document] - Extracted content documents
    - Handles: PDF file parsing and content extraction
    
    DEPENDENCIES:
    - UnstructuredPDFLoader from langchain_community.document_loaders
    
    IMPLEMENTATION NOTES:
    - Handles multiple pages
    - Extracts text from PDF content
    - Returns structured document objects
    */
    
    // Create PDF loader
    loader = UnstructuredPDFLoader(file_path)
    
    // Load and extract content
    documents = loader.load()
    
    RETURN documents
    
END FUNCTION
```

**Workflow Control**: Provides PDF content extraction

**State Management**: Does not manage state

**Communication Patterns**: Receives file paths and returns content

**External Dependencies**:
- **UnstructuredPDFLoader**: From langchain_community.document_loaders

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs file loading operations

**Error Handling**:
- Handles file not found errors
- Handles invalid PDF format errors
- Returns empty list for failed loads

##### Text File Tool

**Component name**: text_file_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Load and extract content from text files
- **Responsibilities**: 
  - Parse plain text files (.txt format)
  - Extract text content with proper encoding
  - Handle various text encodings
  - Provide simple text content output

**Component interface**:
- **Inputs**:
  - file_path: str // Path to text file
- **Outputs**:
  - str // Extracted text content
- **Validations**:
  - File path must be valid and accessible
  - File must be readable text format

**Direct Dependencies with Other Components**:
- **TextLoader**: LangChain text loader

**Internal Logic**:
1. Create TextLoader instance
2. Load text file from specified path
3. Extract text content
4. Return text content as string

**Pseudocode**:
```
FUNCTION text_file_tool(file_path: str) -> str
    /*
    Purpose: Load and extract content from text files
    
    BEHAVIOR:
    - Accepts: file_path (str) - Path to text file
    - Produces: str - Extracted text content
    - Handles: Text file loading and content extraction
    
    DEPENDENCIES:
    - TextLoader from langchain_community.document_loaders
    
    IMPLEMENTATION NOTES:
    - Handles various text encodings
    - Extracts plain text content
    - Returns simple string output
    */
    
    // Create text loader
    loader = TextLoader(file_path)
    
    // Load and extract content
    documents = loader.load()
    
    // Return text content
    IF documents THEN
        RETURN documents[0].page_content
    ELSE
        RETURN ""
    END IF
    
END FUNCTION
```

**Workflow Control**: Provides text content extraction

**State Management**: Does not manage state

**Communication Patterns**: Receives file paths and returns text content

**External Dependencies**:
- **TextLoader**: From langchain_community.document_loaders

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs file loading operations

**Error Handling**:
- Handles file not found errors
- Handles encoding errors
- Returns empty string for failed loads

#### Computation Tools

**Component category**: Mathematical computation and code execution tools

**Component purpose and responsibilities**:
- **Purpose**: Perform mathematical calculations and code execution
- **Responsibilities**: 
  - Evaluate mathematical expressions safely
  - Convert between different units
  - Execute Python code with controlled environment
  - Provide computational capabilities for problem-solving

##### Calculator Tool

**Component name**: calculator

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Evaluate mathematical expressions safely
- **Responsibilities**: 
  - Evaluate basic math expressions (+, -, *, /, **, parentheses)
  - Provide safe mathematical computation
  - Support mathematical functions from math module
  - Prevent execution of dangerous operations

**Component interface**:
- **Inputs**:
  - expression: str // Mathematical expression to evaluate
- **Outputs**:
  - str // Result of the expression as string
- **Validations**:
  - Expression must be valid mathematical expression
  - Expression must not contain dangerous operations

**Direct Dependencies with Other Components**:
- **math module**: For mathematical functions

**Internal Logic**:
1. Define allowed mathematical functions from math module
2. Evaluate expression in controlled environment
3. Return result as string
4. Handle evaluation errors safely

**Pseudocode**:
```
FUNCTION calculator(expression: str) -> str
    /*
    Purpose: Evaluate mathematical expressions safely
    
    BEHAVIOR:
    - Accepts: expression (str) - Mathematical expression
    - Produces: str - Result of evaluation
    - Handles: Safe mathematical computation
    
    DEPENDENCIES:
    - math module for mathematical functions
    
    IMPLEMENTATION NOTES:
    - Uses controlled evaluation environment
    - Supports basic operations and math functions
    - Prevents dangerous operations
    */
    
    // Define allowed mathematical functions
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    
    // Evaluate expression safely
    result = eval(expression, {"__builtins__": None}, allowed_names)
    
    RETURN str(result)
    
END FUNCTION
```

**Workflow Control**: Provides mathematical computation

**State Management**: Does not manage state

**Communication Patterns**: Receives expressions and returns results

**External Dependencies**:
- **math module**: Python standard library for mathematical functions

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs expressions and results

**Error Handling**:
- Handles invalid mathematical expressions
- Handles division by zero errors
- Returns error messages for failed evaluations

##### Unit Converter Tool

**Component name**: unit_converter

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Convert between different units using pint library
- **Responsibilities**: 
  - Convert quantities between different unit systems
  - Support various unit types (length, weight, temperature, etc.)
  - Handle complex unit conversions
  - Provide accurate conversion results

**Component interface**:
- **Inputs**:
  - quantity: str // Quantity with unit (e.g., "10 meters", "5 kg")
  - to_unit: str // Target unit (e.g., "ft", "lbs")
- **Outputs**:
  - str // Converted value as string
- **Validations**:
  - Quantity must be valid format with unit
  - Target unit must be compatible

**Direct Dependencies with Other Components**:
- **pint library**: For unit conversion capabilities

**Internal Logic**:
1. Create pint UnitRegistry instance
2. Parse input quantity with unit
3. Convert to target unit
4. Return converted value as string

**Pseudocode**:
```
FUNCTION unit_converter(quantity: str, to_unit: str) -> str
    /*
    Purpose: Convert quantities between different units
    
    BEHAVIOR:
    - Accepts: quantity (str) - Quantity with unit
    - Accepts: to_unit (str) - Target unit
    - Produces: str - Converted value
    - Handles: Unit conversion using pint library
    
    DEPENDENCIES:
    - pint library for unit conversion
    
    IMPLEMENTATION NOTES:
    - Supports various unit types
    - Handles complex conversions
    - Provides accurate results
    */
    
    // Create unit registry
    ureg = pint.UnitRegistry()
    
    // Parse quantity and convert
    q = ureg(quantity)
    result = q.to(to_unit)
    
    RETURN str(result)
    
END FUNCTION
```

**Workflow Control**: Provides unit conversion capabilities

**State Management**: Does not manage state

**Communication Patterns**: Receives quantities and returns conversions

**External Dependencies**:
- **pint**: Python library for unit conversion

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs conversion operations and results

**Error Handling**:
- Handles invalid unit formats
- Handles incompatible unit conversions
- Returns error messages for failed conversions

##### Python REPL Tool

**Component name**: python_repl_tool

**Component type**: tool function

**Component purpose and responsibilities**:
- **Purpose**: Execute Python code with controlled environment and print statement capture
- **Responsibilities**: 
  - Execute Python code in safe environment
  - Capture output from print statements
  - Support data processing and analysis
  - Provide computational capabilities for complex tasks

**Component interface**:
- **Inputs**:
  - code: str // Python code to execute
- **Outputs**:
  - str // Output from code execution
- **Validations**:
  - Code must be valid Python syntax
  - Code should use print statements for output

**Direct Dependencies with Other Components**:
- **PythonREPLTool**: LangChain Python REPL tool

**Internal Logic**:
1. Create PythonREPLTool instance
2. Execute provided Python code
3. Capture output from print statements
4. Return execution results

**Pseudocode**:
```
FUNCTION python_repl_tool(code: str) -> str
    /*
    Purpose: Execute Python code with controlled environment
    
    BEHAVIOR:
    - Accepts: code (str) - Python code to execute
    - Produces: str - Output from execution
    - Handles: Python code execution with output capture
    
    DEPENDENCIES:
    - PythonREPLTool from langchain_experimental.tools.python.tool
    
    IMPLEMENTATION NOTES:
    - Uses controlled execution environment
    - Captures print statement output
    - Supports data processing tasks
    */
    
    // Create Python REPL tool
    python_repl_tool = PythonREPLTool()
    
    // Execute code and capture output
    result = python_repl_tool.invoke(code)
    
    RETURN result
    
END FUNCTION
```

**Workflow Control**: Provides code execution capabilities

**State Management**: Does not manage persistent state

**Communication Patterns**: Receives code and returns execution results

**External Dependencies**:
- **PythonREPLTool**: From langchain_experimental.tools.python.tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**: @tool

**Logging**: Logs code execution operations

**Error Handling**:
- Handles syntax errors in Python code
- Handles runtime errors during execution
- Returns error messages for failed executions




### Entry Point Components

#### Load Prompt from File

**Component name**: load_prompt_from_file

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Load a prompt from a text file
- **Responsibilities**: 
  - Reads prompt content from specified file path
  - Handles file encoding and error conditions
  - Provides logging for successful and failed operations
  - Returns cleaned prompt content

**Component interface**:
- **Inputs**:
  - file_path: string // Path to the prompt file
- **Outputs**:
  - string // Content of the prompt file
- **Validations**:
  - Handled by file system operations and encoding validation

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Open the file with UTF-8 encoding in read mode
2. Read the entire file content
3. Strip whitespace from the content
4. Log successful loading with debug level
5. Return the cleaned content
6. Handle FileNotFoundError with error logging and re-raise
7. Handle other exceptions with error logging and re-raise

**Pseudocode**:
```
FUNCTION load_prompt_from_file(file_path: string) -> string
    /*
    Purpose: Load a prompt from a text file
    
    BEHAVIOR:
    - Accepts: file_path (string) - Path to the prompt file
    - Produces: string - Content of the prompt file
    - Handles: File reading with proper encoding and error handling
    
    IMPLEMENTATION NOTES:
    - Should use UTF-8 encoding for file reading
    - Must strip whitespace from loaded content
    - Should provide comprehensive error handling
    - Should include logging for debugging
    */
    
    // Open the file with UTF-8 encoding in read mode
    WITH open(file_path, "r", encoding="utf-8") AS f:
        // Read the entire file content
        content = f.read()
        
        // Strip whitespace from the content
        cleaned_content = content.strip()
        
        // Log successful loading with debug level
        LOG_DEBUG(f"Successfully loaded prompt from: {file_path}")
        
        // Return the cleaned content
        RETURN cleaned_content
    END WITH
    
    // Handle FileNotFoundError with error logging and re-raise
    CATCH FileNotFoundError AS error
        LOG_ERROR(f"Prompt file not found: {file_path}")
        RAISE FileNotFoundError(f"Prompt file not found: {file_path}")
    
    // Handle other exceptions with error logging and re-raise
    CATCH Exception AS error
        LOG_ERROR(f"Error reading prompt file {file_path}: {str(error)}")
        RAISE Exception(f"Error reading prompt file {file_path}: {str(error)}")
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file operations

**External Dependencies**:
- **File System**: Access to prompt files on the local file system

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (DEBUG) for successful file loading
- Append logging (ERROR) for file not found errors
- Append logging (ERROR) for other file reading errors

**Error Handling**:
- Raises FileNotFoundError if the prompt file is not found
- Raises Exception for other file reading errors
- Error messages include the file path and specific error details
- All errors are logged before being re-raised

#### Load Baseline Prompts

**Component name**: load_baseline_prompts

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Load all baseline prompts from the prompts/baseline directory
- **Responsibilities**: 
  - Automatically locates the baseline prompts directory
  - Loads all required prompt files for each agent
  - Handles directory path resolution and file loading
  - Returns dictionary of agent prompts
  - Provides comprehensive logging for the loading process

**Component interface**:
- **Inputs**:
  - prompts_dir: string = none // Optional path to the prompts/baseline directory
- **Outputs**:
  - dict[string, string] // Dictionary containing all agent prompts
- **Validations**:
  - Handled by file system operations and load_prompt_from_file function

**Direct Dependencies with Other Components**:
- load_prompt_from_file function

**Internal Logic**:
1. If prompts_dir is None, automatically find the baseline prompts directory
2. Log the directory being used for loading prompts
3. Define the mapping of agent names to prompt file names
4. Iterate through each agent name and file name pair
5. Construct the full file path for each prompt file
6. Load the prompt using load_prompt_from_file function
7. Store the loaded prompt in the prompts dictionary
8. Log successful loading of all prompts
9. Return the complete prompts dictionary

**Pseudocode**:
```
FUNCTION load_baseline_prompts(prompts_dir: string = none) -> dict[string, string]
    /*
    Purpose: Load all baseline prompts from the prompts/baseline directory
    
    BEHAVIOR:
    - Accepts: prompts_dir (string) - Optional path to the prompts/baseline directory
    - Produces: dict[string, string] - Dictionary containing all agent prompts
    - Handles: Automatic directory location and prompt file loading
    
    DEPENDENCIES:
    - load_prompt_from_file: Function to load individual prompt files
    - File System: Access to prompt files on the local file system
    
    IMPLEMENTATION NOTES:
    - Should automatically locate prompts directory if not provided
    - Must load all required prompt files for each agent
    - Should provide comprehensive logging for the loading process
    - Should handle directory path resolution gracefully
    */
    
    // If prompts_dir is None, automatically find the baseline prompts directory
    IF prompts_dir IS none THEN
        // Try to find the baseline prompts directory relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        // Go up one level from src/ to the project root, then into prompts/baseline
        prompts_dir = os.path.join(script_dir, "..", "prompts", "baseline")
        prompts_dir = os.path.normpath(prompts_dir)
    END IF
    
    // Log the directory being used for loading prompts
    LOG_INFO(f"Loading prompts from directory: {prompts_dir}")
    
    // Define the mapping of agent names to prompt file names
    prompt_files = {
        "executor": "executor_system_prompt.txt",
        "guard": "guard_system_prompt.txt",
    }
    
    // Initialize empty prompts dictionary
    prompts = {}
    
    // Iterate through each agent name and file name pair
    FOR EACH (agent_name, filename) IN prompt_files.items() DO
        // Construct the full file path for each prompt file
        file_path = os.path.join(prompts_dir, filename)
        
        // Log debug information for each file being loaded
        LOG_DEBUG(f"Loading prompt for {agent_name} from: {file_path}")
        
        // Load the prompt using load_prompt_from_file function
        prompt_content = load_prompt_from_file(file_path)
        
        // Store the loaded prompt in the prompts dictionary
        prompts[agent_name] = prompt_content
    END FOR
    
    // Log successful loading of all prompts
    LOG_INFO(f"Successfully loaded {len(prompts)} prompts")
    
    // Return the complete prompts dictionary
    RETURN prompts
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file operations

**External Dependencies**:
- **File System**: Access to prompt files on the local file system

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (INFO) for directory being used
- Append logging (DEBUG) for each file being loaded
- Append logging (INFO) for successful completion

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.



#### JSONL File Reader

**Component name**: read_jsonl_file

**Component type**: function

**Component purpose and responsibilities**:
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

**Component interface**:
- **Inputs**:
  - file_path: string // Path to the JSONL file to read
- **Outputs**:
  - Generator yielding dict // Parsed JSON object from each line
- **Validations**:
  - Handled by Python file system validation
  - JSON parsing validation handled by json.loads()

**Direct Dependencies with Other Components**: None

**Internal Logic**:
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

**Pseudocode**:
```
// REQUIRED IMPORTS:
// import json
// import logging

FUNCTION read_jsonl_file(file_path: string) -> Generator[dict]
    /*
    Purpose: Read a JSONL file line by line and yield each parsed JSON object
    
    BEHAVIOR:
    - Accepts: file_path (string) - Path to the JSONL file to read
    - Produces: Generator yielding dict - Parsed JSON object from each line
    - Handles: Line-by-line file processing with JSON parsing
    
    EXTERNAL DEPENDENCIES:
    - Python file system: Library for file reading operations
    - Python json: Library for JSON parsing operations
    - Python logging: Library for debug and error logging
    
    IMPLEMENTATION NOTES:
    - Should open and read JSONL files line by line
    - Must strip whitespace and newlines from each line
    - Should skip empty lines during processing
    - Must parse each non-empty line as JSON
    - Should handle JSON parsing errors gracefully
    - Must log file reading operations and errors
    - Should yield parsed JSON objects as dictionaries
    - Must provide generator-based file processing for memory efficiency
    */
    
    // Log a debug message indicating the JSONL file being read with the file path
    LOG_DEBUG(f"Reading JSONL file: {file_path}")
    
    // Open the file specified by file_path parameter in read mode using "with" statement
    WITH open(file_path, 'r') AS f:
        // Iterate through each line in the file using for loop
        FOR line IN f DO
            // Strip whitespace and newlines from the current line using strip() method
            stripped_line = line.strip()
            
            // Check if the stripped line is not empty (truthy)
            IF stripped_line THEN
                // If line is not empty:
                // Enter a try block to handle potential JSON parsing errors
                TRY
                    // Parse the line as JSON using json.loads(line)
                    json_object = json.loads(stripped_line)
                    // Yield the parsed JSON object as a dictionary
                    YIELD json_object
                    
                CATCH json.JSONDecodeError AS error
                    // If json.JSONDecodeError occurs:
                    // Log an error message with the JSON parsing error details
                    LOG_ERROR(f"Error parsing JSON line: {error}")
                    // Continue to the next line using continue statement
                    CONTINUE
                    
                END TRY
            END IF
            // If line is empty, skip to the next line (implicit in the if condition)
        END FOR
    // Continue iteration until all lines in the file are processed
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file reading operations

**External Dependencies**:
- **Python file system**: Library for file reading operations
- **Python json**: Library for JSON parsing operations
- **Python logging**: Library for debug and error logging

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (DEBUG) when starting to read JSONL file
- Append logging (ERROR) if JSON parsing fails for any line

**Error Handling**:
- Catches json.JSONDecodeError and logs error with details
- Continues processing remaining lines after JSON parsing errors
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### JSONL File Writer

**Component name**: write_jsonl_file

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Write a list of data to a JSONL file, with each element as a separate line
- **Responsibilities**: 
  - Opens and writes to JSONL files in write mode
  - Converts each data item to JSON format
  - Writes each JSON object as a separate line with newline separator
  - Logs file writing operations and completion status
  - Handles file writing operations safely
  - Provides atomic file writing with proper file handling
  - Returns None to indicate completion

**Component interface**:
- **Inputs**:
  - data_list: list[dict] // List of data to write (can be dicts, strings, etc.)
  - output_file_path: string // Path to the output JSONL file
- **Outputs**:
  - None // Function does not return a value
- **Validations**:
  - Handled by Python file system validation
  - JSON serialization validation handled by json.dumps()

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log an info message indicating the number of items being written and the output file path
2. Open the file specified by output_file_path parameter in write mode using "with" statement
3. Iterate through each item in the data_list using for loop
4. Convert the current item to JSON format using json.dumps(item)
5. Write the JSON line to the file followed by a newline character using f.write(json_line + "\n")
6. Continue iteration until all items in data_list are processed
7. Log an info message indicating successful completion with the number of items written and the output file path

**Pseudocode**:
```
// REQUIRED IMPORTS:
// import json
// import logging

FUNCTION write_jsonl_file(data_list: list[dict], output_file_path: string) -> None
    /*
    Purpose: Write a list of data to a JSONL file, with each element as a separate line
    
    BEHAVIOR:
    - Accepts: data_list (list[dict]) - List of data to write (can be dicts, strings, etc.)
    - Accepts: output_file_path (string) - Path to the output JSONL file
    - Produces: None - Function does not return a value
    - Handles: File writing operations with JSON serialization
    
    EXTERNAL DEPENDENCIES:
    - Python file system: Library for file writing operations
    - Python json: Library for JSON serialization operations
    - Python logging: Library for info logging
    
    IMPLEMENTATION NOTES:
    - Should open and write to JSONL files in write mode
    - Must convert each data item to JSON format
    - Should write each JSON object as a separate line with newline separator
    - Must log file writing operations and completion status
    - Should handle file writing operations safely
    - Must provide atomic file writing with proper file handling
    - Should return None to indicate completion
    */
    
    // Log an info message indicating the number of items being written and the output file path
    LOG_INFO(f"Writing {len(data_list)} items to: {output_file_path}")
    
    // Open the file specified by output_file_path parameter in write mode using "with" statement
    WITH open(output_file_path, 'w') AS f:
        // Iterate through each item in the data_list using for loop
        FOR item IN data_list DO
            // Convert the current item to JSON format using json.dumps(item)
            json_line = json.dumps(item)
            // Write the JSON line to the file followed by a newline character using f.write(json_line + "\n")
            f.write(json_line + "\n")
        END FOR
    // Continue iteration until all items in data_list are processed
    
    // Log an info message indicating successful completion with the number of items written and the output file path
    LOG_INFO(f"Successfully wrote {len(data_list)} items to: {output_file_path}")
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file writing operations

**External Dependencies**:
- **Python file system**: Library for file writing operations
- **Python json**: Library for JSON serialization operations
- **Python logging**: Library for info logging

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (INFO) when starting to write items to file
- Append logging (INFO) when successfully completed writing items to file

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### Agent Configuration Factory

**Component name**: make_agent_configs

**Component type**: function

**Component purpose and responsibilities**:
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

**Component interface**:
- **Inputs**:
  - prompts: dict // Dictionary of prompts for each agent
- **Outputs**:
  - dict[str, AgentConfig] // Dictionary of agent configs with agent names as keys and AgentConfig instances as values
- **Validations**:
  - Handled by AgentConfig constructor validation
  - Dictionary key access validation handled by Python

**Direct Dependencies with Other Components**:
- AgentConfig class from multi_agent_system module

**Internal Logic**:
1. Log an info message indicating the start of agent configuration creation
2. Create configs dictionary with agent configurations:
   - "planner": Create AgentConfig with name="planner", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"research_steps": list[str], "expert_steps": list[str]}, system_prompt=prompts["planner"], retry_limit=5
   - "researcher": Create AgentConfig with name="researcher", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"result": str}, system_prompt=prompts["researcher"], retry_limit=5
   - "expert": Create AgentConfig with name="expert", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"expert_answer": str, "reasoning_trace": str}, system_prompt=prompts["expert"], retry_limit=5
   - "critic": Create AgentConfig with name="critic", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"decision": Literal["approve", "reject"], "feedback": str}, system_prompt={"critic_planner":prompts["critic_planner"], "critic_researcher":prompts["critic_researcher"], "critic_expert":prompts["critic_expert"]}, retry_limit=None
   - "finalizer": Create AgentConfig with name="finalizer", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"final_answer": str, "final_reasoning_trace": str}, system_prompt=prompts["finalizer"], retry_limit=None
3. Log an info message indicating successful creation with the number of agent configurations created
4. Return the configs dictionary

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from typing import Literal
// from multi_agent_system import AgentConfig
// import logging

FUNCTION make_agent_configs(prompts: dict) -> dict[str, AgentConfig]
    /*
    Purpose: Make a dictionary of agent configs from the prompts
    
    BEHAVIOR:
    - Accepts: prompts (dict) - Dictionary of prompts for each agent
    - Produces: dict[str, AgentConfig] - Dictionary of agent configs with agent names as keys and AgentConfig instances as values
    - Handles: Agent configuration creation with specific parameters and settings
    
    DEPENDENCIES:
    - AgentConfig class: From multi_agent_system module for agent configuration
    
    EXTERNAL DEPENDENCIES:
    - AgentConfig class: From multi_agent_system module for agent configuration
    - Python typing: Library for Literal type annotations
    - Python logging: Library for info logging
    
    IMPLEMENTATION NOTES:
    - Should create AgentConfig instances for all agent types
    - Must configure each agent with specific parameters and settings
    - Should map prompts to appropriate agent configurations
    - Must set up output schemas for structured responses
    - Should configure retry limits for each agent type
    - Must log configuration creation progress and completion
    - Should return a dictionary containing all agent configurations
    - Must handle different prompt structures for different agent types
    */
    
    // Log an info message indicating the start of agent configuration creation
    LOG_INFO("Creating agent configurations...")
    
    // Create configs dictionary with agent configurations:
    configs = {
        "planner": AgentConfig(name="planner", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"research_steps": list[str], "expert_steps": list[str]}, system_prompt=prompts["planner"], retry_limit=5),
        "researcher": AgentConfig(name="researcher", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"result": str}, system_prompt=prompts["researcher"], retry_limit=5),
        "expert": AgentConfig(name="expert", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"expert_answer": str, "reasoning_trace": str}, system_prompt=prompts["expert"], retry_limit=5),
        "critic": AgentConfig(name="critic", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"decision": Literal["approve", "reject"], "feedback": str}, system_prompt={"critic_planner":prompts["critic_planner"], "critic_researcher":prompts["critic_researcher"], "critic_expert":prompts["critic_expert"]}, retry_limit=None),
        "finalizer": AgentConfig(name="finalizer", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"final_answer": str, "final_reasoning_trace": str}, system_prompt=prompts["finalizer"], retry_limit=None),
    }
    
    // Log an info message indicating successful creation with the number of agent configurations created
    LOG_INFO(f"Created {len(configs)} agent configurations")
    
    // Return the configs dictionary
    RETURN configs
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles configuration creation

**External Dependencies**:
- **AgentConfig class**: From multi_agent_system module for agent configuration
- **Python typing**: Library for Literal type annotations
- **Python logging**: Library for info logging

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (INFO) when starting to create agent configurations
- Append logging (INFO) when successfully created agent configurations with count

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### Main Application Entry Point

**Component name**: main

**Component type**: function

**Component purpose and responsibilities**:
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

**Component interface**:
- **Inputs**: None // Function takes no parameters
- **Outputs**: None // Function does not return a value
- **Validations**:
  - Handled by individual component validations
  - File existence validation handled by file operations

**Direct Dependencies with Other Components**:
- load_baseline_prompts function
- make_agent_configs function
- create_multi_agent_graph function
- read_jsonl_file function
- write_jsonl_file function
- opik.configure function
- uuid.uuid4 function

**Internal Logic**:
1. Enter a try block to handle potential application errors
2. Configure Opik for real-time flushing using opik.configure(use_local=True)
3. Log an info message indicating application start
4. Load baseline prompts:
   - Log info message indicating start of baseline prompt loading
   - Call load_baseline_prompts() function
   - Log info message with number of prompts loaded and their keys
5. Create agent configurations:
   - Call make_agent_configs(prompts) function
6. Create multi-agent graph:
   - Log info message indicating start of graph creation
   - Call create_multi_agent_graph(agent_configs) function to get both graph and opik_tracer
   - Log info message indicating successful graph creation
7. Initialize processing variables:
   - Set jsonl_file_path to "/home/joe/python-proj/hf-ai-agents-course/src/hello_world.jsonl"
   - Initialize empty responses list
   - Log info message indicating start of JSONL file processing
8. Process each item in the JSONL file:
   - Iterate through items returned by read_jsonl_file(jsonl_file_path)
   - Check if item["Level"] equals 1
   - If Level is 1:
     - Log info message with the question being processed
     - Generate unique thread_id using uuid.uuid4()
     - Create config object with opik_tracer callbacks, thread_id, and recursion_limit
     - Check if item["file_name"] is not empty
     - If file_name is not empty, set file_path to "/home/joe/datum/gaia_lvl1/{item['file_name']}"
     - If file_name is empty, set file_path to empty string
     - Invoke graph with question and file_path using graph.invoke() with config
     - Create response dictionary with task_id, model_answer, reasoning_trace, and thread_id
     - Append response to responses list
     - Log info message indicating question completion
     - Flush opik_tracer traces after each question
     - Sleep for 5 seconds using time.sleep(5)
9. Write results to output file:
   - Log info message indicating start of response writing
   - Call write_jsonl_file(responses, "/home/joe/python-proj/hf-ai-agents-course/src/gaia_lvl1_responses.jsonl")
10. Log info message indicating successful application completion
11. If any Exception occurs:
    - Try to flush opik_tracer traces
    - Log error message with exception details
    - Print error message to console
    - Exit application with exit code 1 using sys.exit(1)

**Pseudocode**:
```
// REQUIRED IMPORTS:
// import time
// import sys
// import logging

FUNCTION main() -> None
    /*
    Purpose: Main function to run the application
    
    BEHAVIOR:
    - Accepts: None - Function takes no parameters
    - Produces: None - Function does not return a value
    - Handles: Complete application lifecycle from initialization to completion
    
    DEPENDENCIES:
    - load_baseline_prompts: Loads all agent prompts from files
    - make_agent_configs: Creates agent configurations from prompts
    - create_multi_agent_graph: Builds the multi-agent system graph
    - read_jsonl_file: Reads input questions from JSONL file
    - write_jsonl_file: Writes results to output JSONL file
    
    EXTERNAL DEPENDENCIES:
    - Python time: Library for sleep operations
    - Python sys: Library for system exit operations
    - Python logging: Library for comprehensive logging
    
    IMPLEMENTATION NOTES:
    - Should initialize and orchestrate the entire multi-agent system
    - Must load baseline prompts for all agents
    - Should create agent configurations from prompts
    - Must build the multi-agent graph
    - Should process JSONL input file containing questions
    - Must invoke the graph for each question processing
    - Should collect and store responses
    - Must write results to output file
    - Should handle application lifecycle and error management
    - Must provide comprehensive logging throughout execution
    - Should manage application startup and shutdown
    */
    
    // Enter a try block to handle potential application errors
    TRY
        // Configure Opik for real-time flushing
        from opik import configure
        configure(use_local=True)
        
        // Log an info message indicating application start
        LOG_INFO("Application started")
        
        // Load baseline prompts:
        // Log info message indicating start of baseline prompt loading
        LOG_INFO("Loading baseline prompts...")
        // Call load_baseline_prompts() function
        prompts = load_baseline_prompts()
        // Log info message with number of prompts loaded and their keys
        LOG_INFO(f"Loaded {len(prompts)} prompts: {list(prompts.keys())}")
        
        // Create agent configurations:
        // Call make_agent_configs(prompts) function
        agent_configs = make_agent_configs(prompts)
        
        // Create multi-agent graph:
        // Log info message indicating start of graph creation
        LOG_INFO("Creating multi-agent graph...")
        // Call create_multi_agent_graph(agent_configs) function to get both graph and opik_tracer
        (graph, opik_tracer) = create_multi_agent_graph(agent_configs)
        // Log info message indicating successful graph creation
        LOG_INFO("Graph created successfully!")
        
        // Initialize processing variables:
        // Set jsonl_file_path to "/home/joe/python-proj/hf-ai-agents-course/src/hello_world.jsonl"
        jsonl_file_path = "/home/joe/python-proj/hf-ai-agents-course/src/hello_world.jsonl"
        // Initialize empty responses list
        responses = []
        // Log info message indicating start of JSONL file processing
        LOG_INFO("Starting to process JSONL file...")
        
        // Process each item in the JSONL file:
        // Iterate through items returned by read_jsonl_file(jsonl_file_path)
        FOR item IN read_jsonl_file(jsonl_file_path) DO
            // Check if item["Level"] equals 1
            IF item["Level"] = 1 THEN
                // If Level is 1:
                // Log info message with the question being processed
                LOG_INFO(f"Processing question: {item['Question']}")
                
                // Generate unique thread_id using uuid.uuid4()
                thread_id = str(uuid.uuid4())
                
                // Create config object with opik_tracer callbacks, thread_id, and recursion_limit
                config = {
                    "callbacks": [opik_tracer],
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": 100
                }
                
                // Check if item["file_name"] is not empty
                IF item["file_name"] != "" THEN
                    // If file_name is not empty, set file_path to "/home/joe/datum/gaia_lvl1/{item['file_name']}"
                    file_path = f"/home/joe/datum/gaia_lvl1/{item['file_name']}"
                ELSE
                    // If file_name is empty, set file_path to empty string
                    file_path = ""
                END IF
                
                result = graph.invoke({"question": item["Question"], "file": file_path}, config=config)
                
                // Create response dictionary with task_id, model_answer, reasoning_trace, and thread_id
                response = {
                    "task_id": item["task_id"],
                    "model_answer": result["final_answer"],
                    "reasoning_trace": result["final_reasoning_trace"],
                    "thread_id": thread_id
                }
                
                // Append response to responses list
                responses.append(response)
                
                // Log info message indicating question completion
                LOG_INFO(f"Completed question: {item['Question']}")
                
                // Flush opik_tracer traces after each question
                opik_tracer.flush()
                
                // Sleep for 5 seconds using time.sleep(5)
                time.sleep(5)
            END IF
        END FOR
        
        // Write results to output file:
        // Log info message indicating start of response writing
        LOG_INFO("Writing responses to output file...")
        // Call write_jsonl_file(responses, "/home/joe/python-proj/hf-ai-agents-course/src/gaia_lvl1_responses.jsonl")
        write_jsonl_file(responses, "/home/joe/python-proj/hf-ai-agents-course/src/gaia_lvl1_responses.jsonl")
        
        // Log info message indicating successful application completion
        LOG_INFO("Application finished successfully")
        
    CATCH Exception AS e
        // If any Exception occurs:
        // Try to flush opik_tracer traces
        TRY
            opik_tracer.flush()
        FINALLY
            // Log error message with exception details
            LOG_ERROR(f"Application failed: {str(e)}")
            // Print error message to console
            PRINT(f"Application failed: {str(e)}")
            // Exit application with exit code 1 using sys.exit(1)
            sys.exit(1)
        END TRY
    
END FUNCTION
```

**Workflow Control**: Controls the entire application workflow from initialization to completion.

**State Management**: Does not access any graph states directly, but orchestrates state management through graph invocation.

**Communication Patterns**:
- **Component Orchestration**: Coordinates all major system components
- **File Processing**: Manages input and output file operations
- **Graph Invocation**: Communicates with multi-agent graph for question processing

**External Dependencies**:
- **Python time**: Library for sleep operations
- **Python sys**: Library for system exit operations
- **Python logging**: Library for comprehensive logging
- **Python uuid**: Library for generating unique identifiers
- **Opik**: Library for observability and tracing

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
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

**Error Handling**:
- Catches any Exception and attempts to flush opik_tracer traces
- Logs error with details and prints error message to console
- Exits application with exit code 1 using sys.exit(1)
- Ensures opik_tracer flushing even in error conditions
- All errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

---

## 4. System Workflow

### Main Execution Flow

[To be populated with application startup, question processing loop, response collection and output]

### Agent Workflow

[To be populated with orchestrator decision logic, agent communication patterns, state transitions]

---

## 5. External Dependencies

### LLM Services

[To be populated with OpenAI API integration and model configurations]

### Research Tools

[To be populated with web search, Wikipedia, file processing, YouTube, MCP browser tools]

### Expert Tools

[To be populated with Python REPL, unit conversion, calculator functions]

---

## 6. Configuration Management

### Environment Variables

[To be populated with API keys, endpoints, model settings, file paths]

### Prompt Management

[To be populated with prompt file organization, agent-specific prompts, prompt loading and injection]

---

## 7. Logging and Observability

### Logging Configuration

[To be populated with entry point logging setup, component-level logging, log file management]

### Error Tracking

[To be populated with error logging patterns, exception handling]

---

## 8. Error Handling

### Global Error Strategy

[To be populated with exception propagation, graceful degradation, retry mechanisms]

### Component Error Handling

[To be populated with input validation, external service failures, file operation errors]

---

## 9. File Operations

### Input Processing

[To be populated with JSONL file reading, question filtering, file path resolution]

### Output Generation

[To be populated with response collection, JSONL file writing, result formatting]

---
