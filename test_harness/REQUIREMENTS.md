# Test Harness Requirements

## Overview
A test harness for optimizing prompts used in a LangGraph multi-agent system using Promptfoo for systematic prompt optimization and evaluation.

## Core Requirements

### 1. Prompt Optimization with Promptfoo
- **REQ-001**: The system must use Promptfoo as the primary prompt optimization tool
- **REQ-002**: The system must support multiple prompt variations for each agent through Promptfoo
- **REQ-003**: The system must integrate Promptfoo with LangGraph system for end-to-end testing
- **REQ-004**: The system must identify the best performing prompt variation for each agent using Promptfoo metrics
- **REQ-005**: The system must support iterative prompt improvement based on Promptfoo evaluation results
- **REQ-006**: The system must configure Promptfoo to test prompts against the LangGraph multi-agent system
- **REQ-007**: The system must use Promptfoo's built-in optimization features for prompt refinement

### 2. Evaluation & Validation
- **REQ-008**: The system must run Promptfoo evaluations against the LangGraph system
- **REQ-009**: The system must cache LangGraph execution results to avoid redundant calls during Promptfoo optimization
- **REQ-010**: The system must use Promptfoo's evaluation metrics for performance comparison
- **REQ-011**: The system must validate that prompt improvements maintain or enhance performance using Promptfoo scores
- **REQ-012**: The system must use separate test case sets for optimization vs. final evaluation
- **REQ-013**: The system must prevent overfitting by using different test cases for optimization and evaluation

### 3. Cost Efficiency
- **REQ-014**: The system must minimize expensive LangGraph system calls through Promptfoo's efficient testing
- **REQ-015**: The system must implement caching to avoid redundant evaluations during Promptfoo runs
- **REQ-016**: The system must support early termination if performance degrades during Promptfoo optimization
- **REQ-017**: The system must leverage Promptfoo's optimization algorithms to reduce total LLM calls

### 4. Prompt Management
- **REQ-018**: The system must load original prompts from experiment directories
- **REQ-019**: The system must save optimized prompts with versioning after Promptfoo optimization
- **REQ-020**: The system must support rollback to original prompts if needed
- **REQ-021**: The system must track prompt changes across Promptfoo optimization iterations
- **REQ-022**: The system must validate prompt format and content before use with Promptfoo
- **REQ-023**: The system must manage prompt variations for each agent through Promptfoo configuration

### 5. Experiment Management
- **REQ-024**: The system must track experiments with MLFlow
- **REQ-025**: The system must save Promptfoo evaluation metrics and performance data
- **REQ-026**: The system must provide experiment comparison capabilities using Promptfoo results

### 6. User Interface
- **REQ-027**: The system must provide a CLI interface
- **REQ-028**: The system must accept Promptfoo configuration parameters
- **REQ-029**: The system must provide clear progress feedback during Promptfoo optimization

### 7. Test Execution Engine
- **REQ-030**: The system must provide test execution status reporting for Promptfoo runs
- **REQ-031**: The system must support test execution in different environments (dev, staging)
- **REQ-032**: The system must provide test execution timing and performance metrics from Promptfoo

### 8. Test Data Management
- **REQ-033**: The system must support test data versioning and management for Promptfoo
- **REQ-034**: The system must provide test data validation and sanitization
- **REQ-035**: The system must support test data cleanup and isolation

### 9. Logging & Error Handling
- **REQ-036**: The system must provide comprehensive logging at multiple levels (DEBUG, INFO, WARNING, ERROR)
- **REQ-037**: The system must log all Promptfoo execution steps, inputs, outputs, and timing information
- **REQ-038**: The system must provide detailed error messages with context and stack traces
- **REQ-039**: The system must implement retry mechanisms with exponential backoff for transient failures
- **REQ-040**: The system must provide error recovery and graceful degradation capabilities
- **REQ-041**: The system must log all API calls, responses, and performance metrics
- **REQ-042**: The system must support log rotation and archival for long-running experiments

### 10. Local Execution & Privacy
- **REQ-043**: The system must run sentence transformers locally without using HuggingFace API
- **REQ-044**: The system must not use LangSmith or any external telemetry services
- **REQ-045**: The system must ensure all data processing occurs locally without external API calls
- **REQ-046**: The system must support offline operation for all core functionality

### 11. Prompt Integration with LangGraph
- **REQ-047**: The system must automatically update LangGraph prompts after Promptfoo optimization
- **REQ-048**: The system must ensure optimized prompts are immediately available to the graph
- **REQ-049**: The system must maintain prompt synchronization between Promptfoo and LangGraph
- **REQ-050**: The system must provide rollback capability to previous prompt versions

