## Outline Prompt:

I want to write a somewhat basic test document. It does not need to test performance, user experience, or security.
The test document needs to cover unit tests, integration tests, and system tests for my multi-agent system and entry point code.
The test document MUST be written in a manner that test code can be written from it.

Some context about the tests:
- They will be written using pytest and pytest-mock.
- python's unittest module can be used if needed, but preference for pytest and pytest-mock
- Unit Tests: Individual agent functions, validation utilities, state management
- Integration Tests: Agent communication, coordination mechanisms, system workflows
- System Tests: Complete multi-agent system behavior

The end goal of our conversation is to have you write the test document for me.
Let's start with creating a document outline.
Assume you have access to the architecture and design documents, and the source code.


## Section 1 Meta Prompt:
I want you to write section 1 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
What would be a good prompt to get you to write section 1 the way I want it written?


## Section 1 LLM generated prompt:
Write Section 1 (Introduction & Overview) of the TESTING.md file with the following requirements:
Purpose and Scope (1.1):
- Define the specific objectives for testing this multi-agent system
- Clearly state what will and won't be tested (excluding performance, UX, security)
- Specify the scope covers unit, integration, and system tests
Testing Objectives (1.2):
- List specific goals for each testing level (unit/integration/system)
- Focus on agent behaviors, communication, coordination, and emergent properties
- Emphasize testing static behavior, not LLM outputs
System Overview (1.3):
- Provide a high-level description of the multi-agent architecture
- Explain the main components (planner, researcher, expert, critic, finalizer)
- Describe the workflow and coordination mechanisms
- Keep it concise but informative for test developers
Testing Framework and Tools (1.4):
- Specify pytest and pytest-mock as primary tools
- Mention unittest as backup option
- Include any specific testing utilities or frameworks needed
- Reference the existing test structure in the project
Style Requirements:
- Write in clear, technical language suitable for developers
- Be specific and actionable (not vague or high-level)
- Include concrete examples where helpful
- Keep each subsection focused and concise
- Use bullet points and structured formatting for readability


## Section 2 Meta Prompt:
I want you to write section 2 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
What would be a good prompt to get you to write section 2 the way I want it written?
Write the prompt you generated as raw markdown.


## Section 2 LLM generated Prompt:
Write Section 2 (Test Environment & Setup) of the TESTING.md file with the following requirements:

**Dependencies and Requirements (2.1):**
- List all required Python packages and versions for testing
- Specify system requirements (OS, Python version, etc.)
- Include any external tools or services needed
- Reference the existing requirements files in the project

**Test Data and Fixtures (2.2):**
- Define the test data structures needed (agent states, messages, configurations)
- Specify fixture requirements for different test scenarios
- Include sample data examples for common test cases
- Describe how test data should be organized and managed

**Mocking Strategy (2.3):**
- Detail what external dependencies need mocking (LLMs, APIs, file systems)
- Provide specific mocking patterns and code examples
- Explain how to mock agent interactions and communication
- Include mock data configurations for different scenarios

**Test Organization Structure (2.4):**
- Define the exact file and directory structure for tests
- Specify naming conventions for test files and functions
- Explain how tests should be grouped and organized
- Include examples of test file organization

**Style Requirements:**
- Write in clear, technical language suitable for developers
- Be specific and actionable with concrete examples
- Include code snippets and configuration examples
- Use structured formatting with bullet points and code blocks
- Focus on implementation details that developers can directly use


## Section 3 Meta Prompt:
I want you to write section 3 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
I am also worried that the length of section 3 is too much for you to write all at once.
What would be a good prompt that can be applied to all components individually to get you to write section 3 the way I want it written?
Write the prompt you generated as raw markdown.

## Section 3 Meta Prompt follow-up:
Be sure to specify which dependencies are to be mocked and which dependencies will be directly used.

## Section 3 LLM generated Prompt:
Write the test specifications for [COMPONENT_NAME] in Section 3 of the TESTING.md file with the following requirements:

