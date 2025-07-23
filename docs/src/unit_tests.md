
## Unit Tests
Unit testing must be developed and performed to verify the graph works as expected.
The output content of the LLMs is not what is being tested in unit tests.
The unit tests are designed in a manner to test the following:

**Current Test Coverage Summary:**
- **213 tests total** across 13 test files
- **All tests passing** with comprehensive coverage
- **Error handling and logging** fully implemented and tested
- **State validation** and **retry logic** thoroughly tested
- **Integration tests** cover end-to-end workflows
- **Edge cases** and **security scenarios** extensively tested

### Test Setup and Mock Requirements
- **LLM Mocking**: Mock all LLM calls to return predictable structured outputs
  - Mock `llm_planner` to return valid JSON with research_steps and expert_steps
  - Mock `llm_researcher` to return valid JSON with result field
  - Mock `llm_expert` to return valid JSON with expert_answer and reasoning_trace
  - Mock `llm_critic` to return valid JSON with decision and feedback fields
  - Mock `llm_finalizer` to return valid JSON with final_answer and final_reasoning_trace
- **Tool Mocking**: Mock all external tool calls
  - Mock web search tools to return predictable search results
  - Mock Wikipedia API to return consistent article content
  - Mock YouTube transcript tool to return sample transcripts
  - Mock file reading tools to return sample document content
  - Mock calculator and unit converter tools to return expected calculations
  - Mock Python REPL tool to return safe execution results
- **Subgraph Mocking**: Mock compiled subgraphs for researcher and expert
  - Mock `compiled_researcher_graph.invoke()` to return ResearcherState with result
  - Mock `compiled_expert_graph.invoke()` to return ExpertState with expert_answer and expert_reasoning
- **Network Mocking**: Mock all network calls to simulate success/failure scenarios
  - Mock HTTP requests to external APIs
  - Mock MCP client connections
  - Mock file system operations
- **State Isolation**: Ensure each test starts with clean state
  - Use `empty_graph_state` fixture for consistent test state
  - Reset all state variables before each test
  - Clear agent_messages between tests
  - Reset retry counts and indices
  - Reset error fields (error, error_component) to None
- **Logging Mocking**: Mock logging to capture and verify log messages
  - Mock logger.info, logger.error, logger.warning calls
  - Verify appropriate log messages are generated for each operation
  - Test that errors are properly logged with component context

### Communication
- agent_messages are logged correctly
  - **Assert**: agent_messages list contains expected message with correct sender, receiver, type, content, step_id
  - **Mock**: No external dependencies for this test
- message retrieval works correctly between orchestrator and the agents
  - **Assert**: get_agent_conversation returns only messages between specified agent and orchestrator
  - **Assert**: Message filtering by step_id works correctly
  - **Mock**: Use predefined agent_messages in test state
- No duplication of messages
  - **Assert**: agent_messages list contains no duplicate messages with same content and timestamp
  - **Mock**: Use predefined message list with potential duplicates
- Message structure conforms to AgentMessage schema
  - **Assert**: All messages have required fields: sender, receiver, type, content
  - **Assert**: step_id is Optional[int] and valid when present
  - **Mock**: Create test messages with valid and invalid structures
- Message content is properly escaped/encoded
  - **Assert**: Messages with special characters are properly handled
  - **Assert**: JSON content in messages is valid
  - **Mock**: Create test messages with special characters and JSON content
- Message size limits are respected
  - **Assert**: Messages exceeding size limits are truncated or rejected
  - **Mock**: Create oversized test messages
- Message ordering is maintained
  - **Assert**: Messages appear in chronological order in agent_messages list
  - **Mock**: Use predefined message sequence

### Input Interface
The following default state values are set by the input_interface node: 
- agent_messages = []
- research_steps = []
- expert_steps = []
- current_research_index = -1
- researcher_states = {}
- research_results = []
- expert_state = None
- expert_answer = ""
- expert_reasoning = ""
- critic_planner_decision = ""
- critic_planner_feedback = ""
- critic_researcher_decision = ""
- critic_researcher_feedback = ""
- critic_expert_decision = ""
- critic_expert_feedback = ""
- final_answer = ""
- final_reasoning_trace = ""
- current_step = ""
- next_step = "planner"
- retry_count = 0
- retry_limit = 5
- error = None
- error_component = None

**Assertion Criteria:**
- **Assert**: All state variables are initialized to expected default values
- **Assert**: question field is set to the content of the first message
- **Assert**: next_step is set to "planner"
- **Assert**: error and error_component fields are initialized to None
- **Assert**: State validation passes after initialization
- **Assert**: Appropriate log messages are generated for start and completion
- **Mock**: Provide test input message with sample question content
- **Mock**: Mock logging to verify info messages are generated

### Error Handling and Logging
- **Error State Management**: Verify error states are properly set and propagated
  - **Assert**: Error states are set with component name and error message using `set_error_state()`
  - **Assert**: Error states are logged with appropriate context using `log_error()`
  - **Assert**: Orchestrator detects error states and routes to finalizer
  - **Assert**: Error states include component name and error message
  - **Mock**: Simulate various error conditions in different components
- **State Validation**: Verify state validation works correctly
  - **Assert**: `validate_state()` passes for valid states with all required fields
  - **Assert**: `validate_state()` fails and logs errors for invalid states
  - **Assert**: Missing required fields are detected and logged
  - **Assert**: Invalid field types are detected and logged
  - **Mock**: Create test states with missing or invalid fields