### 12. Modular Architecture & Operations
- **REQ-051**: The system must be modular with clearly defined component boundaries
- **REQ-052**: The system must enforce a defined order of operations for all processes
- **REQ-053**: The system must support independent testing of individual modules
- **REQ-054**: The system must provide clear interfaces between modules

### 13. MLflow Integration
- **REQ-055**: The system must integrate with MLflow for experiment tracking
- **REQ-056**: The system must accept MLflow server URI as a CLI parameter
- **REQ-057**: The system must use the experiment name as the MLflow experiment name
- **REQ-058**: The system must log all Promptfoo optimization metrics, parameters, and artifacts to MLflow
- **REQ-059**: The system must support MLflow model versioning for optimized prompts
- **REQ-060**: The system must log Promptfoo evaluation results as MLflow metrics and artifacts
- **REQ-061**: The system must create unified MLflow runs containing Promptfoo optimization data
- **REQ-062**: The system must support MLflow model comparison between different optimization runs

### 14. Promptfoo Integration
- **REQ-063**: The system must integrate Promptfoo as the primary prompt optimization and evaluation tool
- **REQ-064**: The system must configure Promptfoo to test prompts against the LangGraph multi-agent system
- **REQ-065**: The system must use Promptfoo's optimization features for prompt refinement
- **REQ-066**: The system must provide Promptfoo configuration as CLI parameters
- **REQ-067**: The system must capture and log Promptfoo optimization and evaluation results
- **REQ-068**: The system must log all Promptfoo metrics, scores, and artifacts to MLflow
- **REQ-069**: The system must integrate Promptfoo results with existing MLflow experiment tracking
- **REQ-070**: The system must provide unified reporting using Promptfoo metrics and optimization data

### 15. Prompt Template Structures for Joint Optimization
- **REQ-071**: The system must define standardized template structures for each agent to enable joint optimization
- **REQ-072**: The system must support template variables that can be optimized across multiple agents simultaneously
- **REQ-073**: The system must ensure template compatibility between agents for coordinated optimization
- **REQ-074**: The system must support GAIA level 1 question requirements in all agent templates
- **REQ-075**: The system must enable cross-agent prompt optimization to improve overall system performance

## Prompt Template Structure Requirements

### Planner Agent Template Structure
The planner agent template must support the following structure for joint optimization:

```
## Who you are:
{role_definition}

## What your task is:
{task_description}

## Research Steps Guidelines:
{research_guidelines}

## Expert Steps Guidelines:
{expert_guidelines}

## Question Analysis Framework:
{question_analysis_framework}

## Output Format (JSON)
Output a JSON object with the following schema:
{
    "research_steps": list[str]. Each step is an element in the list,
    "expert_steps": list[str]. Each step is an element in the list.
}
Do not include any other text in your response. It must be a valid JSON object only.

## Context Variables:
- question: {question}
- files: {files}
- previous_feedback: {previous_feedback}
```

**Template Variables for Optimization:**
- `role_definition`: Defines the planner's identity and capabilities
- `task_description`: Describes the planning task and objectives
- `research_guidelines`: Guidelines for creating research steps
- `expert_guidelines`: Guidelines for creating expert steps
- `question_analysis_framework`: Framework for analyzing GAIA level 1 questions

### Researcher Agent Template Structure
```
## Who you are:
{role_definition}

## What your task is:
{task_description}

## Information Gathering Guidelines:
{information_guidelines}

## Tool Usage Guidelines:
{tool_guidelines}

## Quality Standards:
{quality_standards}

## Output Format (JSON)
Output a JSON object with the following schema:
{
    "result": "string containing the research results"
}
Do not include any other text in your response. It must be a valid JSON object only.

## Context Variables:
- research_request: {research_request}
- available_tools: {available_tools}
- previous_feedback: {previous_feedback}
```

### Expert Agent Template Structure
```
## Who you are:
{role_definition}

## What your task is:
{task_description}

## Analysis Framework:
{analysis_framework}

## Reasoning Guidelines:
{reasoning_guidelines}

## Answer Quality Standards:
{answer_standards}

## Output Format (JSON)
Output a JSON object with the following schema:
{
    "expert_answer": "string containing the expert answer",
    "reasoning_trace": "string containing the reasoning trace"
}
Do not include any other text in your response. It must be a valid JSON object only.

## Context Variables:
- question: {question}
- research_data: {research_data}
- expert_steps: {expert_steps}
- previous_feedback: {previous_feedback}
```

