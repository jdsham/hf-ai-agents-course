# Multi-Agent System for GAIA Level 1 Questions

*Inspired by [AWorld: Dynamic Multi-Agent System with Stable Maneuvering for Robust GAIA Problem Solving](https://arxiv.org/html/2508.09889v1#bib)*

A self-contained learning project that demonstrates how to build a multi-agent system to answer complex reasoning questions. This project implements a streamlined multi-agent architecture inspired by AWorld's dynamic supervision approach, achieving 68% accuracy on GAIA Level 1 questions.

## 🎯 What This Project Is

This is a **learning project** that shows how to:
- Build a multi-agent system with dynamic supervision and maneuvering
- Implement an executor agent with comprehensive tool access
- Use agent-as-a-tool architecture for quality control
- Evaluate AI systems using Opik for observability and metrics
- Handle complex reasoning tasks through coordinated agent collaboration

**Note**: This is not a production system or actively maintained project - it's designed for educational purposes and experimentation. The project is essentially complete with the successful implementation and evaluation of the AWorld-inspired architecture.

## 🏗️ System Architecture

The system uses a streamlined multi-agent architecture inspired by AWorld's dynamic supervision approach:

1. **🧠 Executor Agent** - The main brain of the system that:
   - Analyzes tasks and breaks them down into sub-tasks
   - Determines which tools to use for each sub-task
   - Orchestrates the overall problem-solving workflow
   - Invokes the guard agent when help or review is needed

2. **🛠️ Tool Suite** - Comprehensive set of tools for information gathering and processing:
   - **Search Tools**: Tavily search, Wikipedia search, YouTube transcript extraction
   - **Document Tools**: Excel, PowerPoint, PDF, and text file loaders
   - **Computation Tools**: Calculator, unit conversion, Python REPL
   - **Guard Tool**: Agent-as-a-tool for critiquing and course correction

3. **🛡️ Guard Agent** - Embedded as a tool that provides:
   - Dynamic supervision and intervention
   - Course correction during problem-solving
   - Final answer review and validation
   - Quality control throughout the reasoning process

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- Tavily API key
- Local Opik server (for evaluation)

### Installation
```bash
git clone <repository-url>
cd hf-ai-agents-course
pip install -r requirements.txt
```

### Environment Setup
```bash
export OPENAI_API_KEY="your-openai-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

### Basic Usage
```bash
# Answer questions using the multi-agent system
cd src/
python main.py

# Run evaluation with Opik observability
cd opik_eval/
python evaluate_gaia.py
```

## 📁 Project Structure

```
├── src/                          # Core multi-agent system
│   ├── main.py                   # Entry point for running the system
│   └── [multi-agent system files] # Executor agent and tool implementations
├── opik_eval/                    # Evaluation and observability
│   ├── evaluate_gaia.py          # GAIA evaluation script with Opik integration
│   └── [evaluation utilities]    # Opik experiment recording and metrics
└── docs/                         # Documentation
```

## 🧪 Evaluation & Results

### Performance
The system was evaluated on all 53 GAIA Level 1 questions using the official GAIA leaderboard scoring function:
- **Accuracy**: 68% (36 out of 53 questions answered correctly)
- **Scoring**: Exact match evaluation (1 for correct, 0 for incorrect)
- **Target**: Originally aimed for 30% accuracy, significantly exceeded expectations

### Evaluation Methodology
- Uses the official GAIA scoring function for exact answer matching
- Records full agent traces to Opik for observability and analysis
- Evaluates performance across the complete GAIA Level 1 dataset
- Provides detailed experiment tracking and metrics through Opik

## 🔧 Key Components

### 1. Executor Agent
The main orchestrator that analyzes questions, breaks them down into sub-tasks, and coordinates tool usage to arrive at solutions.

### 2. Tool Integration
Comprehensive suite of tools including:
- **Information Gathering**: Web search, document processing, video transcripts
- **Computation**: Calculator, unit conversion, Python code execution
- **Quality Control**: Guard agent for supervision and course correction

### 3. Opik Integration
- **Observability**: Full trace recording of agent interactions
- **Evaluation**: Automated scoring and metrics collection
- **Experiment Tracking**: Detailed analysis of agent performance

### 4. Dynamic Supervision
Inspired by AWorld's maneuvering mechanism, the guard agent provides:
- Proactive course correction during problem-solving
- Final answer validation
- Quality assurance throughout the reasoning process

## 🎓 Learning Objectives

This project demonstrates:
- **Streamlined Multi-Agent Architecture**: Moving from complex 5-agent systems to efficient executor-guard patterns
- **Dynamic Supervision**: Implementing AWorld-inspired maneuvering mechanisms
- **Tool Integration**: Comprehensive tool suite for diverse problem types
- **Observability**: Using Opik for detailed system analysis and evaluation
- **Performance Optimization**: Achieving significant accuracy improvements through architectural refinement

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built for learning and experimentation** 🚀

*This project successfully demonstrates the effectiveness of streamlined multi-agent architectures with dynamic supervision, achieving 68% accuracy on GAIA Level 1 questions while maintaining simplicity and reliability.*
