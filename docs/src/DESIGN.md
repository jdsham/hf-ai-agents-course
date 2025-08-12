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
    file_path: string = none // Optional field, contains the path to the file assosciated to the question if specified

    // Agent-to-Agent Communication
    agent_messages: list = []  // Inter-agent communication messages

    // Planner fields
    research_steps: list = []  // Planned research steps from planner
    expert_steps: list = []  // Planned expert steps from planner

    // Researcher fields
    research_results: list = []  // Results from research execution

    // Expert Fields
    expert_answer: string = ""  // Expert's final answer
    expert_reasoning: string = ""  // Expert's reasoning process

    // Finalizer fields
    final_answer: string // The Finalizer's final answer
    final_reasoning_trace: string // The Finalizer's reasoning trace

    // Critic fields
    critic_planner_decision: string = ""  // Critic decision for planner agent
    critic_planner_feedback: string = ""  // Critic feedback for planner agent
    critic_researcher_decision: string = ""  // Critic decision for researcher agent
    critic_researcher_feedback: string = ""  // Critic feedback for researcher agent
    critic_expert_decision: string = ""  // Critic decision for expert agent
    critic_expert_feedback: string = ""  // Critic feedback for expert agent

    // Workflow
    current_step: string [input, planner, critic_planner, researcher, critic_researcher, expert, critic_expert, finalizer] = "input"  // Current workflow step
    next_step: string [planner, critic_planner, researcher, critic_researcher, expert, critic_expert, finalizer, END] = "planner"  // Next workflow step
    retry_count: mapping[string, integer]  // Mapping of agent name (planner, researcher, or expert) to current retry counter for the specific agent
    retry_limit: mapping[string, integer]  // Mapping of agent name (planner, researcher, or expert) to retry limit for the specific agent
    current_research_step_id: integer = 0  // Current research step identifier
    
    // Subgraph state management
    researcher_states: mapping[integer, ResearcherState] = {}  // Research step states
    expert_state: ExpertState = none  // Expert subgraph state
    
    // Error handling
    error: string = ""  // Error message if any
    error_component: string = ""  // Component that failed
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
    messages: list // LangChain BaseMessage objects for conversation history
        // Implementation type: messages: Annotated[list[BaseMessage], operator.add]
    step_id: integer // Research step identifier
    results: any = none  // Results from research execution
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
    messages: list // LangChain BaseMessage objects for conversation history
        // Implementation type: messages: Annotated[list[BaseMessage], operator.add]
    question: string // The question from the main graph's GraphState
    research_steps: list // The researcher steps
    research_results: list // The research results corresponding to the research step
    expert_answer: string = ""  // Expert's calculated answer
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
    sender: string  // Source agent identifier
    receiver: string // Target agent identifier
    type: string [instruction, feedback, response] // Message type
    content: string // Message content and data
    step_id: integer = null  // Optional research step identifier
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
    name: string  // API keys for external services
    provider: string  // The LLM Provider, like openai or anthropic
    model: string  // LLM model
    temperature: float  // LLM temperature setting
    output_schemas: dict  // Agent output schema
    system_prompt: string | dict  // Agent system prompt or prompts (multiple prompts for critic only)
    retry_limits: object = {}  // Agent retry limits
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
1. Check if every key in output_schema_keys exists in the response dictionary. Could use Python's all() function in implementation.
2. Return True if all keys are present, False if any key is missing

**Pseudocode**:
```
FUNCTION validate_output_matches_json_schema(response: Any, output_schema_keys: list[string]) -> bool
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
    
    // Check if every key in output_schema_keys exists in the response dictionary
    validation_result ← all(key in response for key in output_schema_keys)
    
    // Return validation result
    RETURN validation_result
    
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
1. Call enforce_json_response function to ensure response is a dictionary
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
    
    // Enforce JSON response format
    validated_response ← enforce_json_response(response, component)
    
    // Validate response schema
    schema_valid ← validate_output_matches_json_schema(validated_response, expected_fields)
    
    // Check if schema validation failed
    IF NOT schema_valid THEN
        // Create error message with component context and field details
        error_msg ← f"Component {component} response missing expected fields. Expected: {expected_fields}, Actual: {validated_response}"
        
        // Raise KeyError with context
        RAISE KeyError(error_msg)
    END IF
    
    // Return the validated response dictionary
    RETURN validated_response
    
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
    current_timestamp ← get_current_timestamp()
    
    // Compose AgentMessage with all inputs and timestamp
    agent_message: AgentMessage ← {
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
2. Iterate through each message in the input messages list
3. For each message, check if the sender is "orchestrator"
4. If sender is "orchestrator", create a HumanMessage with the message content
5. If sender is not "orchestrator", create an AIMessage with the message content
6. Append the created message to the converted_messages list
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
    converted_messages ← []
    
    // Iterate through each message in the input messages list
    FOR EACH message IN messages DO
        // Check if the sender is "orchestrator"
        IF message.sender = "orchestrator" THEN
            // Create HumanMessage with the message content
            langchain_message ← HumanMessage(content=message.content)
        ELSE
            // Create AIMessage with the message content
            langchain_message ← AIMessage(content=message.content)
        END IF
        
        // Append the created message to the converted_messages list
        converted_messages ← converted_messages + [langchain_message]
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
2. Create YoutubeLoader instance with the provided URL and add_video_info=True
3. Load documents using the loader
4. Check if documents list is empty
5. If no documents found, log info and return "No transcript found" message
6. Extract transcript content from the first document's page_content
7. Extract metadata from the first document
8. Format video information string with title, author, and duration from metadata
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
    LOG_INFO(f"Starting YouTube transcript extraction for URL: {url}")
    
    // Create YoutubeLoader instance with the provided URL and add_video_info=True
    loader ← YoutubeLoader(url=url, add_video_info=True)
    
    // Load documents using the loader
    documents ← loader.load()
    
    // Check if documents list is empty
    IF documents IS EMPTY THEN
        // Log info and return "No transcript found" message
        LOG_INFO("No transcript found for the provided YouTube URL")
        RETURN "No transcript found"
    END IF
    
    // Extract transcript content from the first document's page_content
    transcript_content ← documents[0].page_content
    
    // Extract metadata from the first document
    metadata ← documents[0].metadata
    
    // Format video information string with title, author, and duration from metadata
    video_info ← f"Title: {metadata['title']}\nAuthor: {metadata['author']}\nDuration: {metadata['duration']}\n\n"
    
    // Log successful completion
    LOG_INFO("YouTube transcript extraction completed successfully")
    
    // Return concatenated video info and transcript content
    RETURN video_info + transcript_content
    
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
- Append logging (INFO) at the beginning of processing with URL
- Append logging (INFO) at the end of successful processing
- Append logging (INFO) if no transcript is found

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
1. Create UnstructuredExcelLoader instance with the provided file path
2. Load the Excel file content using the loader
3. Return the loaded documents as a list of Document objects

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
    
    // Log the beginning of processing with file path
    LOG_INFO(f"Starting Excel file processing for: {file_path}")
    
    // Create UnstructuredExcelLoader instance with the provided file path
    loader ← UnstructuredExcelLoader(file_path=file_path)
    
    // Load the Excel file content using the loader
    documents ← loader.load()
    
    // Log successful completion
    LOG_INFO("Excel file processing completed successfully")
    
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
- **@tool**: LangChain tool decorator - marks function as a LangGraph tool

**Logging**:
- Append logging (INFO) at the beginning of processing with file path
- Append logging (INFO) at the end of successful processing
- Append logging (ERROR) if file loading fails

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
1. Create UnstructuredPowerPointLoader instance with the provided file path
2. Load the PowerPoint file content using the loader
3. Return the loaded documents as a list of Document objects

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
    
    // Log the beginning of processing with file path
    LOG_INFO(f"Starting PowerPoint file processing for: {file_path}")
    
    // Create UnstructuredPowerPointLoader instance with the provided file path
    loader ← UnstructuredPowerPointLoader(file_path=file_path)
    
    // Load the PowerPoint file content using the loader
    documents ← loader.load()
    
    // Log successful completion
    LOG_INFO("PowerPoint file processing completed successfully")
    
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
- Append logging (INFO) at the beginning of processing with file path
- Append logging (INFO) at the end of successful processing
- Append logging (ERROR) if file loading fails

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
1. Create UnstructuredPDFLoader instance with the provided file path
2. Load the PDF file content using the loader
3. Return the loaded documents as a list of Document objects

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
    
    // Log the beginning of processing with file path
    LOG_INFO(f"Starting PDF file processing for: {file_path}")
    
    // Create UnstructuredPDFLoader instance with the provided file path
    loader ← UnstructuredPDFLoader(file_path=file_path)
    
    // Load the PDF file content using the loader
    documents ← loader.load()
    
    // Log successful completion
    LOG_INFO("PDF file processing completed successfully")
    
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
- Append logging (INFO) at the beginning of processing with file path
- Append logging (INFO) at the end of successful processing
- Append logging (ERROR) if file loading fails

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
1. Create a TextLoader instance with the provided file_path parameter
2. Call the load() method on the TextLoader instance to load the text file
3. The load() method returns a list of Document objects containing the file content
4. Check if the documents list is not empty
5. If documents exist, extract the page_content from the first (and typically only) Document in the list
6. If no documents are found, return an empty string
7. Return the extracted text content as a string

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
    
    // Create a TextLoader instance with the provided file_path parameter
    loader ← TextLoader(file_path=file_path)
    
    // Call the load() method on the TextLoader instance to load the text file
    documents ← loader.load()
    
    // Check if the documents list is not empty
    IF documents IS EMPTY THEN
        // If no documents are found, return an empty string
        RETURN ""
    END IF
    
    // If documents exist, extract the page_content from the first Document in the list
    text_content ← documents[0].page_content
    
    // Return the extracted text content as a string
    RETURN text_content
    
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

**Logging**: None. This component does not perform logging operations.

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
  - Returns list of available MCP tools for browser operations

**Component interface**:
- **Inputs**:
  - mcp_url: string // The URL of the browser MCP
- **Outputs**:
  - list // The list of MCP tools
- **Validations**:
  - Handled by MCP client session validation
  - URL format validation handled by streamablehttp_client

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Create async context manager for streamablehttp_client with the MCP URL, unpacking read, write, and unused streams
2. Create async context manager for ClientSession with read and write streams
3. Initialize the MCP session using await session.initialize()
4. Load MCP tools from the session using await load_mcp_tools(session)
5. Return the list of MCP tools

**Pseudocode**:
```
ASYNC FUNCTION get_browser_mcp_tools(mcp_url: string) -> list
    /*
    Purpose: Get the browser MCP tools from the given URL
    
    BEHAVIOR:
    - Accepts: mcp_url (string) - The URL of the browser MCP
    - Produces: list - The list of MCP tools
    - Handles: MCP server connection and tool loading
    
    DEPENDENCIES:
    - MCP Server: Model Context Protocol server for tool access
    - streamablehttp_client: HTTP client for MCP server communication
    - ClientSession: MCP client session management
    - load_mcp_tools: Function to load tools from MCP session from LangChain community
    
    IMPLEMENTATION NOTES:
    - Should handle async context managers for proper resource management
    - Must establish and maintain MCP session connection
    - Should load all available MCP tools from the session
    - Should handle connection errors gracefully
    */
    
    // Create async context manager for streamablehttp_client with the MCP URL
    WITH streamablehttp_client(mcp_url) AS (read_stream, write_stream, unused_stream) DO
        // Create async context manager for ClientSession with read and write streams
        WITH ClientSession(read_stream, write_stream) AS session DO
            // Initialize the MCP session
            AWAIT session.initialize()
            
            // Load MCP tools from the session
            mcp_tools ← AWAIT load_mcp_tools(session)
            
            // Return the list of MCP tools
            RETURN mcp_tools
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
  - list // The list of research tools