**Component Information:**
- **Function/Class Name**: [EXACT_FUNCTION_NAME]
- **Location**: [FILE_PATH:LINE_NUMBER]
- **Purpose**: [BRIEF_DESCRIPTION_OF_WHAT_IT_DOES]

**Test Specifications Required:**

**Function Signature and Parameters:**
- List exact input parameters with types
- Specify expected return types
- Include any side effects or state changes

**Dependencies Analysis:**
- **Dependencies to Mock**: List external dependencies that need mocking (APIs, file systems, network calls, external services)
- **Dependencies to Use Directly**: List built-in functions, standard library functions, and internal functions that can be used without mocking
- **Mock Configuration**: Specify what each mocked dependency should return

**Test Cases to Include:**
- **Happy Path**: Normal operation with valid inputs
- **Edge Cases**: Boundary conditions and unusual inputs
- **Error Conditions**: Invalid inputs, missing data, failure scenarios
- **State Changes**: How the function affects system state

**Mock Configurations:**
- Provide specific mock setups for each external dependency
- Include sample mock data and responses
- Show how to configure mocks for different test scenarios
- Specify mock return values and behaviors

**Direct Usage Examples:**
- Show how to use built-in functions and standard library functions directly
- Provide examples of internal function calls that don't need mocking
- Explain when to use real implementations vs. mocks

**Assertion Specifications:**
- What to verify for each test case
- How to validate return values
- How to check state changes
- How to verify error conditions

**Code Examples:**
- Include actual test function examples
- Show mock configurations for external dependencies
- Show direct usage of built-in/standard library functions
- Provide assertion examples
- Include setup/teardown if needed

**Style Requirements:**
- Write in clear, technical language for developers
- Be specific and actionable with concrete examples
- Include actual code snippets that can be copied and used
- Use structured formatting with bullet points and code blocks
- Focus on implementation details that enable direct test writing
- Clearly distinguish between what needs mocking and what can be used directly

**Format the output as a subsection under the appropriate Section 3 category, following the existing document structure and style.**


## Section 4 Meta Prompt:
I want you to write section 4 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
I am also worried that the length of section 4 is too much for you to write all at once.
You can use the TESTING.md, DESIGN.md, and source code (main.py and multi_agent_system.py) to understand the specifics of the project.
What would be a good prompt that can be applied to all integration tests individually to get you to write section 4 the way I want it written?
Write the prompt you generated as raw markdown.

## Section 4 LLM generated Prompt:
Write the integration test specifications for [INTEGRATION_TEST_NAME] in Section 4 of the TESTING.md file with the following requirements:

**Integration Test Information:**
- **Test Name**: [EXACT_INTEGRATION_TEST_NAME]
- **Location**: [SECTION_4_SUBSECTION]
- **Purpose**: [BRIEF_DESCRIPTION_OF_WHAT_IT_TESTS_WHEN_COMPONENTS_WORK_TOGETHER]

**Integration Test Specifications Required:**

**Test Scope and Boundaries:**
- **Components Involved**: List the specific components/functions that interact in this integration test
- **Integration Points**: Specify where and how the components connect and communicate
- **Data Flow**: Describe the flow of data between components during the test
- **State Management**: Explain how state is shared and managed across components
- **Message Passing**: Describe how messages flow between components in the multi-agent system

**Test Setup Requirements:**
- **Mock Strategy**: Specify which components should be mocked vs. tested together
- **Test Data**: Define the test data needed to exercise the integration
- **Environment Setup**: Describe any special setup needed for the integration test
- **Dependencies**: List external dependencies that need to be available or mocked
- **Graph State Initialization**: How to set up GraphState for integration testing

**Test Scenarios to Include:**
- **Happy Path Integration**: Normal operation when all components work together correctly
- **Component Interaction Patterns**: Different ways components can interact and communicate
- **Data Transformation**: How data flows and transforms between components
- **Error Propagation**: How errors propagate through the integrated system
- **State Synchronization**: How state is maintained and synchronized across components
- **Message Flow**: How AgentMessages flow between orchestrator and agents
- **Retry Logic Integration**: How retry mechanisms work across multiple components
- **Critic Decision Integration**: How critic decisions affect the flow between components