- **LLM Response Validation**: Verify LLM responses are properly validated
  - **Assert**: `validate_llm_response()` passes for valid responses
  - **Assert**: `validate_llm_response()` fails for invalid response types
  - **Assert**: Missing required fields in LLM responses are detected
  - **Mock**: Mock LLM to return malformed or incomplete responses
- **Agent Error Handling**: Verify `handle_agent_error()` works correctly
  - **Assert**: Exceptions are caught and logged with component context
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: Non-recoverable errors route to finalizer
  - **Assert**: Retry limits are enforced correctly
  - **Mock**: Simulate different types of errors (network, validation, etc.)
- **Logging Verification**: Verify appropriate logging throughout the system
  - **Assert**: Info messages are logged for component start/completion
  - **Assert**: Error messages are logged with component context
  - **Assert**: Warning messages are logged for validation failures
  - **Mock**: Mock logging to capture and verify log messages
- **Tool Error Logging**: Verify tool errors are properly logged
  - **Assert**: Calculator errors are logged with appropriate context
  - **Assert**: Unit converter errors are logged with appropriate context
  - **Assert**: Tool error messages are captured and verified
  - **Mock**: Mock tool failures and verify error logging

### Orchestrator

The orchestrator follows a simplified 4-step process as outlined in the logical design:

#### Step 1: Determine the Next Step
The orchestrator determines the next step based on the current step and critic decisions:
- When the critic rejects a particular agent's work, it must set the agent as the next step (to retry)
  - **Assert**: next_step is set to the rejected agent's name
  - **Assert**: retry_count is incremented by 1
  - **Mock**: Set critic decision to "reject" with feedback
- When a critic accepts a particular agent's work, it must set the next agent in the workflow as the next step. The only exception is when performing research. The orchestrator must move to the next research step if any steps remain, otherwise it should set the next step to the expert
  - **Assert**: next_step is set to the next agent in workflow sequence
  - **Assert**: For research, next_step remains "researcher" if more research steps exist
  - **Assert**: For research, next_step becomes "expert" if all research steps complete
  - **Mock**: Set critic decision to "approve" and vary research_steps length
- If no research steps are present, the orchestrator must skip the researcher and the critic for the researcher
  - **Assert**: next_step goes directly from "planner" to "expert" when research_steps is empty
  - **Mock**: Set research_steps to empty list
- When the planner, researcher, or expert are set as the current step, their respective critic must be set as the next step
  - **Assert**: next_step is set to "critic_planner" when current_step is "planner"
  - **Assert**: next_step is set to "critic_researcher" when current_step is "researcher"
  - **Assert**: next_step is set to "critic_expert" when current_step is "expert"
  - **Mock**: Set current_step to each agent type
- If the critic for the planner approves the work, the next step must be set to "researcher" and the research_results and researcher_states variables in the main graph state must be reset to an empty list and an empty dictionary, respectively
  - **Assert**: next_step is set to "researcher"
  - **Assert**: research_results is reset to empty list
  - **Assert**: researcher_states is reset to empty dict
  - **Mock**: Set critic_planner_decision to "approve"

#### Step 2: Check Retry Count
The orchestrator checks if the retry limit has been exceeded:
- If retry count >= retry limit: set the next step for finalizer and set the final answer and reasoning trace as "The question could not be answered."
  - **Assert**: next_step is set to "finalizer" when retry_count >= retry_limit
  - **Assert**: final_answer is set to "The question could not be answered." when retry limit exceeded
  - **Assert**: final_reasoning_trace is set to "The question could not be answered." when retry limit exceeded
  - **Mock**: Set retry_count to retry_limit or higher
- Otherwise, do nothing
  - **Assert**: next_step remains unchanged when retry_count < retry_limit
  - **Mock**: Set retry_count below retry_limit

#### Step 3: Execute the Next Step
The orchestrator executes the next step by setting current_step and sending appropriate messages:
- Set current_step = next_step
  - **Assert**: current_step is updated to match next_step
  - **Mock**: Set next_step to different values and verify current_step is updated
- Send message to the agent being called in the new current step
  - **Assert**: Message is added to agent_messages with correct receiver matching current_step
  - **Assert**: Message sender is "orchestrator"
  - **Mock**: Set current_step to different agent types
- If the orchestrator received critic_decision = reject, it must send the feedback from the critic in the message to the agent that was criticized
  - **Assert**: Message content contains the critic feedback
  - **Assert**: Message receiver is the agent that was criticized
  - **Mock**: Set critic decision to "reject" with specific feedback text
- The orchestrator must correctly send messages to the researcher based on the current research step index when performing research
  - **Assert**: Message step_id matches current_research_index
  - **Assert**: Message content references the correct research step
  - **Mock**: Set current_research_index and research_steps
- Messages must contain the correct sender, receiver, type, content, and step_id fields
  - **Assert**: All required fields are present and have correct types
  - **Assert**: step_id is None for non-research messages
  - **Mock**: Create test messages with various field combinations

#### Step 4: Return State
The orchestrator returns the updated state to continue the graph execution.

#### Orchestrator Error Handling
- The orchestrator must detect error states and route to finalizer appropriately
  - **Assert**: When error state is present, next_step is set to "finalizer"
  - **Assert**: When error state is present, final_answer contains error information
  - **Assert**: When error state is present, final_reasoning_trace contains error information
  - **Assert**: Error states are logged with appropriate context
  - **Mock**: Set error state and verify routing behavior