- **Validations**:
  - Handled by individual tool creation validation
  - MCP tools validation handled by get_browser_mcp_tools function

**Direct Dependencies with Other Components**:
- get_browser_mcp_tools function
- youtube_transcript_tool function
- unstructured_excel_tool function
- unstructured_powerpoint_tool function
- unstructured_pdf_tool function
- text_file_tool function

**Internal Logic**:
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

**Pseudocode**:
```
ASYNC FUNCTION get_research_tools() -> list
    /*
    Purpose: Get the research tools
    
    BEHAVIOR:
    - Accepts: None
    - Produces: list - The list of research tools
    - Handles: Tool creation and compilation for research operations
    
    DEPENDENCIES:
    - WikipediaQueryRun: LangChain Wikipedia tool for knowledge base access
    - WikipediaAPIWrapper: API wrapper for Wikipedia queries
    - TavilySearch: LangChain Tavily search tool for web search
    - get_browser_mcp_tools: Function to retrieve MCP tools
    
    IMPLEMENTATION NOTES:
    - Should create all necessary research tools
    - Must combine built-in tools with external MCP tools
    - Should handle async MCP tool retrieval
    - Should return comprehensive tool list for research operations
    */
    
    // Create Wikipedia tool with API wrapper
    wikipedia_tool ← WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(wiki_client=None))
    
    // Create Tavily search tool
    tavily_tool ← TavilySearch()
    
    // Define browser MCP URL
    browser_mcp_url ← "http://0.0.0.0:3000/mcp"
    
    // Retrieve MCP tools using await get_browser_mcp_tools
    mcp_tools ← AWAIT get_browser_mcp_tools(browser_mcp_url)
    
    // Return comprehensive list of research tools
    research_tools ← [
        youtube_transcript_tool,
        tavily_tool,
        wikipedia_tool,
        unstructured_excel_tool,
        unstructured_powerpoint_tool,
        unstructured_pdf_tool,
        text_file_tool,
        *mcp_tools  // Unpack all MCP tools
    ]
    
    RETURN research_tools
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**:
- **MCP Communication**: Uses get_browser_mcp_tools to communicate with MCP server
- **Tool Integration**: Combines multiple tool types into unified list

**External Dependencies**:
- **WikipediaQueryRun**: LangChain Wikipedia tool for knowledge base access
- **WikipediaAPIWrapper**: API wrapper for Wikipedia queries
- **TavilySearch**: LangChain Tavily search tool for web search

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
  - Validates LLM response against output schema
  - Returns appropriate response format based on validation result

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompt and output schema
  - llm_researcher: ChatOpenAI // The LLM instance for researcher operations
- **Outputs**:
  - Callable[[ResearcherState], ResearcherState] // The researcher LLM node function
- **Validations**:
  - Handled by validate_output_matches_json_schema function

**Direct Dependencies with Other Components**:
- validate_output_matches_json_schema function

**Internal Logic**:
1. Define inner function researcher_llm_node that takes ResearcherState as parameter
2. Create system prompt using SystemMessage with config.system_prompt content
3. Invoke LLM with system prompt concatenated with state messages
4. Check if response matches output schema using validate_output_matches_json_schema
5. If validation succeeds, return messages with JSON-dumped response and result field
6. If validation fails, return messages with raw response
7. Return the inner researcher_llm_node function

**Pseudocode**:
```
FUNCTION create_researcher_llm_node(config: AgentConfig, llm_researcher: ChatOpenAI) -> Callable[[ResearcherState], ResearcherState]
    /*
    Purpose: Create a researcher LLM node function with the given prompt and LLM
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The agent configuration containing system prompt and output schema
    - Accepts: llm_researcher (ChatOpenAI) - The LLM instance for researcher operations
    - Produces: Callable[[ResearcherState], ResearcherState] - The researcher LLM node function
    - Handles: LLM node creation with dependency injection and response validation
    
    DEPENDENCIES:
    - LangChain SystemMessage: Library for creating system messages
    - LangChain AIMessage: Library for creating AI response messages
    - ChatOpenAI: LLM interface for researcher operations
    - validate_output_matches_json_schema: Function for response validation
    
    CLOSED-OVER VARIABLES:
    - config: AgentConfig - Configuration passed from outer scope
    - llm_researcher: ChatOpenAI - LLM instance passed from outer scope
    
    IMPLEMENTATION NOTES:
    - Should create inner function with injected dependencies
    - Must handle LLM invocation with proper message formatting
    - Should validate responses against output schema
    - Should return appropriate response format based on validation
    */
    
    // Define inner function researcher_llm_node that takes ResearcherState as parameter
    FUNCTION researcher_llm_node(state: ResearcherState) -> ResearcherState
        // Create system prompt using SystemMessage with config.system_prompt content
        system_prompt ← SystemMessage(content=config.system_prompt)
        
        // Invoke LLM with system prompt concatenated with state messages
        response ← llm_researcher.invoke([system_prompt] + state.messages)
        
        // Check if response matches output schema using validate_output_matches_json_schema
        IF validate_output_matches_json_schema(response.content, config.output_schemas.keys()) THEN
            // If validation succeeds, return messages with JSON-dumped response and result field
            result_message ← AIMessage(content=json.dumps({"result": response.content}))
        ELSE
            // If validation fails, return messages with raw response
            result_message ← AIMessage(content=response.content)
        END IF
        
        // Return updated state with new messages
        RETURN ResearcherState(messages=state.messages + [result_message], step_id=state.step_id, results=state.results)
    END FUNCTION
    
    // Return the inner researcher_llm_node function
    RETURN researcher_llm_node
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses messages field in ResearcherState input and returns updated ResearcherState with new messages.