### Critic Agent Template Structure
```
## Who you are:
{role_definition}

## Your task:
{task_description}

## Evaluation Criteria:
{evaluation_criteria}

## Feedback Guidelines:
{feedback_guidelines}

## Decision Framework:
{decision_framework}

## Output Format (JSON)
Output a JSON object with the following schema:
{
    "decision": "approve" | "reject",
    "feedback": "string containing the feedback on how to improve the agent's work"
}
Do not include any other text in your response. It must be a valid JSON object only.

## Context Variables:
- question: {question}
- agent_output: {agent_output}
- agent_type: {agent_type}
- previous_feedback: {previous_feedback}
```

### Finalizer Agent Template Structure
```
## Who you are:
{role_definition}

## What your task is:
{task_description}

## Synthesis Guidelines:
{synthesis_guidelines}

## Answer Formatting:
{answer_formatting}

## Quality Assurance:
{quality_assurance}

## Output Format (JSON)
Output a JSON object with the following schema:
{
    "final_answer": "string containing the final answer",
    "final_reasoning_trace": "string containing the final reasoning trace"
}
Do not include any other text in your response. It must be a valid JSON object only.

## Context Variables:
- question: {question}
- research_steps: {research_steps}
- expert_steps: {expert_steps}
- expert_answer: {expert_answer}
- expert_reasoning: {expert_reasoning}
```

### Joint Optimization Strategy
- **REQ-076**: The system must optimize shared template variables across all agents simultaneously
- **REQ-077**: The system must ensure consistency in terminology and approach across agent templates
- **REQ-078**: The system must support coordinated optimization of critic evaluation criteria
- **REQ-079**: The system must optimize the overall workflow through joint agent prompt improvements
- **REQ-080**: The system must maintain agent role clarity while enabling coordinated optimization

## Non-Functional Requirements

### Performance
- **NFR-001**: Promptfoo optimization must complete within 30 minutes
- **NFR-002**: System must leverage Promptfoo's efficient testing to minimize LangGraph calls

### Reliability
- **NFR-003**: System must handle API failures gracefully with retry mechanisms
- **NFR-004**: System must provide rollback capability for failed optimizations
- **NFR-005**: System must provide comprehensive logging and error tracking
- **NFR-006**: System must support graceful degradation when components fail

### Usability
- **NFR-007**: System must be easy to install and configure with Promptfoo
- **NFR-008**: System must provide clear error messages with actionable guidance
- **NFR-009**: System must work with existing LangGraph system without modifications

## Workflow Requirements

### Promptfoo Optimization Workflow
1. **Initial Setup**: Load test cases and original prompts
2. **MLflow Initialization**: Set up experiment tracking with provided experiment name
3. **Promptfoo Configuration**: Configure Promptfoo to test prompts against LangGraph system
4. **Baseline Evaluation**: Run Promptfoo evaluation on original prompts to establish baseline
5. **Prompt Variation Testing**: Use Promptfoo to test different prompt variations systematically
6. **Optimization**: Leverage Promptfoo's optimization features to refine prompts
7. **Prompt Updates**: Automatically update LangGraph prompts with best performing variations
8. **Prompt Synchronization**: Ensure LangGraph system uses updated prompts immediately
9. **Final Evaluation**: Run final Promptfoo evaluation on optimized prompts
10. **MLflow Logging**: Log all Promptfoo metrics, parameters, and artifacts to MLflow
11. **Results Analysis**: Analyze Promptfoo optimization results and performance improvements
12. **Best Prompt Selection**: Identify and deploy the best performing prompts for each agent
13. **Unified Reporting**: Create comprehensive MLflow runs with Promptfoo optimization data

## Input/Output Requirements

### Input
- Test cases in JSONL format for Promptfoo evaluation
- Original prompts for each agent
- Prompt variations for each agent
- Promptfoo configuration parameters
- MLflow server URI (optional CLI parameter)
- Experiment name (used for MLflow experiment name)

### Output
- Optimized prompts for each agent (selected by Promptfoo)
- Promptfoo optimization metrics and scores
- Promptfoo evaluation metrics and scores
- Performance analysis using Promptfoo results
- Unified MLflow experiment runs with Promptfoo optimization data
- MLflow artifacts including Promptfoo reports and evaluation results
- Experiment logs and tracking data
- Performance comparison reports using Promptfoo metrics
- Cached execution results for reproducibility

## Constraints
- Must work with existing LangGraph multi-agent system
- Must use Promptfoo as the primary prompt optimization tool
- Must support OpenAI API for LLM calls
- Must be compatible with Python 3.8+
- Must run sentence transformers locally (no HuggingFace API)
- Must not use LangSmith or external telemetry services
- Must ensure data privacy through local processing
- Must integrate Promptfoo with LangGraph system for end-to-end testing 