**Mock Configurations:**
- **Partial Mocking**: Show how to mock some components while testing others together
- **Integration Boundaries**: Define clear boundaries between mocked and real components
- **Mock Data Setup**: Provide realistic mock data that exercises the integration
- **Mock Behavior**: Specify how mocks should behave to test integration scenarios
- **LLM Mocking**: How to mock LLM responses for integration testing
- **Tool Mocking**: How to mock external tools while testing component integration

**Assertion Specifications:**
- **Integration Verification**: What to verify about component interactions
- **Data Flow Validation**: How to validate data transformation across components
- **State Consistency**: How to verify state consistency across the integrated system
- **Error Handling**: How to verify error propagation and handling
- **Message Validation**: How to verify AgentMessage composition and flow
- **Graph State Validation**: How to verify GraphState updates across components
- **Performance Metrics**: What performance aspects to measure and verify

**Code Examples:**
- **Integration Test Functions**: Complete integration test functions
- **Test Setup and Teardown**: Proper setup and cleanup for integration tests
- **Mock Configurations**: How to configure mocks for integration testing
- **Assertion Examples**: Specific assertions for integration scenarios
- **Test Data Management**: How to manage test data for integration tests
- **Graph State Setup**: How to initialize and manage GraphState for tests
- **Agent Message Validation**: How to verify AgentMessage creation and flow

**Style Requirements:**
- Write in clear, technical language for developers
- Be specific and actionable with concrete examples
- Include actual code snippets that can be copied and used
- Use structured formatting with bullet points and code blocks
- Focus on integration details that enable direct test writing
- Clearly distinguish between unit testing and integration testing approaches
- Emphasize testing the "glue" between components rather than individual component behavior
- Follow the existing document structure and style from Section 3
- Include proper imports and mock configurations specific to the multi-agent system

**Format the output as a subsection under the appropriate Section 4 category, following the existing document structure and style.**

**Note**: This integration test should focus on testing how the specified components work together in the multi-agent system, not their individual behavior (which is covered in Section 3). The goal is to verify that components integrate correctly, communicate properly through the AgentMessage protocol, handle GraphState updates correctly, and manage the flow between orchestrator and agents as expected.


## Section 5 Meta Prompt:
I want you to write section 5 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
I am also worried that the length of section 5 is too much for you to write all at once.
You can use the TESTING.md, DESIGN.md, and source code (main.py and multi_agent_system.py) to understand the specifics of the project.
What would be a good prompt that can be applied to all system tests individually to get you to write section 5 the way I want it written?
Write the prompt you generated as raw markdown.

## Section 5 LLM generated Prompt:
Write the system test specifications for [EXACT_SYSTEM_TEST_NAME] in Section 5 of the TESTING.md file with the following requirements:

**System Test Information:**
- **Test Name**: [EXACT_SYSTEM_TEST_NAME]
- **Location**: [SECTION_5_SUBSECTION]
- **Purpose**: [BRIEF_DESCRIPTION_OF_WHAT_IT_TESTS_WHEN_THE_ENTIRE_SYSTEM_WORKS_TOGETHER]

**System Test Specifications Required:**

**Test Scope and System Boundaries:**
- **System Components Involved**: List all components that participate in this system test
- **System Integration Points**: Specify where and how all components connect and communicate in the complete system
- **End-to-End Data Flow**: Describe the complete flow of data through the entire system during the test
- **System State Management**: Explain how state is managed and synchronized across the entire system
- **System Message Flow**: Describe how messages flow through the complete multi-agent system

**System Test Setup Requirements:**
- **Mock Strategy**: Specify which external dependencies should be mocked vs. tested with real system components
- **System Test Data**: Define the complete test data needed to exercise the entire system workflow
- **System Environment Setup**: Describe any special setup needed for the complete system test
- **External Dependencies**: List all external dependencies that need to be mocked for system testing
- **System State Initialization**: How to set up the complete system state for end-to-end testing