- The orchestrator must validate state after each step
  - **Assert**: `validate_state()` is called after each step
  - **Assert**: Validation failures are logged as warnings
  - **Mock**: Create invalid states and verify validation behavior
- The orchestrator must handle exceptions gracefully
  - **Assert**: Exceptions are caught and logged using `handle_agent_error()`
  - **Assert**: Error state is set with component and error information
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: Orchestrator logs start and completion messages
  - **Mock**: Simulate exceptions in orchestrator functions

#### Orchestrator Handling of Research Step
- The orchestrator must correctly increment the current research step index when performing research. Either increment it by 1 when the critic approves of the previous research step or the current research step index must remain the same if the critic rejects the current research step
  - **Assert**: current_research_index increments by 1 when critic approves
  - **Assert**: current_research_index remains same when critic rejects
  - **Mock**: Set critic decision to "approve" or "reject" and track index changes
- The current research step index must not change when not calling the researcher
  - **Assert**: current_research_index remains unchanged when current_step is not "researcher"
  - **Mock**: Set current_step to non-researcher agents
- The orchestrator must handle the case when all research steps are completed
  - **Assert**: next_step is set to "expert" when current_research_index >= len(research_steps)
  - **Mock**: Set research_steps and current_research_index to trigger completion

#### Orchestrator Correctly Handles Retries
- The orchestrator must increment the retry count by one when the critic rejects an agent's work
  - **Assert**: retry_count increases by 1 after critic rejection
  - **Mock**: Set critic decision to "reject" and track retry_count
- The orchestrator must set finalizer as next step if the retry count exceeds the retry limit
  - **Assert**: next_step is set to "finalizer" when retry_count >= retry_limit
  - **Mock**: Set retry_count to retry_limit or higher
- If the retry count exceeds the retry limit the final answer must be "The question could not be answered."
  - **Assert**: final_answer is set to "The question could not be answered." when retry limit exceeded
  - **Mock**: Set retry_count to exceed retry_limit
- The orchestrator must track retry counts separately for different agents if needed
  - **Assert**: Retry count tracking works correctly for each agent type
  - **Mock**: Simulate multiple rejections from different agents

### Planner
- Retrieves messages correctly between orchestrator and planner
  - **Assert**: get_agent_conversation returns only planner-orchestrator messages
  - **Mock**: Create test agent_messages with planner conversations
- Updates the state graph with research_steps and expert_steps
  - **Assert**: research_steps and expert_steps are updated with LLM response values
  - **Assert**: Both fields are lists of strings
  - **Mock**: Mock LLM to return specific research_steps and expert_steps
- Outputs empty list for research steps if no research is needed
  - **Assert**: research_steps is empty list when question doesn't require research
  - **Mock**: Mock LLM to return empty research_steps list
- Sends message correctly to orchestrator that the plan is done
  - **Assert**: Message is sent to orchestrator with "plan complete" content
  - **Assert**: Message sender is "planner"
  - **Mock**: No additional mocking needed
- Handles feedback from critic correctly when plan is rejected
  - **Assert**: Planner processes critic feedback and updates plan accordingly
  - **Assert**: Updated plan addresses critic's concerns
  - **Mock**: Mock LLM to return updated plan based on feedback
- Generates valid JSON output conforming to expected schema
  - **Assert**: LLM response contains valid JSON with required fields
  - **Assert**: research_steps and expert_steps are lists
  - **Mock**: Mock LLM to return malformed JSON to test error handling
- Handles errors gracefully with proper logging and state management
  - **Assert**: Exceptions are caught and logged with component context using `handle_agent_error()`
  - **Assert**: Error state is set with component name and error message
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: State validation is performed after successful execution
  - **Assert**: LLM response validation is performed using `validate_llm_response()`
  - **Mock**: Simulate LLM failures and verify error handling
- Logs appropriate messages for start and completion
  - **Assert**: Info messages are logged for start and successful completion
  - **Assert**: Error messages are logged for failures
  - **Mock**: Mock logging to verify message generation

### Researcher Node In Graph
- The researcher node in the main graph must correctly handle research states. It has to keep track of them by research step index and preserve the states
  - **Assert**: researcher_states dict contains entry for each research step index
  - **Assert**: State is preserved between retries for same step
  - **Mock**: Create test researcher_states with multiple step indices
- It must retrieve messages correctly for a specific current research index
  - **Assert**: get_agent_conversation filters messages by correct step_id
  - **Mock**: Create test messages with different step_ids
- It must add a new researcher state to the main graph state when performing a new research step
  - **Assert**: New ResearcherState is created and added to researcher_states
  - **Assert**: step_index matches current_research_index
  - **Mock**: Set current_research_index to trigger new state creation
- It must use the same research state from the main graph when performing a retry
  - **Assert**: Existing ResearcherState is reused for retry
  - **Assert**: Messages are appended to existing state
  - **Mock**: Create existing ResearcherState and simulate retry
- It must dynamically build research results as research steps are completed. The research_results list is not pre-allocated with a length equal to research_steps
  - **Assert**: research_results list starts as empty and grows dynamically
  - **Assert**: New result is appended to end of list when research step completes
  - **Assert**: research_results[current_research_index] is updated with new result when retrying
  - **Assert**: List length matches the number of completed research steps
  - **Mock**: Mock researcher subgraph to return specific results and verify dynamic growth
