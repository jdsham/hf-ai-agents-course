"""
Pytest configuration and fixtures for multi-agent system tests.
"""
import pytest
import sys
import os
from typing import Dict, Any, List

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import (
    GraphState, ResearcherState, ExpertState, AgentMessage,
    llm_planner, llm_researcher, llm_expert, llm_critic, llm_finalizer
)


@pytest.fixture
def mock_llm_planner(mocker):
    """Mock the planner LLM to return predictable structured outputs."""
    mock = mocker.patch('multi_agent_system.llm_planner')
    mock.with_structured_output.return_value.invoke.return_value = {
        "research_steps": ["Research step 1", "Research step 2"],
        "expert_steps": ["Expert step 1", "Expert step 2"]
    }
    return mock


@pytest.fixture
def mock_llm_researcher(mocker):
    """Mock the researcher LLM to return predictable structured outputs."""
    mock = mocker.patch('multi_agent_system.llm_researcher')
    mock.with_structured_output.return_value.invoke.return_value = {
        "result": "Research result content"
    }
    return mock


@pytest.fixture
def mock_llm_expert(mocker):
    """Mock the expert LLM to return predictable structured outputs."""
    mock = mocker.patch('multi_agent_system.llm_expert')
    mock.with_structured_output.return_value.invoke.return_value = {
        "expert_answer": "Expert answer content",
        "reasoning_trace": "Expert reasoning trace"
    }
    return mock


@pytest.fixture
def mock_llm_critic(mocker):
    """Mock the critic LLM to return predictable structured outputs."""
    mock = mocker.patch('multi_agent_system.llm_critic')
    mock.with_structured_output.return_value.invoke.return_value = {
        "decision": "approve",
        "feedback": "Good work"
    }
    return mock


@pytest.fixture
def mock_llm_finalizer(mocker):
    """Mock the finalizer LLM to return predictable structured outputs."""
    mock = mocker.patch('multi_agent_system.llm_finalizer')
    mock.with_structured_output.return_value.invoke.return_value = {
        "final_answer": "Final answer content",
        "final_reasoning_trace": "Final reasoning trace"
    }
    return mock


@pytest.fixture
def mock_tools(mocker):
    """Mock all external tool calls."""
    mock_research_tools = mocker.patch('multi_agent_system.research_tools')
    mock_expert_tools = mocker.patch('multi_agent_system.expert_tools')
    
    # Mock research tools
    mock_research_tools.__iter__.return_value = [
        mocker.Mock(name="web_search", return_value="Search result"),
        mocker.Mock(name="wikipedia", return_value="Wikipedia content"),
        mocker.Mock(name="youtube_transcript", return_value="Transcript content"),
        mocker.Mock(name="file_reader", return_value="File content")
    ]
    
    # Mock expert tools
    mock_expert_tools.__iter__.return_value = [
        mocker.Mock(name="calculator", return_value="42"),
        mocker.Mock(name="unit_converter", return_value="100 ft"),
        mocker.Mock(name="python_repl", return_value="Execution result")
    ]
    
    return mock_research_tools, mock_expert_tools


@pytest.fixture
def mock_network(mocker):
    """Mock network calls to simulate success/failure scenarios."""
    mock_run = mocker.patch('multi_agent_system.asyncio.run')
    mock_client = mocker.patch('multi_agent_system.streamablehttp_client')
    
    mock_run.return_value = [mocker.Mock(), mocker.Mock(), mocker.Mock()]
    mock_client.return_value.__aenter__.return_value = (mocker.Mock(), mocker.Mock(), mocker.Mock())
    
    return mock_run, mock_client


@pytest.fixture
def sample_question():
    """Sample question for testing."""
    return "What is CRISPR and who invented it?"


@pytest.fixture
def empty_graph_state():
    """Create an empty graph state for testing."""
    return {
        "messages": [],
        "agent_messages": [],
        "question": "",
        "files": None,
        "research_steps": [],
        "expert_steps": [],
        "current_research_index": -1,
        "researcher_states": {},
        "research_results": [],
        "expert_state": None,
        "expert_answer": "",
        "expert_reasoning": "",
        "critic_planner_decision": "",
        "critic_planner_feedback": "",
        "critic_researcher_decision": "",
        "critic_researcher_feedback": "",
        "critic_expert_decision": "",
        "critic_expert_feedback": "",
        "final_answer": "",
        "final_reasoning_trace": "",
        "current_step": "",
        "next_step": "",
        "retry_count": 0,
        "retry_limit": 5,
        "error": None,
        "error_component": None
    }


@pytest.fixture
def sample_agent_message():
    """Sample agent message for testing."""
    return {
        "sender": "orchestrator",
        "receiver": "planner",
        "type": "instruction",
        "content": "Develop a plan to answer the question",
        "step_id": None
    }


@pytest.fixture
def sample_researcher_state():
    """Sample researcher state for testing."""
    return {
        "messages": [],
        "step_index": 0,
        "result": None
    }


@pytest.fixture
def sample_expert_state():
    """Sample expert state for testing."""
    return {
        "messages": [],
        "question": "Test question",
        "research_steps": ["Research step 1"],
        "research_results": ["Research result 1"],
        "expert_answer": "",
        "expert_reasoning": ""
    }


@pytest.fixture
def mock_subgraphs(mocker):
    """Mock the compiled subgraphs."""
    mock_researcher = mocker.patch('multi_agent_system.compiled_researcher_graph')
    mock_expert = mocker.patch('multi_agent_system.compiled_expert_graph')
    
    mock_researcher.invoke.return_value = {
        "messages": [mocker.Mock()],
        "step_index": 0,
        "result": "Research result"
    }
    
    mock_expert.invoke.return_value = {
        "messages": [mocker.Mock()],
        "question": "Test question",
        "research_steps": ["Research step 1"],
        "research_results": ["Research result 1"],
        "expert_answer": "Expert answer",
        "expert_reasoning": "Expert reasoning"
    }
        
    return mock_researcher, mock_expert 