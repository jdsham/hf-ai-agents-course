# Multi-Agent System Tests

This directory contains comprehensive unit tests for the multi-agent system based on the specifications in `docs/unit_tests.md`.

## Test Structure

The tests are organized into the following files:

- `conftest.py` - Pytest configuration and fixtures
- `test_communication.py` - Tests for communication functionality
- `test_input_interface.py` - Tests for input interface functionality
- `test_orchestrator.py` - Tests for orchestrator functionality
- `test_planner.py` - Tests for planner functionality
- `test_researcher.py` - Tests for researcher functionality
- `test_expert.py` - Tests for expert functionality
- `test_critic.py` - Tests for critic functionality
- `test_finalizer.py` - Tests for finalizer functionality
- `test_routing.py` - Tests for routing functionality
- `test_error_handling.py` - Tests for error handling
- `test_error_handling_logging.py` - Tests for error handling, logging, and state validation
- `test_performance.py` - Tests for retry logic and infinite loop prevention
- `test_integration.py` - Tests for integration scenarios
- `test_edge_cases.py` - Tests for edge cases and security

## Running the Tests

### Prerequisites

Install the test dependencies:

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

From the project root directory:

```bash
pytest tests/
```

### Run Specific Test Files

```bash
# Run only communication tests
pytest tests/test_communication.py

# Run only planner tests
pytest tests/test_planner.py

# Run only integration tests
pytest tests/test_integration.py
```

### Run Tests with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Tests with Verbose Output

```bash
pytest tests/ -v
```

### Run Tests and Stop on First Failure

```bash
pytest tests/ -x
```

## Test Categories

### 1. Communication Tests
- Agent message logging
- Message retrieval between agents
- Message structure validation
- No message duplication

### 2. Input Interface Tests
- Default state initialization
- Question extraction
- State variable setup

### 3. Orchestrator Tests
- Step management
- Critic rejection/acceptance logic
- Next step routing
- Retry mechanism

### 4. Agent Tests (Planner, Researcher, Expert, Critic, Finalizer)
- Message processing
- State updates
- LLM interaction mocking
- Completion message sending
- Error handling

### 5. Routing Tests
- Correct node routing
- Invalid step handling
- Edge case management

### 6. Error Handling Tests
- Network failures
- Invalid inputs
- Malformed responses
- Tool failures
- Memory issues

### 7. Error Handling and Logging Tests
- Error state management
- State validation
- LLM response validation
- Logging verification
- Error recovery mechanisms
- Component-specific error handling

### 8. Retry Logic Tests
- Infinite loop prevention
- Retry count tracking
- Retry limit enforcement
- System termination on repeated failures
- Retry count state preservation

### 9. Integration Tests
- End-to-end workflows
- Agent communication
- State management
- Data flow
- System robustness

### 10. Edge Cases Tests
- Various question types
- Empty inputs
- Very long inputs
- Special characters
- Security vulnerabilities
- Unicode handling

## Mocking Strategy

The tests use comprehensive mocking to isolate the system under test:

- **LLM Mocking**: All LLM calls are mocked to return predictable structured outputs
- **Tool Mocking**: External tool calls (web search, Wikipedia, etc.) are mocked
- **Network Mocking**: HTTP requests and network operations are mocked
- **State Isolation**: Each test uses clean state to prevent interference
- **Logging Mocking**: Logger calls are mocked to verify appropriate log messages are generated

## Test Data

Test fixtures provide:
- Empty graph state for testing
- Sample agent messages
- Mock LLM responses
- Various question types

## Assertion Criteria

Each test includes specific assertions that verify:
- Correct state updates
- Proper message handling
- Expected function behavior
- Error conditions
- Performance characteristics

## Continuous Integration

These tests are designed to run in CI/CD pipelines and provide:
- Fast execution
- Reliable results
- Comprehensive coverage
- Clear failure messages

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use appropriate mocking
3. Include clear assertions
4. Add descriptive docstrings
5. Update this README if adding new test categories 