- It must send the correct message to the orchestrator that research is complete
  - **Assert**: Message is sent with "research complete" content
  - **Assert**: Message step_id matches current_research_index
  - **Mock**: Mock researcher subgraph completion
- It must handle the case when all research steps are completed
  - **Assert**: No new researcher state is created when all steps complete
  - **Mock**: Set current_research_index to exceed research_steps length
- Handles errors gracefully with proper logging and state management
  - **Assert**: Exceptions are caught and logged with component context
  - **Assert**: Subgraph errors are properly handled and logged
  - **Assert**: Error state is set with component name and error message
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: State validation is performed after successful execution
  - **Mock**: Simulate subgraph failures and verify error handling
- Logs appropriate messages for start and completion
  - **Assert**: Info messages are logged for start and successful completion
  - **Assert**: Error messages are logged for failures
  - **Mock**: Mock logging to verify message generation

### Expert
- It must retrieve messages correctly between the orchestrator and the expert
  - **Assert**: get_agent_conversation returns only expert-orchestrator messages
  - **Mock**: Create test agent_messages with expert conversations
- It must send the correct message to the orchestrator that expert is complete
  - **Assert**: Message is sent with "expert complete" content
  - **Assert**: Message contains expert answer and reasoning
  - **Mock**: Mock expert subgraph to return specific answer and reasoning
- It must correctly set the expert state to the main graph state
  - **Assert**: expert_state is updated with ExpertState from subgraph
  - **Assert**: expert_answer and expert_reasoning are updated
  - **Mock**: Mock expert subgraph to return specific ExpertState
- The messages in the expert state must be current based on the retrieved messages
  - **Assert**: ExpertState messages match latest orchestrator-expert conversation
  - **Mock**: Create test conversation history
- If the expert is asked to retry, it must have the latest message for feedback appended to the messages variable in the expert state
  - **Assert**: Latest feedback message is appended to ExpertState messages
  - **Mock**: Create test feedback message and verify it's appended
- It must generate valid JSON output conforming to expected schema
  - **Assert**: LLM response contains valid JSON with expert_answer and reasoning_trace
  - **Mock**: Mock LLM to return malformed JSON to test error handling

### Critic
- When the critic is reviewing the planner's, researcher's, and expert's work, it must set the correct state variables for critic decision and feedback
  - **Assert**: critic_*_decision and critic_*_feedback are set based on LLM response
  - **Assert**: Decision is either "approve" or "reject"
  - **Mock**: Mock LLM to return specific decision and feedback
- It must retrieve the latest message from the orchestrator only
  - **Assert**: Only the most recent orchestrator message is processed
  - **Mock**: Create test message history with multiple messages
- It must send the correct message, with the correct sender, to the orchestrator agent when the critique is completed
  - **Assert**: Message sender matches critic type (critic_planner, critic_researcher, critic_expert)
  - **Assert**: Message receiver is "orchestrator"
  - **Mock**: Set current_step to different critic types
- It must generate valid JSON output conforming to expected schema
  - **Assert**: LLM response contains valid JSON with decision and feedback
  - **Mock**: Mock LLM to return malformed JSON to test error handling
- It must handle different types of work (planner, researcher, expert) correctly
  - **Assert**: Correct critic state variables are updated based on work type
  - **Assert**: Appropriate system prompt is used for each work type
  - **Mock**: Set current_step to different agent types and verify critic behavior
- Handles errors gracefully with proper logging and state management
  - **Assert**: Exceptions are caught and logged with component context
  - **Assert**: Error state is set with component name and error message
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: LLM response validation is performed
  - **Mock**: Simulate LLM failures and verify error handling
- Logs appropriate messages for start and completion
  - **Assert**: Info messages are logged for start and successful completion
  - **Assert**: Error messages are logged for failures
  - **Mock**: Mock logging to verify message generation

### Finalizer
- The finalizer node must correctly retrieve messages from the orchestrator to the finalizer
  - **Assert**: get_agent_conversation returns only finalizer-orchestrator messages
  - **Mock**: Create test agent_messages with finalizer conversations
- It must correctly set the state variables for final answer and final reasoning trace
  - **Assert**: final_answer and final_reasoning_trace are set based on LLM response
  - **Mock**: Mock LLM to return specific final answer and reasoning
- It must correctly send the message to the orchestrator when completed
  - **Assert**: Message is sent with "finalizer complete" content
  - **Assert**: Message contains final answer and reasoning trace
  - **Mock**: Mock LLM to return specific final output
- It must generate valid JSON output conforming to expected schema
  - **Assert**: LLM response contains valid JSON with final_answer and final_reasoning_trace
  - **Mock**: Mock LLM to return malformed JSON to test error handling
- Handles errors gracefully with proper logging and state management
  - **Assert**: Exceptions are caught and logged with component context using `handle_agent_error()`
  - **Assert**: Error state is set with component name and error message
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: State validation is performed after successful execution
  - **Assert**: LLM response validation is performed using `validate_llm_response()`
  - **Mock**: Simulate LLM failures and verify error handling
- Logs appropriate messages for start and completion
  - **Assert**: Info messages are logged for start and successful completion
  - **Assert**: Error messages are logged for failures
  - **Mock**: Mock logging to verify message generation