**Communication Patterns**: None. This component does not communicate, rather it creates a function for LLM processing

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **LangChain AIMessage**: Library for creating AI response messages
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
    graph ← StateGraph(ResearcherState)
    
    // Add "researcher" node to the graph using researcher_llm_node function
    graph.add_node("researcher", researcher_llm_node)
    
    // Add "tools" node to the graph using ToolNode with research_tools
    graph.add_node("tools", ToolNode(research_tools))
    
    // Add edge from START to "researcher" node
    graph.add_edge(START, "researcher")
    
    // Add conditional edges from "researcher" node using tools_condition
    graph.add_conditional_edges("researcher", tools_condition)
    
    // Add edge from "tools" node back to "researcher" node
    graph.add_edge("tools", "researcher")
    
    // Compile the graph and return the compiled StateGraph
    compiled_graph ← graph.compile()
    
    RETURN compiled_graph
    
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
    LOG_INFO(f"Starting unit conversion: {quantity} to {to_unit}")
    
    // Create Pint UnitRegistry instance
    ureg ← UnitRegistry()
    
    // Parse the input quantity string using the UnitRegistry
    parsed_quantity ← ureg(quantity)
    
    // Convert the quantity to the target unit using the to() method
    converted_quantity ← parsed_quantity.to(to_unit)
    
    // Log the conversion result
    LOG_INFO(f"Unit conversion completed: {converted_quantity}")
    
    // Return the result as a string
    RETURN str(converted_quantity)
    
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
- Append logging (INFO) at the beginning of processing with quantity and target unit
- Append logging (INFO) at the end of successful processing with result

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
3. Create allowed_names dictionary with math functions (excluding those starting with "__")
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
    LOG_INFO(f"Starting calculation: {expression}")
    
    // Import the math module
    IMPORT math
    
    // Create allowed_names dictionary with math functions (excluding those starting with "__")
    allowed_names ← {}
    FOR EACH name IN dir(math) DO
        IF NOT name.startswith("__") THEN
            allowed_names[name] ← getattr(math, name)
        END IF
    END FOR
    
    // Evaluate the expression using eval with restricted namespace (no builtins, only math functions)
    result ← eval(expression, {"__builtins__": {}}, allowed_names)
    
    // Log the calculation result
    LOG_INFO(f"Calculation completed: {result}")
    
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
- Append logging (INFO) at the beginning of processing with expression
- Append logging (INFO) at the end of successful processing with result

**Error Handling**:
- None. All errors and exceptions will be uncaught and bubble up the call stack.
- This enables a global error handling design implemented in the entry point.

#### Expert Tools Factory

**Component name**: get_expert_tools

**Component type**: function

**Component purpose and responsibilities**:
- **Purpose**: Get the expert tools
- **Responsibilities**: 
  - Creates Python REPL tool for code execution
  - Compiles list of expert tools including unit converter and calculator
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

**Internal Logic**:
1. Create Python REPL tool using PythonREPLTool()
2. Return list containing unit_converter, calculator, and python_repl_tool

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
    - LangChain PythonREPLTool: Library for creating Python REPL tool
    - unit_converter: Function for unit conversion operations
    - calculator: Function for mathematical calculations
    
    IMPLEMENTATION NOTES:
    - Should create Python REPL tool for code execution
    - Must include unit converter and calculator tools
    - Should provide comprehensive expert-level computation tools
    - Should return list of tools for expert reasoning
    */
    
    // Create Python REPL tool using PythonREPLTool()
    python_repl_tool ← PythonREPLTool()
    
    // Return list containing unit_converter, calculator, and python_repl_tool
    expert_tools ← [unit_converter, calculator, python_repl_tool]
    
    RETURN expert_tools
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Does not access any graph states.

**Communication Patterns**: None. This component does not communicate, rather it creates tool instances

**External Dependencies**:
- **LangChain PythonREPLTool**: Library for creating Python REPL tool

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
  - Validates LLM response against output schema
  - Updates expert state with answer and reasoning
  - Returns appropriate response format based on validation result

**Component interface**:
- **Inputs**:
  - config: AgentConfig // The agent configuration containing system prompt and output schema
  - llm_expert: ChatOpenAI // The LLM instance for expert operations
- **Outputs**:
  - Callable[[ExpertState], ExpertState] // The expert LLM node function
- **Validations**:
  - Handled by validate_output_matches_json_schema function

**Direct Dependencies with Other Components**:
- validate_output_matches_json_schema function

**Internal Logic**:
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
        // Create system prompt using SystemMessage with config.system_prompt content
        system_prompt ← SystemMessage(content=config.system_prompt)
        
        // Invoke LLM with system prompt concatenated with state messages
        response ← llm_expert.invoke([system_prompt] + state.messages)
        
        // Check if response matches output schema using validate_output_matches_json_schema
        IF validate_output_matches_json_schema(response.content, config.output_schemas.keys()) THEN
            // If validation succeeds:
            // Update state["expert_answer"] with response["expert_answer"]
            state.expert_answer ← response["expert_answer"]
            
            // Update state["expert_reasoning"] with response["reasoning_trace"]
            state.expert_reasoning ← response["reasoning_trace"]
            
            // Create AIMessage with formatted expert answer and reasoning content
            result_message ← AIMessage(content=json.dumps({
                "expert_answer": response["expert_answer"],
                "reasoning_trace": response["reasoning_trace"]
            }))
        ELSE
            // Return messages with raw response
            result_message ← AIMessage(content=response.content)
        END IF
        
        // Return updated state with new messages
        RETURN ExpertState(
            messages=state.messages + [result_message],
            question=state.question,
            research_steps=state.research_steps,
            research_results=state.research_results,
            expert_answer=state.expert_answer,
            expert_reasoning=state.expert_reasoning
        )
    END FUNCTION
    
    // Return the inner expert_llm_node function
    RETURN expert_llm_node
    
