# Multi-Agent System Design Document

## Table of Contents

1. [Summary](#1-summary)
2. [Data Structures](#2-data-structures)
   - [Multi-Agent System Data Structures](#multi-agent-system-data-structures)
   - [Entry Point Data Structures](#entry-point-data-structures)
3. [Component Specifications](#3-component-specifications)
   - [Infrastructure and Utility Components](#infrastructure-and-utility-components)
   - [Researcher Subgraph Components](#researcher-subgraph-components)
   - [Expert Subgraph Components](#expert-subgraph-components)
   - [Main Graph Components](#main-graph-components)
   - [Entry Point Components](#entry-point-components)
4. [System Workflow](#4-system-workflow)
   - [Main Execution Flow](#main-execution-flow)
   - [Agent Workflow](#agent-workflow)
5. [External Dependencies](#5-external-dependencies)
   - [LLM Services](#llm-services)
   - [Research Tools](#research-tools)
   - [Expert Tools](#expert-tools)
6. [Configuration Management](#6-configuration-management)
   - [Environment Variables](#environment-variables)
   - [Prompt Management](#prompt-management)
7. [Logging and Observability](#7-logging-and-observability)
   - [Logging Configuration](#logging-configuration)
   - [Error Tracking](#error-tracking)
8. [Error Handling](#8-error-handling)
   - [Global Error Strategy](#global-error-strategy)
   - [Component Error Handling](#component-error-handling)
9. [File Operations](#9-file-operations)
   - [Input Processing](#input-processing)
   - [Output Generation](#output-generation)

---

## 1. Summary

[To be populated with system overview and key components]

---

## 2. Data Structures

### Multi-Agent System Data Structures

#### Graph State

**Purpose**: Central state container for workflow orchestration and agent coordination

**Usage**: Used by the main graph to manage workflow state, coordinate between agents, and track progress through the question-answering process

**Validation**: Validated via LangGraph (Pydantic + typing)

**Definition**:
```
DATA_STRUCTURE GraphState
    Fields:
    // Input related fields
    question: string // User's question to be answered
    file: string = none // Optional field, contains the path to the file associated with the question if specified

    // Agent-to-Agent Communication
    agent_messages: list[AgentMessage] = []  // Inter-agent communication messages

    // Planner fields
    research_steps: list[string] = []  // Planned research steps from planner
    expert_steps: list[string] = []  // Planned expert steps from planner

    // Researcher fields
    current_research_index: integer = -1  // Current research step identifier
    researcher_states: dict[integer, ResearcherState] = {}  // Research step states
    research_results: list[any] = []  // Results from research execution

    // Expert Fields
    expert_state: ExpertState = none  // Expert subgraph state
    expert_answer: any = ""  // Expert's final answer
    expert_reasoning: string = ""  // Expert's reasoning process

    // Critic fields
    critic_planner_decision: string = ""  // Critic decision for planner agent
    critic_planner_feedback: string = ""  // Critic feedback for planner agent
    critic_researcher_decision: string = ""  // Critic decision for researcher agent
    critic_researcher_feedback: string = ""  // Critic feedback for researcher agent
    critic_expert_decision: string = ""  // Critic decision for expert agent
    critic_expert_feedback: string = ""  // Critic feedback for expert agent

    // Finalizer fields
    final_answer: string = "" // The Finalizer's final answer
    final_reasoning_trace: string = "" // The Finalizer's reasoning trace

    // Workflow Control
    current_step: Literal["input", "planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer", ""] = "input"  // Current workflow step
    next_step: Literal["planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer", ""] = "planner"  // Next workflow step
    
    // Retry Management
    planner_retry_count: integer = 0  // Current retry counter for planner agent
    researcher_retry_count: integer = 0  // Current retry counter for researcher agent
    expert_retry_count: integer = 0  // Current retry counter for expert agent
    planner_retry_limit: integer  // Retry limit for planner agent
    researcher_retry_limit: integer  // Retry limit for researcher agent
    expert_retry_limit: integer  // Retry limit for expert agent
    retry_failed: boolean = false  // Flag indicating if retry limit was exceeded
END DATA_STRUCTURE
```

#### Researcher Subgraph State

**Purpose**: State management for research agent workflows

**Usage**: Used by researcher subgraph to execute graph runs

**Validation**: Validated via LangGraph (Pydantic + typing)

**Definition**:
```
DATA_STRUCTURE ResearcherState
    Fields:
    messages: list[BaseMessage] // LangChain BaseMessage objects for conversation history
        // Implementation type: messages: Annotated[list[BaseMessage], operator.add]
    step_index: integer // Research step identifier
    result: any = none  // Results from research execution
END DATA_STRUCTURE
```

#### Expert Subgraph State

**Purpose**: State management for expert agent workflows

**Usage**: Used by expert subgraph execute graph runs

**Validation**: Validated via LangGraph (Pydantic + typing)

**Definition**:
```
DATA_STRUCTURE ExpertState
    Fields:
    messages: list[BaseMessage] // LangChain BaseMessage objects for conversation history
        // Implementation type: messages: Annotated[list[BaseMessage], operator.add]
    question: string // The question from the main graph's GraphState
    research_steps: list[string] // The researcher steps
    research_results: list[any] // The research results corresponding to the research step
    expert_answer: any = ""  // Expert's calculated answer
    expert_reasoning: string = ""  // Expert's reasoning process
END DATA_STRUCTURE
```

#### Agent Message

**Purpose**: JSON schema for message Inter-agent communication protocol

**Usage**: Used by agents to communicate with the orchestrator, supporting instruction, feedback, and response message types

**Validation**: Validated by separate agent message validation component

**Definition**:
```
DATA_STRUCTURE AgentMessage
    Fields:
    timestamp: string // Message timestamp
    sender: string  // Source agent identifier ("critic", "expert", "orchestrator")
    receiver: string // Target agent identifier ("expert", "orchestrator", "all")
    type: string [instruction, feedback, question] // Message type
    content: string // Natural language message
    step_id: Optional[integer] = null  // Optional research step identifier
END DATA_STRUCTURE
```

**Implementation Notes**:
- **Python**: Implement as `TypedDict` with `Optional[int]` for step_id
- **Type Constraints**: sender and receiver must be valid agent names ("critic", "expert", "orchestrator", "all")
- **Optional Fields**: step_id is optional and can be None/null
- **Validation**: All fields except step_id are required

#### Agent LLM Conversations

**Purpose**: Conversation flow pattern for agent-LLM interactions

**Usage**: Used by all agents to maintain conversation history and interact with LLMs through LangChain

**Validation**: Validated via LangGraph (Pydantic + typing)

**Definition**:
```
DATA_STRUCTURE AgentLLMConversation
    Pattern:
    conversation: list = []  // LangChain BaseMessage objects in specific order
    // Conversation Flow Pattern:
    // 1. The agent's system prompt (always first): SystemMessage
    // 2. Orchestrator's message for initial task instruction: HumanMessage
    // 2. Agent's response: AIMessage
    // 4. [Optional] Orchestrator's feedback: HumanMessage
    // 5. [Optional] Agent's improved response: AIMessage
    // Pattern repeats: HumanMessage (orchestrator) -> AIMessage (agent) for feedback loops
END DATA_STRUCTURE
```

### Entry Point Data Structures

#### Agent Configuration

**Purpose**: Agent configuration and parameter management. Composes the Graph Configuration.
It is used to configure the LLM provider, LLM model, output schema, agent system prompt, and agent retry limits.

**Usage**: Used by the entry point to store and manage agent configuration.
It is supplied in part to the graph factory function.

**Validation**: Basic validation functions for configuration loading and environment variable validation

**Definition**:
```
DATA_STRUCTURE AgentConfig
    Fields:
    name: string  // Agent name identifier
    provider: string  // The LLM Provider, like openai or anthropic
    model: string  // LLM model
    temperature: float  // LLM temperature setting
    output_schema: dict  // Agent output schema
    system_prompt: string | dict  // Agent system prompt or prompts (multiple prompts for critic only)
    retry_limit: integer = null  // Agent retry limit (null for critic and finalizer)
END DATA_STRUCTURE
```

#### Planner Output Schema

**Purpose**: Structured output schema for planner agent LLM responses

**Usage**: Used by planner agent LLM to provide structured results including research and expert steps

**Validation**: LLM output structure will be validated against this schema by a separate LLM output validation component

**Definition**:
```
DATA_STRUCTURE PlannerOutputSchema
    Type: dict / JSON object
    Structure:
        {
            "research_steps": list[string],  // Planned research steps
            "expert_steps": list[string]     // Planned expert steps
        }
END DATA_STRUCTURE
```

#### Researcher Output Schema

**Purpose**: Structured output schema for researcher agent LLM responses

**Usage**: Used by researcher agent LLMs to provide structured research results

**Validation**: LLM output structure will be validated against this schema by a separate LLM output validation component

**Definition**:
```
DATA_STRUCTURE ResearcherOutputSchema
    Type: dict / JSON object
    Structure:
        {
            "results": string  // The research results
        }
END DATA_STRUCTURE
```

#### Expert Output Schema

**Purpose**: Structured output schema for expert agent LLM responses

**Usage**: Used by expert agent LLMs to provide structured expert answer and expert reasoning

**Validation**: LLM output structure will be validated against this schema by a separate LLM output validation component

**Definition**:
```
DATA_STRUCTURE ExpertOutputSchema
    Type: dict / JSON object
    Structure:
        {
            "expert_answer": string,        // The expert's answer
            "reasoning_trace": string       // The expert's reasoning trace used to synthesize the answer
        }
END DATA_STRUCTURE
```

#### Critic Output Schema

**Purpose**: Structured output schema for critic agent LLM responses

**Usage**: Used by critic agent LLMs to provide structured evaluation results including decisions and feedback

**Validation**: LLM output structure will be validated against this schema by a separate LLM output validation component

**Definition**:
```
DATA_STRUCTURE CriticOutputSchema
    Type: dict / JSON object
    Structure:
        {
            "decision": string,      // Critic's decision: "approve" or "reject"
            "feedback": string,      // Detailed feedback and suggestions
        }
END DATA_STRUCTURE
```

#### Finalizer Output Schema

**Purpose**: Structured output schema for finalizer agent LLM responses

**Usage**: Used by finalizer agent LLM to provide structured final answers with sources and confidence levels

**Validation**: LLM output structure will be validated against this schema by a separate LLM output validation component

**Definition**:
```
DATA_STRUCTURE FinalizerOutputSchema
    Type: dict / JSON object
    Structure:
        {
            "final_answer": string,         // Final compiled answer
            "final_reasoning_trace": string // Final answer reasoning trace
        }
END DATA_STRUCTURE
```

---

## 3. Component Specifications

### Infrastructure and Utility Components

#### MCP Tool Synchronous Wrapper Factory

**Component name**: create_sync_wrapper_for_mcp_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create a synchronous wrapper for an asynchronous MCP tool
- **Responsibilities**: 
  - Wraps asynchronous MCP tools to make them synchronous
  - Handles event loop management for async-to-sync conversion
  - Preserves tool metadata and properties
  - Enables integration of async MCP tools in synchronous contexts

**Component interface**:
- **Inputs**:
  - async_tool: Any // The asynchronous MCP tool to wrap
- **Outputs**:
  - Callable // The synchronous wrapper function
- **Validations**:
  - Handled by Python function creation and metadata copying

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Define inner sync_wrapper function that takes arbitrary arguments
2. Import asyncio module for event loop management
3. Try to get the currently running event loop
4. If event loop is running, use ThreadPoolExecutor to run async tool in new thread
5. If no event loop is running, create new event loop and run async tool
6. Copy tool metadata (name, doc, args_schema, return_direct) to wrapper
7. Return the synchronous wrapper function

**Pseudocode**:
```
FUNCTION create_sync_wrapper_for_mcp_tool(async_tool)
    /*
    Purpose: Create a synchronous wrapper for an asynchronous MCP tool
    
    BEHAVIOR:
    - Accepts: async_tool (Any) - The asynchronous MCP tool to wrap
    - Produces: Callable - The synchronous wrapper function
    - Handles: Async-to-sync conversion with proper event loop management
    
    DEPENDENCIES:
    - Python asyncio: Library for asynchronous programming
    - Python concurrent.futures: Library for thread pool execution
    
    IMPLEMENTATION NOTES:
    - Should handle both running and non-running event loop scenarios
    - Must preserve all tool metadata and properties
    - Should use thread pool executor for running event loop case
    - Should create new event loop for non-running case
    */
    
    // Define inner sync_wrapper function that takes arbitrary arguments
    FUNCTION sync_wrapper(*args, **kwargs)
        // Import asyncio module for event loop management
        IMPORT asyncio
        TRY
            // Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            // If we are, we need to run in a new thread to avoid blocking
            IMPORT concurrent.futures
            WITH concurrent.futures.ThreadPoolExecutor() AS executor DO
                future = executor.submit(asyncio.run, async_tool.arun(*args, **kwargs))
                RETURN future.result()
            END WITH
        CATCH RuntimeError
            // No event loop running, we can create one
            RETURN asyncio.run(async_tool.arun(*args, **kwargs))
        END TRY
    END FUNCTION
    
    // Copy the tool's metadata to the wrapper
    sync_wrapper.__name__ = async_tool.name
    sync_wrapper.__doc__ = async_tool.description
    sync_wrapper.args_schema = async_tool.args_schema
    sync_wrapper.return_direct = async_tool.return_direct
    
    // Return the synchronous wrapper function
    RETURN sync_wrapper
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it creates wrapper functions

**External Dependencies**:
- **Python asyncio**: Library for asynchronous programming
- **Python concurrent.futures**: Library for thread pool execution

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- Handles RuntimeError when no event loop is running
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### JSON Response Enforcement

**Component name**: enforce_json_response

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Enforce that the LLM response is either a dictionary or a JSON string. If it is a string, try to parse it as JSON.
- **Responsibilities**: 
  - Validates response type and structure
  - Converts string responses to JSON dictionaries
  - Provides error handling for invalid responses
  - Ensures consistent dictionary output format

**Component interface**:
- **Inputs**:
  - response: Any // The response from the LLM
  - component: string // The component that generated the response
- **Outputs**:
  - dict // The response as a dictionary
- **Validations**:
  - Handled by Python type checking and JSON parsing validation

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Check if the response is already a dictionary using isinstance(response, dict)
2. If the response is a dictionary, return it directly
3. If the response is not a dictionary, attempt to parse it as JSON using json.loads(response)
4. If JSON parsing succeeds, return the parsed data as a dictionary
5. If JSON parsing fails (raises an exception), raise a ValueError with component context and response details

**Pseudocode**:
```
FUNCTION enforce_json_response(response: Any, component: string) -> dict
    /*
    Purpose: Enforce that the LLM response is either a dictionary or a JSON string
    
    BEHAVIOR:
    - Accepts: response (Any) - The response from the LLM
    - Accepts: component (string) - The component that generated the response
    - Produces: dict - The response as a dictionary
    - Handles: Response type validation and JSON parsing
    
    DEPENDENCIES:
    - Python json module: For JSON parsing and validation
    
    IMPLEMENTATION NOTES:
    - Should handle errors gracefully with descriptive error messages
    - Must return consistent dictionary format
    */
    
    // Check if response is already a dictionary
    IF isinstance(response, dict) THEN
        RETURN response
    END IF
    
    // Attempt to parse response as JSON
    TRY
        parsed_response ← json.loads(response)
        RETURN parsed_response
    CATCH ANY_ERROR AS error
        // Create error message with component context
        error_msg ← f"Component {component} returned invalid JSON: {response}"
        
        // Raise ValueError with context
        RAISE ValueError(error_msg)
    END TRY
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles data validation

**External Dependencies**:
- **Python json module**: Library for JSON parsing and validation

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- Raises ValueError if the response is not a dictionary or a valid JSON string
- Error message includes the component name and the invalid response for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Output Schema Validation

**Component name**: validate_output_matches_json_schema

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Check if the LLM response has all the expected fields. Assumes the response is a dictionary when evaluating
- **Responsibilities**: 
  - Validates that all required output schema keys are present in the response
  - Provides boolean validation result for response completeness
  - Supports schema validation for LLM responses
  - Enables response structure validation

**Component interface**:
- **Inputs**:
  - response: Any // The response from the LLM
  - output_schema_keys: list[string] // The expected fields that should be present in the response
- **Outputs**:
  - bool // True if the response has all the expected fields, False otherwise
- **Validations**:
  - Handled by Python all() function and dictionary key checking

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Use Python's all() function to check if every key in output_schema_keys exists in the response dictionary
2. Return the result directly (True if all keys are present, False if any key is missing)

**Pseudocode**:
```
FUNCTION validate_output_matches_json_schema(response: Any, output_schema_keys: list[str]) -> bool
    /*
    Purpose: Check if the LLM response has all the expected fields
    
    BEHAVIOR:
    - Accepts: response (Any) - The response from the LLM
    - Accepts: output_schema_keys (list[string]) - The expected fields that should be present
    - Produces: bool - True if all expected fields are present, False otherwise
    - Handles: Schema validation for LLM responses
    
    IMPLEMENTATION NOTES:
    - Assumes response is a dictionary when evaluating
    - Should use Python's all() function for efficient validation
    - Must handle missing keys gracefully
    */
    
    // Use Python's all() function to check if every key in output_schema_keys exists in the response dictionary
    RETURN all(key in response for key in output_schema_keys)
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles data validation

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### LLM Response Validation

**Component name**: validate_llm_response

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Validate LLM response has expected structure and fields
- **Responsibilities**: 
  - Enforces JSON response format using enforce_json_response function
  - Validates response schema using validate_output_matches_json_schema function
  - Provides comprehensive LLM response validation
  - Returns validated response as dictionary or raises appropriate errors

**Component interface**:
- **Inputs**:
  - response: Any // The response from the LLM
  - expected_fields: List[string] // The expected fields that should be present in the response
  - component: string // The component that generated the response
- **Outputs**:
  - dict // The response as a validated dictionary
- **Validations**:
  - Handled by enforce_json_response and validate_output_matches_json_schema functions

**Direct Dependencies with Other Components**:
- enforce_json_response function
- validate_output_matches_json_schema function

**Internal Logic**:
1. Call enforce_json_response function to ensure response is a dictionary and assign to response variable
2. Check if the response matches the expected schema using validate_output_matches_json_schema function
3. If schema validation fails, raise KeyError with component context and field details
4. Return the validated response dictionary

**Pseudocode**:
```
FUNCTION validate_llm_response(response: Any, expected_fields: List[string], component: string) -> dict
    /*
    Purpose: Validate LLM response has expected structure and fields
    
    BEHAVIOR:
    - Accepts: response (Any) - The response from the LLM
    - Accepts: expected_fields (List[string]) - The expected fields that should be present
    - Accepts: component (string) - The component that generated the response
    - Produces: dict - The response as a validated dictionary
    - Handles: Comprehensive LLM response validation
    
    DEPENDENCIES:
    - enforce_json_response function: For JSON format enforcement
    - validate_output_matches_json_schema function: For schema validation
    
    IMPLEMENTATION NOTES:
    - Should provide comprehensive validation with clear error messages
    - Must handle both JSON format and schema validation
    - Should include component context in error messages
    */
    
    // Enforce JSON response format and assign to response variable
    response = enforce_json_response(response, component)
    
    // Check if the response matches the expected schema using validate_output_matches_json_schema function
    IF NOT validate_output_matches_json_schema(response, expected_fields) THEN
        // Raise KeyError with component context and field details
        RAISE KeyError(f"{component}: Response does not contain all expected fields. Expected fields: {expected_fields}, Response: {response}")
    END IF
    
    // Return the validated response dictionary
    RETURN response
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles data validation

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- Raises KeyError if the response does not contain all the expected fields
- Error message includes the component name, expected fields, and actual response for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Agent Message Composer

**Component name**: compose_agent_message

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Composes an agent message using the AgentMessage protocol and data structure
- **Responsibilities**: Handles agent message composition to be compliant with the AgentMessage protocol

**Component interface**:
- **Inputs**:
  - sender: string // The entity sending the message, either an agent or the orchestrator
  - receiver: string // The entity receiving the message, either an agent or the orchestrator
  - message_type: string // The type of message that is being sent: instruction, response, feedback
  - content: string // The message content / message body
  - step_id: integer = none // Optional. The specific research step id associated with message being composed
- **Outputs**:
  - agent_message: AgentMessage // The composed message as an AgentMessage
- **Validations**:
  - Handled by Pydantic + Typing in LangGraph

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Get the current timestamp
2. Take the inputs and current timestamp, and use them to compose an AgentMessage type variable that follows the AgentMessage data structure. Variable must be explicitly typed as AgentMessage.
3. Return the composed message

**Pseudocode**:
```
FUNCTION compose_agent_message(sender: string, receiver: string, message_type: string, content: string, step_id: integer = none) -> AgentMessage
    /*
    Purpose: Composes an agent message using the AgentMessage protocol and data structure
    
    BEHAVIOR:
    - Accepts: sender (string) - The entity sending the message
    - Accepts: receiver (string) - The entity receiving the message
    - Accepts: message_type (string) - The type of message being sent
    - Accepts: content (string) - The message content/body
    - Accepts: step_id (integer) - Optional research step id
    - Produces: AgentMessage - The composed message as an AgentMessage
    - Handles: Agent message composition compliant with protocol
    
    IMPLEMENTATION NOTES:
    - Should create properly formatted AgentMessage with timestamp
    - Must explicitly type the return value as AgentMessage
    - Should handle optional step_id parameter
    */
    
    // Get the current timestamp
    current_timestamp = get_current_timestamp()
    
    // Compose AgentMessage with all inputs and timestamp
    agent_message: AgentMessage = {
        "timestamp": current_timestamp,
        "sender": sender,
        "receiver": receiver,
        "type": message_type,
        "content": content,
        "step_id": step_id
    }
    
    // Log successful message composition
    LOG_INFO("Agent message composed successfully")
    
    // Return the composed message
    RETURN agent_message
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles communication

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: 
- Append logging (INFO) at the end of the logical steps.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Agent Message Sending

**Component name**: send_message

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Adds a message to the agent_messages field in the main graph state
- **Responsibilities**: Message storage in main graph state

**Component interface**:
- **Inputs**:
  - state: GraphState // The main graph state
  - message: AgentMessage // The agent message
- **Outputs**:
  - state: GraphState // The main graph state
- **Validations**:
  - Handled by Pydantic + Typing in LangGraph

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Update the state (GraphState) and append the message to the agent_messages field
2. Return the state

**Pseudocode**:
```
FUNCTION send_message(state: GraphState, message: AgentMessage) -> GraphState
    /*
    Purpose: Adds a message to the agent_messages field in the main graph state
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The main graph state
    - Accepts: message (AgentMessage) - The agent message to store
    - Produces: GraphState - The updated state with message added
    - Handles: Message storage in main graph state
    
    IMPLEMENTATION NOTES:
    - Should append message to existing agent_messages list
    - Must preserve all other state fields unchanged
    - Should handle list operations safely
    */
    
    // Append the message to the agent_messages field in state
    state.agent_messages ← state.agent_messages + [message]
    
    // Log successful message storage
    LOG_INFO("Agent message stored successfully")
    
    // Return the updated state
    RETURN state
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses the agent_messages field in the state input variable (GraphState) and appends the input message to the agent_messages field (list).

**Communication Patterns**: None. This component does not communicate, rather it handles communication

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: 
- Append logging (INFO) at the end of the logical steps.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Agent Conversation Retrieval

**Component name**: get_agent_conversation

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Get the conversation between the orchestrator and the agent
- **Responsibilities**: 
  - Retrieves messages between orchestrator and specific agent
  - Filters messages by message types when specified
  - Filters messages by step ID when specified
  - Provides filtered conversation history for agent communication

**Component interface**:
- **Inputs**:
  - state: GraphState // The current state of the graph
  - agent_name: string // The name of the agent
  - types: Optional[List[string]] = none // Optional. The types of messages to get
  - step_id: Optional[integer] = none // Optional. The step id to get messages for
- **Outputs**:
  - List[AgentMessage] // The list of AgentMessages between the agent and orchestrator
- **Validations**:
  - Handled by Pydantic + Typing in LangGraph

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Create initial inbox by filtering all agent_messages from state based on sender/receiver logic:
   - Include messages where sender = agent_name and receiver = "orchestrator"
   - Include messages where sender = "orchestrator" and receiver = agent_name
2. If step_id is not None, filter inbox to only include messages with matching step_id
3. If types is not None, filter inbox to only include messages where message type is in the types list
4. Return the filtered inbox list

**Pseudocode**:
```
FUNCTION get_agent_conversation(state: GraphState, agent_name: string, types: Optional[List[string]] = none, step_id: Optional[integer] = none) -> List[AgentMessage]
    /*
    Purpose: Get the conversation between the orchestrator and the agent
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The current state of the graph
    - Accepts: agent_name (string) - The name of the agent
    - Accepts: types (Optional[List[string]]) - Optional message types to filter by
    - Accepts: step_id (Optional[integer]) - Optional step id to filter by
    - Produces: List[AgentMessage] - The filtered conversation messages
    - Handles: Message filtering and conversation history retrieval
    
    IMPLEMENTATION NOTES:
    - Should filter messages based on sender/receiver logic
    - Must handle optional filtering parameters gracefully
    - Should return empty list if no messages match criteria
    */
    
    // Create initial inbox by filtering agent_messages based on sender/receiver logic
    inbox ← []
    FOR EACH message IN state.agent_messages DO
        // Include messages where sender = agent_name and receiver = "orchestrator"
        IF (message.sender = agent_name AND message.receiver = "orchestrator") OR
           (message.sender = "orchestrator" AND message.receiver = agent_name) THEN
            inbox ← inbox + [message]
        END IF
    END FOR
    
    // Filter by step_id if provided
    IF step_id IS NOT none THEN
        filtered_inbox ← []
        FOR EACH message IN inbox DO
            IF message.step_id = step_id THEN
                filtered_inbox ← filtered_inbox + [message]
            END IF
        END FOR
        inbox ← filtered_inbox
    END IF
    
    // Filter by types if provided
    IF types IS NOT none THEN
        filtered_inbox ← []
        FOR EACH message IN inbox DO
            IF message.type IN types THEN
                filtered_inbox ← filtered_inbox + [message]
            END IF
        END FOR
        inbox ← filtered_inbox
    END IF
    
    // Return the filtered inbox list
    RETURN inbox
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses the agent_messages field in the state input variable (GraphState) to retrieve specified messages. Does not alter the state in any way.

**Communication Patterns**: None. This component does not communicate, rather it handles communication retrieval

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Agent Message to LangChain Conversion

**Component name**: convert_agent_messages_to_langchain

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Convert a list of AgentMessages to a list of LangChain BaseMessages
- **Responsibilities**: 
  - Converts AgentMessage protocol to LangChain message format
  - Maps sender types to appropriate LangChain message types
  - Provides protocol translation for LLM integration
  - Enables communication between agent system and LangChain components

**Component interface**:
- **Inputs**:
  - messages: List[AgentMessage] // The list of AgentMessages to convert
- **Outputs**:
  - List[BaseMessage] // The list of LangChain BaseMessages
- **Validations**:
  - Handled by Pydantic + Typing in LangGraph

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Initialize an empty list called converted_messages
2. Iterate through each message in the input messages list using variable name 'm'
3. For each message, check if the sender is "orchestrator" using dictionary access
4. If sender is "orchestrator", create a HumanMessage with the message content using dictionary access
5. If sender is not "orchestrator", create an AIMessage with the message content using dictionary access
6. Append the created message to the converted_messages list using append() method
7. Return the converted_messages list

**Pseudocode**:
```
FUNCTION convert_agent_messages_to_langchain(messages: List[AgentMessage]) -> List[BaseMessage]
    /*
    Purpose: Convert a list of AgentMessages to a list of LangChain BaseMessages
    
    BEHAVIOR:
    - Accepts: messages (List[AgentMessage]) - The list of AgentMessages to convert
    - Produces: List[BaseMessage] - The list of LangChain BaseMessages
    - Handles: Protocol translation for LLM integration
    
    DEPENDENCIES:
    - LangChain BaseMessage: Library for LangChain message types
    - HumanMessage: LangChain message type for human/orchestrator messages
    - AIMessage: LangChain message type for agent messages
    
    IMPLEMENTATION NOTES:
    - Should map orchestrator messages to HumanMessage
    - Should map agent messages to AIMessage
    - Must preserve message content during conversion
    */
    
    // Initialize empty list for converted messages
    converted_messages = []
    
    // Iterate through each message in the input messages list using variable name 'm'
    FOR m IN messages DO
        // Check if the sender is "orchestrator" using dictionary access
        IF m["sender"] = "orchestrator" THEN
            // Create HumanMessage with the message content using dictionary access
            message = HumanMessage(content=m["content"])
        ELSE
            // Create AIMessage with the message content using dictionary access
            message = AIMessage(content=m["content"])
        END IF
        
        // Append the created message to the converted_messages list using append() method
        converted_messages.append(message)
    END FOR
    
    // Return the converted_messages list
    RETURN converted_messages
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles protocol conversion

**External Dependencies**:
- **LangChain BaseMessage**: Library for LangChain message types
- **HumanMessage**: LangChain message type for human/orchestrator messages
- **AIMessage**: LangChain message type for agent messages

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

### Researcher Subgraph Components

#### YouTube Video Transcribing Tool

**Component name**: youtube_transcript_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Extracts transcript from a YouTube video URL. Use this when you need to get the content/transcript from a specific YouTube video.
- **Responsibilities**: 
  - Loads YouTube video transcript using LangChain YoutubeLoader
  - Extracts transcript content and video metadata
  - Handles video information processing and formatting
  - Provides formatted transcript with video metadata

**Component interface**:
- **Inputs**:
  - url: string // The YouTube video URL to extract transcript from
- **Outputs**:
  - transcript: string // The transcript text from the video with metadata
- **Validations**:
  - Handled by LangChain YoutubeLoader validation
  - URL format validation handled by YoutubeLoader

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of processing with the URL
2. Create YoutubeLoader instance using from_youtube_url with the provided URL and add_video_info=True
3. Load documents using the loader
4. Check if documents list is empty
5. If no documents found, log info and return "No transcript found for this YouTube video." message
6. Extract transcript content from the first document's page_content
7. Extract metadata from the first document
8. Format video information string with title, author, and duration from metadata using .get() with defaults
9. Log successful completion
10. Return concatenated video info and transcript content

**Pseudocode**:
```
FUNCTION youtube_transcript_tool(url: string) -> string
    /*
    Purpose: Extracts transcript from a YouTube video URL
    
    BEHAVIOR:
    - Accepts: url (string) - The YouTube video URL to extract transcript from
    - Produces: string - The transcript text from the video with metadata
    - Handles: YouTube video transcript extraction and formatting
    
    DEPENDENCIES:
    - YouTube API: Access to YouTube video data and transcripts
    - LangChain YoutubeLoader: Library for YouTube video processing
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should handle cases where no transcript is available
    - Must format video metadata with transcript content
    - Should provide comprehensive logging for debugging
    */
    
    // Log the beginning of processing with the URL
    LOG_INFO(f"YouTube transcript tool processing URL: {url}")
    
    // Create YoutubeLoader instance using from_youtube_url with the provided URL and add_video_info=True
    loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
    
    // Load documents using the loader
    documents = loader.load()
    
    // Check if documents list is empty
    IF NOT documents THEN
        // Log info and return "No transcript found for this YouTube video." message
        LOG_INFO("No transcript found for YouTube video")
        RETURN "No transcript found for this YouTube video."
    END IF
    
    // Extract transcript content from the first document's page_content
    transcript = documents[0].page_content
    
    // Extract metadata from the first document
    metadata = documents[0].metadata
    
    // Format video information string with title, author, and duration from metadata using .get() with defaults
    video_info = f"Video Title: {metadata.get('title', 'Unknown')}\n"
    video_info += f"Channel: {metadata.get('author', 'Unknown')}\n"
    video_info += f"Duration: {metadata.get('length', 'Unknown')} seconds\n\n"
    
    // Log successful completion
    LOG_INFO(f"YouTube transcript tool completed successfully")
    
    // Return concatenated video info and transcript content
    RETURN video_info + transcript
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles external API communication

**External Dependencies**:
- **YouTube API**: Access to YouTube video data and transcripts
- **LangChain YoutubeLoader**: Library for YouTube video processing
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with URL: "YouTube transcript tool processing URL: {url}"
- Append logging (INFO) if no transcript is found: "No transcript found for YouTube video"
- Append logging (INFO) at the end of successful processing: "YouTube transcript tool completed successfully"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Unstructured Excel Tool

**Component name**: unstructured_excel_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Loads an Excel file and returns the content as documents
- **Responsibilities**: 
  - Loads Excel files using LangChain UnstructuredExcelLoader
  - Extracts content from Excel files
  - Returns structured document format for processing
  - Handles Excel file parsing and content extraction

**Component interface**:
- **Inputs**:
  - file_path: string // The path to the Excel file to load
- **Outputs**:
  - documents: list[Document] // The Excel file content as a list of Document objects
- **Validations**:
  - Handled by LangChain UnstructuredExcelLoader validation
  - File path validation handled by UnstructuredExcelLoader

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of Excel file loading with the file path
2. Create UnstructuredExcelLoader instance with the provided file path
3. Load the Excel file content using the loader
4. Return the loaded documents as a list of Document objects

**Pseudocode**:
```
FUNCTION unstructured_excel_tool(file_path: string) -> list[Document]
    /*
    Purpose: Loads an Excel file and returns the content as documents
    
    BEHAVIOR:
    - Accepts: file_path (string) - The path to the Excel file to load
    - Produces: list[Document] - The Excel file content as a list of Document objects
    - Handles: Excel file parsing and content extraction
    
    DEPENDENCIES:
    - LangChain UnstructuredExcelLoader: Library for Excel file processing
    - File System: Access to Excel files on the local file system
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should handle various Excel file formats (.xlsx, .xls)
    - Must return structured Document objects for processing
    - Should provide logging for debugging file operations
    */
    
    // Log the beginning of Excel file loading with the file path
    LOG_INFO(f"Loading Excel file: {file_path}")
    
    // Create UnstructuredExcelLoader instance with the provided file path
    loader = UnstructuredExcelLoader(file_path)
    
    // Load the Excel file content using the loader
    documents = loader.load()
    
    // Return the loaded documents as a list of Document objects
    RETURN documents
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file processing

**External Dependencies**:
- **LangChain UnstructuredExcelLoader**: Library for Excel file processing
- **File System**: Access to Excel files on the local file system
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- None

**Logging**:
- Append logging (INFO) at the beginning of processing with file path: "Loading Excel file: {file_path}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Unstructured PowerPoint Tool

**Component name**: unstructured_powerpoint_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Loads a PowerPoint file and returns the content as documents
- **Responsibilities**: 
  - Loads PowerPoint files using LangChain UnstructuredPowerPointLoader
  - Extracts content from PowerPoint files
  - Returns structured document format for processing
  - Handles PowerPoint file parsing and content extraction

**Component interface**:
- **Inputs**:
  - file_path: string // The path to the PowerPoint file to load
- **Outputs**:
  - documents: list[Document] // The PowerPoint file content as a list of Document objects
- **Validations**:
  - Handled by LangChain UnstructuredPowerPointLoader validation
  - File path validation handled by UnstructuredPowerPointLoader

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of PowerPoint file loading with the file path
2. Create UnstructuredPowerPointLoader instance with the provided file path
3. Load the PowerPoint file content using the loader
4. Return the loaded documents as a list of Document objects

**Pseudocode**:
```
FUNCTION unstructured_powerpoint_tool(file_path: string) -> list[Document]
    /*
    Purpose: Loads a PowerPoint file and returns the content as documents
    
    BEHAVIOR:
    - Accepts: file_path (string) - The path to the PowerPoint file to load
    - Produces: list[Document] - The PowerPoint file content as a list of Document objects
    - Handles: PowerPoint file parsing and content extraction
    
    DEPENDENCIES:
    - LangChain UnstructuredPowerPointLoader: Library for PowerPoint file processing
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    - File System: Access to PowerPoint files on the local file system
    
    IMPLEMENTATION NOTES:
    - Should handle various PowerPoint file formats (.pptx, .ppt)
    - Must return structured Document objects for processing
    - Should provide logging for debugging file operations
    */
    
    // Log the beginning of PowerPoint file loading with the file path
    LOG_INFO(f"Loading PowerPoint file: {file_path}")
    
    // Create UnstructuredPowerPointLoader instance with the provided file path
    loader = UnstructuredPowerPointLoader(file_path)
    
    // Load the PowerPoint file content using the loader
    documents = loader.load()
    
    // Return the loaded documents as a list of Document objects
    RETURN documents
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file processing

**External Dependencies**:
- **LangChain UnstructuredPowerPointLoader**: Library for PowerPoint file processing
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool
- **File System**: Access to PowerPoint files on the local file system

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with file path: "Loading PowerPoint file: {file_path}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Unstructured PDF Tool

**Component name**: unstructured_pdf_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Loads a PDF file and returns the content as documents
- **Responsibilities**: 
  - Loads PDF files using LangChain UnstructuredPDFLoader
  - Extracts content from PDF files
  - Returns structured document format for processing
  - Handles PDF file parsing and content extraction

**Component interface**:
- **Inputs**:
  - file_path: string // The path to the PDF file to load
- **Outputs**:
  - documents: list[Document] // The PDF file content as a list of Document objects
- **Validations**:
  - Handled by LangChain UnstructuredPDFLoader validation
  - File path validation handled by UnstructuredPDFLoader

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of PDF file loading with the file path
2. Create UnstructuredPDFLoader instance with the provided file path
3. Load the PDF file content using the loader
4. Return the loaded documents as a list of Document objects

**Pseudocode**:
```
FUNCTION unstructured_pdf_tool(file_path: string) -> list[Document]
    /*
    Purpose: Loads a PDF file and returns the content as documents
    
    BEHAVIOR:
    - Accepts: file_path (string) - The path to the PDF file to load
    - Produces: list[Document] - The PDF file content as a list of Document objects
    - Handles: PDF file parsing and content extraction
    
    DEPENDENCIES:
    - LangChain UnstructuredPDFLoader: Library for PDF file processing
    - File System: Access to PDF files on the local file system
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should handle various PDF file formats and structures
    - Must return structured Document objects for processing
    - Should provide logging for debugging file operations
    */
    
    // Log the beginning of PDF file loading with the file path
    LOG_INFO(f"Loading PDF file: {file_path}")
    
    // Create UnstructuredPDFLoader instance with the provided file path
    loader = UnstructuredPDFLoader(file_path)
    
    // Load the PDF file content using the loader
    documents = loader.load()
    
    // Return the loaded documents as a list of Document objects
    RETURN documents
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file processing

**External Dependencies**:
- **LangChain UnstructuredPDFLoader**: Library for PDF file processing
- **File System**: Access to PDF files on the local file system
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with file path: "Loading PDF file: {file_path}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Text File Tool

**Component name**: text_file_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Load a text file and return the content as a string
- **Responsibilities**: 
  - Loads text files using LangChain TextLoader
  - Extracts text content from loaded documents
  - Returns file content as a string for processing
  - Provides text file reading capabilities for research operations

**Component interface**:
- **Inputs**:
  - file_path: string // The path to the text file to load
- **Outputs**:
  - string // The content of the text file as a string
- **Validations**:
  - Handled by LangChain TextLoader validation
  - File existence and accessibility validation handled by TextLoader

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of text file loading with the file path
2. Create a TextLoader instance with the provided file_path parameter
3. Call the load() method on the TextLoader instance to load the text file
4. The load() method returns a list of Document objects containing the file content
5. Check if the documents list is not empty
6. If documents exist, extract the page_content from the first (and typically only) Document in the list
7. If no documents are found, return an empty string
8. Return the extracted text content as a string

**Pseudocode**:
```
FUNCTION text_file_tool(file_path: string) -> string
    /*
    Purpose: Load a text file and return the content as a string
    
    BEHAVIOR:
    - Accepts: file_path (string) - The path to the text file to load
    - Produces: string - The content of the text file as a string
    - Handles: Text file loading and content extraction
    
    DEPENDENCIES:
    - LangChain TextLoader: Library for loading text files and creating Document objects
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should handle various text file encodings
    - Must extract content from Document objects
    - Should handle empty files gracefully
    - Should return empty string if no documents found
    */
    
    // Log the beginning of text file loading with the file path
    LOG_INFO(f"Loading text file: {file_path}")
    
    // Create a TextLoader instance with the provided file_path parameter
    loader = TextLoader(file_path)
    
    // Call the load() method on the TextLoader instance to load the text file
    documents = loader.load()
    
    // Check if the documents list is not empty
    IF documents THEN
        // If documents exist, extract the page_content from the first Document in the list
        text_content = documents[0].page_content
        // Return the extracted text content as a string
        RETURN text_content
    ELSE
        // If no documents are found, return an empty string
        RETURN ""
    END IF
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file loading operations

**External Dependencies**:
- **LangChain TextLoader**: Library for loading text files and creating Document objects
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with file path: "Loading text file: {file_path}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Wikipedia Search Tool

**Component name**: wikipedia_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Search for information on Wikipedia
- **Responsibilities**: 
  - Creates WikipediaQueryRun instance with WikipediaAPIWrapper
  - Performs Wikipedia searches using provided query
  - Returns search results as formatted strings
  - Provides Wikipedia search capabilities for research operations

**Component interface**:
- **Inputs**:
  - query: string // The search query to perform
- **Outputs**:
  - string // The search results as a string
- **Validations**:
  - Handled by WikipediaQueryRun validation
  - Query format validation handled by Wikipedia API

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of Wikipedia search with the query
2. Create WikipediaQueryRun instance with WikipediaAPIWrapper
3. Invoke the WikipediaQueryRun with the provided query
4. Return the search results

**Pseudocode**:
```
FUNCTION wikipedia_tool(query: string) -> string
    /*
    Purpose: Search for information on Wikipedia
    
    BEHAVIOR:
    - Accepts: query (string) - The search query to perform
    - Produces: string - The search results as a string
    - Handles: Wikipedia search using Wikipedia API
    
    DEPENDENCIES:
    - LangChain WikipediaQueryRun: Library for Wikipedia search operations
    - LangChain WikipediaAPIWrapper: Library for Wikipedia API wrapper
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should create WikipediaQueryRun instance with WikipediaAPIWrapper for each search
    - Must handle Wikipedia search queries effectively
    - Should return formatted search results
    - Should provide Wikipedia search capabilities for research operations
    */
    
    // Log the beginning of Wikipedia search with the query
    LOG_INFO(f"Wikipedia tool searching for: {query}")
    
    // Create WikipediaQueryRun instance with WikipediaAPIWrapper
    wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(wiki_client=None))
    
    // Invoke the WikipediaQueryRun with the provided query
    result = wikipedia_tool.invoke(query)
    
    // Return the search results
    RETURN result
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it performs Wikipedia search operations

**External Dependencies**:
- **LangChain WikipediaQueryRun**: Library for Wikipedia search operations
- **LangChain WikipediaAPIWrapper**: Library for Wikipedia API wrapper
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with query: "Wikipedia tool searching for: {query}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Tavily Search Tool

**Component name**: tavily_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Search for information on the web using Tavily search
- **Responsibilities**: 
  - Creates TavilySearch instance for web search
  - Performs web searches using provided query
  - Returns search results as formatted strings
  - Provides web search capabilities for research operations

**Component interface**:
- **Inputs**:
  - query: string // The search query to perform
- **Outputs**:
  - string // The search results as a string
- **Validations**:
  - Handled by TavilySearch validation
  - Query format validation handled by Tavily API

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of Tavily search with the query
2. Create TavilySearch instance
3. Invoke the TavilySearch with the provided query
4. Return the search results

**Pseudocode**:
```
FUNCTION tavily_tool(query: string) -> string
    /*
    Purpose: Search for information on the web using Tavily search
    
    BEHAVIOR:
    - Accepts: query (string) - The search query to perform
    - Produces: string - The search results as a string
    - Handles: Web search using Tavily API
    
    DEPENDENCIES:
    - LangChain TavilySearch: Library for web search operations
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should create TavilySearch instance for each search
    - Must handle web search queries effectively
    - Should return formatted search results
    - Should provide web search capabilities for research operations
    */
    
    // Log the beginning of Tavily search with the query
    LOG_INFO(f"Tavily tool searching for: {query}")
    
    // Create TavilySearch instance
    tavily_tool = TavilySearch()
    
    // Invoke the TavilySearch with the provided query
    result = tavily_tool.invoke(query)
    
    // Return the search results
    RETURN result
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it performs web search operations

**External Dependencies**:
- **LangChain TavilySearch**: Library for web search operations
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with query: "Tavily tool searching for: {query}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Get Browser MCP Tools

**Component name**: get_browser_mcp_tools

**Component type**: async function

**Component purpose and responsibilities**:
- **Purpose**: Get the browser MCP tools from the given URL
- **Responsibilities**: 
  - Establishes connection to MCP server using streamablehttp_client
  - Initializes MCP session with the server
  - Loads MCP tools from the session
  - Creates synchronous wrappers for async MCP tools
  - Returns list of available MCP tools for browser operations

**Component interface**:
- **Inputs**:
  - mcp_url: string // The URL of the browser MCP
- **Outputs**:
  - list // The list of MCP tools with sync wrappers
- **Validations**:
  - Handled by MCP client session validation
  - URL format validation handled by streamablehttp_client

**Direct Dependencies with Other Components**:
- create_sync_wrapper_for_mcp_tool function

**Internal Logic**:
1. Create async context manager for streamablehttp_client with the MCP URL
2. Create async context manager for ClientSession with read and write streams
3. Initialize the MCP session using await session.initialize()
4. Load MCP tools from the session using await load_mcp_tools(session)
5. Create sync wrappers for each MCP tool using create_sync_wrapper_for_mcp_tool
6. Convert sync wrappers back to LangChain Tool objects
7. Return the list of wrapped MCP tools

**Pseudocode**:
```
ASYNC FUNCTION get_browser_mcp_tools(mcp_url: string) -> list
    /*
    Purpose: Get the browser MCP tools from the given URL
    
    BEHAVIOR:
    - Accepts: mcp_url (string) - The URL of the browser MCP
    - Produces: list - The list of MCP tools with sync wrappers
    - Handles: MCP server connection and tool loading with sync wrappers
    
    DEPENDENCIES:
    - MCP Server: Model Context Protocol server for tool access
    - streamablehttp_client: HTTP client for MCP server communication
    - ClientSession: MCP client session management
    - load_mcp_tools: Function to load tools from MCP session from LangChain community
    - create_sync_wrapper_for_mcp_tool: Function to create sync wrappers
    
    IMPLEMENTATION NOTES:
    - Should handle async context managers for proper resource management
    - Must establish and maintain MCP session connection
    - Should load all available MCP tools from the session
    - Should create sync wrappers for all async tools
    - Should handle connection errors gracefully
    */
    
    // Create async context manager for streamablehttp_client with the MCP URL
    WITH streamablehttp_client(mcp_url) AS (read, write, _) DO
        // Create async context manager for ClientSession with read and write streams
        WITH ClientSession(read, write) AS session DO
            // Initialize the MCP session
            AWAIT session.initialize()
            
            // Load MCP tools from the session
            mcp_tools = await load_mcp_tools(session)
            
            // Create sync wrappers for each MCP tool
            sync_mcp_tools = []
            FOR mcp_tool IN mcp_tools DO
                sync_tool = create_sync_wrapper_for_mcp_tool(mcp_tool)
                // Convert the sync wrapper back to a LangChain Tool
                IMPORT tool FROM langchain_core.tools
                wrapped_tool = tool(sync_tool)
                sync_mcp_tools.append(wrapped_tool)
            END FOR
            
            // Return the list of wrapped MCP tools
            RETURN sync_mcp_tools
        END WITH
    END WITH
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**:
- **MCP Protocol**: Communicates with Model Context Protocol server
- **HTTP Streaming**: Uses streamable HTTP client for connection
- **Session Management**: Manages MCP session lifecycle

**External Dependencies**:
- **MCP Server**: Model Context Protocol server for tool access
- **streamablehttp_client**: HTTP client for MCP server communication
- **ClientSession**: MCP client session management
- **load_mcp_tools**: Function to load tools from MCP session from LangChain community

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Get Research Tools

**Component name**: get_research_tools

**Component type**: async function

**Component purpose and responsibilities**:
- **Purpose**: Get the research tools
- **Responsibilities**: 
  - Creates Wikipedia tool with API wrapper
  - Creates Tavily search tool
  - Retrieves browser MCP tools from MCP server
  - Compiles and returns comprehensive list of research tools
  - Combines built-in tools with external MCP tools

**Component interface**:
- **Inputs**: None
- **Outputs**:
  - list[Tool] // The list of research tools
- **Validations**:
  - Handled by individual tool creation validation
  - MCP tools validation handled by get_browser_mcp_tools function

**Direct Dependencies with Other Components**:
- get_browser_mcp_tools function
- youtube_transcript_tool function
- tavily_tool function
- wikipedia_tool function
- unstructured_excel_tool function
- unstructured_powerpoint_tool function
- unstructured_pdf_tool function
- text_file_tool function

**Internal Logic**:
1. Define browser MCP URL as "http://0.0.0.0:3000/mcp"
2. Retrieve MCP tools using await get_browser_mcp_tools(browser_mcp_url)
3. Return list containing:
   - youtube_transcript_tool
   - tavily_tool
   - wikipedia_tool
   - unstructured_excel_tool
   - unstructured_powerpoint_tool
   - unstructured_pdf_tool
   - text_file_tool
   - all mcp_tools (unpacked using *mcp_tools)

**Pseudocode**:
```
ASYNC FUNCTION get_research_tools() -> list[Tool]
    /*
    Purpose: Get the research tools
    
    BEHAVIOR:
    - Accepts: None
    - Produces: list[Tool] - The list of research tools
    - Handles: Tool creation and compilation for research operations
    
    DEPENDENCIES:
    - get_browser_mcp_tools: Function to retrieve MCP tools
    - Built-in research tools: Various file and web search tools
    
    IMPLEMENTATION NOTES:
    - Should combine built-in tools with external MCP tools
    - Should handle async MCP tool retrieval
    - Should return comprehensive tool list for research operations
    */
    
    // Define browser MCP URL
    browser_mcp_url = "http://0.0.0.0:3000/mcp"
    
    // Retrieve MCP tools using await get_browser_mcp_tools
    mcp_tools = await get_browser_mcp_tools(browser_mcp_url)
    
    // Return comprehensive list of research tools
    RETURN [
        youtube_transcript_tool,
        tavily_tool,
        wikipedia_tool,
        unstructured_excel_tool,
        unstructured_powerpoint_tool,
        unstructured_pdf_tool,
        text_file_tool,
        *mcp_tools  // Unpack all MCP tools
    ]
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**:
- **MCP Communication**: Uses get_browser_mcp_tools to communicate with MCP server
- **Tool Integration**: Combines multiple tool types into unified list

**External Dependencies**:
- **MCP Server**: Model Context Protocol server for tool access

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Researcher LLM Node Factory

**Component name**: create_researcher_llm_node

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create a researcher LLM node function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a researcher LLM node
  - Injects configuration and LLM dependencies into the node function
  - Handles LLM invocation with system prompt and state messages
  - Logs tool calls if present in the response
  - Returns response in messages format for subgraph processing

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompt
  - llm_researcher: ChatOpenAI // The LLM instance for researcher operations
- **Outputs**:
  - Callable[[ResearcherState], ResearcherState] // The researcher LLM node function
- **Validations**:
  - Handled by subgraph processing

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Define inner function researcher_llm_node that takes ResearcherState as parameter
2. Create system prompt as list containing SystemMessage with config.system_prompt content
3. Invoke LLM with system prompt concatenated with state messages
4. Check if response has tool_calls attribute and tool_calls exist
5. Log tool calls if present
6. Return messages with the response in dictionary format
7. Return the inner researcher_llm_node function

**Pseudocode**:
```
FUNCTION create_researcher_llm_node(config: AgentConfig, llm_researcher: ChatOpenAI) -> Callable[[ResearcherState], ResearcherState]
    /*
    Purpose: Create a researcher LLM node function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing system prompt
    - Accepts: llm_researcher (ChatOpenAI) - The LLM instance for researcher operations
    - Produces: Callable[[ResearcherState], ResearcherState] - The researcher LLM node function
    - Handles: LLM node creation with dependency injection and response handling
    
    DEPENDENCIES:
    - LangChain SystemMessage: Library for creating system messages
    - ChatOpenAI: LLM interface for researcher operations
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - llm_researcher: ChatOpenAI - LLM instance passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create inner function with injected dependencies
    - Must handle LLM invocation with proper message formatting
    - Should log tool calls if present in the response
    - Should return response in messages format for subgraph processing
    */
    
    // Define inner function researcher_llm_node that takes ResearcherState as parameter
    FUNCTION researcher_llm_node(state: ResearcherState) -> ResearcherState
        // Create system prompt as list containing SystemMessage with config.system_prompt content
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        
        // Invoke LLM with system prompt concatenated with state messages
        response = llm_researcher.invoke(sys_prompt + state["messages"])
        
        // Check if response has tool_calls attribute and tool_calls exist
        IF hasattr(response, 'tool_calls') AND response.tool_calls THEN
            // Log tool calls with INFO level
            LOG_INFO(f"Researcher tool calls: {response.tool_calls}")
        END IF
        
        // Return messages with the response in dictionary format
        RETURN {"messages": [response]}
    END FUNCTION
    
    // Return the inner researcher_llm_node function
    RETURN researcher_llm_node
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses messages field in ResearcherState input and returns updated ResearcherState with new messages. No state field updates are performed.

**Communication Patterns**: None. This component does not communicate, rather it creates a function for LLM processing

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for researcher operations

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- llm_researcher: ChatOpenAI - LLM instance passed from outer scope

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Researcher Subgraph Factory

**Component name**: create_researcher_subgraph

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create and compile a researcher subgraph with the given prompt and LLM
- **Responsibilities**: 
  - Creates a StateGraph for researcher workflow
  - Adds researcher LLM node to the graph
  - Adds tools node to the graph
  - Configures graph edges and conditional routing
  - Compiles and returns the complete subgraph

**Component interface**:
- **Inputs**:
  - researcher_llm_node: Callable // The researcher LLM node function
  - research_tools: list // The list of research tools to include in the subgraph
- **Outputs**:
  - StateGraph // The compiled researcher subgraph
- **Validations**:
  - Handled by LangGraph StateGraph validation

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Create StateGraph instance with ResearcherState as the state type
2. Add "researcher" node to the graph using researcher_llm_node function
3. Add "tools" node to the graph using ToolNode with research_tools
4. Add edge from START to "researcher" node
5. Add conditional edges from "researcher" node using tools_condition
6. Add edge from "tools" node back to "researcher" node
7. Compile the graph and return the compiled StateGraph

**Pseudocode**:
```
FUNCTION create_researcher_subgraph(researcher_llm_node: Callable, research_tools: list) -> StateGraph
    /*
    Purpose: Create and compile a researcher subgraph with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: researcher_llm_node (Callable) - The researcher LLM node function
    - Accepts: research_tools (list) - The list of research tools to include in the subgraph
    - Produces: StateGraph - The compiled researcher subgraph
    - Handles: Graph creation and compilation for researcher workflow
    
    DEPENDENCIES:
    - LangGraph StateGraph: Library for creating state-based graphs
    - LangGraph ToolNode: Library for creating tool nodes in graphs
    - LangGraph START: Library constant for graph start node
    - tools_condition: Function for determining tool usage conditions
    
    IMPLEMENTATION NOTES:
    - Should create StateGraph with ResearcherState as state type
    - Must add researcher LLM node and tools node to graph
    - Should configure proper edges and conditional routing
    - Should compile and return complete subgraph
    */
    
    // Create StateGraph instance with ResearcherState as the state type
    researcher_graph = StateGraph(ResearcherState)
    
    // Add "researcher" node to the graph using researcher_llm_node function
    researcher_graph.add_node("researcher", researcher_llm_node)
    
    // Add "tools" node to the graph using ToolNode with research_tools
    researcher_graph.add_node("tools", ToolNode(research_tools))
    
    // Add edge from START to "researcher" node
    researcher_graph.add_edge(START, "researcher")
    
    // Add conditional edges from "researcher" node using tools_condition
    researcher_graph.add_conditional_edges("researcher", tools_condition)
    
    // Add edge from "tools" node back to "researcher" node
    researcher_graph.add_edge("tools", "researcher")
    
    // Compile the graph and return the compiled StateGraph
    RETURN researcher_graph.compile()
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it creates a graph structure

**External Dependencies**:
- **LangGraph StateGraph**: Library for creating state-based graphs
- **LangGraph ToolNode**: Library for creating tool nodes in graphs
- **LangGraph START**: Library constant for graph start node
- **tools_condition**: Function for determining tool usage conditions

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

### Expert Subgraph Components

#### Unit Converter Tool

**Component name**: unit_converter

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Convert a quantity to a different unit
- **Responsibilities**: 
  - Parses quantity strings with units using Pint library
  - Performs unit conversions between different measurement systems
  - Handles various unit types (length, mass, temperature, etc.)
  - Returns converted values as formatted strings

**Component interface**:
- **Inputs**:
  - quantity: string // A string like '10 meters', '5 kg', '32 fahrenheit'
  - to_unit: string // The unit to convert to, e.g. 'ft', 'lbs', 'celsius'
- **Outputs**:
  - string // The converted value as a string
- **Validations**:
  - Handled by Pint UnitRegistry validation
  - Unit format validation handled by Pint library

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of unit conversion with quantity and target unit
2. Create Pint UnitRegistry instance
3. Parse the input quantity string using the UnitRegistry
4. Convert the quantity to the target unit using the to() method
5. Log the conversion result
6. Return the result as a string

**Pseudocode**:
```
FUNCTION unit_converter(quantity: string, to_unit: string) -> string
    /*
    Purpose: Convert a quantity to a different unit
    
    BEHAVIOR:
    - Accepts: quantity (string) - A string like '10 meters', '5 kg', '32 fahrenheit'
    - Accepts: to_unit (string) - The unit to convert to, e.g. 'ft', 'lbs', 'celsius'
    - Produces: string - The converted value as a string
    - Handles: Unit conversion calculations using Pint library
    
    DEPENDENCIES:
    - Pint UnitRegistry: Library for unit conversion and dimensional analysis
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should handle various unit types (length, mass, temperature, etc.)
    - Must parse quantity strings with units correctly
    - Should perform conversions between different measurement systems
    - Should return formatted string results
    */
    
    // Log the beginning of unit conversion with quantity and target unit
    LOG_INFO(f"Unit converter converting {quantity} to {to_unit}")
    
    // Create Pint UnitRegistry instance
    ureg = pint.UnitRegistry()
    
    // Parse the input quantity string using the UnitRegistry
    q = ureg(quantity)
    
    // Convert the quantity to the target unit using the to() method
    result = q.to(to_unit)
    
    // Log the conversion result
    LOG_INFO(f"Unit converter result: {result}")
    
    // Return the result as a string
    RETURN str(result)
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it performs unit conversion calculations

**External Dependencies**:
- **Pint UnitRegistry**: Library for unit conversion and dimensional analysis
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with quantity and target unit: "Unit converter converting {quantity} to {to_unit}"
- Append logging (INFO) at the end of successful processing with result: "Unit converter result: {result}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Calculator Tool

**Component name**: calculator

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Evaluate a basic math expression. Supports +, -, *, /, **, and parentheses
- **Responsibilities**: 
  - Parses mathematical expressions as strings
  - Evaluates expressions using Python's eval with restricted namespace
  - Provides access to mathematical functions from Python's math module
  - Returns calculation results as formatted strings

**Component interface**:
- **Inputs**:
  - expression: string // A mathematical expression to evaluate
- **Outputs**:
  - string // The calculated result as a string
- **Validations**:
  - Handled by Python eval function validation
  - Expression format validation handled by eval function

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of calculation with the expression
2. Import the math module
3. Create allowed_names dictionary with math functions using dictionary comprehension (excluding those starting with "__")
4. Evaluate the expression using eval with restricted namespace (no builtins, only math functions)
5. Log the calculation result
6. Return the result as a string

**Pseudocode**:
```
FUNCTION calculator(expression: string) -> string
    /*
    Purpose: Evaluate a basic math expression. Supports +, -, *, /, **, and parentheses
    
    BEHAVIOR:
    - Accepts: expression (string) - A mathematical expression to evaluate
    - Produces: string - The calculated result as a string
    - Handles: Mathematical expression evaluation with restricted namespace
    
    DEPENDENCIES:
    - Python math module: Library for mathematical functions and constants
    - Python eval function: Built-in function for expression evaluation
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should support basic math operations (+, -, *, /, **, parentheses)
    - Must use restricted namespace for security (no builtins, only math functions)
    - Should exclude math functions starting with "__" for security
    - Should return formatted string results
    */
    
    // Log the beginning of calculation with the expression
    LOG_INFO(f"Calculator evaluating expression: {expression}")
    
    // Import the math module
    IMPORT math
    
    // Create allowed_names dictionary with math functions using dictionary comprehension (excluding those starting with "__")
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    
    // Evaluate the expression using eval with restricted namespace (no builtins, only math functions)
    result = eval(expression, {"__builtins__": None}, allowed_names)
    
    // Log the calculation result
    LOG_INFO(f"Calculator result: {result}")
    
    // Return the result as a string
    RETURN str(result)
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it performs mathematical calculations

**External Dependencies**:
- **Python math module**: Library for mathematical functions and constants
- **Python eval function**: Built-in function for expression evaluation
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with expression: "Calculator evaluating expression: {expression}"
- Append logging (INFO) at the end of successful processing with result: "Calculator result: {result}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Python REPL Tool

**Component name**: python_repl_tool

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Execute Python code and return the result
- **Responsibilities**: 
  - Creates a Python REPL tool instance for code execution
  - Executes Python code provided as a string
  - Returns the result of code execution as a string
  - Provides Python code execution capabilities for expert reasoning

**Component interface**:
- **Inputs**:
  - code: string // The Python code to execute
- **Outputs**:
  - string // The result of the code execution as a string
- **Validations**:
  - Handled by PythonREPLTool validation
  - Code execution validation handled by Python interpreter

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Log the beginning of Python code execution with the code
2. Create PythonREPLTool instance
3. Invoke the Python REPL tool with the provided code
4. Return the result of code execution

**Pseudocode**:
```
FUNCTION python_repl_tool(code: string) -> string
    /*
    Purpose: Execute Python code and return the result
    
    BEHAVIOR:
    - Accepts: code (string) - The Python code to execute
    - Produces: string - The result of the code execution as a string
    - Handles: Python code execution using LangChain PythonREPLTool
    
    DEPENDENCIES:
    - LangChain PythonREPLTool: Library for Python code execution
    - LangChain @tool Decorator: Library to mark function as a LangGraph tool
    
    IMPLEMENTATION NOTES:
    - Should create PythonREPLTool instance for each execution
    - Must execute Python code safely using LangChain's implementation
    - Should return execution results as formatted strings
    - Should provide Python code execution capabilities for expert reasoning
    */
    
    // Log the beginning of Python code execution with the code
    LOG_INFO(f"Executing the following python code: {code}")
    
    // Create PythonREPLTool instance
    python_repl_tool = PythonREPLTool()
    
    // Invoke the Python REPL tool with the provided code
    result = python_repl_tool.invoke(code)
    
    // Return the result of code execution
    RETURN result
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it executes Python code

**External Dependencies**:
- **LangChain PythonREPLTool**: Library for Python code execution
- **LangChain @tool Decorator**: Library to mark function as a LangGraph tool

**Global variables**: None

**Closed-over variables**: None

**Decorators**:
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with code to be executed

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Expert Tools Factory

**Component name**: get_expert_tools

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Get the expert tools
- **Responsibilities**: 
  - Returns list of existing expert tools (unit_converter, calculator, python_repl_tool)
  - Provides expert-level computation and analysis tools
  - Returns comprehensive list of tools for expert reasoning

**Component interface**:
- **Inputs**: None
- **Outputs**:
  - List[Tool] // The list of expert tools
- **Validations**:
  - Handled by LangChain tool creation validation

**Direct Dependencies with Other Components**:
- unit_converter function
- calculator function
- python_repl_tool function

**Internal Logic**:
1. Return list containing unit_converter, calculator, and python_repl_tool

**Pseudocode**:
```
FUNCTION get_expert_tools() -> List[Tool]
    /*
    Purpose: Get the expert tools
    
    BEHAVIOR:
    - Accepts: None
    - Produces: List[Tool] - The list of expert tools
    - Handles: Tool compilation for expert-level computation and analysis
    
    DEPENDENCIES:
    - unit_converter: Function for unit conversion operations
    - calculator: Function for mathematical calculations
    - python_repl_tool: Function for Python code execution
    
    IMPLEMENTATION NOTES:
    - Should return existing unit converter and calculator tools
    - Should return existing Python REPL tool
    - Should provide comprehensive expert-level computation tools
    - Should return list of tools for expert reasoning
    */
    
    // Return list containing unit_converter, calculator, and python_repl_tool
    expert_tools = [unit_converter, calculator, python_repl_tool]
    
    RETURN expert_tools
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it returns existing tool instances

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Expert LLM Node Factory

**Component name**: create_expert_llm_node

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create an expert LLM node function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns an expert LLM node
  - Injects configuration and LLM dependencies into the node function
  - Handles LLM invocation with system prompt and state messages
  - Logs tool calls if present in the response
  - Returns response in messages format for subgraph processing

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompt
  - llm_expert: ChatOpenAI // The LLM instance for expert operations
- **Outputs**:
  - Callable[[ExpertState], ExpertState] // The expert LLM node function
- **Validations**:
  - Handled by subgraph processing

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Define inner function expert_llm_node that takes ExpertState as parameter
2. Create system prompt as list containing SystemMessage with config.system_prompt content
3. Invoke LLM with system prompt concatenated with state messages
4. Check if response has tool_calls attribute and tool_calls exist
5. If tool calls exist, log them with INFO level
6. Return messages with the response in dictionary format
7. Return the inner expert_llm_node function

**Pseudocode**:
```
FUNCTION create_expert_llm_node(config: AgentConfig, llm_expert: ChatOpenAI) -> Callable[[ExpertState], ExpertState]
    /*
    Purpose: Create an expert LLM node function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing system prompt and output schema
    - Accepts: llm_expert (ChatOpenAI) - The LLM instance for expert operations
    - Produces: Callable[[ExpertState], ExpertState] - The expert LLM node function
    - Handles: LLM node creation with dependency injection and response validation
    
    DEPENDENCIES:
    - LangChain SystemMessage: Library for creating system messages
    - LangChain AIMessage: Library for creating AI response messages
    - ChatOpenAI: LLM interface for expert operations
    - validate_output_matches_json_schema: Function for response validation
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - llm_expert: ChatOpenAI - LLM instance passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create inner function with injected dependencies
    - Must handle LLM invocation with proper message formatting
    - Should validate responses against output schema
    - Should update expert state with answer and reasoning when validation succeeds
    - Should return appropriate response format based on validation result
    */
    
    // Define inner function expert_llm_node that takes ExpertState as parameter
    FUNCTION expert_llm_node(state: ExpertState) -> ExpertState
        // Create system prompt as list containing SystemMessage with config.system_prompt content
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        
        // Invoke LLM with system prompt concatenated with state messages
        response = llm_expert.invoke(sys_prompt + state["messages"])
        
        // Check if response has tool_calls attribute and tool_calls exist
        IF hasattr(response, 'tool_calls') AND response.tool_calls THEN
            // Log tool calls with INFO level
            LOG_INFO(f"Expert tool calls: {response.tool_calls}")
        END IF
        
        // Return messages with the response in dictionary format
        RETURN {"messages": [response]}
    END FUNCTION
    
    // Return the inner expert_llm_node function
    RETURN expert_llm_node
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses messages field in ExpertState input and returns updated ExpertState with new messages. No state field updates are performed.

**Communication Patterns**: None. This component does not communicate, rather it creates a function for LLM processing

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for expert operations

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- llm_expert: ChatOpenAI - LLM instance passed from outer scope

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Expert Subgraph Factory

**Component name**: create_expert_subgraph

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create and compile an expert subgraph with the given prompt and LLM
- **Responsibilities**: 
  - Creates a StateGraph for expert workflow
  - Adds expert LLM node to the graph
  - Adds tools node to the graph
  - Configures graph edges and conditional routing
  - Compiles and returns the complete subgraph

**Component interface**:
- **Inputs**:
  - expert_llm_node: Callable // The expert LLM node function
  - expert_tools: list // The list of expert tools to include in the subgraph
- **Outputs**:
  - StateGraph // The compiled expert subgraph
- **Validations**:
  - Handled by LangGraph StateGraph validation

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Create StateGraph instance with ExpertState as the state type
2. Add "expert" node to the graph using expert_llm_node function
3. Add "tools" node to the graph using ToolNode with expert_tools
4. Add edge from START to "expert" node
5. Add conditional edges from "expert" node using tools_condition
6. Add edge from "tools" node back to "expert" node
7. Compile the graph and return the compiled StateGraph

**Pseudocode**:
```
FUNCTION create_expert_subgraph(expert_llm_node: Callable, expert_tools: list) -> StateGraph
    /*
    Purpose: Create and compile an expert subgraph with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: expert_llm_node (Callable) - The expert LLM node function
    - Accepts: expert_tools (list) - The list of expert tools to include in the subgraph
    - Produces: StateGraph - The compiled expert subgraph
    - Handles: Graph creation and compilation for expert workflow
    
    DEPENDENCIES:
    - LangGraph StateGraph: Library for creating state-based graphs
    - LangGraph ToolNode: Library for creating tool nodes in graphs
    - LangGraph START: Library constant for graph start node
    - tools_condition: Function for determining tool usage conditions
    
    IMPLEMENTATION NOTES:
    - Should create StateGraph with ExpertState as state type
    - Must add expert LLM node and tools node to graph
    - Should configure proper edges and conditional routing
    - Should compile and return complete subgraph
    */
    
    // Create StateGraph instance with ExpertState as the state type
    expert_graph = StateGraph(ExpertState)
    
    // Add "expert" node to the graph using expert_llm_node function
    expert_graph.add_node("expert", expert_llm_node)
    
    // Add "tools" node to the graph using ToolNode with expert_tools
    expert_graph.add_node("tools", ToolNode(expert_tools))
    
    // Add edge from START to "expert" node
    expert_graph.add_edge(START, "expert")
    
    // Add conditional edges from "expert" node using tools_condition
    expert_graph.add_conditional_edges("expert", tools_condition)
    
    // Add edge from "tools" node back to "expert" node
    expert_graph.add_edge("tools", "expert")
    
    // Compile the graph and return the compiled StateGraph
    RETURN expert_graph.compile()
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it creates a graph structure

**External Dependencies**:
- **LangGraph StateGraph**: Library for creating state-based graphs
- **LangGraph ToolNode**: Library for creating tool nodes in graphs
- **LangGraph START**: Library constant for graph start node
- **tools_condition**: Function for determining tool usage conditions

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

### Main Graph Components

#### Input Interface Factory

**Component name**: create_input_interface

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create an input interface function with the given retry limit
- **Responsibilities**: 
  - Creates a factory function that returns an input interface node
  - Injects agent configuration dependencies into the interface function
  - Handles input validation and error checking
  - Initializes all state fields for workflow execution
  - Sets up retry limits from agent configurations
  - Provides system entry point for user interactions

**Component interface**:
- **Inputs**:
  - agent_configs: dict[str, AgentConfig] // Dictionary containing all agent configurations
- **Outputs**:
  - Callable[[GraphState], GraphState] // The input interface function
- **Validations**:
  - Handled by input validation logic within the function

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Define inner function input_interface that takes GraphState as parameter
2. Log the beginning of input interface execution
3. Handle question extraction with proper error handling:
   - Check if state.get("question") is falsy or if len(state["question"]) == 0
   - Raise ValueError if no question is provided
4. Initialize all state fields first to ensure they exist for error handling:
   - Set file field with existing value or None
   - Initialize planner work fields (research_steps and expert_steps as empty lists)
   - Initialize researcher work fields (current_research_index = -1, researcher_states = dict(), research_results = [])
   - Initialize expert work fields (expert_state = None, expert_answer = "", expert_reasoning = "")
   - Initialize critic work fields (all decision and feedback fields to empty strings)
   - Initialize finalizer work fields (final_answer = "", final_reasoning_trace = "")
   - Initialize orchestrator work fields (agent_messages = [], current_step = "input", next_step = "planner")
   - Initialize retry counts to 0 for all agents (planner_retry_count, researcher_retry_count, expert_retry_count)
   - Set retry limits from agent_configs for planner, researcher, and expert
   - Set retry_failed to False
5. Log successful completion
6. Return the updated state
7. Return the inner input_interface function

**Pseudocode**:
```
FUNCTION create_input_interface(agent_configs: dict[str, AgentConfig]) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create an input interface function with the given retry limit
    
    BEHAVIOR:
    - Accepts: agent_configs (dict[str, AgentConfig]) - Dictionary containing all agent configurations
    - Produces: Callable[[GraphState], GraphState] - The input interface function
    - Handles: Input validation and state initialization for workflow execution
    
    CLOSED-OVER VARIABLES:
    - agent_configs: dict[str, AgentConfig] - Agent configurations passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create inner function with injected agent configurations
    - Must handle input validation and error checking
    - Should initialize all state fields for workflow execution
    - Should set up retry limits from agent configurations
    - Should provide system entry point for user interactions
    */
    
    // Define inner function input_interface that takes GraphState as parameter
    FUNCTION input_interface(state: GraphState) -> GraphState
        // Log the beginning of input interface execution
        LOG_INFO("Input interface starting execution")
        
        // Handle question extraction with proper error handling
        IF NOT state.get("question") OR LENGTH(state["question"]) = 0 THEN
            RAISE ValueError("No question provided to input interface")
        END IF
        
        // Initialize all state fields first to ensure they exist for error handling
        state["file"] = state["file"] IF state["file"] ELSE none
        
        // Initialize planner work fields (research_steps and expert_steps as empty lists)
        state["research_steps"] = []
        state["expert_steps"] = []
        
        // Initialize researcher work fields
        state["current_research_index"] = -1
        state["researcher_states"] = dict()
        state["research_results"] = []
        
        // Initialize expert work fields
        state["expert_state"] = none
        state["expert_answer"] = ""
        state["expert_reasoning"] = ""
        
        // Initialize critic work fields (all decision and feedback fields to empty strings)
        state["critic_planner_decision"] = ""
        state["critic_planner_feedback"] = ""
        state["critic_researcher_decision"] = ""
        state["critic_researcher_feedback"] = ""
        state["critic_expert_decision"] = ""
        state["critic_expert_feedback"] = ""
        
        // Initialize finalizer work fields (final_answer and final_reasoning_trace to empty strings)
        state["final_answer"] = ""
        state["final_reasoning_trace"] = ""
        
        // Initialize orchestrator work fields
        state["agent_messages"] = []
        state["current_step"] = "input"
        state["next_step"] = "planner"
        
        // Initialize retry counts to 0 for all agents
        state["planner_retry_count"] = 0
        state["researcher_retry_count"] = 0
        state["expert_retry_count"] = 0
        
        // Set retry limits from agent_configs for planner, researcher, and expert
        state["planner_retry_limit"] = agent_configs["planner"].retry_limit
        state["researcher_retry_limit"] = agent_configs["researcher"].retry_limit
        state["expert_retry_limit"] = agent_configs["expert"].retry_limit
        state["retry_failed"] = False
        
        // Log successful completion
        LOG_INFO("Input interface completed successfully")
        
        // Return the updated state
        RETURN state
    END FUNCTION
    
    // Return the inner input_interface function
    RETURN input_interface
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses and initializes all fields in GraphState input and returns updated GraphState with initialized values.

**Communication Patterns**: None. This component does not communicate, rather it initializes system state

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**:
- agent_configs: dict[str, AgentConfig] - Agent configurations passed from outer scope

**Decorators**: None

**Logging**:
- Logs INFO level message at the beginning: "Input interface starting execution"
- Logs INFO level message at the end: "Input interface completed successfully"

**Error Handling**:
- Raises ValueError if no question is provided to input interface
- Error message includes context about missing question
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Next Step Determination

**Component name**: determine_next_step

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Orchestrator logic to determine the next step based on current step and critic decisions
- **Responsibilities**: 
  - Handles critic decisions and sets the next step accordingly
  - Handles initial state and non-critic steps
  - Handles retry counter incrementation
  - Manages workflow state transitions
  - Determines routing logic for multi-agent workflow

**Component interface**:
- **Inputs**:
  - state: GraphState // The current state of the graph
- **Outputs**:
  - GraphState // The updated state of the graph with next_step determined
- **Validations**:
  - Handled by state field access validation

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Handle critic decisions and set next step accordingly using elif control structure:
   - If current_step is "critic_planner":
     - Check if critic_planner_decision equals "approve"
     - If critic_planner_decision is "approve":
       - Log "Planner approved."
       - Check if length of research_steps list is greater than 0
       - If research_steps has items, set next_step to "researcher"
       - If research_steps is empty, set next_step to "expert"
     - If critic_planner_decision is "reject":
       - Set next_step to "planner"
       - Increment planner_retry_count by 1
       - Log "Planner rejected. Retry count: {planner_retry_count}"
2. If current_step is "critic_researcher":
   - Check if critic_researcher_decision equals "approve"
   - If critic_researcher_decision is "approve":
     - Log "Researcher approved."
     - Check if current_research_index + 1 is greater than or equal to length of research_steps
     - If all research steps completed, set next_step to "expert"
     - If more research steps remain, set next_step to "researcher"
   - If critic_researcher_decision is "reject":
     - Set next_step to "researcher"
     - Increment researcher_retry_count by 1
     - Log "Researcher rejected. Retry count: {researcher_retry_count}"
3. If current_step is "critic_expert":
   - Check if critic_expert_decision equals "approve"
   - If critic_expert_decision is "approve":
     - Log "Expert approved."
     - Set next_step to "finalizer"
   - If critic_expert_decision is "reject":
     - Set next_step to "expert"
     - Increment expert_retry_count by 1
     - Log "Expert rejected. Retry count: {expert_retry_count}"
4. Handle initial state and non-critic steps using elif:
   - If current_step is empty string or equals "input", set next_step to "planner"
   - If current_step equals "planner", set next_step to "critic_planner"
   - If current_step equals "researcher", set next_step to "critic_researcher"
   - If current_step equals "expert", set next_step to "critic_expert"
5. Return the updated state

**Pseudocode**:
```
FUNCTION determine_next_step(state: GraphState) -> GraphState
    /*
    Purpose: Orchestrator logic to determine the next step based on current step and critic decisions
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The current state of the graph
    - Produces: GraphState - The updated state of the graph with next_step determined
    - Handles: Workflow state transitions and routing logic for multi-agent workflow
    
    IMPLEMENTATION NOTES:
    - Should handle critic decisions and set next step accordingly
    - Must handle initial state and non-critic steps
    - Should handle retry counter incrementation
    - Should manage workflow state transitions
    - Should determine routing logic for multi-agent workflow
    */
    
    // Handle critic decisions and set next step accordingly
    IF state["current_step"] = "critic_planner" THEN
        IF state["critic_planner_decision"] = "approve" THEN
            LOG_INFO("Planner approved.")
            IF LENGTH(state["research_steps"]) > 0 THEN
                state["next_step"] = "researcher"
            ELSE
                state["next_step"] = "expert"
            END IF
        ELSE IF state["critic_planner_decision"] = "reject" THEN
            state["next_step"] = "planner"
            state["planner_retry_count"] += 1
            LOG_INFO(f"Planner rejected. Retry count: {state['planner_retry_count']}")
        END IF
    
    ELSE IF state["current_step"] = "critic_researcher" THEN
        IF state["critic_researcher_decision"] = "approve" THEN
            LOG_INFO("Researcher approved.")
            // Check if all research steps are completed
            IF state["current_research_index"] + 1 >= LENGTH(state["research_steps"]) THEN
                state["next_step"] = "expert"
            ELSE
                state["next_step"] = "researcher"
            END IF
        ELSE IF state["critic_researcher_decision"] = "reject" THEN
            state["next_step"] = "researcher"
            state["researcher_retry_count"] += 1
            LOG_INFO(f"Researcher rejected. Retry count: {state['researcher_retry_count']}")
        END IF
    
    ELSE IF state["current_step"] = "critic_expert" THEN
        IF state["critic_expert_decision"] = "approve" THEN
            LOG_INFO("Expert approved.")
            state["next_step"] = "finalizer"
        ELSE IF state["critic_expert_decision"] = "reject" THEN
            state["next_step"] = "expert"
            state["expert_retry_count"] += 1
            LOG_INFO(f"Expert rejected. Retry count: {state['expert_retry_count']}")
        END IF
    
    // Handle initial state and non-critic steps
    ELSE IF state["current_step"] = "" OR state["current_step"] = "input" THEN
        state["next_step"] = "planner"
    ELSE IF state["current_step"] = "planner" THEN
        state["next_step"] = "critic_planner"
    ELSE IF state["current_step"] = "researcher" THEN
        state["next_step"] = "critic_researcher"
    ELSE IF state["current_step"] = "expert" THEN
        state["next_step"] = "critic_expert"
    END IF
    
    // Return the updated state
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Controls workflow state transitions by determining the next step based on current state and critic decisions.

**State Management**: Reads current_step, critic decisions, and retry counts from state. Updates next_step and retry counts (planner_retry_count, researcher_retry_count, expert_retry_count) in state based on decision logic.

**Communication Patterns**: None. This component does not communicate, rather it determines workflow routing

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Retry Limit Check

**Component name**: check_retry_limit

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Orchestrator logic to check retry count and handle limit exceeded
- **Responsibilities**: 
  - Handles retry limit exceeded and sets the next step to finalizer
  - Handles graceful failure and sets the final answer and reasoning trace
  - Monitors retry counts for all agents (planner, researcher, expert)
  - Prevents infinite retry loops by enforcing retry limits
  - Provides graceful degradation when limits are exceeded

**Component interface**:
- **Inputs**:
  - state: GraphState // The current state of the graph
- **Outputs**:
  - GraphState // The updated state of the graph
- **Validations**:
  - Handled by retry count comparison validation

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Check if any agent has exceeded its retry limit using a single if statement with or conditions:
   - Check if planner_retry_count >= planner_retry_limit OR
   - Check if researcher_retry_count >= researcher_retry_limit OR  
   - Check if expert_retry_count >= expert_retry_limit
2. If any retry limit is exceeded:
   - Log graceful failure message with next_step information
   - Set retry_failed to True
   - Set next_step to "finalizer"
   - Set final_answer to "The question could not be answered."
   - Set final_reasoning_trace to "The question could not be answered."
3. Return the updated state

**Pseudocode**:
```
FUNCTION check_retry_limit(state: GraphState) -> GraphState
    /*
    Purpose: Orchestrator logic to check retry count and handle limit exceeded
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The current state of the graph
    - Produces: GraphState - The updated state of the graph
    - Handles: Retry limit checking and graceful failure handling
    
    IMPLEMENTATION NOTES:
    - Should handle retry limit exceeded and set next step to finalizer
    - Must handle graceful failure and set final answer and reasoning trace
    - Should monitor retry counts for all agents (planner, researcher, expert)
    - Should prevent infinite retry loops by enforcing retry limits
    - Should provide graceful degradation when limits are exceeded
    */
    
    // Check if any agent has exceeded its retry limit using a single if statement with or conditions
    IF (state["planner_retry_count"] >= state["planner_retry_limit"] 
        OR state["researcher_retry_count"] >= state["researcher_retry_limit"] 
        OR state["expert_retry_count"] >= state["expert_retry_limit"]) THEN
        
        // Log the failure with next_step information
        LOG_INFO(f"Graceful Failure: Retry limit exceeded for {state['next_step']}")
        
        // Set retry_failed to True
        state["retry_failed"] = True
        
        // Set next_step to "finalizer"
        state["next_step"] = "finalizer"
        
        // Set final_answer to "The question could not be answered."
        state["final_answer"] = "The question could not be answered."
        
        // Set final_reasoning_trace to "The question could not be answered."
        state["final_reasoning_trace"] = "The question could not be answered."
    END IF
    
    // Return the updated state
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Controls workflow termination by checking retry limits and routing to finalizer when limits are exceeded.

**State Management**: Reads retry counts and retry limits from state. Updates retry_failed, next_step, final_answer, and final_reasoning_trace in state when limits are exceeded.

**Communication Patterns**: None. This component does not communicate, rather it checks retry limits

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Logs INFO level message when retry limit is exceeded with format: "Graceful Failure: Retry limit exceeded for {next_step}"

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Next Step Execution

**Component name**: execute_next_step

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Orchestrator logic to execute the next step by setting current_step and sending message
- **Responsibilities**: 
  - Handles the different steps and sends the appropriate message
  - Includes any context needed in the message
  - Sets current_step to next_step
  - Composes and sends agent messages based on current step
  - Manages message content and context for each agent type
  - Handles retry scenarios with feedback

**Component interface**:
- **Inputs**:
  - state: GraphState // The current state of the graph
- **Outputs**:
  - GraphState // The updated state of the graph
- **Validations**:
  - Handled by state field access validation

**Direct Dependencies with Other Components**:
- compose_agent_message function
- send_message function
- orchestrator_msg_to_critic_planner message template
- orchestrator_msg_to_critic_planner_with_file message template
- orchestrator_msg_to_critic_researcher message template
- orchestrator_msg_to_expert message template
- orchestrator_msg_to_critic_expert message template
- orchestrator_msg_to_finalizer message template
- orchestrator_msg_to_finalizer_retry_failed message template

**Internal Logic**:
1. Set state["current_step"] to state["next_step"] value
2. Use elif control structure to check current_step values
3. If current_step is "planner":
   - Check if critic_planner_decision equals "reject"
   - If critic_planner_decision is "reject":
     - Create retry message using compose_agent_message with sender="orchestrator", receiver="planner", type="instruction", and content formatted as "Use the following feedback to improve the plan:\n{state['critic_planner_feedback']}"
   - If critic_planner_decision is not "reject":
     - Initialize file_info as empty string
     - Check if state["file"] exists
     - If file exists, set file_info to "\n\nInclude using following file in any of the research steps:" + "\n".join(state["file"])
     - Create initial planning message using compose_agent_message with sender="orchestrator", receiver="planner", type="instruction", and content formatted as "Develop a logical plan to answer the following question:\n{state['question']}{file_info}"
4. If current_step is "critic_planner":
   - Check if state["file"] exists
   - If file exists, use orchestrator_msg_to_critic_planner_with_file template with question, file, research_steps, and expert_steps parameters
   - If file does not exist, use orchestrator_msg_to_critic_planner template with question, research_steps, and expert_steps parameters
   - Create critic message using compose_agent_message with sender="orchestrator", receiver="critic_planner", type="instruction", and content from template
5. If current_step is "researcher":
   - Check if critic_researcher_decision equals "reject"
   - If critic_researcher_decision is "reject":
     - Create retry message using compose_agent_message with sender="orchestrator", receiver="researcher", type="instruction", content formatted as "Use the following feedback to improve the research:\n{state["critic_researcher_feedback"]}", and step_id=state["current_research_index"]
   - If critic_researcher_decision is not "reject":
     - Increment state["current_research_index"] by 1
     - Create research instruction message using compose_agent_message with sender="orchestrator", receiver="researcher", type="instruction", content formatted as "Research the following topic or question: {state['research_steps'][state['current_research_index']]}", and step_id=state["current_research_index"]
6. If current_step is "critic_researcher":
   - Use orchestrator_msg_to_critic_researcher template with research_topic and research_results parameters
   - Create critic message using compose_agent_message with sender="orchestrator", receiver="critic_researcher", type="instruction", and content from template
7. If current_step is "expert":
   - Check if critic_expert_decision equals "reject"
   - If critic_expert_decision is "reject":
     - Create retry message using compose_agent_message with sender="orchestrator", receiver="expert", type="instruction", and content formatted as "Use the following feedback to improve your answer:\n{state["critic_expert_feedback"]}"
   - If critic_expert_decision is not "reject":
     - Use orchestrator_msg_to_expert template with research_results, expert_steps, and question parameters
     - Create expert instruction message using compose_agent_message with sender="orchestrator", receiver="expert", type="instruction", and content from template
8. If current_step is "critic_expert":
   - Use orchestrator_msg_to_critic_expert template with question, research_results, expert_answer, and expert_reasoning parameters
   - Create critic message using compose_agent_message with sender="orchestrator", receiver="critic_expert", type="instruction", and content from template
9. If current_step is "finalizer":
   - Check if state["retry_failed"] is True
   - If retry_failed is True:
     - Use orchestrator_msg_to_finalizer_retry_failed template
   - If retry_failed is False:
     - Use orchestrator_msg_to_finalizer template with question, research_steps, expert_steps, expert_answer, and expert_reasoning parameters
   - Create finalizer instruction message using compose_agent_message with sender="orchestrator", receiver="finalizer", type="instruction", and content from template
10. If current_step is invalid (not matching any condition):
    - Raise ValueError with message formatted as "Invalid current step: {state['current_step']}"
11. Send the composed message using send_message function with state and message parameters
12. Return the updated state

**Pseudocode**:
```
FUNCTION execute_next_step(state: GraphState) -> GraphState
    /*
    Purpose: Orchestrator logic to execute the next step by setting current_step and sending message
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The current state of the graph
    - Produces: GraphState - The updated state of the graph
    - Handles: Workflow execution by setting current_step and sending appropriate messages to agents
    
    DEPENDENCIES:
    - compose_agent_message: Function for creating agent messages
    - send_message: Function for sending messages to agents
    
    IMPLEMENTATION NOTES:
    - Should handle the different steps and send appropriate messages
    - Must include context needed in messages
    - Should set current_step to next_step
    - Should compose and send agent messages based on current step
    - Should manage message content and context for each agent type
    - Should handle retry scenarios with feedback
    */
    
    // Set state["current_step"] to state["next_step"] value
    state["current_step"] = state["next_step"]
    
    // Send appropriate message based on the current step
    IF state["current_step"] = "planner" THEN
        IF state["critic_planner_decision"] = "reject" THEN
            // Retry with feedback
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "planner",
                type= "instruction",
                content= f"Use the following feedback to improve the plan:\n{state['critic_planner_feedback']}",
            )
        ELSE
            // Initial planning request
            file_info = ""
            IF state["file"] THEN
                file_info = "\n\nInclude using following file in any of the research steps:" + "\n".join(state["file"])
            END IF
            
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "planner",
                type= "instruction",
                content= f"Develop a logical plan to answer the following question:\n{state['question']}{file_info}",
            )
        END IF
    
    ELSE IF state["current_step"] = "critic_planner" THEN
        // Add context to the last message to the critic
        IF state["file"] THEN
            content = orchestrator_msg_to_critic_planner_with_file.format(question=state["question"], file=state["file"], research_steps=state["research_steps"], expert_steps=state["expert_steps"])
        ELSE
            content = orchestrator_msg_to_critic_planner.format(question=state["question"], research_steps=state["research_steps"], expert_steps=state["expert_steps"])
        END IF
        
        message = compose_agent_message(
            sender= "orchestrator",
            receiver= "critic_planner",
            type= "instruction",
            content= content,
        )
    
    ELSE IF state["current_step"] = "researcher" THEN
        IF state["critic_researcher_decision"] = "reject" THEN
            // Retry with feedback
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "researcher",
                type= "instruction",
                content= f"Use the following feedback to improve the research:\n{state["critic_researcher_feedback"]}",
                step_id=state["current_research_index"],
            )
        ELSE
            // Increment research index for new step
            state["current_research_index"] += 1
            
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "researcher",
                type= "instruction",
                content= f"Research the following topic or question: {state['research_steps'][state['current_research_index']]}",
                step_id= state["current_research_index"],
            )   
        END IF
    
    ELSE IF state["current_step"] = "critic_researcher" THEN
        message = compose_agent_message(
            sender= "orchestrator",
            receiver= "critic_researcher",
            type= "instruction",
            content= orchestrator_msg_to_critic_researcher.format(research_topic=state["research_steps"][state["current_research_index"]], research_results=state["research_results"][state["current_research_index"]]),
        )
    
    ELSE IF state["current_step"] = "expert" THEN
        IF state["critic_expert_decision"] = "reject" THEN
            // Retry with feedback
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "expert",
                type= "instruction",
                content= f"Use the following feedback to improve your answer:\n{state["critic_expert_feedback"]}",
            )
        ELSE
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "expert",
                type= "instruction",
                content= orchestrator_msg_to_expert.format(research_results=state["research_results"], expert_steps=state["expert_steps"], question=state["question"]),
            )
        END IF
    
    ELSE IF state["current_step"] = "critic_expert" THEN
        message = compose_agent_message(
            sender= "orchestrator",
            receiver= "critic_expert",
            type= "instruction",
            content= orchestrator_msg_to_critic_expert.format(question=state["question"], research_results=state["research_results"], expert_answer=state["expert_answer"], expert_reasoning=state["expert_reasoning"]),
        )
    
    ELSE IF state["current_step"] = "finalizer" THEN
        IF state["retry_failed"] THEN
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "finalizer",
                type= "instruction",
                content= orchestrator_msg_to_finalizer_retry_failed,
            )
        ELSE
            message = compose_agent_message(
                sender= "orchestrator",
                receiver= "finalizer",
                type= "instruction",
                content= orchestrator_msg_to_finalizer.format(question=state["question"], research_steps=state["research_steps"], expert_steps=state["expert_steps"], expert_answer=state["expert_answer"], expert_reasoning=state["expert_reasoning"]),
            )
        END IF
    
    ELSE
        RAISE ValueError(f"Invalid current step: {state['current_step']}")
    END IF
    
    // Send the message
    send_message(state, message)
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Controls workflow execution by setting current_step and sending appropriate messages to agents.

**State Management**: Reads next_step and various state fields to compose messages. Updates current_step and current_research_index in state. Sends messages through send_message function.

**Communication Patterns**:
- **Agent Communication**: Sends messages to different agents based on current step
- **Message Composition**: Creates context-rich messages for each agent type
- **Feedback Integration**: Includes critic feedback in retry scenarios

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- Raises ValueError if current_step is invalid
- Error message includes the invalid current step for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Main Orchestrator

**Component name**: orchestrator

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Orchestrator logic to coordinate the multi-agent workflow
- **Responsibilities**: 
  - Follows the 4-step process outlined in the logical design
  - Determines the next step in the workflow
  - Checks retry count and handles limit exceeded scenarios
  - Executes the next step by setting current_step and sending message
  - Coordinates all agent interactions and workflow transitions
  - Manages workflow state and progression

**Component interface**:
- **Inputs**:
  - state: GraphState // The current state of the graph
- **Outputs**:
  - GraphState // The updated state of the graph
- **Validations**:
  - Handled by state field access validation

**Direct Dependencies with Other Components**:
- determine_next_step function
- check_retry_limit function
- execute_next_step function

**Internal Logic**:
1. Log the beginning of orchestrator execution with current step using safe state access
2. Call determine_next_step function to determine next step
3. Call check_retry_limit function to check retry limits
4. Call execute_next_step function to execute the next step
5. Log successful completion with next step using safe state access
6. Return the updated state

**Pseudocode**:
```
FUNCTION orchestrator(state: GraphState) -> GraphState
    /*
    Purpose: Orchestrator logic to coordinate the multi-agent workflow
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The current state of the graph
    - Produces: GraphState - The updated state of the graph
    - Handles: Multi-agent workflow coordination and state management
    
    DEPENDENCIES:
    - determine_next_step: Function to determine the next step in the workflow
    - check_retry_limit: Function to check retry count and handle limit exceeded scenarios
    - execute_next_step: Function to execute the next step by setting current_step and sending message
    
    IMPLEMENTATION NOTES:
    - Should follow the 4-step process outlined in the logical design
    - Must determine the next step in the workflow
    - Should check retry count and handle limit exceeded scenarios
    - Should execute the next step by setting current_step and sending message
    - Should coordinate all agent interactions and workflow transitions
    - Should manage workflow state and progression
    */
    
    // Log the beginning of orchestrator execution with current step using safe state access
    LOG_INFO(f"Orchestrator starting execution. Current step: {state.get('current_step', 'unknown')}")
    
    // Call determine_next_step function to determine next step
    state = determine_next_step(state)
    
    // Call check_retry_limit function to check retry limits
    state = check_retry_limit(state)
    
    // Call execute_next_step function to execute the next step
    state = execute_next_step(state)
    
    // Log successful completion with next step using safe state access
    LOG_INFO(f"Orchestrator completed successfully. Next step: {state.get('next_step', 'unknown')}")
    
    // Return the updated state
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Controls the entire multi-agent workflow by coordinating the 4-step process and managing workflow state transitions.

**State Management**: Reads and updates state throughout the workflow process. Coordinates state transitions between different workflow steps.

**Communication Patterns**:
- **Workflow Coordination**: Coordinates all agent interactions and workflow transitions
- **State Management**: Manages workflow state and progression

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: 
- @track: Opik tracking decorator for observability and tracing

**Logging**:
- Append logging (INFO) at the beginning of execution with current step
- Append logging (INFO) at the end of successful completion with next step

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Orchestrator Routing

**Component name**: route_from_orchestrator

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Route the state to the appropriate agent based on the current step
- **Responsibilities**: 
  - Determines which agent should receive the state based on current_step
  - Maps current_step values to appropriate agent names
  - Handles routing for all agent types (planner, researcher, expert, critic, finalizer)
  - Provides conditional routing logic for workflow execution
  - Validates current_step and raises error for invalid steps

**Component interface**:
- **Inputs**:
  - state: GraphState // The current state of the graph
- **Outputs**:
  - str // The name of the agent to route to
- **Validations**:
  - Handled by current_step validation logic

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Check if current_step is "planner" using dictionary access
2. If planner, return "planner"
3. Check if current_step is "researcher" using elif
4. If researcher, return "researcher"
5. Check if current_step is "expert" using elif
6. If expert, return "expert"
7. Check if current_step is "critic_planner" using elif
8. If critic_planner, return "critic"
9. Check if current_step is "critic_researcher" using elif
10. If critic_researcher, return "critic"
11. Check if current_step is "critic_expert" using elif
12. If critic_expert, return "critic"
13. Check if current_step is "finalizer" using elif
14. If finalizer, return "finalizer"
15. If current_step is invalid, raise ValueError with error message using dictionary access

**Pseudocode**:
```
FUNCTION route_from_orchestrator(state: GraphState) -> str
    /*
    Purpose: Route the state to the appropriate agent based on the current step
    
    BEHAVIOR:
    - Accepts: state (GraphState) - The current state of the graph
    - Produces: str - The name of the agent to route to
    - Handles: Conditional routing logic for workflow execution
    
    IMPLEMENTATION NOTES:
    - Should determine which agent should receive the state based on current_step
    - Must map current_step values to appropriate agent names
    - Should handle routing for all agent types (planner, researcher, expert, critic, finalizer)
    - Should provide conditional routing logic for workflow execution
    - Should validate current_step and raise error for invalid steps
    */
    
    // Check if current_step is "planner" using dictionary access
    IF state["current_step"] = "planner" THEN
        // If planner, return "planner"
        RETURN "planner"
    // Check if current_step is "researcher" using elif
    ELSE IF state["current_step"] = "researcher" THEN
        // If researcher, return "researcher"
        RETURN "researcher"
    // Check if current_step is "expert" using elif
    ELSE IF state["current_step"] = "expert" THEN
        // If expert, return "expert"
        RETURN "expert"
    // Check if current_step is "critic_planner" using elif
    ELSE IF state["current_step"] = "critic_planner" THEN
        // If critic_planner, return "critic"
        RETURN "critic"
    // Check if current_step is "critic_researcher" using elif
    ELSE IF state["current_step"] = "critic_researcher" THEN
        // If critic_researcher, return "critic"
        RETURN "critic"
    // Check if current_step is "critic_expert" using elif
    ELSE IF state["current_step"] = "critic_expert" THEN
        // If critic_expert, return "critic"
        RETURN "critic"
    // Check if current_step is "finalizer" using elif
    ELSE IF state["current_step"] = "finalizer" THEN
        // If finalizer, return "finalizer"
        RETURN "finalizer"
    ELSE
        // If current_step is invalid, raise ValueError with error message using dictionary access
        RAISE ValueError(f"Invalid current step: {state['current_step']}")
    END IF
    
END FUNCTION
```

**Workflow Control**: Controls workflow routing by determining which agent should receive the state based on current_step.

**State Management**: Reads current_step from state to determine routing destination. Does not modify state, only reads for routing decision.

**Communication Patterns**: None. This component does not communicate, rather it determines routing destination

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- Raises ValueError if current_step is invalid
- Error message includes the invalid current step for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Planner Agent Factory

**Component name**: create_planner_agent

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create a planner agent function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a planner agent
  - Injects configuration and LLM dependencies into the agent function
  - Handles LLM invocation with system prompt and message history
  - Validates LLM response against output schema
  - Updates state with research_steps and expert_steps
  - Composes and sends response message to orchestrator
  - Provides planning capabilities for workflow execution

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompt and output schema
  - llm_planner: ChatOpenAI // The LLM instance for planner operations
- **Outputs**:
  - Callable[[GraphState], GraphState] // The planner agent function
- **Validations**:
  - Handled by validate_llm_response function

**Direct Dependencies with Other Components**:
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

**Internal Logic**:
1. Define inner function planner_agent that takes GraphState as parameter
2. Log the beginning of planner execution
3. Create system prompt as list containing SystemMessage with config.system_prompt content
4. Get agent conversation history using get_agent_conversation function
5. Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
6. Invoke LLM with system prompt concatenated with message history
7. Validate response using validate_llm_response function with config.output_schema.keys() and "planner" component name
8. Update state["research_steps"] with response["research_steps"] using dictionary assignment
9. Update state["expert_steps"] with response["expert_steps"] using dictionary assignment
10. Compose agent message using compose_agent_message function with sender="planner", receiver="orchestrator", type="response", and formatted content string containing research steps and expert steps
11. Send message using send_message function and assign returned state
12. Log successful completion
13. Return the updated state
14. Return the inner planner_agent function

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langchain.schema import SystemMessage
// from langchain_openai import ChatOpenAI

FUNCTION create_planner_agent(config: AgentConfig, llm_planner: ChatOpenAI) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create a planner agent function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing system prompt and output schema
    - Accepts: llm_planner (ChatOpenAI) - The LLM instance for planner operations
    - Produces: Callable[[GraphState], GraphState] - The planner agent function
    - Handles: LLM invocation with system prompt and message history
    
    DEPENDENCIES:
    - get_agent_conversation: Retrieves agent conversation history
    - convert_agent_messages_to_langchain: Converts agent messages to LangChain format
    - validate_llm_response: Validates LLM response against output schema
    - compose_agent_message: Composes agent messages
    - send_message: Sends agent messages
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - llm_planner: ChatOpenAI - LLM instance passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create a factory function that returns a planner agent
    - Must inject configuration and LLM dependencies into the agent function
    - Should handle LLM invocation with system prompt and message history
    - Must validate LLM response against output schema
    - Should update state with research_steps and expert_steps
    - Must compose and send response message to orchestrator
    - Should provide planning capabilities for workflow execution
    */
    
    // Define inner function planner_agent that takes GraphState as parameter
    FUNCTION planner_agent(state: GraphState) -> GraphState
        // Log the beginning of planner execution
        LOG_INFO("Planner starting execution")
        
        // Create system prompt as list containing SystemMessage with config.system_prompt content
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        
        // Get agent conversation history using get_agent_conversation function
        message_history = get_agent_conversation(state, "planner")
        
        // Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
        message_in = convert_agent_messages_to_langchain(message_history)
        
        // Invoke LLM with system prompt concatenated with message history
        response = llm_planner.invoke(sys_prompt + message_in)
        
        // Validate response using validate_llm_response function with config.output_schema.keys() and "planner" component name
        response = validate_llm_response(response, config.output_schema.keys(), "planner")
        
        // Update state["research_steps"] with response["research_steps"] using dictionary assignment
        state["research_steps"] = response["research_steps"]
        
        // Update state["expert_steps"] with response["expert_steps"] using dictionary assignment
        state["expert_steps"] = response["expert_steps"]
        
        // Compose agent message using compose_agent_message function with sender="planner", receiver="orchestrator", type="response", and formatted content string containing research steps and expert steps
        agent_message = compose_agent_message(
            sender= "planner",
            receiver= "orchestrator",
            type= "response",
            content= f"Planner complete. Research steps: {response['research_steps']}, Expert steps: {response['expert_steps']}",   
        )
        
        // Send message using send_message function and assign returned state
        state = send_message(state, agent_message)
        
        // Log successful completion
        LOG_INFO("Planner completed successfully")
        
        // Return the updated state
        RETURN state
    END FUNCTION
    
    // Return the inner planner_agent function
    RETURN planner_agent
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Reads message history from state and updates research_steps and expert_steps fields. Sends response message through send_message function.

**Communication Patterns**:
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with planning results
- **LLM Integration**: Communicates with LLM for planning operations

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for planner operations

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- llm_planner: ChatOpenAI - LLM instance passed from outer scope

**Decorators**: None

**Logging**:
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### Researcher Agent Factory

**Component name**: create_researcher_agent

**Component type**: function

**Component purpose and responsibilities**:
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

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing output schema
  - compiled_researcher_graph: Callable // The compiled researcher subgraph function
- **Outputs**:
  - Callable[[GraphState], GraphState] // The researcher agent function
- **Validations**:
  - Handled by validate_llm_response function

**Direct Dependencies with Other Components**:
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

**Internal Logic**:
1. Define inner function researcher_agent that takes GraphState as parameter
2. Log the beginning of researcher execution
3. Get current research index from state using dictionary access
4. Get agent conversation history using get_agent_conversation function with step_id = current research index
5. Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
6. Check if ResearcherState exists for current index
7. If ResearcherState doesn't exist:
   - Create new ResearcherState with messages, step_index, and result=None
8. If ResearcherState exists:
   - Get existing ResearcherState from state
   - Append only the latest message to ResearcherState messages
9. Execute research using compiled_researcher_graph.invoke with ResearcherState
10. Validate response using validate_llm_response function with researcher_state["messages"][-1].content, config.output_schema.keys(), and step-specific component name
11. Store response result in ResearcherState using dictionary access
12. Update ResearcherState in state using dictionary assignment
13. Store research results in state:
    - If research_results list length <= current index, append result
    - Otherwise, update result at current index
14. Compose agent message using compose_agent_message function with sender="researcher", receiver="orchestrator", type="response", step_id=current_research_index, and formatted content string containing research completion status
15. Send message using send_message function and assign returned state
16. Log successful completion
17. Return the updated state
18. Return the inner researcher_agent function

**Pseudocode**:
```
FUNCTION create_researcher_agent(config: AgentConfig, compiled_researcher_graph: Callable) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create a researcher agent function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing output schema
    - Accepts: compiled_researcher_graph (Callable) - The compiled researcher subgraph function
    - Produces: Callable[[GraphState], GraphState] - The researcher agent function
    - Handles: Researcher state management for individual research steps
    
    DEPENDENCIES:
    - get_agent_conversation: Retrieves agent conversation history
    - convert_agent_messages_to_langchain: Converts agent messages to LangChain format
    - validate_llm_response: Validates LLM response against output schema
    - compose_agent_message: Composes agent messages
    - send_message: Sends agent messages
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - compiled_researcher_graph: Callable - Compiled researcher subgraph passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create a factory function that returns a researcher agent
    - Must inject configuration and compiled researcher graph dependencies
    - Should handle researcher state management for individual research steps
    - Must execute research using compiled researcher subgraph
    - Should validate LLM response against output schema
    - Must update state with research results and researcher states
    - Should compose and send response message to orchestrator
    - Must provide research capabilities for workflow execution
    */
    
    // Define inner function researcher_agent that takes GraphState as parameter
    FUNCTION researcher_agent(state: GraphState) -> GraphState
        // Log the beginning of researcher execution
        LOG_INFO("Researcher starting execution")
        
        // Get current research index from state using dictionary access
        idx = state["current_research_index"]
        
        // Get agent conversation history using get_agent_conversation function with step_id = current research index
        message_history = get_agent_conversation(state, "researcher", step_id=idx)
        
        // Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
        message_in = convert_agent_messages_to_langchain(message_history)
        
        // Get or create ResearcherState for this step
        IF idx NOT IN state["researcher_states"] THEN
            // If ResearcherState doesn't exist:
            // Create new ResearcherState with messages, step_index, and result=None
            researcher_state = ResearcherState(
                messages=message_in,
                step_index=idx,
                result=None
            )
        ELSE
            // If ResearcherState exists:
            // Get existing ResearcherState from state
            researcher_state = state["researcher_states"][idx]
            // Append only the latest message to ResearcherState messages
            researcher_state["messages"].append(message_in[-1])
        END IF
        
        // Execute research using compiled_researcher_graph.invoke with ResearcherState
        researcher_state = compiled_researcher_graph.invoke(researcher_state)
        
        // Validate response using validate_llm_response function with researcher_state["messages"][-1].content, config.output_schema.keys(), and step-specific component name
        response = validate_llm_response(researcher_state["messages"][-1].content, config.output_schema.keys(), f"researcher step {state['current_research_index']}")
        
        // Store response in ResearcherState in case of text JSON response
        researcher_state["result"] = response["result"]
        
        // Update ResearcherState in state using dictionary assignment
        state["researcher_states"][idx] = researcher_state
        
        // Store research results in state:
        IF LENGTH(state["research_results"]) <= idx THEN
            // If research_results list length <= current index, append result
            state["research_results"].append(response["result"])
        ELSE
            // Otherwise, update result at current index
            state["research_results"][idx] = response["result"]
        END IF
        
        // Send response to orchestrator
        agent_message = compose_agent_message(
            sender= "researcher",
            receiver= "orchestrator",
            type= "response",
            content= f"Researcher complete for step {state['current_research_index']}",
            step_id= state["current_research_index"],
        )
        
        // Send message using send_message function and assign returned state
        state = send_message(state, agent_message)
        
        // Log successful completion
        LOG_INFO("Researcher completed successfully")
        
        // Return the updated state
        RETURN state
    END FUNCTION
    
    // Return the inner researcher_agent function
    RETURN researcher_agent
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Reads current_research_index and manages researcher_states and research_results fields. Creates and updates ResearcherState for individual research steps. Sends response message through send_message function.

**Communication Patterns**:
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with research completion status
- **Subgraph Integration**: Communicates with compiled researcher subgraph

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- compiled_researcher_graph: Callable - Compiled researcher subgraph passed from outer scope

**Decorators**: None

**Logging**:
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### Expert Agent Factory

**Component name**: create_expert_agent

**Component type**: function

**Component purpose and responsibilities**:
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

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing output schema
  - compiled_expert_graph: Callable // The compiled expert subgraph function
- **Outputs**:
  - Callable[[GraphState], GraphState] // The expert agent function
- **Validations**:
  - Handled by validate_llm_response function

**Direct Dependencies with Other Components**:
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

**Internal Logic**:
1. Define inner function expert_agent that takes GraphState as parameter
2. Log the beginning of expert execution
3. Get agent conversation history using get_agent_conversation function
4. Convert agent messages to LangChain format and take only the last message as a list
5. Get expert_state from state using dictionary access
6. Check if expert_state is None
7. If expert_state is None:
   - Create new ExpertState with messages, question, research_steps, research_results, and empty expert fields
8. If expert_state exists:
   - Extend expert_state messages with new message_in using extend method
9. Execute expert reasoning using compiled_expert_graph.invoke with expert_state
10. Validate response using validate_llm_response function with expert_state["messages"][-1].content, config.output_schema.keys(), and "expert" component name
11. Store response expert_answer and expert_reasoning in expert_state using dictionary access
12. Update expert_state in state using dictionary assignment
13. Store expert_answer and expert_reasoning in state using dictionary assignment
14. Compose agent message using compose_agent_message function with sender="expert", receiver="orchestrator", type="response", and formatted content string containing expert answer and reasoning
15. Send message using send_message function and assign returned state
16. Log successful completion
17. Return the updated state
18. Return the inner expert_agent function

**Pseudocode**:
```
FUNCTION create_expert_agent(config: AgentConfig, compiled_expert_graph: Callable) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create an expert agent function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing output schema
    - Accepts: compiled_expert_graph (Callable) - The compiled expert subgraph function
    - Produces: Callable[[GraphState], GraphState] - The expert agent function
    - Handles: Expert state management for reasoning operations
    
    DEPENDENCIES:
    - get_agent_conversation: Retrieves agent conversation history
    - convert_agent_messages_to_langchain: Converts agent messages to LangChain format
    - validate_llm_response: Validates LLM response against output schema
    - compose_agent_message: Composes agent messages
    - send_message: Sends agent messages
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - compiled_expert_graph: Callable - Compiled expert subgraph passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create a factory function that returns an expert agent
    - Must inject configuration and compiled expert graph dependencies
    - Should handle expert state management for reasoning operations
    - Must execute expert reasoning using compiled expert subgraph
    - Should validate LLM response against output schema
    - Must update state with expert answer and reasoning
    - Should compose and send response message to orchestrator
    - Must provide expert reasoning capabilities for workflow execution
    */
    
    // Define inner function expert_agent that takes GraphState as parameter
    FUNCTION expert_agent(state: GraphState) -> GraphState
        // Log the beginning of expert execution
        LOG_INFO("Expert starting execution")
        
        // Get agent conversation history using get_agent_conversation function
        message_history = get_agent_conversation(state, "expert")
        
        // Convert agent messages to LangChain format and take only the last message as a list
        message_in = [convert_agent_messages_to_langchain(message_history)[-1]]
        
        // Get expert_state from state using dictionary access
        expert_state = state["expert_state"]
        
        // Check if expert_state is None
        IF expert_state IS None THEN
            // If expert_state is None:
            // Create new ExpertState with messages, question, research_steps, research_results, and empty expert fields
            expert_state = ExpertState(
                messages=message_in,
                question=state["question"],
                research_steps=state["research_steps"],
                research_results=state["research_results"],
                expert_answer="",
                expert_reasoning="",
            )
        ELSE
            // If expert_state exists:
            // Extend expert_state messages with new message_in using extend method
            expert_state["messages"].extend(message_in)
        END IF
        
        // Execute expert reasoning using compiled_expert_graph.invoke with expert_state
        expert_state = compiled_expert_graph.invoke(expert_state)
        
        // Validate response using validate_llm_response function with expert_state["messages"][-1].content, config.output_schema.keys(), and "expert" component name
        response = validate_llm_response(expert_state["messages"][-1].content, config.output_schema.keys(), "expert")
        
        // Store response expert_answer and expert_reasoning in expert_state using dictionary access
        expert_state["expert_answer"] = response["expert_answer"]
        expert_state["expert_reasoning"] = response["reasoning_trace"]
        
        // Update expert_state in state using dictionary assignment
        state["expert_state"] = expert_state
        
        // Store expert_answer and expert_reasoning in state using dictionary assignment
        state["expert_answer"] = response["expert_answer"]
        state["expert_reasoning"] = response["reasoning_trace"]
        
        // Compose agent message using compose_agent_message function with sender="expert", receiver="orchestrator", type="response", and formatted content string containing expert answer and reasoning
        agent_message = compose_agent_message(
            sender= "expert",
            receiver= "orchestrator",
            type= "response",
            content= f"Expert complete. Answer: {expert_state['expert_answer']}, Reasoning: {expert_state['expert_reasoning']}",
        )
        
        // Send message using send_message function and assign returned state
        state = send_message(state, agent_message)
        
        // Log successful completion
        LOG_INFO("Expert completed successfully")
        
        // Return the updated state
        RETURN state
    END FUNCTION
    
    // Return the inner expert_agent function
    RETURN expert_agent
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Reads expert_state from state and manages expert_answer and expert_reasoning fields. Creates and updates ExpertState for reasoning operations. Sends response message through send_message function.

**Communication Patterns**:
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with expert answer and reasoning
- **Subgraph Integration**: Communicates with compiled expert subgraph

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- compiled_expert_graph: Callable - Compiled expert subgraph passed from outer scope

**Decorators**: None

**Logging**:
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### Critic Agent Factory

**Component name**: create_critic_agent

**Component type**: function

**Component purpose and responsibilities**:
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

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompts and output schema
  - llm_critic: ChatOpenAI // The LLM instance for critic operations
- **Outputs**:
  - Callable[[GraphState], GraphState] // The critic agent function
- **Validations**:
  - Handled by validate_llm_response function

**Direct Dependencies with Other Components**:
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

**Internal Logic**:
1. Define inner function critic_agent that takes GraphState as parameter
2. Log the beginning of critic execution with current step information
3. Determine which critic to run based on current_step
4. If current_step is "critic_planner":
   - Get critic_prompt from config.system_prompt["critic_planner"]
5. If current_step is "critic_researcher":
   - Get critic_prompt from config.system_prompt["critic_researcher"]
6. If current_step is "critic_expert":
   - Get critic_prompt from config.system_prompt["critic_expert"]
7. If current_step is invalid, raise RuntimeError
8. Create system prompt as list containing SystemMessage with critic_prompt content
9. Get agent conversation history using get_agent_conversation function with current_step
10. Convert agent messages to LangChain format and take only the last message as a list
11. Invoke LLM with system prompt concatenated with message history
12. Validate response using validate_llm_response function with config.output_schema.keys() and "critic" component name
13. Store critic decision and feedback based on current step:
    - If critic_planner: store in critic_planner_decision and critic_planner_feedback
    - If critic_researcher: store in critic_researcher_decision and critic_researcher_feedback
    - If critic_expert: store in critic_expert_decision and critic_expert_feedback
14. Compose agent message using compose_agent_message function with sender="critic", receiver="orchestrator", type="response", and formatted content string containing decision and feedback
15. Send message using send_message function and assign returned state
16. Log successful completion
17. Return the updated state
18. Return the inner critic_agent function

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langchain.schema import SystemMessage
// from langchain_openai import ChatOpenAI

FUNCTION create_critic_agent(config: AgentConfig, llm_critic: ChatOpenAI) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create a critic agent function with the given prompts for different critic types
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing system prompts and output schema
    - Accepts: llm_critic (ChatOpenAI) - The LLM instance for critic operations
    - Produces: Callable[[GraphState], GraphState] - The critic agent function
    - Handles: Different critic types based on current_step
    
    DEPENDENCIES:
    - get_agent_conversation: Retrieves agent conversation history
    - convert_agent_messages_to_langchain: Converts agent messages to LangChain format
    - validate_llm_response: Validates LLM response against output schema
    - compose_agent_message: Composes agent messages
    - send_message: Sends agent messages
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - llm_critic: ChatOpenAI - LLM instance passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create a factory function that returns a critic agent
    - Must inject configuration and LLM dependencies into the agent function
    - Should handle different critic types based on current_step (critic_planner, critic_researcher, critic_expert)
    - Must select appropriate system prompt based on critic type
    - Should handle LLM invocation with system prompt and message history
    - Must validate LLM response against output schema
    - Should update state with critic decisions and feedback
    - Must compose and send response message to orchestrator
    - Should provide quality assessment capabilities for workflow execution
    */
    
    // Define inner function critic_agent that takes GraphState as parameter
    FUNCTION critic_agent(state: GraphState) -> GraphState
        // Log the beginning of critic execution with current step information
        LOG_INFO(f"Critic starting execution - {state['current_step']}")
        
        // Determine which critic to run and get the appropriate prompt
        IF state["current_step"] = "critic_planner" THEN
            // Get critic_prompt from config.system_prompt["critic_planner"]
            critic_prompt = config.system_prompt["critic_planner"]
        // If current_step is "critic_researcher":
        ELSE IF state["current_step"] = "critic_researcher" THEN
            // Get critic_prompt from config.system_prompt["critic_researcher"]
            critic_prompt = config.system_prompt["critic_researcher"]
        // If current_step is "critic_expert":
        ELSE IF state["current_step"] = "critic_expert" THEN
            // Get critic_prompt from config.system_prompt["critic_expert"]
            critic_prompt = config.system_prompt["critic_expert"]
        // If current_step is invalid, raise RuntimeError
        ELSE
            RAISE RuntimeError(f"Invalid critic step: {state['current_step']}")
        END IF
        
        // Create system prompt as list containing SystemMessage with critic_prompt content
        sys_prompt = [SystemMessage(content=critic_prompt)]
        
        // Get agent conversation history using get_agent_conversation function with current_step
        message_history = get_agent_conversation(state, state["current_step"])
        
        // Convert agent messages to LangChain format and take only the last message as a list
        message_in = [convert_agent_messages_to_langchain(message_history)[-1]]
        
        // Invoke LLM with system prompt concatenated with message history
        response = llm_critic.invoke(sys_prompt + message_in)
        
        // Validate response using validate_llm_response function with config.output_schema.keys() and "critic" component name
        response = validate_llm_response(response, config.output_schema.keys(), "critic")
        
        // Store critic decision and feedback based on current step
        IF state["current_step"] = "critic_planner" THEN
            // If critic_planner: store in critic_planner_decision and critic_planner_feedback
            state["critic_planner_decision"] = response["decision"]
            state["critic_planner_feedback"] = response["feedback"]
        ELSE IF state["current_step"] = "critic_researcher" THEN
            // If critic_researcher: store in critic_researcher_decision and critic_researcher_feedback
            state["critic_researcher_decision"] = response["decision"]
            state["critic_researcher_feedback"] = response["feedback"]
        ELSE IF state["current_step"] = "critic_expert" THEN
            // If critic_expert: store in critic_expert_decision and critic_expert_feedback
            state["critic_expert_decision"] = response["decision"]
            state["critic_expert_feedback"] = response["feedback"]
        END IF
        
        // Compose agent message using compose_agent_message function with sender="critic", receiver="orchestrator", type="response", and formatted content string containing decision and feedback
        message = compose_agent_message(
            sender= "critic",
            receiver= "orchestrator",
            type= "response",
            content= f"Critic complete. Decision: {response['decision']}, Feedback: {response['feedback']}",
        )
        
        // Send message using send_message function and assign returned state
        state = send_message(state, message)
        
        // Log successful completion
        LOG_INFO("Critic completed successfully")
        
        // Return the updated state
        RETURN state
    END FUNCTION
    
    // Return the inner critic_agent function
    RETURN critic_agent
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Reads current_step from state and updates critic decision and feedback fields based on critic type. Sends response message through send_message function.

**Communication Patterns**:
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with critic decision and feedback
- **LLM Integration**: Communicates with LLM for quality assessment operations

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for critic operations

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- llm_critic: ChatOpenAI - LLM instance passed from outer scope

**Decorators**: None

**Logging**:
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

**Error Handling**:
- Raises RuntimeError if current_step is invalid for critic operations
- Error message includes the invalid current step for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Finalizer Agent Factory

**Component name**: create_finalizer_agent

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create a finalizer agent function with the given prompt and LLM
- **Responsibilities**: 
  - Creates a factory function that returns a finalizer agent
  - Injects configuration and LLM dependencies into the agent function
  - Handles LLM invocation with system prompt and message history
  - Validates LLM response against output schema
  - Updates state with final answer and reasoning trace
  - Composes and sends response message to orchestrator
  - Provides final answer generation capabilities for workflow execution

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompt and output schema
  - llm_finalizer: ChatOpenAI // The LLM instance for finalizer operations
- **Outputs**:
  - Callable[[GraphState], GraphState] // The finalizer agent function
- **Validations**:
  - Handled by validate_llm_response function

**Direct Dependencies with Other Components**:
- get_agent_conversation function
- convert_agent_messages_to_langchain function
- validate_llm_response function
- compose_agent_message function
- send_message function

**Internal Logic**:
1. Define inner function finalizer_agent that takes GraphState as parameter
2. Log the beginning of finalizer execution
3. Create system prompt as list containing SystemMessage with config.system_prompt content
4. Get agent conversation history using get_agent_conversation function
5. Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
6. Invoke LLM with system prompt concatenated with message history
7. Validate response using validate_llm_response function with config.output_schema.keys() and "finalizer" component name
8. Update state["final_answer"] with response["final_answer"]
9. Update state["final_reasoning_trace"] with response["final_reasoning_trace"]
10. Compose agent message using compose_agent_message function with sender="finalizer", receiver="orchestrator", type="response", and formatted content string containing final answer and reasoning trace
11. Send message using send_message function and assign returned state
12. Log successful completion
13. Return the updated state
14. Return the inner finalizer_agent function

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langchain.schema import SystemMessage
// from langchain_openai import ChatOpenAI

FUNCTION create_finalizer_agent(config: AgentConfig, llm_finalizer: ChatOpenAI) -> Callable[[GraphState], GraphState]
    /*
    Purpose: Create a finalizer agent function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing system prompt and output schema
    - Accepts: llm_finalizer (ChatOpenAI) - The LLM instance for finalizer operations
    - Produces: Callable[[GraphState], GraphState] - The finalizer agent function
    - Handles: LLM invocation with system prompt and message history
    
    DEPENDENCIES:
    - get_agent_conversation: Retrieves agent conversation history
    - convert_agent_messages_to_langchain: Converts agent messages to LangChain format
    - validate_llm_response: Validates LLM response against output schema
    - compose_agent_message: Composes agent messages
    - send_message: Sends agent messages
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - llm_finalizer: ChatOpenAI - LLM instance passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create a factory function that returns a finalizer agent
    - Must inject configuration and LLM dependencies into the agent function
    - Should handle LLM invocation with system prompt and message history
    - Must validate LLM response against output schema
    - Should update state with final answer and reasoning trace
    - Must compose and send response message to orchestrator
    - Should provide final answer generation capabilities for workflow execution
    */
    
    // Define inner function finalizer_agent that takes GraphState as parameter
    FUNCTION finalizer_agent(state: GraphState) -> GraphState
        // Log the beginning of finalizer execution
        LOG_INFO("Finalizer starting execution")
        
        // Create system prompt as list containing SystemMessage with config.system_prompt content
        sys_prompt = [SystemMessage(content=config.system_prompt)]
        
        // Get agent conversation history using get_agent_conversation function
        message_history = get_agent_conversation(state, "finalizer")
        
        // Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
        message_in = convert_agent_messages_to_langchain(message_history)
        
        // Invoke LLM with system prompt concatenated with message history
        response = llm_finalizer.invoke(sys_prompt + message_in)
        
        // Validate response using validate_llm_response function with config.output_schema.keys() and "finalizer" component name
        response = validate_llm_response(response, config.output_schema.keys(), "finalizer")
        
        // Update state["final_answer"] with response["final_answer"]
        state["final_answer"] = response["final_answer"]
        
        // Update state["final_reasoning_trace"] with response["final_reasoning_trace"]
        state["final_reasoning_trace"] = response["final_reasoning_trace"]
        
        // Compose agent message using compose_agent_message function with sender="finalizer", receiver="orchestrator", type="response", and formatted content string containing final answer and reasoning trace
        message = compose_agent_message(
            sender= "finalizer",
            receiver= "orchestrator",
            type= "response",
            content= f"Finalizer complete. The final answer is:\n{response['final_answer']}\n\n## The final reasoning trace is:\n{response['final_reasoning_trace']}",
        )
        
        // Send message using send_message function and assign returned state
        state = send_message(state, message)
        
        // Log successful completion
        LOG_INFO("Finalizer completed successfully")
        
        // Return the updated state
        RETURN state
    END FUNCTION
    
    // Return the inner finalizer_agent function
    RETURN finalizer_agent
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Reads message history from state and updates final_answer and final_reasoning_trace fields. Sends response message through send_message function.

**Communication Patterns**:
- **Agent Communication**: Sends response message to orchestrator
- **Message Composition**: Creates response message with final answer and reasoning trace
- **LLM Integration**: Communicates with LLM for final answer generation operations

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **ChatOpenAI**: LLM interface for finalizer operations

**Global variables**: None

**Closed-over variables**:
- config: AgentConfig - Configuration passed from outer scope
- llm_finalizer: ChatOpenAI - LLM instance passed from outer scope

**Decorators**: None

**Logging**:
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### OpenAI LLM Factory

**Component name**: openai_llm_factory

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Create an OpenAI LLM with the given model and temperature, with conditional structured output and tool binding
- **Responsibilities**: 
  - Creates ChatOpenAI instance with specified model and temperature
  - Binds tools to LLM if provided
  - Configures structured output with JSON mode only for non-researcher/expert agents
  - Provides factory pattern for OpenAI LLM creation
  - Enables consistent LLM configuration across the system

**Component interface**:
- **Inputs**:
  - name: string // The agent name for conditional structured output logic
  - model: string // The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
  - temperature: float // The temperature setting for the LLM (0.0 to 2.0)
  - output_schema: dict = none // Optional structured output schema for JSON mode
  - tools: list = none // Optional list of tools to bind to the LLM
- **Outputs**:
  - ChatOpenAI // The configured OpenAI LLM instance
- **Validations**:
  - Handled by ChatOpenAI constructor validation
  - Temperature range validation handled by OpenAI API

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Create ChatOpenAI instance with provided model and temperature parameters
2. If tools are provided, bind them to the LLM using bind_tools method
3. If output_schema is provided and agent name is not "researcher" or "expert", configure structured output using json_mode method
4. Return the configured ChatOpenAI instance

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langchain_openai import ChatOpenAI

FUNCTION openai_llm_factory(name: string, model: string, temperature: float, output_schema: dict = none, tools: list = none) -> ChatOpenAI
    /*
    Purpose: Create an OpenAI LLM with the given model and temperature
    
    BEHAVIOR:
    - Accepts: name (string) - The agent name for conditional structured output logic
    - Accepts: model (string) - The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
    - Accepts: temperature (float) - The temperature setting for the LLM (0.0 to 2.0)
    - Accepts: output_schema (dict) - Optional structured output schema for JSON mode
    - Accepts: tools (list) - Optional list of tools to bind to the LLM
    - Produces: ChatOpenAI - The configured OpenAI LLM instance
    - Handles: LLM configuration with conditional structured output and tool binding
    
    EXTERNAL DEPENDENCIES:
    - LangChain ChatOpenAI: Library for OpenAI LLM interface
    - OpenAI API: External API for LLM access
    
    IMPLEMENTATION NOTES:
    - Should create ChatOpenAI instance with specified model and temperature
    - Must bind tools if provided
    - Should configure structured output only for non-researcher/expert agents
    - Must provide factory pattern for OpenAI LLM creation
    - Should enable consistent LLM configuration across the system
    */
    
    // Create ChatOpenAI instance with provided model and temperature parameters
    llm = ChatOpenAI(model=model, temperature=temperature)
    
    // If tools are provided, bind them to the LLM using bind_tools method
    IF tools IS NOT none THEN
        llm = llm.bind_tools(tools)
    END IF
    
    // If output_schema is provided and agent name is not "researcher" or "expert", configure structured output using json_mode method
    IF output_schema IS NOT none AND name NOT IN ("researcher", "expert") THEN
        llm = llm.with_structured_output(output_schema, method="json_mode")
    END IF
    
    // Return the configured ChatOpenAI instance
    RETURN llm
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it creates LLM instances

**External Dependencies**:
- **LangChain ChatOpenAI**: Library for OpenAI LLM interface
- **OpenAI API**: External API for LLM access

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

#### LLM Factory

**Component name**: llm_factory

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Get the appropriate LLM factory based on the provider
- **Responsibilities**: 
  - Routes to appropriate LLM factory based on provider configuration
  - Supports multiple LLM providers through factory pattern
  - Delegates LLM creation to provider-specific factories
  - Provides unified interface for LLM creation across different providers

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The configuration for the agent containing provider, model, temperature, and output_schema
  - tools: list = none // Optional list of tools to bind to the LLM
- **Outputs**:
  - ChatOpenAI // The LLM with structured output
- **Validations**:
  - Handled by provider validation logic
  - Provider-specific factory validation

**Direct Dependencies with Other Components**:
- openai_llm_factory function

**Internal Logic**:
1. Check if config.provider equals "openai"
2. If provider is "openai":
   - Call openai_llm_factory function with config.name, config.model, config.temperature, config.output_schema, and tools
   - Return the result from openai_llm_factory
3. If provider is not "openai":
   - Raise ValueError with invalid provider message

**Pseudocode**:
```
FUNCTION llm_factory(config: AgentConfig, tools: list = none) -> ChatOpenAI
    /*
    Purpose: Get the appropriate LLM factory based on the provider
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The configuration for the agent containing provider, model, temperature, and output_schema
    - Accepts: tools (list) - Optional list of tools to bind to the LLM
    - Produces: ChatOpenAI - The LLM with structured output
    - Handles: Provider routing and LLM factory delegation
    
    DEPENDENCIES:
    - openai_llm_factory: Creates OpenAI LLM instances with structured output
    
    IMPLEMENTATION NOTES:
    - Should route to appropriate LLM factory based on provider configuration
    - Must support multiple LLM providers through factory pattern
    - Should delegate LLM creation to provider-specific factories
    - Must provide unified interface for LLM creation across different providers
    - Should pass tools to provider-specific factories
    */
    
    // Check if config.provider equals "openai"
    IF config.provider = "openai" THEN
        // If provider is "openai":
        // Call openai_llm_factory function with config.name, config.model, config.temperature, config.output_schema, and tools
        llm = openai_llm_factory(config.name, config.model, config.temperature, config.output_schema, tools)
        // Return the result from openai_llm_factory
        RETURN llm
    ELSE
        // If provider is not "openai":
        // Raise ValueError with invalid provider message
        RAISE ValueError(f"Invalid provider: {config.provider}")
    END IF
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it routes to appropriate LLM factories

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**:
- Raises ValueError if provider is not "openai"
- Error message includes the invalid provider for debugging
- All other errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Multi-Agent Graph Factory

**Component name**: create_multi_agent_graph

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Factory function that creates and compiles a multi-agent graph with injected prompts
- **Responsibilities**: 
  - Creates LLM instances for all agents using factory pattern
  - Creates researcher and expert subgraphs with tools
  - Creates all agent functions with injected prompts and LLMs
  - Builds complete StateGraph with all nodes and edges
  - Compiles and returns the complete multi-agent workflow graph
  - Provides unified graph creation interface for multi-agent system

**Component interface**:
- **Inputs**:
  - agent_configs: dict[str, AgentConfig] // Dictionary containing all agent configurations
- **Outputs**:
  - Tuple[StateGraph, OpikTracer] // Compiled graph and OpikTracer ready for invocation
- **Validations**:
  - Handled by LangGraph StateGraph validation
  - Agent configuration validation handled by individual factory functions

**Direct Dependencies with Other Components**:
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

**Internal Logic**:
1. Define Agent Tools:
   - Get research tools using asyncio.run(get_research_tools())
   - Get expert tools using get_expert_tools()
2. Create LLMs dynamically:
   - Create llm_planner using llm_factory with planner config
   - Create llm_researcher using llm_factory with researcher config and research_tools
   - Create llm_expert using llm_factory with expert config and expert_tools
   - Create llm_critic using llm_factory with critic config
   - Create llm_finalizer using llm_factory with finalizer config
3. Create Researcher Subgraphs:
   - Create researcher node using create_researcher_llm_node with researcher config and llm_researcher
   - Create researcher graph using create_researcher_subgraph with researcher_node and research_tools
4. Create Expert Subgraphs:
   - Create expert node using create_expert_llm_node with expert config and llm_expert
   - Create expert graph using create_expert_subgraph with expert_node and expert_tools
5. Create agent functions with injected prompts and LLMs:
   - Create planner_agent using create_planner_agent
   - Create researcher_agent using create_researcher_agent
   - Create expert_agent using create_expert_agent
   - Create critic_agent using create_critic_agent
   - Create finalizer_agent using create_finalizer_agent
6. Create input interface with retry limit using create_input_interface with agent_configs
7. Build the graph:
   - Create StateGraph instance with GraphState
   - Add all nodes to the graph (input_interface, orchestrator, planner, researcher, expert, critic, finalizer)
8. Add edges to the graph:
   - Add edge from START to input_interface
   - Add edge from input_interface to orchestrator
   - Add edges from all agents to orchestrator
   - Add edge from finalizer to END
9. Add conditional edges from orchestrator using route_from_orchestrator function with mapping dictionary containing "planner", "researcher", "expert", "critic", and "finalizer" routes
10. Compile the graph using builder.compile()
11. Create the OpikTracer for LangGraph using OpikTracer(graph=app.get_graph(xray=True))
12. Return both the compiled graph and OpikTracer

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langgraph import StateGraph, START, END
// import asyncio

FUNCTION create_multi_agent_graph(agent_configs: dict[str, AgentConfig]) -> Tuple[StateGraph, OpikTracer]
    /*
    Purpose: Factory function that creates and compiles a multi-agent graph with injected prompts
    
    BEHAVIOR:
    - Accepts: agent_configs (dict[str, AgentConfig]) - Dictionary containing all agent configurations
    - Produces: Tuple[StateGraph, OpikTracer] - Compiled graph and OpikTracer ready for invocation
    - Handles: Complete multi-agent system graph creation and compilation
    
    DEPENDENCIES:
    - llm_factory: Creates LLM instances for all agents
    - get_research_tools: Provides research tools for researcher subgraph
    - get_expert_tools: Provides expert tools for expert subgraph
    - create_researcher_llm_node: Creates researcher LLM node
    - create_researcher_subgraph: Creates researcher subgraph
    - create_expert_llm_node: Creates expert LLM node
    - create_expert_subgraph: Creates expert subgraph
    - create_planner_agent: Creates planner agent function
    - create_researcher_agent: Creates researcher agent function
    - create_expert_agent: Creates expert agent function
    - create_critic_agent: Creates critic agent function
    - create_finalizer_agent: Creates finalizer agent function
    - create_input_interface: Creates input interface function
    - orchestrator: Creates orchestrator function
    - route_from_orchestrator: Creates routing function
    
    EXTERNAL DEPENDENCIES:
    - LangGraph StateGraph: Library for creating state-based graphs
    - LangGraph START/END: Library constants for graph start and end nodes
    - asyncio: Library for asynchronous operations
    
    IMPLEMENTATION NOTES:
    - Should create LLM instances for all agents using factory pattern
    - Must create researcher and expert subgraphs with tools
    - Should create all agent functions with injected prompts and LLMs
    - Must build complete StateGraph with all nodes and edges
    - Should compile and return the complete multi-agent workflow graph
    - Must provide unified graph creation interface for multi-agent system
    */
    
    // Define Agent Tools
    research_tools = asyncio.run(get_research_tools())
    expert_tools = get_expert_tools()

    // Create LLMs dynamically
    llm_planner = llm_factory(agent_configs["planner"])
    llm_researcher = llm_factory(agent_configs["researcher"], research_tools)
    llm_expert = llm_factory(agent_configs["expert"], expert_tools)
    llm_critic = llm_factory(agent_configs["critic"])
    llm_finalizer = llm_factory(agent_configs["finalizer"])   
   
    // Create Researcher Subgraphs    
    researcher_node = create_researcher_llm_node(agent_configs["researcher"], llm_researcher)
    researcher_graph = create_researcher_subgraph(researcher_node, research_tools)
    
    // Create Expert Subgraphs
    expert_node = create_expert_llm_node(agent_configs["expert"], llm_expert)
    expert_graph = create_expert_subgraph(expert_node, expert_tools)
    
    // Create agent functions with injected prompts and LLMs:
    // Create planner_agent using create_planner_agent
    planner_agent = create_planner_agent(agent_configs["planner"], llm_planner)
    // Create researcher_agent using create_researcher_agent
    researcher_agent = create_researcher_agent(agent_configs["researcher"], researcher_graph)
    // Create expert_agent using create_expert_agent
    expert_agent = create_expert_agent(agent_configs["expert"], expert_graph)
    // Create critic_agent using create_critic_agent
    critic_agent = create_critic_agent(agent_configs["critic"], llm_critic)
    // Create finalizer_agent using create_finalizer_agent
    finalizer_agent = create_finalizer_agent(agent_configs["finalizer"], llm_finalizer)
    
    // Create input interface with retry limit
    input_interface = create_input_interface(agent_configs)
    
    // Build the graph:
    // Create StateGraph instance with GraphState
    builder = StateGraph(GraphState)
    // Add all nodes to the graph (input_interface, orchestrator, planner, researcher, expert, critic, finalizer)
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
    
    // Add conditional edges from orchestrator using route_from_orchestrator function with mapping dictionary containing "planner", "researcher", "expert", "critic", and "finalizer" routes
    builder.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "planner": "planner",
            "researcher": "researcher",
            "expert": "expert",
            "critic": "critic",
            "finalizer": "finalizer"
        }
    )
    
    // Compile and return the graph
    app = builder.compile()

    // Create the OpikTracer for LangGraph
    opik_tracer = OpikTracer(graph=app.get_graph(xray=True))
    
    RETURN app, opik_tracer
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it creates graph structure

**External Dependencies**:
- **LangGraph StateGraph**: Library for creating state-based graphs
- **LangGraph START/END**: Library constants for graph start and end nodes
- **asyncio**: Library for asynchronous operations

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**: None. This component does not perform logging operations.

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

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
    WITH open(file_path, "r", encoding="utf-8") AS file DO
        // Read the entire file content
        content ← file.read()
        
        // Strip whitespace from the content
        cleaned_content ← content.strip()
        
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
        script_dir ← os.path.dirname(os.path.abspath(__file__))
        // Go up one level from src/ to the project root, then into prompts/baseline
        prompts_dir ← os.path.join(script_dir, "..", "prompts", "baseline")
        prompts_dir ← os.path.normpath(prompts_dir)
    END IF
    
    // Log the directory being used for loading prompts
    LOG_INFO(f"Loading prompts from directory: {prompts_dir}")
    
    // Define the mapping of agent names to prompt file names
    prompt_files ← {
        "planner": "planner_system_prompt.txt",
        "critic_planner": "critic_planner_system_prompt.txt",
        "researcher": "researcher_system_prompt.txt",
        "critic_researcher": "critic_researcher_system_prompt.txt",
        "expert": "expert_system_prompt.txt",
        "critic_expert": "critic_expert_system_prompt.txt",
        "finalizer": "finalizer_system_prompt.txt"
    }
    
    // Initialize empty prompts dictionary
    prompts ← {}
    
    // Iterate through each agent name and file name pair
    FOR EACH (agent_name, filename) IN prompt_files.items() DO
        // Construct the full file path for each prompt file
        file_path ← os.path.join(prompts_dir, filename)
        
        // Log debug information for each file being loaded
        LOG_DEBUG(f"Loading prompt for {agent_name} from: {file_path}")
        
        // Load the prompt using load_prompt_from_file function
        prompt_content ← load_prompt_from_file(file_path)
        
        // Store the loaded prompt in the prompts dictionary
        prompts[agent_name] ← prompt_content
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

#### Prompt File Loader

**Component name**: load_prompt_from_file

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Load a prompt from a text file and return its content as a string
- **Responsibilities**: 
  - Opens and reads text files with UTF-8 encoding
  - Strips whitespace from file content
  - Handles file not found errors gracefully
  - Handles general file reading errors
  - Logs successful file loading operations
  - Logs error conditions with detailed context
  - Returns cleaned prompt content for system use

**Component interface**:
- **Inputs**:
  - file_path: string // The path to the prompt file to load
- **Outputs**:
  - string // The content of the prompt file with whitespace stripped
- **Validations**:
  - Handled by Python file system validation
  - UTF-8 encoding validation handled by file opening

**Direct Dependencies with Other Components**: None

**Internal Logic**:
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

**Pseudocode**:
```
FUNCTION load_prompt_from_file(file_path: string) -> string
    /*
    Purpose: Load a prompt from a text file and return its content as a string
    
    BEHAVIOR:
    - Accepts: file_path (string) - The path to the prompt file to load
    - Produces: string - The content of the prompt file with whitespace stripped
    - Handles: File reading operations with error handling
    
    EXTERNAL DEPENDENCIES:
    - Python file system: Library for file reading operations
    - Python logging: Library for debug and error logging
    
    IMPLEMENTATION NOTES:
    - Should open and read text files with UTF-8 encoding
    - Must strip whitespace from file content
    - Should handle file not found errors gracefully
    - Must handle general file reading errors
    - Should log successful file loading operations
    - Must log error conditions with detailed context
    - Should return cleaned prompt content for system use
    */
    
    // Enter a try block to handle potential file reading errors
    TRY
        // Open the file specified by file_path parameter with UTF-8 encoding in read mode using "with" statement
        WITH open(file_path, 'r', encoding='utf-8') AS f:
            // Read the entire file content using f.read() method
            content = f.read()
        
        // Strip whitespace from the beginning and end of the content using strip() method
        cleaned_content = content.strip()
        
        // Log a debug message indicating successful prompt loading with the file path
        LOG_DEBUG(f"Successfully loaded prompt from: {file_path}")
        
        // Return the cleaned content string
        RETURN cleaned_content
        
    CATCH FileNotFoundError AS error
        // If FileNotFoundError occurs:
        // Log an error message with the file path that was not found
        LOG_ERROR(f"File not found: {file_path}")
        // Raise a new FileNotFoundError with the same message
        RAISE FileNotFoundError(f"File not found: {file_path}")
        
    CATCH Exception AS error
        // If any other Exception occurs:
        // Log an error message with the file path and the exception details
        LOG_ERROR(f"Error reading file {file_path}: {error}")
        // Raise a new Exception with the file path and exception details
        RAISE Exception(f"Error reading file {file_path}: {error}")
        
    END TRY
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file reading operations

**External Dependencies**:
- **Python file system**: Library for file reading operations
- **Python logging**: Library for debug and error logging

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (DEBUG) when prompt is successfully loaded
- Append logging (ERROR) if file is not found
- Append logging (ERROR) if any other file reading error occurs

**Error Handling**:
- Catches FileNotFoundError and re-raises with context
- Catches general Exception and re-raises with context
- Logs all error conditions before re-raising exceptions
- All errors and exceptions will be uncaught and bubble up the call stack
- This enables a global error handling design implemented in the entry point.

#### Baseline Prompts Loader

**Component name**: load_baseline_prompts

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Load all baseline prompts from the prompts/baseline directory
- **Responsibilities**: 
  - Automatically determines the correct prompts directory path if not provided
  - Loads all required prompt files for each agent type
  - Manages prompt file naming and organization
  - Coordinates loading of multiple prompt files
  - Logs loading progress and completion status
  - Returns a dictionary containing all agent prompts
  - Handles path resolution and normalization

**Component interface**:
- **Inputs**:
  - prompts_dir: string = None // Optional path to the prompts/baseline directory. If None, will automatically find the correct path.
- **Outputs**:
  - dict[str, str] // Dictionary containing all agent prompts with agent names as keys and prompt content as values
- **Validations**:
  - Handled by load_prompt_from_file function validation
  - Path existence validation handled by file system operations

**Direct Dependencies with Other Components**:
- load_prompt_from_file function

**Internal Logic**:
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

**Pseudocode**:
```
// REQUIRED IMPORTS:
// import os
// import logging

FUNCTION load_baseline_prompts(prompts_dir: string = None) -> dict[str, str]
    /*
    Purpose: Load all baseline prompts from the prompts/baseline directory
    
    BEHAVIOR:
    - Accepts: prompts_dir (string) - Optional path to the prompts/baseline directory. If None, will automatically find the correct path.
    - Produces: dict[str, str] - Dictionary containing all agent prompts with agent names as keys and prompt content as values
    - Handles: Automatic path resolution and multiple prompt file loading
    
    DEPENDENCIES:
    - load_prompt_from_file: Loads individual prompt files with error handling
    
    EXTERNAL DEPENDENCIES:
    - Python os.path: Library for path manipulation and directory operations
    - Python logging: Library for info and debug logging
    
    IMPLEMENTATION NOTES:
    - Should automatically determine the correct prompts directory path if not provided
    - Must load all required prompt files for each agent type
    - Should manage prompt file naming and organization
    - Must coordinate loading of multiple prompt files
    - Should log loading progress and completion status
    - Must return a dictionary containing all agent prompts
    - Should handle path resolution and normalization
    */
    
    // Check if prompts_dir parameter is None
    IF prompts_dir IS None THEN
        // If prompts_dir is None:
        // Get the directory of the current script using os.path.dirname(os.path.abspath(__file__))
        script_dir = os.path.dirname(os.path.abspath(__file__))
        // Construct the prompts directory path by going up one level from src/ to project root, then into prompts/baseline using os.path.join(script_dir, "..", "prompts", "baseline")
        prompts_dir = os.path.join(script_dir, "..", "prompts", "baseline")
        // Normalize the path using os.path.normpath(prompts_dir)
        prompts_dir = os.path.normpath(prompts_dir)
    END IF
    
    // Log an info message indicating the prompts directory being loaded from
    LOG_INFO(f"Loading prompts from directory: {prompts_dir}")
    
    // Define prompt_files dictionary with agent names as keys and filenames as values:
    prompt_files = {
        "planner": "planner_system_prompt.txt",
        "critic_planner": "critic_planner_system_prompt.txt",
        "researcher": "researcher_system_prompt.txt",
        "critic_researcher": "critic_researcher_system_prompt.txt",
        "expert": "expert_system_prompt.txt",
        "critic_expert": "critic_expert_system_prompt.txt",
        "finalizer": "finalizer_system_prompt.txt"
    }
    
    // Initialize empty prompts dictionary
    prompts = {}
    
    // Iterate through each agent_name and filename in prompt_files.items():
    FOR agent_name, filename IN prompt_files.items() DO
        // Construct the full file path using os.path.join(prompts_dir, filename)
        file_path = os.path.join(prompts_dir, filename)
        // Log a debug message indicating which agent prompt is being loaded and from which file path
        LOG_DEBUG(f"Loading {agent_name} prompt from: {file_path}")
        // Load the prompt content using load_prompt_from_file(file_path)
        prompt_content = load_prompt_from_file(file_path)
        // Store the loaded prompt in prompts dictionary with agent_name as key
        prompts[agent_name] = prompt_content
    END FOR
    
    // Log an info message indicating successful loading with the number of prompts loaded
    LOG_INFO(f"Successfully loaded {len(prompts)} prompts")
    
    // Return the prompts dictionary
    RETURN prompts
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it handles file loading operations

**External Dependencies**:
- **Python os.path**: Library for path manipulation and directory operations
- **Python logging**: Library for info and debug logging

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (INFO) when starting to load prompts from directory
- Append logging (DEBUG) for each individual prompt file being loaded
- Append logging (INFO) when successfully loaded all prompts with count

**Error Handling**: None. All errors and exceptions will be uncaught and bubble up the call stack. This enables a global error handling design implemented in the entry point.

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
                    LOG_ERROR(f"JSON parsing error in line: {error}")
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
