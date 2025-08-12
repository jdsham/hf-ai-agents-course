# Multi-Agent System for GAIA Level 1 Questions

A self-contained learning project that demonstrates how to build a multi-agent system to answer complex reasoning questions. This project implements a coordinated workflow of specialized AI agents working together to solve GAIA Level 1 questions.

## 🎯 What This Project Is

This is a **learning project** that shows how to:
- Build a multi-agent system with specialized roles
- Optimize prompts for different agent types
- Test and evaluate AI systems systematically
- Handle complex reasoning tasks through agent collaboration

**Note**: This is not a production system or actively maintained project - it's designed for educational purposes and experimentation.

## 🏗️ System Architecture

The system uses 5 specialized agents working together:

1. **🧠 Planner** - Breaks down questions into executable steps
2. **🔍 Researcher** - Gathers information using web search and tools  
3. **🎯 Expert** - Synthesizes answers using reasoning and calculations
4. **🧪 Critic** - Quality control and feedback mechanism
5. **✨ Finalizer** - Produces final formatted answers

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (or compatible provider)

### Installation
```bash
git clone <repository-url>
cd hf-ai-agents-course
pip install -r requirements.txt
```

### Basic Usage
```bash
# Answer a single question
python src/main.py "What is the capital of France?"

# Process GAIA Level 1 questions from a JSONL file
python src/main.py --input data/synthetic_gaia_testcases.jsonl --output results.jsonl
```

## 📁 Project Structure

```
├── src/                          # Core multi-agent system
│   ├── main.py                   # Entry point for running the system
│   ├── multi_agent_system.py     # Main agent orchestration logic
│   └── prompts/                  # Agent prompt templates
├── prompts/                      # Prompt variants and experiments
│   ├── baseline/                 # Original prompts
│   ├── variants/                 # Different prompt versions
│   └── templates/                # Reusable prompt templates
├── test_harness/                 # Testing and optimization tools
├── data/                         # Test datasets
│   ├── synthetic_gaia_testcases.jsonl    # For development/tuning
│   └── synthetic_gaia_evalset.jsonl      # For final evaluation
├── tests/                        # Unit tests
├── docs/                         # Detailed documentation
└── examples/                     # Example usage and demonstrations
```

## 🧪 Testing and Optimization

### Test Data
The project includes two separate test datasets:
- **Development set** (`synthetic_gaia_testcases.jsonl`): Use for prompt tuning and development
- **Evaluation set** (`synthetic_gaia_evalset.jsonl`): Use only for final evaluation

**Important**: Never use the evaluation set for tuning to avoid overfitting!

### Running Tests
```bash
# Run unit tests
pytest tests/

# Run the test harness for prompt optimization
cd test_harness/promptfoo_planner_optimization/
promptfoo eval
```

## 🔧 Key Components

### 1. Multi-Agent System (`src/multi_agent_system.py`)
The core orchestration logic that coordinates all agents. Each agent has a specific role and the system manages the workflow between them.

### 2. Prompt Optimization (`test_harness/`)
Tools for systematically testing and improving agent prompts using promptfoo.

### 3. Prompt Variants (`prompts/`)
Different versions of prompts for each agent type, allowing you to experiment with different approaches.

### 4. Test Data (`data/`)
Synthetic GAIA Level 1 questions for testing and evaluation.

## 📚 Documentation

- **[Architecture](docs/src/architecture.md)** - System design and architecture
- **[Design Patterns](docs/src/design.md)** - Implementation patterns and decisions
- **[Logical Flow](docs/src/logical_flow.md)** - How the agents work together
- **[Unit Tests](docs/src/unit_tests.md)** - Testing strategy and examples
- **[Requirements](docs/src/SOURCE_CODE_REQUIREMENTS.md)** - Functional requirements

## 🎓 Learning Objectives

This project demonstrates:
- **Multi-agent orchestration**: How to coordinate multiple AI agents
- **Prompt engineering**: Systematic approaches to prompt optimization
- **Testing AI systems**: How to evaluate and validate AI performance
- **Tool integration**: Using external tools (web search, calculators, etc.)
- **Quality control**: Building feedback loops and error handling

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built for learning and experimentation** 🚀