END FUNCTION
```

**Workflow Control**: None

**State Management**: Accesses messages field in ExpertState input and returns updated ExpertState with new messages. Updates expert_answer and expert_reasoning fields in state when validation succeeds.

**Communication Patterns**: None. This component does not communicate, rather it creates a function for LLM processing

**External Dependencies**:
- **LangChain SystemMessage**: Library for creating system messages
- **LangChain AIMessage**: Library for creating AI response messages
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
    graph ← StateGraph(ExpertState)
    
    // Add "expert" node to the graph using expert_llm_node function
    graph.add_node("expert", expert_llm_node)
    
    // Add "tools" node to the graph using ToolNode with expert_tools
    graph.add_node("tools", ToolNode(expert_tools))
    
    // Add edge from START to "expert" node
    graph.add_edge(START, "expert")
    
    // Add conditional edges from "expert" node using tools_condition
    graph.add_conditional_edges("expert", tools_condition)
    
    // Add edge from "tools" node back to "expert" node
    graph.add_edge("tools", "expert")
    
    // Compile the graph and return the compiled StateGraph
    compiled_graph ← graph.compile()
    
    RETURN compiled_graph
    
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
        LOG_INFO("Starting input interface execution")
        
        // Check if state has question, handle error if not provided
        IF state.question IS EMPTY OR state.question IS none THEN
            RAISE ValueError("No question provided to input interface")
        END IF
        
        // Initialize file field with existing value or None
        file_path ← state.file_path OR none
        
        // Initialize planner work fields (research_steps and expert_steps as empty lists)
        research_steps ← []
        expert_steps ← []
        
        // Initialize researcher work fields
        current_research_index ← -1
        researcher_states ← {}
        research_results ← []
        
        // Initialize expert work fields
        expert_state ← none
        expert_answer ← ""
        expert_reasoning ← ""
        
        // Initialize critic work fields (all decision and feedback fields to empty strings)
        critic_planner_decision ← ""
        critic_planner_feedback ← ""
        critic_researcher_decision ← ""
        critic_researcher_feedback ← ""
        critic_expert_decision ← ""
        critic_expert_feedback ← ""
        
        // Initialize finalizer work fields (final_answer and final_reasoning_trace to empty strings)
        final_answer ← ""
        final_reasoning_trace ← ""
        
        // Initialize orchestrator work fields
        agent_messages ← []
        current_step ← "input"
        next_step ← "planner"
        
        // Initialize retry counts to 0 for all agents
        retry_count ← {"planner": 0, "researcher": 0, "expert": 0}
        
        // Set retry limits from agent_configs for planner, researcher, and expert
        retry_limit ← {
            "planner": agent_configs["planner"].retry_limits.get("planner", 3),
            "researcher": agent_configs["researcher"].retry_limits.get("researcher", 3),
            "expert": agent_configs["expert"].retry_limits.get("expert", 3)
        }
        
        // Log successful completion
        LOG_INFO("Input interface execution completed successfully")
        
        // Return the updated state
        RETURN GraphState(
            question=state.question,
            file_path=file_path,
            research_steps=research_steps,
            expert_steps=expert_steps,
            current_research_index=current_research_index,
            researcher_states=researcher_states,
            research_results=research_results,
            expert_state=expert_state,
            expert_answer=expert_answer,
            expert_reasoning=expert_reasoning,
            critic_planner_decision=critic_planner_decision,
            critic_planner_feedback=critic_planner_feedback,
            critic_researcher_decision=critic_researcher_decision,
            critic_researcher_feedback=critic_researcher_feedback,
            critic_expert_decision=critic_expert_decision,
            critic_expert_feedback=critic_expert_feedback,
            final_answer=final_answer,
            final_reasoning_trace=final_reasoning_trace,
            agent_messages=agent_messages,
            current_step=current_step,
            next_step=next_step,
            retry_count=retry_count,
            retry_limit=retry_limit
        )
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
- Append logging (INFO) at the beginning of execution
- Append logging (INFO) at the end of successful completion

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
    
    // Check if current_step equals "critic_planner"
    IF state.current_step = "critic_planner" THEN
        // Check if critic_planner_decision equals "approve"
        IF state.critic_planner_decision = "approve" THEN
            // Check if length of research_steps list is greater than 0
            IF length(state.research_steps) > 0 THEN
                // If research_steps has items, set next_step to "researcher"
                state.next_step ← "researcher"
            ELSE
                // If research_steps is empty, set next_step to "expert"
                state.next_step ← "expert"
            END IF
        ELSE
            // If critic_planner_decision is "reject":
            // Set next_step to "planner"
            state.next_step ← "planner"
            // Increment planner_retry_count by 1
            state.retry_count["planner"] ← state.retry_count["planner"] + 1
        END IF
    END IF
    
    // Check if current_step equals "critic_researcher"
    IF state.current_step = "critic_researcher" THEN
        // Check if critic_researcher_decision equals "approve"
        IF state.critic_researcher_decision = "approve" THEN
            // Check if current_research_index + 1 is greater than or equal to length of research_steps
            IF (state.current_research_index + 1) >= length(state.research_steps) THEN
                // If all research steps completed, set next_step to "expert"
                state.next_step ← "expert"
            ELSE
                // If more research steps remain, set next_step to "researcher"
                state.next_step ← "researcher"
            END IF
        ELSE
            // If critic_researcher_decision is "reject":
            // Set next_step to "researcher"
            state.next_step ← "researcher"
            // Increment researcher_retry_count by 1
            state.retry_count["researcher"] ← state.retry_count["researcher"] + 1
        END IF
    END IF
    
    // Check if current_step equals "critic_expert"
    IF state.current_step = "critic_expert" THEN
        // Check if critic_expert_decision equals "approve"
        IF state.critic_expert_decision = "approve" THEN
            // Set next_step to "finalizer"
            state.next_step ← "finalizer"
        ELSE
            // If critic_expert_decision is "reject":
            // Set next_step to "expert"
            state.next_step ← "expert"
            // Increment expert_retry_count by 1
            state.retry_count["expert"] ← state.retry_count["expert"] + 1
        END IF
    END IF
    
    // Handle initial state and non-critic steps:
    // Check if current_step is empty string or equals "input"
    IF state.current_step = "" OR state.current_step = "input" THEN
        // If current_step is empty or "input", set next_step to "planner"
        state.next_step ← "planner"
    ELSE IF state.current_step = "planner" THEN
        // If current_step equals "planner", set next_step to "critic_planner"
        state.next_step ← "critic_planner"
    ELSE IF state.current_step = "researcher" THEN
        // If current_step equals "researcher", set next_step to "critic_researcher"
        state.next_step ← "critic_researcher"
    ELSE IF state.current_step = "expert" THEN
        // If current_step equals "expert", set next_step to "critic_expert"
        state.next_step ← "critic_expert"
    END IF
    
    // Return the updated state
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Controls workflow state transitions by determining the next step based on current state and critic decisions.

**State Management**: Reads current_step, critic decisions, and retry counts from state. Updates next_step and retry counts in state based on decision logic.

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
    
    // Check if any agent has exceeded its retry limit:
    // Compare planner_retry_count >= planner_retry_limit
    planner_limit_exceeded ← state.retry_count["planner"] >= state.retry_limit["planner"]
    
    // Compare researcher_retry_count >= researcher_retry_limit
    researcher_limit_exceeded ← state.retry_count["researcher"] >= state.retry_limit["researcher"]
    
    // Compare expert_retry_count >= expert_retry_limit
    expert_limit_exceeded ← state.retry_count["expert"] >= state.retry_limit["expert"]
    
    // If any retry limit is exceeded:
    IF planner_limit_exceeded OR researcher_limit_exceeded OR expert_limit_exceeded THEN
        // Log graceful failure message with next_step information
        LOG_INFO(f"Retry limit exceeded. Routing to finalizer. Next step: {state.next_step}")
        
        // Set next_step to "finalizer"
        state.next_step ← "finalizer"
        
        // Set final_answer to "The question could not be answered."
        state.final_answer ← "The question could not be answered."
        
        // Set final_reasoning_trace to "The question could not be answered."
        state.final_reasoning_trace ← "The question could not be answered."
    END IF
    
    // Return the updated state
    RETURN state
    
END FUNCTION
```