### Routing on the Main Graph
The main graph must correctly route to the correct node based on the current step
- Verify routing logic handles all possible current_step values
  - **Assert**: route_from_orchestrator returns correct node name for each current_step
  - **Assert**: All valid current_step values are handled
  - **Mock**: Set current_step to each possible value
- Verify routing logic handles edge cases and invalid states
  - **Assert**: Invalid current_step values raise appropriate exceptions
  - **Assert**: Edge cases like empty current_step are handled
  - **Mock**: Set invalid current_step values

### Researcher SubGraph
- Verify correct tool functionality and selection
  - **Assert**: Appropriate tools are selected based on research request
  - **Assert**: Tool parameters are correctly formatted
  - **Mock**: Mock tool selection logic and tool responses
- Verify tool parameter validation and error handling
  - **Assert**: Invalid tool parameters are rejected with appropriate errors
  - **Assert**: Tool errors are handled gracefully
  - **Mock**: Mock tool calls with invalid parameters and error responses
- Verify tool response processing and parsing
  - **Assert**: Tool responses are correctly parsed and formatted
  - **Assert**: Tool response content is preserved in final result
  - **Mock**: Mock tool responses with various content types
- State management tests to make sure message sending and filtering is correct
  - **Assert**: Messages are correctly added to ResearcherState
  - **Assert**: Tool messages are properly formatted
  - **Mock**: Create test message sequences
- Agent conversation is correctly preserved across tool calls
  - **Assert**: Conversation history is maintained during tool usage
  - **Assert**: Tool calls don't interfere with conversation flow
  - **Mock**: Mock conversation history and tool calls
- State transitions and updates are appropriately handled
  - **Assert**: ResearcherState transitions correctly between nodes
  - **Assert**: State updates preserve required fields
  - **Mock**: Mock state transitions and verify state integrity
- Correctly receives structured output from the LLM when returning a response to the orchestrator
  - **Assert**: LLM response is properly structured with result field
  - **Assert**: Structured output is correctly parsed
  - **Mock**: Mock LLM to return structured and unstructured responses
- Correct LLM response handling (structured/unstructured)
  - **Assert**: Both structured and unstructured responses are handled correctly
  - **Assert**: Response format is consistent
  - **Mock**: Mock LLM to return various response formats
- Verify tool availability and fallback mechanisms
  - **Assert**: System handles unavailable tools gracefully
  - **Assert**: Fallback tools are used when primary tools fail
  - **Mock**: Mock tool unavailability and fallback scenarios
- Verify conversation history preservation during tool usage
  - **Assert**: Tool usage doesn't corrupt conversation history
  - **Assert**: History is properly maintained across multiple tool calls
  - **Mock**: Create complex conversation with multiple tool calls

### Expert SubGraph
- Verify correct tool functionality and selection (calculator, unit converter, Python REPL)
  - **Assert**: Appropriate tools are selected based on expert instructions
  - **Assert**: Tool parameters match expected format
  - **Mock**: Mock tool selection and parameter validation
- Verify calculation tool usage and accuracy
  - **Assert**: Calculator tool returns correct mathematical results
  - **Assert**: Complex expressions are evaluated correctly
  - **Mock**: Mock calculator with various mathematical expressions
- Verify unit conversion accuracy and error handling
  - **Assert**: Unit converter returns accurate conversions
  - **Assert**: Invalid unit combinations are handled gracefully
  - **Mock**: Mock unit converter with valid and invalid conversions
- Verify Python REPL safety and execution limits
  - **Assert**: Python REPL executes safe code correctly
  - **Assert**: Dangerous operations are prevented or limited
  - **Mock**: Mock Python REPL with safe and unsafe code
- State management tests to make sure message sending and filtering is correct
  - **Assert**: Messages are correctly added to ExpertState
  - **Assert**: Tool messages are properly formatted
  - **Mock**: Create test message sequences
- Agent conversation is correctly preserved across tool calls
  - **Assert**: Conversation history is maintained during tool usage
  - **Assert**: Tool calls don't interfere with conversation flow
  - **Mock**: Mock conversation history and tool calls
- State transitions and updates are appropriately handled
  - **Assert**: ExpertState transitions correctly between nodes
  - **Assert**: State updates preserve required fields
  - **Mock**: Mock state transitions and verify state integrity
- Correctly receives structured output from the LLM when returning a response to the orchestrator
  - **Assert**: LLM response is properly structured with expert_answer and reasoning_trace
  - **Assert**: Structured output is correctly parsed
  - **Mock**: Mock LLM to return structured and unstructured responses
- Correct LLM response handling (structured/unstructured)
  - **Assert**: Both structured and unstructured responses are handled correctly
  - **Assert**: Response format is consistent
  - **Mock**: Mock LLM to return various response formats
- Verify reasoning trace generation and validation
  - **Assert**: Reasoning trace is generated and contains logical steps
  - **Assert**: Reasoning trace references tools and calculations used
  - **Mock**: Mock reasoning trace generation
- Verify answer validation and formatting
  - **Assert**: Expert answer is properly formatted and complete
  - **Assert**: Answer addresses the original question
  - **Mock**: Mock answer generation and validation