**System Test Scenarios to Include:**
- **Happy Path System Test**: Complete end-to-end operation when all system components work together correctly
- **System Component Interaction Patterns**: Different ways all system components can interact and communicate
- **System Data Transformation**: How data flows and transforms through the entire system
- **System Error Propagation**: How errors propagate through the complete system
- **System State Synchronization**: How state is maintained and synchronized across the entire system
- **System Message Flow**: How AgentMessages flow through the complete multi-agent system
- **System Retry Logic**: How retry mechanisms work across the entire system
- **System Decision Making**: How system-level decisions emerge from agent interactions

**System Mock Configurations:**
- **Complete System Mocking**: Show how to mock all external dependencies while testing the real system
- **System Integration Boundaries**: Define clear boundaries between mocked external dependencies and real system components
- **System Mock Data Setup**: Provide realistic mock data that exercises the complete system workflow
- **System Mock Behavior**: Specify how mocks should behave to test complete system scenarios
- **LLM Mocking for System**: How to mock LLM responses for all agents in the complete system
- **External Service Mocking**: How to mock all external services while testing the complete system

**System Assertion Specifications:**
- **System Integration Verification**: What to verify about complete system interactions
- **System Data Flow Validation**: How to validate data transformation across the entire system
- **System State Consistency**: How to verify state consistency across the complete system
- **System Error Handling**: How to verify error propagation and handling across the system
- **System Message Validation**: How to verify AgentMessage flow through the complete system
- **System State Validation**: How to verify GraphState updates across the entire system
- **System Performance Metrics**: What performance aspects to measure and verify for the complete system

**System Test Code Examples:**
- **Complete System Test Functions**: Full end-to-end system test functions
- **System Test Setup and Teardown**: Proper setup and cleanup for complete system tests
- **System Mock Configurations**: How to configure mocks for complete system testing
- **System Assertion Examples**: Specific assertions for complete system scenarios
- **System Test Data Management**: How to manage test data for complete system tests
- **System State Setup**: How to initialize and manage complete system state for tests
- **System Message Validation**: How to verify complete AgentMessage flow through the system

**Style Requirements:**
- Write in clear, technical language for developers
- Be specific and actionable with concrete examples
- Include actual code snippets that can be copied and used
- Use structured formatting with bullet points and code blocks
- Focus on system-level details that enable direct test writing
- Clearly distinguish between unit testing, integration testing, and system testing approaches
- Emphasize testing the complete system behavior rather than individual component behavior
- Follow the existing document structure and style from Sections 3 and 4
- Include proper imports and mock configurations specific to the complete multi-agent system

**Format the output as a subsection under the appropriate Section 5 category, following the existing document structure and style.**

**Note**: This system test should focus on testing the complete multi-agent system as a unified whole, not individual components (Section 3) or component interactions (Section 4). The goal is to verify that the entire system works correctly end-to-end, demonstrates emergent behaviors, handles system-wide errors gracefully, and manages global state consistently across all agents and components.


## Section 6.1 Meta Prompt:
I want you to write section 6.1 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
I am also worried that the length of section 6.1 is too much for you to write all at once.
You can use the TESTING.md, DESIGN.md, and source code (main.py and multi_agent_system.py) to understand the specifics of the project.
What would be a good prompt that can be applied to all subsections in section 6.1 individually to get you to write section 6.1 the way I want it written?
Write the prompt you generated as raw markdown.

## Section 6.1 LLM generated Prompt:
Write the test infrastructure specifications for [SUBSECTION_NAME] in Section 6.1 of the TESTING.md file with the following requirements:

**Function Information:**
- Purpose: Define reusable test fixtures and setup utilities for [SPECIFIC_COMPONENT]
- Scope: Standardized test data, configurations, and helper functions used across multiple test suites
- Dependencies: pytest fixtures, mock objects, test data structures

**Signature and Parameters:**
- Fixture function signatures with proper typing
- Configuration parameters and default values
- Return types and data structures

**Dependencies:**
- pytest fixtures and decorators
- Mock libraries and configurations
- Test data generation utilities
- State management helpers

**Test Cases:**
- **Happy Path**: Standard fixture setup with typical test data
- **Edge Cases**: Minimal configurations, large datasets, special characters, empty states
- **Error Conditions**: Invalid configurations, missing dependencies, corrupted test data