**Workflow Control**: Controls workflow termination by checking retry limits and routing to finalizer when limits are exceeded.

**State Management**: Reads retry counts and retry limits from state. Updates next_step, final_answer, and final_reasoning_trace in state when limits are exceeded.

**Communication Patterns**: None. This component does not communicate, rather it checks retry limits

**External Dependencies**: None

**Global variables**: None

**Closed-over variables**: None

**Decorators**: None

**Logging**:
- Append logging (INFO) when retry limit is exceeded with graceful failure message

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

**Internal Logic**:
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
    state.current_step ← state.next_step
    
    // Check if current_step equals "planner"
    IF state.current_step = "planner" THEN
        // Check if critic_planner_decision equals "reject"
        IF state.critic_planner_decision = "reject" THEN
            // Create retry message using compose_agent_message
            message ← compose_agent_message(
                sender="orchestrator",
                receiver="planner",
                type="instruction",
                content=f"Use the following feedback to improve the plan:\n{state.critic_planner_feedback}"
            )
        ELSE
            // Initialize file_info as empty string
            file_info ← ""
            
            // Check if state["file"] exists
            IF state.file_path IS NOT none THEN
                // If file exists, set file_info
                file_info ← f"\n\nInclude using following file in any of the research steps:\n{state.file_path}"
            END IF
            
            // Create initial planning message using compose_agent_message
            message ← compose_agent_message(
                sender="orchestrator",
                receiver="planner",
                type="instruction",
                content=f"Develop a logical plan to answer the following question:\n{state.question}{file_info}"
            )
        END IF
    END IF
    
    // Check if current_step equals "critic_planner"
    IF state.current_step = "critic_planner" THEN
        // Build task context string
        task_context ← f"Use the following context to answer the User Question:\n\n## Context\n### Planner Task\nThe planner was asked to develop a logical plan to answer the following input question: {state.question}\n\n"
        
        // Initialize file_info as empty string
        file_info ← ""
        
        // Check if state["file"] exists
        IF state.file_path IS NOT none THEN
            // If file exists, append file_info
            file_info ← f"\n\nThe following file must be used in reference to answer the question:\n{state.file_path}"
        END IF
        
        // Build research_steps string
        research_steps ← f"### Planner's Plan\nThe planner determined the following research steps were needed to answer the question: {state.research_steps}"
        
        // Build expert_steps string
        expert_steps ← f"\nThe planner determined the following expert steps were needed to answer the question: {state.expert_steps}\n\n"
        
        // Build user_question string
        user_question ← "## User Question:\nDoes the planner's plan have the correct and logical research and expert steps needed to answer the input question? If yes, approve. If no, reject."
        
        // Create critic message using compose_agent_message
        message ← compose_agent_message(
            sender="orchestrator",
            receiver="critic_planner",
            type="instruction",
            content=task_context + research_steps + expert_steps + user_question
        )
    END IF
    
    // Check if current_step equals "researcher"
    IF state.current_step = "researcher" THEN
        // Check if critic_researcher_decision equals "reject"
        IF state.critic_researcher_decision = "reject" THEN
            // Create retry message using compose_agent_message
            message ← compose_agent_message(
                sender="orchestrator",
                receiver="researcher",
                type="instruction",
                content=f"Use the following feedback to improve the research:\n{state.critic_researcher_feedback}",
                step_id=state.current_research_index
            )
        ELSE
            // Increment state["current_research_index"] by 1
            state.current_research_index ← state.current_research_index + 1
            
            // Create research instruction message using compose_agent_message
            message ← compose_agent_message(
                sender="orchestrator",
                receiver="researcher",
                type="instruction",
                content=f"Research the following topic or question: {state.research_steps[state.current_research_index]}",
                step_id=state.current_research_index
            )
        END IF
    END IF
    
    // Check if current_step equals "critic_researcher"
    IF state.current_step = "critic_researcher" THEN
        // Build topic context string
        topic_context ← f"Use the following context to answer the User Question:\n\n## Context\n### Research Topic\nThe researcher was asked to research the following topic: {state.research_steps[state.current_research_index]}\n\n"
        
        // Build results string
        results ← f"### Research Results\nThe researcher's results are: {state.research_results[state.current_research_index]}\n\n"
        
        // Build user_question string
        user_question ← "## User Question:\nDoes the researcher's results contain sufficient information on the topic? If yes, approve. If no, reject."
        
        // Create critic message using compose_agent_message
        message ← compose_agent_message(
            sender="orchestrator",
            receiver="critic_researcher",
            type="instruction",
            content=topic_context + results + user_question
        )
    END IF
    
    // Check if current_step equals "expert"
    IF state.current_step = "expert" THEN
        // Check if critic_expert_decision equals "reject"
        IF state.critic_expert_decision = "reject" THEN
            // Create retry message using compose_agent_message
            message ← compose_agent_message(
                sender="orchestrator",
                receiver="expert",
                type="instruction",
                content=f"Use the following feedback to improve your answer:\n{state.critic_expert_feedback}"
            )
        ELSE
            // Build context string
            context ← f"Use the following context and recommended instructions to answer the question:\n ## Context:\n{state.research_results}\n\n"
            
            // Build expert_steps string
            expert_steps ← f"## Recommended Instructions:\nIt was recommended to perform the following steps to answer the question:\n{state.expert_steps}\n\n"
            
            // Build user_question string
            user_question ← f"## The Question:\nAnswer the question: {state.question}"
            
            // Create expert instruction message using compose_agent_message
            message ← compose_agent_message(
                sender="orchestrator",
                receiver="expert",
                type="instruction",
                content=context + expert_steps + user_question
            )
        END IF
    END IF
    
    // Check if current_step equals "critic_expert"
    IF state.current_step = "critic_expert" THEN
        // Build question context string
        question_context ← f"Use the following context answer the User Question:\n ## Context:\n\n### Expert Question:\n The expert was asked to answer the following question: {state.question}\n\n"
        
        // Build context string
        context ← f"### Researched Information:\nThe expert had the following researched information to use to answer the question:\n{state.research_results}\n\n"
        
        // Build expert_answer string
        expert_answer ← f"## Expert Answer:\nThe expert gave the following response and reasoning:\nExpert answer: {state.expert_answer}\nExpert reasoning: {state.expert_reasoning}\n\n"
        
        // Build user_question string
        user_question ← "## User Question:\nDoes the expert's answer actually answer the question to a satisfactory level? If yes, approve. If no, reject."
        
        // Create critic message using compose_agent_message
        message ← compose_agent_message(
            sender="orchestrator",
            receiver="critic_expert",
            type="instruction",
            content=question_context + context + expert_answer + user_question
        )
    END IF
    
    // Check if current_step equals "finalizer"
    IF state.current_step = "finalizer" THEN
        // Create finalizer instruction message using compose_agent_message
        message ← compose_agent_message(
            sender="orchestrator",
            receiver="finalizer",
            type="instruction",
            content="Generate the final answer and reasoning trace (logical steps) to answer the question."
        )
    END IF
    
    // If current_step is invalid (not matching any condition):
    IF message IS NOT DEFINED THEN
        // Raise ValueError with message
        RAISE ValueError(f"Invalid current step: {state.current_step}")
    END IF
    
    // Send the composed message using send_message function
    state ← send_message(state, message)
    
    // Return the updated state
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
1. Log the beginning of orchestrator execution with current step
2. Call determine_next_step function to determine next step
3. Call check_retry_limit function to check retry limits
4. Call execute_next_step function to execute the next step
5. Log successful completion with next step
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
    
    // Log the beginning of orchestrator execution with current step
    LOG_INFO(f"Starting orchestrator execution. Current step: {state.current_step}")
    
    // Call determine_next_step function to determine next step
    state ← determine_next_step(state)
    
    // Call check_retry_limit function to check retry limits
    state ← check_retry_limit(state)
    
    // Call execute_next_step function to execute the next step
    state ← execute_next_step(state)
    
    // Log successful completion with next step
    LOG_INFO(f"Orchestrator execution completed successfully. Next step: {state.next_step}")
    
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