- Handles errors gracefully with proper logging and state management
  - **Assert**: Exceptions are caught and logged with component context
  - **Assert**: Subgraph errors are properly handled and logged
  - **Assert**: Error state is set with component name and error message
  - **Assert**: Retry count is incremented for recoverable errors
  - **Assert**: State validation is performed after successful execution
  - **Mock**: Simulate subgraph failures and verify error handling
- Logs appropriate messages for start and completion
  - **Assert**: Info messages are logged for start and successful completion
  - **Assert**: Error messages are logged for failures
  - **Mock**: Mock logging to verify message generation

### Error Handling
- Handle network failures gracefully (tool calls, API calls)
  - **Assert**: Network failures don't crash the system
  - **Assert**: Appropriate error messages are logged
  - **Assert**: System attempts retry or fallback mechanisms
  - **Assert**: Error states are properly set and propagated
  - **Mock**: Mock network failures and timeouts
- Handle invalid input questions (empty, malformed, too long)
  - **Assert**: Empty questions are rejected with appropriate error
  - **Assert**: Malformed questions are handled gracefully
  - **Assert**: Questions exceeding length limits are truncated or rejected
  - **Assert**: Error states are properly set and logged
  - **Mock**: Create test questions with various invalid formats
- Handle malformed agent responses (invalid JSON, missing fields)
  - **Assert**: Invalid JSON responses are handled gracefully
  - **Assert**: Missing required fields trigger appropriate error handling
  - **Assert**: System attempts to recover from malformed responses
  - **Assert**: LLM response validation catches malformed responses
  - **Mock**: Mock LLM to return malformed responses
- Handle tool failures
  - **Assert**: Tool failures don't crash the system
  - **Assert**: Alternative tools are used when available
  - **Assert**: Tool errors are logged with appropriate context
  - **Mock**: Mock tool failures
- Handle memory exhaustion and resource limits
  - **Assert**: Memory limits are respected
  - **Assert**: Resource cleanup occurs when limits are reached
  - **Assert**: System degrades gracefully under resource pressure
  - **Mock**: Mock memory exhaustion scenarios
- Handle concurrent access and race conditions
  - **Assert**: Concurrent access doesn't corrupt state
  - **Assert**: Race conditions are prevented or handled
  - **Assert**: State remains consistent under concurrent operations
  - **Mock**: Simulate concurrent access scenarios
- Handle malformed messages in the communication system
  - **Assert**: Malformed messages are rejected or sanitized
  - **Assert**: Communication system remains stable
  - **Assert**: Error messages are logged for debugging
  - **Mock**: Create malformed test messages
- Handle state validation failures
  - **Assert**: Invalid states are detected and logged
  - **Assert**: Missing required fields are identified
  - **Assert**: Invalid field types are detected
  - **Assert**: State validation warnings are logged
  - **Mock**: Create test states with validation issues
- Handle LLM response validation failures
  - **Assert**: Invalid LLM responses are detected and logged
  - **Assert**: Missing required fields in responses are identified
  - **Assert**: Response validation errors trigger error handling
  - **Mock**: Mock LLM to return invalid responses

### State Consistency
- Verify state remains consistent across graph transitions
  - **Assert**: All required state fields are present after each transition
  - **Assert**: State field types remain correct throughout execution
  - **Assert**: No state corruption occurs during transitions
  - **Mock**: Create test states and verify consistency after transitions
- Verify no state pollution between different question runs
  - **Assert**: State from previous runs doesn't affect current run
  - **Assert**: agent_messages are cleared between runs
  - **Assert**: All state variables are properly reset
  - **Mock**: Run multiple questions and verify state isolation
- Verify proper cleanup after completion or failure
  - **Assert**: Resources are properly released after completion
  - **Assert**: Temporary files and connections are cleaned up
  - **Assert**: Memory is freed appropriately
  - **Mock**: Simulate completion and failure scenarios
- Verify state isolation between concurrent runs
  - **Assert**: Concurrent runs don't interfere with each other
  - **Assert**: Each run has its own isolated state
  - **Assert**: No shared state corruption occurs
  - **Mock**: Simulate concurrent execution scenarios
- Verify state validation and integrity checks
  - **Assert**: State validation catches invalid states
  - **Assert**: Integrity checks prevent state corruption
  - **Assert**: Invalid states trigger appropriate error handling
  - **Mock**: Create invalid test states
- Verify proper initialization of all state variables
  - **Assert**: All state variables are properly initialized
  - **Assert**: Initial values match expected defaults
  - **Assert**: No uninitialized variables exist
  - **Assert**: Error fields (error, error_component) are initialized to None
  - **Mock**: Create fresh state and verify initialization

### Message Validation
- Verify message structure conforms to AgentMessage schema
  - **Assert**: All messages have required fields (sender, receiver, type, content)
  - **Assert**: Optional fields (step_id) are properly typed
  - **Assert**: Invalid message structures are rejected
  - **Mock**: Create test messages with valid and invalid structures
- Verify message content is properly escaped/encoded
  - **Assert**: Special characters in content are properly handled
  - **Assert**: JSON content is valid and properly formatted
  - **Assert**: Unicode characters are handled correctly
  - **Mock**: Create test messages with special characters and JSON content
- Verify message size limits are respected
  - **Assert**: Messages exceeding size limits are handled appropriately
  - **Assert**: Large content is truncated or rejected
  - **Assert**: Size limits are consistently enforced
  - **Mock**: Create oversized test messages
