"""
Tests for Integration functionality as specified in unit_tests.md
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from multi_agent_system import (
    input_interface, orchestrator, planner, researcher_node, expert, 
    critic, finalizer, route_from_orchestrator
)


class TestIntegration:
    """Test integration functionality."""

    def test_end_to_end_workflow_simple_question(self):
        """Test complete end-to-end workflow with simple question."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is 2 + 2?")]
        }

        # Act
        # Step 1: Input interface
        state = input_interface(initial_state)
        assert state["question"] == "What is 2 + 2?"
        assert state["next_step"] == "planner"

        # Step 2: Orchestrator sets current_step
        state["current_step"] = "planner"

        # Step 3: Planner
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": [],
                "expert_steps": ["Calculate 2 + 2"]
            }
            state = planner(state)
            assert state["research_steps"] == []
            assert state["expert_steps"] == ["Calculate 2 + 2"]

        # Step 4: Orchestrator routes to critic
        state["current_step"] = "critic_planner"
        # Add message for critic to process
        state["agent_messages"].append({
            "sender": "orchestrator", 
            "receiver": "critic_planner", 
            "type": "instruction", 
            "content": "Review plan", 
            "step_id": None
        })

        # Step 5: Critic approves plan
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good plan"
            }
            state = critic(state)
            assert state["critic_planner_decision"] == "approve"
        
        # Step 6: Orchestrator routes to expert (since no research needed)
        state["current_step"] = "expert"
        # Add message for expert to process
        state["agent_messages"].append({
            "sender": "orchestrator", 
            "receiver": "expert", 
            "type": "instruction", 
            "content": "Calculate 2 + 2", 
            "step_id": None
        })

        # Step 7: Expert calculates answer
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "What is 2 + 2?",
                "research_steps": [],
                "research_results": [],
                "expert_answer": "4",
                "expert_reasoning": "2 + 2 = 4"
            }
            state = expert(state)
            assert state["expert_answer"] == "4"
        
        # Step 8: Orchestrator routes to critic_expert
        state["current_step"] = "critic_expert"
        # Add message for critic_expert to process
        state["agent_messages"].append({
            "sender": "orchestrator", 
            "receiver": "critic_expert", 
            "type": "instruction", 
            "content": "Review expert answer", 
            "step_id": None
        })

        # Step 9: Critic_expert approves expert answer
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good answer"
            }
            state = critic(state)
            assert state["critic_expert_decision"] == "approve"
        
        # Step 10: Orchestrator routes to finalizer
        state["current_step"] = "finalizer"
        
        # Step 11: Finalizer provides final answer
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "2 + 2 = 4",
                "final_reasoning_trace": "Simple arithmetic calculation"
            }
            state = finalizer(state)
            assert state["final_answer"] == "2 + 2 = 4"
        
        # Assert: Complete workflow produces expected result
        assert state["final_answer"] == "2 + 2 = 4"

    def test_end_to_end_workflow_complex_question(self):
        """Test complete end-to-end workflow with complex question requiring research."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR and who invented it?")]
        }
        
        # Act
        # Step 1: Input interface
        state = input_interface(initial_state)
        assert "CRISPR" in state["question"]
        
        # Step 2: Planner
        state["current_step"] = "planner"
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Research CRISPR definition", "Research CRISPR inventors"],
                "expert_steps": ["Define CRISPR", "Identify inventors"]
            }
            state = planner(state)
            assert len(state["research_steps"]) == 2
        
        # Step 3: Critic approves plan
        state["current_step"] = "critic_planner"
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good plan"
            }
            state = critic(state)
        
        # Step 4: Researcher for first step
        state["current_step"] = "researcher"
        state["current_research_index"] = 0
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "step_index": 0,
                "result": "CRISPR is a gene editing technology"
            }
            state = researcher_node(state)
            assert state["research_results"][0] == "CRISPR is a gene editing technology"
        
        # Step 5: Researcher for second step
        state["current_research_index"] = 1
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "step_index": 1,
                "result": "CRISPR was invented by Jennifer Doudna and Emmanuelle Charpentier"
            }
            state = researcher_node(state)
            assert state["research_results"][1] == "CRISPR was invented by Jennifer Doudna and Emmanuelle Charpentier"
        
        # Step 6: Expert
        state["current_step"] = "expert"
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "What is CRISPR and who invented it?",
                "research_steps": ["Research CRISPR definition", "Research CRISPR inventors"],
                "research_results": ["CRISPR is a gene editing technology", "CRISPR was invented by Jennifer Doudna and Emmanuelle Charpentier"],
                "expert_answer": "CRISPR is a gene editing technology invented by Doudna and Charpentier",
                "expert_reasoning": "Based on research findings"
            }
            state = expert(state)
        
        # Step 7: Critic approves expert work
        state["current_step"] = "critic_expert"
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "approve",
                "feedback": "Good answer"
            }
            state = critic(state)
        
        # Step 8: Finalizer
        state["current_step"] = "finalizer"
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "CRISPR is a revolutionary gene editing technology co-invented by Jennifer Doudna and Emmanuelle Charpentier.",
                "final_reasoning_trace": "Based on comprehensive research and expert analysis"
            }
            state = finalizer(state)
        
        # Assert: Complete workflow produces comprehensive result
        assert "CRISPR" in state["final_answer"]
        assert "Doudna" in state["final_answer"]
        assert "Charpentier" in state["final_answer"]

    def test_agent_communication_integration(self):
        """Test integration of agent communication system."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        state["current_step"] = "planner"
        
        # Test planner communication
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Research CRISPR"],
                "expert_steps": ["Define CRISPR"]
            }
            state = planner(state)
        
        # Assert: Messages are properly logged
        assert len(state["agent_messages"]) > 0
        assert any(msg["sender"] == "planner" for msg in state["agent_messages"])

    def test_state_management_integration(self):
        """Test integration of state management across all agents."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        
        # Test state propagation through agents
        state["current_step"] = "planner"
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Research CRISPR"],
                "expert_steps": ["Define CRISPR"]
            }
            state = planner(state)
        
        # Assert: State is properly managed and propagated
        assert state["research_steps"] == ["Research CRISPR"]
        assert state["expert_steps"] == ["Define CRISPR"]
        assert state["question"] == "What is CRISPR?"

    def test_routing_integration(self):
        """Test integration of routing system with all agents."""
        # Arrange
        test_steps = ["planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer"]
        
        # Act & Assert: Routing works for all agent types
        for step in test_steps:
            state = {"current_step": step}
            route = route_from_orchestrator(state)
            
            if step.startswith("critic_"):
                assert route == "critic"
            else:
                assert route == step

    def test_error_handling_integration(self):
        """Test integration of error handling across the system."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        state["current_step"] = "planner"
        
        # Test error handling in planner
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Network error")
            
            # Act
            result = planner(state)
            # Assert: Error state is set
            assert result["error"] is not None
            assert "Network error" in result["error"]
            assert result["error_component"] == "planner"

    def test_retry_mechanism_integration(self):
        """Test integration of retry mechanisms across the system."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        state["current_step"] = "planner"
        
        # Test retry mechanism
        state["retry_count"] = 1
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Research CRISPR"],
                "expert_steps": ["Define CRISPR"]
            }
            state = planner(state)
        
        # Assert: Retry mechanism works
        assert state["retry_count"] == 1

    def test_data_flow_integration(self):
        """Test integration of data flow between agents."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        
        # Test data flow: Input → Planner → Researcher → Expert → Finalizer
        state["current_step"] = "planner"
        with patch('multi_agent_system.llm_planner') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "research_steps": ["Research CRISPR"],
                "expert_steps": ["Define CRISPR"]
            }
            state = planner(state)
        
        # Test researcher data flow
        state["current_step"] = "researcher"
        state["current_research_index"] = 0
        with patch('multi_agent_system.compiled_researcher_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "step_index": 0,
                "result": "CRISPR is a gene editing tool"
            }
            state = researcher_node(state)
        
        # Test expert data flow
        state["current_step"] = "expert"
        # Add message for expert to process
        state["agent_messages"].append({
            "sender": "orchestrator", 
            "receiver": "expert", 
            "type": "instruction", 
            "content": "Perform expert steps", 
            "step_id": None
        })
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "What is CRISPR?",
                "research_steps": ["Research CRISPR"],
                "research_results": ["CRISPR is a gene editing tool"],
                "expert_answer": "CRISPR is a gene editing technology",
                "expert_reasoning": "Based on research"
            }
            state = expert(state)

        # Assert: Data flows correctly through the system
        assert state["research_steps"] == ["Research CRISPR"]
        assert state["research_results"] == ["CRISPR is a gene editing tool"]
        assert state["expert_answer"] == "CRISPR is a gene editing technology"

    def test_critic_integration_with_all_agents(self):
        """Test integration of critic with all other agents."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        
        # Test critic integration with planner
        state["current_step"] = "critic_planner"
        state["research_steps"] = ["Research CRISPR"]
        state["expert_steps"] = ["Define CRISPR"]
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "critic_planner", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.llm_critic') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "decision": "reject",
                "feedback": "Need more detail"
            }
            state = critic(state)
        
        # Assert: Critic properly integrates with planner
        assert state["critic_planner_decision"] == "reject"

    def test_finalizer_integration_with_all_context(self):
        """Test integration of finalizer with all previous agent outputs."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act
        state = input_interface(initial_state)
        
        # Set up all agent outputs
        state["research_steps"] = ["Research CRISPR definition"]
        state["research_results"] = ["CRISPR is a gene editing technology"]
        state["expert_answer"] = "CRISPR is a revolutionary gene editing tool"
        state["expert_reasoning"] = "Based on research findings"
        state["current_step"] = "finalizer"
        
        with patch('multi_agent_system.llm_finalizer') as mock_llm:
            mock_llm.with_structured_output.return_value.invoke.return_value = {
                "final_answer": "CRISPR is a revolutionary gene editing technology with wide applications.",
                "final_reasoning_trace": "Synthesized from research and expert analysis"
            }
            state = finalizer(state)
        
        # Assert: Finalizer integrates all context
        assert "revolutionary" in state["final_answer"]
        assert "Synthesized" in state["final_reasoning_trace"]

    def test_system_robustness_integration(self):
        """Test overall system robustness and integration."""
        # Arrange
        initial_state = {
            "messages": [HumanMessage(content="What is CRISPR?")]
        }
        
        # Act: Test system can handle various scenarios
        state = input_interface(initial_state)
        
        # Test with empty research steps
        state["research_steps"] = []
        state["research_results"] = []
        state["current_step"] = "expert"
        state["agent_messages"] = [
            {"sender": "orchestrator", "receiver": "expert", "type": "instruction", "content": "test", "step_id": None}
        ]
        
        with patch('multi_agent_system.compiled_expert_graph') as mock_graph:
            mock_graph.invoke.return_value = {
                "messages": [Mock()],
                "question": "What is CRISPR?",
                "research_steps": [],
                "research_results": [],
                "expert_answer": "CRISPR is a gene editing technology",
                "expert_reasoning": "Based on general knowledge"
            }
            state = expert(state)
        
        # Assert: System handles edge cases robustly
        assert state["expert_answer"] == "CRISPR is a gene editing technology" 