**Decorators**: None

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
    
    // Check if current_step is "planner"
    IF state.current_step = "planner" THEN
        // If planner, return "planner"
        RETURN "planner"
    END IF
    
    // Check if current_step is "researcher"
    IF state.current_step = "researcher" THEN
        // If researcher, return "researcher"
        RETURN "researcher"
    END IF
    
    // Check if current_step is "expert"
    IF state.current_step = "expert" THEN
        // If expert, return "expert"
        RETURN "expert"
    END IF
    
    // Check if current_step is "critic_planner"
    IF state.current_step = "critic_planner" THEN
        // If critic_planner, return "critic"
        RETURN "critic"
    END IF
    
    // Check if current_step is "critic_researcher"
    IF state.current_step = "critic_researcher" THEN
        // If critic_researcher, return "critic"
        RETURN "critic"
    END IF
    
    // Check if current_step is "critic_expert"
    IF state.current_step = "critic_expert" THEN
        // If critic_expert, return "critic"
        RETURN "critic"
    END IF
    
    // Check if current_step is "finalizer"
    IF state.current_step = "finalizer" THEN
        // If finalizer, return "finalizer"
        RETURN "finalizer"
    END IF
    
    // If current_step is invalid, raise ValueError with error message
    RAISE ValueError(f"Invalid current step: {state.current_step}")
    
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
        
        // Create system prompt using SystemMessage with config.system_prompt content
        system_prompt = SystemMessage(content=config.system_prompt)
        
        // Get agent conversation history using get_agent_conversation function
        conversation_history = get_agent_conversation(state, "planner")
        
        // Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
        langchain_messages = convert_agent_messages_to_langchain(conversation_history)
        
        // Invoke LLM with system prompt concatenated with message history
        messages = [system_prompt] + langchain_messages
        response = llm_planner.invoke(messages)
        
        // Validate response using validate_llm_response function
        validated_response = validate_llm_response(response, config.output_schemas)
        
        // Update state["research_steps"] with response["research_steps"]
        state.research_steps = validated_response["research_steps"]
        
        // Update state["expert_steps"] with response["expert_steps"]
        state.expert_steps = validated_response["expert_steps"]
        
        // Compose agent message using compose_agent_message function with sender="planner", receiver="orchestrator", type="response", and content containing research steps and expert steps
        message_content = {
            "research_steps": validated_response["research_steps"],
            "expert_steps": validated_response["expert_steps"]
        }
        agent_message = compose_agent_message("planner", "orchestrator", "response", message_content)
        
        // Send message using send_message function
        send_message(state, agent_message)
        
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
        
        // Get current research index from state
        current_research_index = state.current_research_step_id
        
        // Get agent conversation history using get_agent_conversation function with step_id = current research index
        conversation_history = get_agent_conversation(state, "researcher", current_research_index)
        
        // Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
        langchain_messages = convert_agent_messages_to_langchain(conversation_history)
        
        // Check if ResearcherState exists for current index
        IF current_research_index NOT IN state.researcher_states THEN
            // If ResearcherState doesn't exist:
            // Create new ResearcherState with messages, step_index, and result=None
            researcher_state = ResearcherState(
                messages=langchain_messages,
                step_id=current_research_index,
                results=None
            )
        ELSE
            // If ResearcherState exists:
            // Get existing ResearcherState from state
            researcher_state = state.researcher_states[current_research_index]
            // Append latest message to ResearcherState messages
            researcher_state.messages = researcher_state.messages + langchain_messages
        END IF
        
        // Execute research using compiled_researcher_graph.invoke with ResearcherState
        response = compiled_researcher_graph.invoke(researcher_state)
        
        // Validate response using validate_llm_response function
        validated_response = validate_llm_response(response, config.output_schemas)
        
        // Store response result in ResearcherState
        researcher_state.results = validated_response["results"]
        
        // Update ResearcherState in state
        state.researcher_states[current_research_index] = researcher_state
        
        // Store research results in state:
        IF LENGTH(state.research_results) <= current_research_index THEN
            // If research_results list length <= current index, append result
            state.research_results.append(validated_response["results"])
        ELSE
            // Otherwise, update result at current index
            state.research_results[current_research_index] = validated_response["results"]
        END IF
        
        // Compose agent message using compose_agent_message function with sender="researcher", receiver="orchestrator", type="response", step_id=current_research_index, and content containing research completion status
        message_content = {
            "research_completed": True,
            "step_id": current_research_index,
            "results": validated_response["results"]
        }
        agent_message = compose_agent_message("researcher", "orchestrator", "response", message_content, current_research_index)
        
        // Send message using send_message function
        send_message(state, agent_message)
        
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
        conversation_history = get_agent_conversation(state, "expert")
        
        // Convert agent messages to LangChain format and take only the last message
        langchain_messages = convert_agent_messages_to_langchain(conversation_history)
        message_in = langchain_messages[-1]  // Take only the last message
        
        // Get expert_state from state
        expert_state = state.expert_state
        
        // Check if expert_state is None
        IF expert_state IS None THEN
            // If expert_state is None:
            // Create new ExpertState with messages, question, research_steps, research_results, and empty expert fields
            expert_state = ExpertState(
                messages=[message_in],
                question=state.question,
                research_steps=state.research_steps,
                research_results=state.research_results,
                expert_answer="",
                expert_reasoning=""
            )
        ELSE
            // If expert_state exists:
            // Extend expert_state messages with new message_in
            expert_state.messages = expert_state.messages + [message_in]
        END IF
        
        // Execute expert reasoning using compiled_expert_graph.invoke with expert_state
        response = compiled_expert_graph.invoke(expert_state)
        
        // Validate response using validate_llm_response function
        validated_response = validate_llm_response(response, config.output_schemas)
        
        // Store response expert_answer and expert_reasoning in expert_state
        expert_state.expert_answer = validated_response["expert_answer"]
        expert_state.expert_reasoning = validated_response["reasoning_trace"]
        
        // Update expert_state in state
        state.expert_state = expert_state
        
        // Store expert_answer and expert_reasoning in state
        state.expert_answer = validated_response["expert_answer"]
        state.expert_reasoning = validated_response["reasoning_trace"]
        
        // Compose agent message using compose_agent_message function with sender="expert", receiver="orchestrator", type="response", and content containing expert answer and reasoning
        message_content = {
            "expert_answer": validated_response["expert_answer"],
            "expert_reasoning": validated_response["reasoning_trace"]
        }
        agent_message = compose_agent_message("expert", "orchestrator", "response", message_content)
        
        // Send message using send_message function
        send_message(state, agent_message)
        
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
        // Log the beginning of critic execution
        LOG_INFO("Critic starting execution")
        
        // Determine which critic to run based on current_step
        critic_type = state.current_step
        
        // If current_step is "critic_planner":
        IF critic_type = "critic_planner" THEN
            // Get critic_prompt from config.system_prompt["critic_planner"]
            critic_prompt = config.system_prompt["critic_planner"]
        // If current_step is "critic_researcher":
        ELSE IF critic_type = "critic_researcher" THEN
            // Get critic_prompt from config.system_prompt["critic_researcher"]
            critic_prompt = config.system_prompt["critic_researcher"]
        // If current_step is "critic_expert":
        ELSE IF critic_type = "critic_expert" THEN
            // Get critic_prompt from config.system_prompt["critic_expert"]
            critic_prompt = config.system_prompt["critic_expert"]
        // If current_step is invalid, raise RuntimeError
        ELSE
            RAISE RuntimeError(f"Invalid critic type: {critic_type}")
        END IF
        
        // Create system prompt using SystemMessage with critic_prompt content
        system_prompt = SystemMessage(content=critic_prompt)
        
        // Get agent conversation history using get_agent_conversation function with current_step
        conversation_history = get_agent_conversation(state, critic_type)
        
        // Convert agent messages to LangChain format and take only the last message
        langchain_messages = convert_agent_messages_to_langchain(conversation_history)
        message_in = langchain_messages[-1]  // Take only the last message
        
        // Invoke LLM with system prompt concatenated with message history
        messages = [system_prompt] + [message_in]
        response = llm_critic.invoke(messages)
        
        // Validate response using validate_llm_response function
        validated_response = validate_llm_response(response, config.output_schemas)
        
        // Store critic decision and feedback based on current step:
        IF critic_type = "critic_planner" THEN
            // If critic_planner: store in critic_planner_decision and critic_planner_feedback
            state.critic_planner_decision = validated_response["decision"]
            state.critic_planner_feedback = validated_response["feedback"]
        ELSE IF critic_type = "critic_researcher" THEN
            // If critic_researcher: store in critic_researcher_decision and critic_researcher_feedback
            state.critic_researcher_decision = validated_response["decision"]
            state.critic_researcher_feedback = validated_response["feedback"]
        ELSE IF critic_type = "critic_expert" THEN
            // If critic_expert: store in critic_expert_decision and critic_expert_feedback
            state.critic_expert_decision = validated_response["decision"]
            state.critic_expert_feedback = validated_response["feedback"]
        END IF
        
        // Compose agent message using compose_agent_message function with sender="critic", receiver="orchestrator", type="response", and content containing decision and feedback
        message_content = {
            "decision": validated_response["decision"],
            "feedback": validated_response["feedback"]
        }
        agent_message = compose_agent_message("critic", "orchestrator", "response", message_content)
        
        // Send message using send_message function
        send_message(state, agent_message)
        
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
        
        // Create system prompt using SystemMessage with config.system_prompt content
        system_prompt = SystemMessage(content=config.system_prompt)
        
        // Get agent conversation history using get_agent_conversation function
        conversation_history = get_agent_conversation(state, "finalizer")
        
        // Convert agent messages to LangChain format using convert_agent_messages_to_langchain function
        langchain_messages = convert_agent_messages_to_langchain(conversation_history)
        
        // Invoke LLM with system prompt concatenated with message history
        messages = [system_prompt] + langchain_messages
        response = llm_finalizer.invoke(messages)
        
        // Validate response using validate_llm_response function
        validated_response = validate_llm_response(response, config.output_schemas)
        
        // Update state["final_answer"] with response["final_answer"]
        state.final_answer = validated_response["final_answer"]
        
        // Update state["final_reasoning_trace"] with response["final_reasoning_trace"]
        state.final_reasoning_trace = validated_response["final_reasoning_trace"]
        
        // Compose agent message using compose_agent_message function with sender="finalizer", receiver="orchestrator", type="response", and content containing final answer and reasoning trace
        message_content = {
            "final_answer": validated_response["final_answer"],
            "final_reasoning_trace": validated_response["final_reasoning_trace"]
        }
        agent_message = compose_agent_message("finalizer", "orchestrator", "response", message_content)
        
        // Send message using send_message function
        send_message(state, agent_message)
        
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
- **Purpose**: Create an OpenAI LLM with the given model and temperature
- **Responsibilities**: 
  - Creates ChatOpenAI instance with specified model and temperature
  - Configures structured output with JSON mode
  - Provides factory pattern for OpenAI LLM creation
  - Enables consistent LLM configuration across the system