- Verify message ordering is maintained
  - **Assert**: Messages appear in chronological order
  - **Assert**: Message timestamps are properly handled
  - **Assert**: Order is preserved during filtering and retrieval
  - **Mock**: Create test message sequences with timestamps
- Verify message filtering works correctly for different agents
  - **Assert**: get_agent_conversation returns correct messages for each agent
  - **Assert**: Filtering by step_id works correctly
  - **Assert**: Filtering by message type works correctly
  - **Mock**: Create test messages for different agents and scenarios
- Verify message conversion between formats works correctly
  - **Assert**: convert_agent_messages_to_langchain produces correct format
  - **Assert**: Conversion preserves message content and meaning
  - **Assert**: Conversion handles all message types correctly
  - **Mock**: Create test AgentMessage objects and verify conversion

### Retry Logic
- Verify no infinite loops in retry scenarios
  - **Assert**: retry_count never exceeds retry_limit
  - **Assert**: System eventually terminates even with repeated failures
  - **Assert**: Infinite retry scenarios are prevented
  - **Assert**: System terminates with retry_count=4 and retry_limit=5 on next rejection
  - **Mock**: Simulate repeated failure scenarios
- Verify retry count tracking per agent
  - **Assert**: Retry counts are properly incremented on critic rejections
  - **Assert**: Retry limits are enforced consistently
  - **Assert**: Final answer is set when retry limit is exceeded
  - **Assert**: Retry count is not incremented on critic approvals
  - **Assert**: System handles different retry limits correctly
  - **Assert**: System handles edge cases like zero retry limit
  - **Assert**: System handles negative retry count values
  - **Assert**: System handles large retry count values
  - **Assert**: Retry count state is preserved correctly
  - **Mock**: Simulate multiple rejections from different agents

### Integration
- Verify end-to-end question answering flow from start to finish
  - **Assert**: Complete question answering flow executes successfully
  - **Assert**: All agents are called in correct sequence
  - **Assert**: Final answer is generated and returned
  - **Assert**: Simple questions (e.g., "What is 2 + 2?") complete successfully
  - **Assert**: Complex questions (e.g., "What is CRISPR and who invented it?") complete successfully
  - **Mock**: Mock all components and verify end-to-end flow
- Verify proper tool integration and usage across the system
  - **Assert**: Tools are properly integrated and accessible
  - **Assert**: Tool usage is consistent across agents
  - **Assert**: Tool responses are properly handled
  - **Mock**: Mock tool integration and verify usage patterns
- Verify correct data flow between agents and subgraphs
  - **Assert**: Data flows correctly between main graph and subgraphs
  - **Assert**: State is properly shared and updated
  - **Assert**: Messages are correctly passed between components
  - **Assert**: Agent communication integration works correctly
  - **Assert**: State management integration works correctly
  - **Assert**: Routing integration works correctly
  - **Mock**: Create test data flows and verify propagation
- Verify proper error propagation and handling
  - **Assert**: Errors are properly propagated through the system
  - **Assert**: Error handling is consistent across components
  - **Assert**: Error recovery mechanisms work correctly
  - **Assert**: Retry mechanism integration works correctly
  - **Mock**: Inject errors at various points and verify handling
- Verify system behavior with various question types
  - **Assert**: System handles factual questions correctly
  - **Assert**: System handles calculation questions correctly
  - **Assert**: System handles research-intensive questions correctly
  - **Mock**: Create test questions of various types
- Verify system behavior with different research requirements
  - **Assert**: System handles questions requiring no research
  - **Assert**: System handles questions requiring single research step
  - **Assert**: System handles questions requiring multiple research steps
  - **Mock**: Create test questions with varying research requirements
- Verify system behavior with different expert step complexities
  - **Assert**: System handles simple expert reasoning correctly
  - **Assert**: System handles complex multi-step reasoning correctly
  - **Assert**: System handles expert reasoning requiring multiple tools
  - **Mock**: Create test scenarios with varying expert complexity
- Verify critic integration with all agents
  - **Assert**: Critic properly reviews planner work
  - **Assert**: Critic properly reviews researcher work
  - **Assert**: Critic properly reviews expert work
  - **Assert**: Critic decisions are properly handled by orchestrator
  - **Mock**: Mock critic responses and verify integration
- Verify finalizer integration with all context
  - **Assert**: Finalizer receives all necessary context
  - **Assert**: Finalizer generates comprehensive final answer
  - **Assert**: Finalizer generates comprehensive reasoning trace
  - **Mock**: Mock finalizer responses and verify integration
- Verify system robustness integration
  - **Assert**: System handles various failure scenarios gracefully
  - **Assert**: System maintains state consistency across failures
  - **Assert**: System recovers appropriately from errors
  - **Mock**: Simulate various failure scenarios and verify robustness

### Edge Cases
- Handle questions that require no research steps
  - **Assert**: System skips researcher and critic_researcher
  - **Assert**: Flow goes directly from planner to expert
  - **Assert**: No research-related state is created
  - **Mock**: Create test questions that don't require research
- Handle questions that require multiple research steps
  - **Assert**: All research steps are executed in sequence
  - **Assert**: Each step is properly criticized and approved
  - **Assert**: Research results are accumulated correctly
  - **Mock**: Create test questions requiring multiple research steps
- Handle questions that require complex expert reasoning
  - **Assert**: Complex reasoning is broken down into manageable steps
  - **Assert**: Multiple tools are used appropriately
  - **Assert**: Reasoning trace is comprehensive and logical
  - **Mock**: Create test questions requiring complex reasoning