**Mock Configurations:**
- Mock objects for external dependencies
- Partial mocking strategies for complex components
- Mock data generation patterns

**Direct Usage Examples:**
- How to use the fixture in test functions
- Parameter customization examples
- Integration with existing test patterns

**Assertion Specifications:**
- Validation of fixture setup correctness
- Data structure integrity checks
- Configuration completeness verification

**Code Examples:**
```python
# Example fixture definition and usage
@pytest.fixture
def [fixture_name]([parameters]):
    """[Description of what this fixture provides]"""
    # Setup code
    # Return test data/objects
```

Include all necessary imports, proper typing, and follow the established patterns from Sections 3-5. Focus on reusability and maintainability of test infrastructure.

## Section 6.2 Meta Prompt:
I want you to write section 6.2 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
I am also worried that the length of section 6.2 is too much for you to write all at once.
You can use the TESTING.md, DESIGN.md, and source code (main.py and multi_agent_system.py) to understand the specifics of the project.
What would be a good prompt that can be applied to all subsections in section 6.2 individually to get you to write section 6.2 the way I want it written?
Write the prompt you generated as raw markdown.

## Section 6.2 LLM generated Prompt:
Write the mock configuration specifications for [SUBSECTION_NAME] in Section 6.2 of the TESTING.md file with the following requirements:

**Function Information:**
- Purpose: Define standardized mock configurations and setup patterns for [SPECIFIC_COMPONENT]
- Scope: Reusable mock objects, patching strategies, and configuration templates used across multiple test suites
- Dependencies: unittest.mock, pytest-mock, patching decorators, mock object factories

**Signature and Parameters:**
- Mock configuration function signatures with proper typing
- Patching decorator patterns and parameter configurations
- Return types and mock object structures

**Dependencies:**
- `unittest.mock.Mock`, `unittest.mock.patch`, `unittest.mock.MagicMock`
- `pytest-mock` fixtures and utilities
- Mock object factories and builders
- Configuration templates and patterns

**Test Cases:**
- **Happy Path**: Standard mock configurations with typical behavior, normal response patterns
- **Edge Cases**: Complex mock chains, conditional responses, stateful mocks, large data structures
- **Error Conditions**: Mock failures, invalid configurations, missing dependencies, corrupted mock states

**Mock Configurations:**
- Mock object setup and configuration patterns
- Patching strategies for different component types
- Mock response templates and data structures
- Mock behavior customization and parameterization

**Direct Usage Examples:**
- How to apply the mock configuration in test functions
- Parameter customization and override examples
- Integration with existing test patterns and fixtures

**Assertion Specifications:**
- Validation of mock configuration correctness
- Mock object behavior verification
- Patching strategy effectiveness checks
- Configuration completeness and reusability verification

**Code Examples:**
```python
# Example mock configuration and usage
@patch('[MODULE_PATH].[COMPONENT_NAME]')
def test_with_mock_configuration(mock_component):
    """[Description of what this mock configuration provides]"""
    # Mock setup and configuration
    # Test implementation
    # Mock verification
```

Include all necessary imports, proper typing, and follow the established patterns from Sections 3-5 and 6.1. Focus on reusability, maintainability, and standardization of mock configurations across the test suite.

## Section 6.3 Meta Prompt:
I want you to write section 6.3 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
I am also worried that the length of section 6.3 is too much for you to write all at once.
You can use the TESTING.md, DESIGN.md, and source code (main.py and multi_agent_system.py) to understand the specifics of the project.
What would be a good prompt that can be applied to all subsections in section 6.3 individually to get you to write section 6.3 the way I want it written?
Write the prompt you generated as raw markdown.


## Section 6.3 LLM generated Prompt:
Write the test utility specifications for [SUBSECTION_NAME] in Section 6.3 of the TESTING.md file with the following requirements:

**Function Information:**
- Purpose: Define standardized test utility functions and helper components for [SPECIFIC_COMPONENT]
- Scope: Reusable utility functions, helper methods, and support tools used across multiple test suites
- Dependencies: pytest utilities, test data generators, assertion helpers, mock setup utilities

