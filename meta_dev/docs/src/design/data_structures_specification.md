# Multi-Agent System Data Structures Specification

## Based on Architecture Document and Design Guidelines

### Purpose
This document provides complete specifications for all data structures used in the multi-agent system, following the simplified design guidelines and matching the architecture implementation. All data structures are designed to support the graph-based workflow orchestration with specialized agents and simple logging.

---

## Table of Contents

1. [Multi-Agent System Data Structures](#1-multi-agent-system-data-structures)
2. [Entry Point Data Structures](#2-entry-point-data-structures)
2. [Cross-System Data Structures](#3-cross-system-data-structures)
4. [Data Structure Relationships](#4-data-structure-relationships)
5. [Validation and Serialization](#5-validation-and-serialization)

---

## 1. Multi-Agent System Data Structures

### 1.1 Graph State

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

### 1.2 Researcher Subgraph State

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

### 1.3 Expert Subgraph State

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

### 1.4 Agent Message

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

### 1.5 Agent LLM Conversations

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

---



## 2. Cross-System Data Structures

### 2.1 Agent Configuration

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

### 2.2 Planner Output Schema

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

### 2.3 Researcher Output Schema

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

### 2.4 Expert Output Schema

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

### 2.5 Critic Output Schema

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

### 2.6 Finalizer Output Schema

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

### 2.7 Log Entry Structure

**Purpose**: Simple text-based log entries with component identification

**Usage**: Used by all components across the system to create standardized log entries for debugging and monitoring

**Validation**: No explicit validation - uses Python standard library logging

**Definition**:
```
DATA_STRUCTURE LogEntryStructure
    Fields:
    timestamp: string = ""  // Standard timestamp format (YYYY-MM-DD HH:MM:SS,mmm)
    level: string [DEBUG, INFO, WARN, ERROR] = "INFO"  // Log level
    component: string = none  // Name of the component creating the log entry
    message: string = none  // Log message content
END DATA_STRUCTURE
```

---

*This specification provides complete data structure definitions following the simplified guidelines format, ensuring consistency and clarity across the multi-agent system implementation.* 