- Handle questions that result in critic rejections and retries
  - **Assert**: Rejected work is properly retried
  - **Assert**: Feedback is incorporated into retry attempts
  - **Assert**: Retry count is properly tracked
  - **Mock**: Simulate critic rejection scenarios
- Handle questions that hit retry limits
  - **Assert**: System gracefully handles retry limit exceeded
  - **Assert**: Final answer indicates failure appropriately
  - **Assert**: System doesn't crash or hang
  - **Mock**: Simulate scenarios that hit retry limits
- Handle questions with very long or very short answers
  - **Assert**: Very long questions are handled without truncation issues
  - **Assert**: Very short questions are properly formatted
  - **Assert**: Question length doesn't affect system stability
  - **Mock**: Create test questions with extreme lengths
- Handle questions with special characters and security concerns
  - **Assert**: Questions with emojis and unicode are handled correctly
  - **Assert**: Questions with HTML tags are handled safely
  - **Assert**: Questions with SQL injection attempts are handled safely
  - **Assert**: Questions with XSS attempts are handled safely
  - **Assert**: Questions with command injection attempts are handled safely
  - **Assert**: Questions with path traversal attempts are handled safely
  - **Assert**: Questions with null bytes and control characters are handled safely
  - **Assert**: Questions with very large numbers are handled correctly
  - **Assert**: Questions with repeated characters are handled correctly
  - **Assert**: Questions with malformed UTF-8 are handled safely
  - **Assert**: Questions with only whitespace, punctuation, numbers, or symbols are handled
  - **Assert**: Questions with mixed content types are handled correctly
  - **Mock**: Create test questions with various security and edge case scenarios
- Handle questions that require specific tool usage patterns
  - **Assert**: Specific tools are selected appropriately
  - **Assert**: Tool usage patterns are optimized
  - **Assert**: Tool dependencies are handled correctly
  - **Mock**: Create test questions requiring specific tool patterns
- Handle questions that trigger different critic decision paths
  - **Assert**: All critic decision paths are handled correctly
  - **Assert**: Different feedback types are processed appropriately
  - **Assert**: Decision logic is consistent and reliable
  - **Mock**: Create test scenarios that trigger different critic decisions

### Prompt Loading and Dynamic Prompt Building
- **Prompt File Loading**: Verify that each agent system prompt is loaded from the correct file in `src/prompts/`.
  - **Assert**: The content of each loaded prompt matches the content of the corresponding file.
  - **Mock**: Use a temporary or test prompt file with known content.
- **Prompt Placeholders**: Verify that all required placeholders (e.g., `{question}`, `{research_steps_and_results}`) are present in the loaded prompt strings.
  - **Assert**: Placeholders are found in the loaded prompt content.
- **Dynamic Prompt Building**: Verify that dynamic prompt construction (e.g., using `.format()` or helper functions like `make_research_steps_and_results`) correctly fills in placeholders with provided values.
  - **Assert**: The resulting prompt string contains the expected substituted values and no unfilled placeholders remain.
  - **Mock**: Use test values for all placeholders and check the output string.
- **Error Handling**: Verify that missing prompt files or missing placeholders raise appropriate errors and are logged.
  - **Assert**: FileNotFoundError or KeyError is raised and logged when appropriate.
  - **Mock**: Remove or rename a prompt file, or omit a placeholder in `.format()`.

## Test Implementation Status

### Current Test Files
1. **test_input_interface.py** - Tests input interface initialization and state management
2. **test_orchestrator.py** - Tests orchestrator 4-step process and routing logic
3. **test_planner.py** - Tests planner agent functionality and error handling
4. **test_researcher.py** - Tests researcher agent and subgraph integration
5. **test_expert.py** - Tests expert agent and subgraph integration
6. **test_critic.py** - Tests critic agent functionality for all agent types
7. **test_finalizer.py** - Tests finalizer agent functionality
8. **test_communication.py** - Tests inter-agent communication system
9. **test_error_handling.py** - Tests error handling utilities and functions
10. **test_error_handling_logging.py** - Tests comprehensive error handling and logging
11. **test_integration.py** - Tests end-to-end workflows and system integration
12. **test_edge_cases.py** - Tests edge cases and security scenarios
13. **test_performance.py** - Tests retry logic and performance scenarios
14. **test_routing.py** - Tests routing logic and conditional edges

### Test Coverage Summary
- **Total Tests**: 213 tests across all files
- **Test Status**: All tests passing (100% success rate)
- **Coverage Areas**: All major components, error handling, edge cases, integration scenarios
- **Mock Strategy**: Comprehensive mocking of LLMs, tools, subgraphs, and external dependencies
- **Error Handling**: Full error handling and logging implementation tested
- **State Management**: Complete state validation and management tested
- **Security**: Extensive edge case and security scenario testing

### Key Test Features
- **Error Handling**: All agents use `handle_agent_error()` for consistent error management
- **State Validation**: `validate_state()` and `validate_llm_response()` ensure data integrity
- **Logging**: Comprehensive logging with component context throughout the system
- **Retry Logic**: Robust retry mechanism with configurable limits
- **Security**: Extensive testing of malicious input handling
- **Integration**: Complete end-to-end workflow testing
- **Edge Cases**: Comprehensive edge case coverage including boundary conditions