**Signature and Parameters:**
- Utility function signatures with proper typing
- Helper method parameters and default values
- Return types and utility object structures

**Dependencies:**
- `pytest` fixtures and utilities
- `unittest.mock` for mock setup
- Test data generation libraries
- Assertion and validation helpers

**Test Cases:**
- **Happy Path**: Standard utility functions with typical behavior, normal operation patterns, successful helper execution
- **Edge Cases**: Complex utility chains, conditional operations, stateful utilities, large data structures, performance optimization
- **Error Conditions**: Utility failures, invalid configurations, missing dependencies, corrupted utility states, validation errors

**Utility Configurations:**
- Utility function setup and configuration patterns
- Helper method strategies for different component types
- Utility response templates and data structures
- Utility behavior customization and parameterization

**Direct Usage Examples:**
- How to apply the utility functions in test functions
- Parameter customization and override examples
- Integration with existing test patterns and fixtures

**Assertion Specifications:**
- Validation of utility function correctness and completeness
- Utility object behavior verification
- Helper strategy effectiveness checks
- Configuration completeness and reusability verification

**Code Examples:**
```python
# Example utility function and usage
def [utility_name]([parameters]):
    """[Description of what this utility provides]"""
    # Utility implementation
    # Return utility result

# Example usage in tests
def test_with_utility_function():
    """[Description of utility usage in testing]"""
    # Utility setup and configuration
    # Test implementation
    # Utility verification
```

Include all necessary imports, proper typing, and follow the established patterns from Sections 3-5 and 6.1-6.2. Focus on reusability, maintainability, and standardization of test utilities across the test suite.

## Section 7 Meta Prompt:
I want you to write section 7 of the TESTING.md file. But I don't know how to properly instruct you to do it the way I want.
You can use the TESTING.md, DESIGN.md, and source code (main.py and multi_agent_system.py) to understand the specifics of the project.
What would be a good prompt that can to get you to write 7 the way I want it written?
Write the prompt you generated as raw markdown.

## Section 7 LLM generated Prompt:
Write the test execution strategy specifications for Section 7.1 of the TESTING.md file with the following requirements:

**Function Information:**
- Purpose: Define standardized test execution strategies and patterns for the multi-agent system test suite
- Scope: Test execution frameworks, execution patterns, test organization, and execution workflows
- Dependencies: pytest execution framework, test discovery, test categorization, execution optimization

**Strategy and Configuration:**
- Test execution patterns and workflows
- Test categorization and organization strategies
- Execution optimization and parallelization
- Test discovery and filtering mechanisms

**Implementation Details:**
- Execution strategy configuration patterns
- Test suite organization and categorization
- Execution workflow definitions
- Performance optimization strategies

**Direct Usage Examples:**
- How to execute different test categories (unit, integration, system)
- How to configure test execution parameters
- How to organize and run test suites
- How to optimize test execution performance

**Configuration Specifications:**
- Test execution configuration and parameters
- Test categorization and filtering options
- Execution workflow definitions
- Performance optimization settings

**Code Examples:**
```python
# Example execution configuration and usage
def [execution_function]([parameters]):
    """[Description of execution strategy]"""
    # Execution implementation
    # Return execution result

# Example usage in test execution
def test_execution_example():
    """[Description of execution example]"""
    # Execution setup and configuration
    # Test execution implementation
    # Result validation and reporting
```

Include all necessary imports, proper typing, and follow the established patterns from Sections 3-6. Focus on practical implementation, automation, and integration with the multi-agent system architecture. Provide comprehensive coverage of test execution strategies, test organization, execution workflows, and performance optimization for the multi-agent system test suite.


## Prompting to Write Code (Plan from LLM)
I want to be able to have you follow the TESTING.md document and write all the test files and test code.
However, I don't know how to get you to do it the right way.
There seems to be a lot of content to write and has to be done in multiple phases.
What would be the logical steps that you need to follow to write the test code correctly?


## Phase 1 Meta Prompting:
I want you to follow phase 1 of the plan in test_code_writing_plan.md.
What prompt do you need to be able to correctly do this?