**Component interface**:
- **Inputs**:
  - model: string // The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
  - temperature: float // The temperature setting for the LLM (0.0 to 2.0)
  - output_schema: dict // The structured output schema for JSON mode
- **Outputs**:
  - ChatOpenAI // The configured OpenAI LLM instance
- **Validations**:
  - Handled by ChatOpenAI constructor validation
  - Temperature range validation handled by OpenAI API

**Direct Dependencies with Other Components**: None

**Internal Logic**:
1. Create ChatOpenAI instance with provided model and temperature parameters
2. Configure the LLM with structured output using the provided output_schema and json_mode method
3. Return the configured ChatOpenAI instance

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langchain_openai import ChatOpenAI

FUNCTION openai_llm_factory(model: string, temperature: float, output_schema: dict) -> ChatOpenAI
    /*
    Purpose: Create an OpenAI LLM with the given model and temperature
    
    BEHAVIOR:
    - Accepts: model (string) - The OpenAI model to use (e.g., "gpt-4", "gpt-3.5-turbo")
    - Accepts: temperature (float) - The temperature setting for the LLM (0.0 to 2.0)
    - Accepts: output_schema (dict) - The structured output schema for JSON mode
    - Produces: ChatOpenAI - The configured OpenAI LLM instance
    - Handles: LLM configuration with structured output
    
    EXTERNAL DEPENDENCIES:
    - LangChain ChatOpenAI: Library for OpenAI LLM interface
    - OpenAI API: External API for LLM access
    
    IMPLEMENTATION NOTES:
    - Should create ChatOpenAI instance with specified model and temperature
    - Must configure structured output with JSON mode
    - Should provide factory pattern for OpenAI LLM creation
    - Must enable consistent LLM configuration across the system
    */
    
    // Create ChatOpenAI instance with provided model and temperature parameters
    llm = ChatOpenAI(model=model, temperature=temperature)
    
    // Configure the LLM with structured output using the provided output_schema and json_mode method
    configured_llm = llm.with_structured_output(output_schema, method="json_mode")
    
    // Return the configured ChatOpenAI instance
    RETURN configured_llm
    
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
   - Call openai_llm_factory function with config.model, config.temperature, and config.output_schema
   - Return the result from openai_llm_factory
3. If provider is not "openai":
   - Raise ValueError with invalid provider message

**Pseudocode**:
```
FUNCTION llm_factory(config: AgentConfig) -> ChatOpenAI
    /*
    Purpose: Get the appropriate LLM factory based on the provider
    
    BEHAVIOR:
    - Accepts: config (AgentConfig) - The configuration for the agent containing provider, model, temperature, and output_schema
    - Produces: ChatOpenAI - The LLM with structured output
    - Handles: Provider routing and LLM factory delegation
    
    DEPENDENCIES:
    - openai_llm_factory: Creates OpenAI LLM instances with structured output
    
    IMPLEMENTATION NOTES:
    - Should route to appropriate LLM factory based on provider configuration
    - Must support multiple LLM providers through factory pattern
    - Should delegate LLM creation to provider-specific factories
    - Must provide unified interface for LLM creation across different providers
    */
    
    // Check if config.provider equals "openai"
    IF config.provider = "openai" THEN
        // If provider is "openai":
        // Call openai_llm_factory function with config.model, config.temperature, and config.output_schema
        llm = openai_llm_factory(config.model, config.temperature, config.output_schema)
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
  - StateGraph // Compiled graph ready for invocation
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

**Pseudocode**:
```
// REQUIRED IMPORTS:
// from langgraph import StateGraph, START, END
// import asyncio

FUNCTION create_multi_agent_graph(agent_configs: dict[str, AgentConfig]) -> StateGraph
    /*
    Purpose: Factory function that creates and compiles a multi-agent graph with injected prompts
    
    BEHAVIOR:
    - Accepts: agent_configs (dict[str, AgentConfig]) - Dictionary containing all agent configurations
    - Produces: StateGraph - Compiled graph ready for invocation
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
    
    // Create LLM instances dynamically for all agents:
    // Create llm_planner using llm_factory with planner config
    llm_planner = llm_factory(agent_configs["planner"])
    // Create llm_researcher using llm_factory with researcher config
    llm_researcher = llm_factory(agent_configs["researcher"])
    // Create llm_expert using llm_factory with expert config
    llm_expert = llm_factory(agent_configs["expert"])
    // Create llm_critic using llm_factory with critic config
    llm_critic = llm_factory(agent_configs["critic"])
    // Create llm_finalizer using llm_factory with finalizer config
    llm_finalizer = llm_factory(agent_configs["finalizer"])
    
    // Create Researcher Subgraphs:
    // Get research tools using asyncio.run(get_research_tools())
    research_tools = asyncio.run(get_research_tools())
    // Bind research tools to llm_researcher
    llm_researcher_with_tools = llm_researcher.bind_tools(research_tools)
    // Create researcher node using create_researcher_llm_node
    researcher_node = create_researcher_llm_node(llm_researcher_with_tools)
    // Create researcher graph using create_researcher_subgraph
    researcher_graph = create_researcher_subgraph(researcher_node)
    
    // Create Expert Subgraphs:
    // Get expert tools using get_expert_tools()
    expert_tools = get_expert_tools()
    // Bind expert tools to llm_expert
    llm_expert_with_tools = llm_expert.bind_tools(expert_tools)
    // Create expert node using create_expert_llm_node
    expert_node = create_expert_llm_node(llm_expert_with_tools)
    // Create expert graph using create_expert_subgraph
    expert_graph = create_expert_subgraph(expert_node)
    
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
    
    // Create input interface with retry limit using create_input_interface
    input_interface = create_input_interface(agent_configs["planner"].retry_limits)
    
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
    
    // Add edges to the graph:
    // Add edge from START to input_interface
    builder.set_entry_point("input_interface")
    // Add edge from input_interface to orchestrator
    builder.add_edge("input_interface", "orchestrator")
    // Add edges from all agents to orchestrator
    builder.add_edge("planner", "orchestrator")
    builder.add_edge("researcher", "orchestrator")
    builder.add_edge("expert", "orchestrator")
    builder.add_edge("critic", "orchestrator")
    // Add edge from finalizer to END
    builder.set_finish_point("finalizer")
    
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
    
    // Compile and return the graph using builder.compile()
    compiled_graph = builder.compile()
    RETURN compiled_graph
    
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
   - "planner": Create AgentConfig with name="planner", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"research_steps": list[str], "expert_steps": list[str]}, system_prompt=prompts["planner"], retry_limit=3
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
    LOG_INFO("Creating agent configurations")
    
    // Create configs dictionary with agent configurations:
    configs = {
        // "planner": Create AgentConfig with name="planner", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"research_steps": list[str], "expert_steps": list[str]}, system_prompt=prompts["planner"], retry_limit=3
        "planner": AgentConfig(
            name="planner",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            output_schema={"research_steps": list[str], "expert_steps": list[str]},
            system_prompt=prompts["planner"],
            retry_limits={"planner": 3}
        ),
        
        // "researcher": Create AgentConfig with name="researcher", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"result": str}, system_prompt=prompts["researcher"], retry_limit=5
        "researcher": AgentConfig(
            name="researcher",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            output_schema={"results": str},
            system_prompt=prompts["researcher"],
            retry_limits={"researcher": 5}
        ),
        
        // "expert": Create AgentConfig with name="expert", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"expert_answer": str, "reasoning_trace": str}, system_prompt=prompts["expert"], retry_limit=5
        "expert": AgentConfig(
            name="expert",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            output_schema={"expert_answer": str, "reasoning_trace": str},
            system_prompt=prompts["expert"],
            retry_limits={"expert": 5}
        ),
        
        // "critic": Create AgentConfig with name="critic", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"decision": Literal["approve", "reject"], "feedback": str}, system_prompt={"critic_planner":prompts["critic_planner"], "critic_researcher":prompts["critic_researcher"], "critic_expert":prompts["critic_expert"]}, retry_limit=None
        "critic": AgentConfig(
            name="critic",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            output_schema={"decision": Literal["approve", "reject"], "feedback": str},
            system_prompt={
                "critic_planner": prompts["critic_planner"],
                "critic_researcher": prompts["critic_researcher"],
                "critic_expert": prompts["critic_expert"]
            },
            retry_limits={}
        ),
        
        // "finalizer": Create AgentConfig with name="finalizer", provider="openai", model="gpt-4o-mini", temperature=0.0, output_schema={"final_answer": str, "final_reasoning_trace": str}, system_prompt=prompts["finalizer"], retry_limit=None
        "finalizer": AgentConfig(
            name="finalizer",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.0,
            output_schema={"final_answer": str, "final_reasoning_trace": str},
            system_prompt=prompts["finalizer"],
            retry_limits={}
        )
    }
    
    // Log an info message indicating successful creation with the number of agent configurations created
    LOG_INFO(f"Successfully created {len(configs)} agent configurations")
    
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

**Internal Logic**:
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
        // Log an info message indicating application start
        LOG_INFO("Starting multi-agent system application")
        
        // Load baseline prompts:
        // Log info message indicating start of baseline prompt loading
        LOG_INFO("Loading baseline prompts")
        // Call load_baseline_prompts() function
        prompts = load_baseline_prompts()
        // Log info message with number of prompts loaded and their keys
        LOG_INFO(f"Loaded {len(prompts)} prompts: {list(prompts.keys())}")
        
        // Create agent configurations:
        // Call make_agent_configs(prompts) function
        agent_configs = make_agent_configs(prompts)
        
        // Create multi-agent graph:
        // Log info message indicating start of graph creation
        LOG_INFO("Creating multi-agent graph")
        // Call create_multi_agent_graph(agent_configs) function
        graph = create_multi_agent_graph(agent_configs)
        // Log info message indicating successful graph creation
        LOG_INFO("Successfully created multi-agent graph")
        
        // Initialize processing variables:
        // Set jsonl_file_path to "/home/joe/python-proj/hf-agents-course/src/metadata.jsonl"
        jsonl_file_path = "/home/joe/python-proj/hf-agents-course/src/metadata.jsonl"
        // Initialize empty responses list
        responses = []
        // Log info message indicating start of JSONL file processing
        LOG_INFO("Starting JSONL file processing")
        
        // Process each item in the JSONL file:
        // Iterate through items returned by read_jsonl_file(jsonl_file_path)
        FOR item IN read_jsonl_file(jsonl_file_path) DO
            // Check if item["Level"] equals 1
            IF item["Level"] = 1 THEN
                // If Level is 1:
                // Log info message with the question being processed
                LOG_INFO(f"Processing question: {item['question']}")
                // Check if item["file_name"] is not empty
                IF item["file_name"] THEN
                    // If file_name is not empty, set file_path to "/home/joe/datum/gaia_lvl1/{item['file_name']}"
                    file_path = f"/home/joe/datum/gaia_lvl1/{item['file_name']}"
                ELSE
                    // If file_name is empty, set file_path to empty string
                    file_path = ""
                END IF
                
                // Invoke graph with question and file_path using graph.invoke()
                result = graph.invoke({
                    "question": item["question"],
                    "file_path": file_path
                })
                
                // Create response dictionary with task_id, model_answer, and reasoning_trace
                response = {
                    "task_id": item["task_id"],
                    "model_answer": result["final_answer"],
                    "reasoning_trace": result["final_reasoning_trace"]
                }
                
                // Append response to responses list
                responses.append(response)
                
                // Log info message indicating question completion
                LOG_INFO(f"Completed question: {item['task_id']}")
                
                // Sleep for 5 seconds using time.sleep(5)
                time.sleep(5)
            END IF
        END FOR
        
        // Write results to output file:
        // Log info message indicating start of response writing
        LOG_INFO("Writing responses to output file")
        // Call write_jsonl_file(responses, "/home/joe/python-proj/hf-agents-course/src/gaia_lvl1_responses.jsonl")
        write_jsonl_file(responses, "/home/joe/python-proj/hf-agents-course/src/gaia_lvl1_responses.jsonl")
        
        // Log info message indicating successful application completion
        LOG_INFO("Application completed successfully")
        
    CATCH Exception AS error
        // If any Exception occurs:
        // Log error message with exception details
        LOG_ERROR(f"Application failed: {error}")
        // Print error message to console
        PRINT(f"Application failed: {error}")
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
- Catches any Exception and logs error with details
- Prints error message to console
- Exits application with exit code 1 using sys.exit(1)
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