## Phase 1 LLM generated prompt:
I want you to implement Phase 1 of the test infrastructure setup for the multi-agent system. Please create the complete test directory structure and implement all the test infrastructure utilities from Section 6 of the TESTING.md document.

**Requirements:**

1. **Create the test directory structure:**
   - Create `tests/` directory with subdirectories: `unit/`, `integration/`, `system/`, `performance/`
   - Create `tests/conftest.py` for shared pytest fixtures
   - Create `tests/__init__.py` files

2. **Implement Section 6.1 Test Fixtures in `tests/conftest.py`:**
   - **6.1.1 Agent Configuration Fixtures:** `agent_config_fixture`, `llm_fixture`, `agent_configs_fixture`, `minimal_agent_config_fixture`
   - **6.1.2 State Management Fixtures:** `graph_state_fixture`, `researcher_state_fixture`, `expert_state_fixture`, `agent_message_fixture`, `complete_workflow_state_fixture`, `edge_case_state_fixture`
   - **6.1.3 Mock Data Fixtures:** `mock_llm_response_fixture`, `mock_document_fixture`, `mock_external_service_fixture`, `mock_file_content_fixture`, `mock_tool_response_fixture`, `mock_error_response_fixture`

3. **Create `tests/utils/` directory with utility modules:**
   - **`tests/utils/mock_configurations.py`** - Implement Section 6.2 Mock Configurations:
     - **6.2.1 LLM Mock Configurations:** `configure_llm_mock`, `configure_llm_factory_mock`, `configure_structured_output_mock`, `configure_multiple_llm_mocks`, `configure_llm_error_mock`
     - **6.2.2 External Service Mocks:** `configure_youtube_service_mock`, `configure_wikipedia_service_mock`, `configure_web_search_service_mock`, `configure_browser_mcp_service_mock`, `configure_file_loader_service_mock`, `configure_external_service_error_mock`, `configure_multiple_external_services_mock`
     - **6.2.3 File System Mocks:** `configure_file_io_mock`, `configure_path_operations_mock`, `configure_json_operations_mock`, `configure_prompt_file_mock`, `configure_file_system_error_mock`, `configure_large_file_mock`, `configure_special_characters_file_mock`, `configure_jsonl_file_mock`, `configure_directory_structure_mock`

   - **`tests/utils/test_utilities.py`** - Implement Section 6.3 Test Utilities:
     - **6.3.1 Test Data Generators:** `generate_test_questions`, `generate_agent_messages`, `generate_test_responses`, `generate_test_documents`, `generate_test_state_data`, `generate_test_config_data`
     - **6.3.2 Assertion Helpers:** `assert_agent_message_valid`, `assert_graph_state_valid`, `assert_llm_response_valid`, `assert_agent_config_valid`, `assert_document_valid`, `assert_workflow_progression_valid`, `assert_error_handling_valid`, `assert_performance_valid`
     - **6.3.3 Mock Setup Utilities:** `setup_complete_mock_environment`, `setup_agent_mocks`, `setup_external_service_mocks`, `setup_file_system_mocks`, `mock_environment_context`, `setup_error_scenario_mocks`, `setup_performance_test_mocks`, `setup_large_data_mocks`

4. **Follow the exact specifications from TESTING.md:**
   - Use the exact function signatures, parameters, and return types specified
   - Include all the test cases (happy path, edge cases, error conditions) as specified
   - Implement all the code examples exactly as written in the document
   - Include proper imports and dependencies
   - Follow the established patterns and structure

5. **Create proper Python modules:**
   - Add `__init__.py` files to make directories proper Python packages
   - Include proper imports and exports
   - Ensure all functions are properly typed and documented

6. **Test the infrastructure:**
   - Create simple test files to verify the infrastructure works correctly
   - Ensure all fixtures and utilities can be imported and used
   - Verify that the mock configurations work as expected

Please implement this infrastructure exactly as specified in the TESTING.md document, following all the detailed specifications, function signatures, and code examples provided in Sections 6.1, 6.2, and 6.3.