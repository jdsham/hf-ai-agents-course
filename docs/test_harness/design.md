# Test Harness Design

## Overview
This document provides detailed design specifications for implementing the test harness system. It includes configuration examples, implementation patterns, and specific technical details for each component.

## Entry Point Specifications

### Test Harness Entry Point (`test_harness/optimization_runner.py`)
```bash
# Usage: Run complete three-step experiment
python test_harness/optimization_runner.py \
    --experiment-name "exp_001" \
    --optimization-trials 100 \
    --optimization-test-cases gaia_lvl1_optimization.jsonl \
    --evaluation-test-cases gaia_lvl1_evaluation.jsonl \
    --mlflow-uri http://localhost:5000
```

**Requirements:**
- **OPT-001**: Must accept experiment name as required parameter
- **OPT-002**: Must accept optimization trial count as required parameter
- **OPT-003**: Must accept optimization test cases file path as required parameter
- **OPT-004**: Must accept evaluation test cases file path as required parameter
- **OPT-005**: Must accept optional MLflow server URI
- **OPT-006**: Must execute complete three-step workflow: baseline, optimization, evaluation
- **OPT-007**: Must create separate MLflow runs for each step with proper naming
- **OPT-008**: Must pass optimization trial count parameter to Optuna study
- **OPT-009**: Must pass prompt indices for each agent to Optuna using the inclusive range [0, N] where N is the total number of prompts (baseline + variants), with dynamic detection of variant count per agent
- **OPT-010**: Must convert Optuna trial parameters to actual prompts during optimization trials
- **OPT-011**: Must inject converted prompts into the multi-agent system during trials
- **OPT-012**: Must save best optimized prompts to file for evaluation step
- **OPT-013**: Must provide progress feedback during all three steps
- **OPT-014**: Must handle errors gracefully with detailed logging
- **OPT-015**: Must log prompts, aggregate metrics, and factual correctness count to MLflow

## CLI Usage Examples

### Test Data Manager Commands
```bash
# Use latest versions (default behavior)
python test_harness/optimization_runner.py \
    --experiment-name "exp_001" \
    --optimization-trials 100

# Use specific versions (overrides latest)
python test_harness/optimization_runner.py \
    --experiment-name "exp_001" \
    --optimization-trials 100 \
    --optimization-version "v1.0.0" \
    --evaluation-version "v1.0.0"

# Use latest optimization, specific evaluation version
python test_harness/optimization_runner.py \
    --experiment-name "exp_001" \
    --optimization-trials 100 \
    --evaluation-version "v1.0.0"

# Create new version
python test_harness/test_data_manager.py create-version \
    --type optimization \
    --version v2.1.0 \
    --description "Added scientific questions" \
    --source-dir new_optimization_data/

# Set specific version as latest
python test_harness/test_data_manager.py set-latest \
    --optimization-version v1.1.0 \
    --evaluation-version v1.0.0

# List versions with latest indicators
python test_harness/test_data_manager.py list-versions
```

## Configuration Specifications

### Promptfoo Configuration and Evaluation

#### Test Case Format
Test cases must follow the JSONL format with the following structure:
```json
{"question": "What is the tallest mountain in Africa?", "files": [], "answer": "Mount Kilimanjaro"}
{"question": "Summarize the main topic of the attached file.", "files": ["data/sample_article.txt"], "answer": "The article is about the impact of renewable energy, especially solar and wind, on global electricity production."}
```

**Required Fields:**
- `question`: The GAIA Level 1 question to be answered
- `files`: Array of file paths to load for context (can be empty)
- `answer`: Expected answer for evaluation comparison

#### Promptfoo Configuration Example
```python
def create_promptfoo_config_for_trial(prompts, test_cases, trial_number):
    config = {
        "prompts": {
            "system": f"""
            You are a multi-agent system with the following agents:
            - Planner: {prompts["planner"]}
            - Researcher: {prompts["researcher"]}
            - Expert: {prompts["expert"]}
            - Critic Planner: {prompts["critic_planner"]}
            - Critic Researcher: {prompts["critic_researcher"]}
            - Critic Expert: {prompts["critic_expert"]}
            - Finalizer: {prompts["finalizer"]}
            
            Answer the user's question using these agents and return only the final answer.
            """
        },
        "providers": ["openai/gpt-4"],
        "tests": [
            {
                "vars": {
                    "question": test_case["question"],
                    "files": test_case.get("files", []),
                    "expected_answer": test_case["answer"]
                }
            }
            for test_case in test_cases
        ],
        "defaultTest": {
            "assert": [
                {
                    "type": "llm-rubric",
                    "value": """
                    Evaluate the final answer based on these criteria:
                    1. Factuality: Is the information accurate and factual compared to the expected answer?
                    2. Completeness: Does the answer fully address the question asked?
                    3. Relevance: Is the answer relevant to the question asked?

                    Expected answer: {{expected_answer}}
                    Actual answer: {{output}}

                    Grade each criterion on a scale of 0.0 to 1.0 and provide an overall score.
                    Also indicate if the answer is factually correct (true/false).
                    """,
                    "threshold": 0.8,
                    "metric": "CompositeScore"
                },
                {
                    "type": "javascript",
                    "value": |
                        // Check if the answer contains the same facts as expected
                        const expected = vars.expected_answer.toLowerCase();
                        const actual = output.toLowerCase();
                        
                        // Simple factual correctness check
                        const isFactuallyCorrect = actual.includes(expected) || 
                                                 expected.includes(actual) ||
                                                 actual === expected;
                        
                        return {
                            pass: isFactuallyCorrect,
                            score: isFactuallyCorrect ? 1.0 : 0.0,
                            reason: isFactuallyCorrect ? 'Contains same facts as expected' : 'Does not contain expected facts'
                        };
                    "metric": "FactualCorrectness"
                }
            ]
        },
        "output_path": f"results/trial_{trial_number}",
        "derivedMetrics": [
            {
                "name": "FactuallyCorrectCount",
                "value": "sum(FactualCorrectness)"
            },
            {
                "name": "AverageCompositeScore", 
                "value": "mean(CompositeScore)"
            },
            {
                "name": "FactualCorrectnessPercentage",
                "value": "FactuallyCorrectCount / length(scores) * 100"
            }
        ]
    }
    return config

def process_promptfoo_results(results):
    """Process Promptfoo results to extract multiple metrics including composite score and factual correctness count"""
    composite_scores = []
    factual_correct_count = 0
    
    for result in results:
        # Extract composite score from llm-rubric
        if "CompositeScore" in result and "score" in result["CompositeScore"]:
            composite_scores.append(result["CompositeScore"]["score"])
        
        # Extract factual correctness from javascript assertion
        if "FactualCorrectness" in result and "score" in result["FactualCorrectness"]:
            if result["FactualCorrectness"]["score"] == 1.0:
                factual_correct_count += 1
    
    avg_composite_score = sum(composite_scores) / len(composite_scores) if composite_scores else 0.0
    
    return {
        "composite_score": avg_composite_score,
        "factual_correct_count": factual_correct_count,
        "total_questions": len(results)
    }
```

#### Evaluation Process
1. **System Execution**: Multi-agent system processes each test case
2. **Final Answer Extraction**: Extract `final_answer` from graph state output
3. **Promptfoo Evaluation**: Use `llm-rubric` to compare final answer with expected answer
4. **Score Aggregation**: Calculate average score across all test cases
5. **Optuna Optimization**: Use aggregated score for optimization

### Optuna Configuration with Baseline Integration

#### Optuna Study Configuration Example
```python
def create_optuna_study_with_baseline(prompt_lists, n_trials):
    # Create study for multi-objective optimization (maximize both factual correctness and composite score)
    study = optuna.create_study(
        directions=["maximize", "maximize"],  # [factual_correctness_count, composite_score]
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # Define search space using list indices (0=baseline, 1+=variants)
    def objective(trial):
        # Suggest prompt indices for each agent using dynamic range [0, N] where N is total prompts
        planner_idx = trial.suggest_categorical("planner", list(range(len(prompt_lists["planner"]))))
        researcher_idx = trial.suggest_categorical("researcher", list(range(len(prompt_lists["researcher"]))))
        expert_idx = trial.suggest_categorical("expert", list(range(len(prompt_lists["expert"]))))
        critic_planner_idx = trial.suggest_categorical("critic_planner", list(range(len(prompt_lists["critic_planner"]))))
        critic_researcher_idx = trial.suggest_categorical("critic_researcher", list(range(len(prompt_lists["critic_researcher"]))))
        critic_expert_idx = trial.suggest_categorical("critic_expert", list(range(len(prompt_lists["critic_expert"]))))
        finalizer_idx = trial.suggest_categorical("finalizer", list(range(len(prompt_lists["finalizer"]))))
        
        # Get prompts directly from lists using indices
        prompts = {
            "planner": prompt_lists["planner"][planner_idx],
            "researcher": prompt_lists["researcher"][researcher_idx],
            "expert": prompt_lists["expert"][expert_idx],
            "critic_planner": prompt_lists["critic_planner"][critic_planner_idx],
            "critic_researcher": prompt_lists["critic_researcher"][critic_researcher_idx],
            "critic_expert": prompt_lists["critic_expert"][critic_expert_idx],
            "finalizer": prompt_lists["finalizer"][finalizer_idx],
        }
        
        # Evaluate prompts using Promptfoo and return both metrics
        results = evaluate_prompts_with_promptfoo(prompts, test_cases)
        factual_correctness_count = results["factual_correct_count"]
        composite_score = results["composite_score"]
        
        return factual_correctness_count, composite_score
    
    # Enqueue baseline trial as the first trial
    baseline_params = {
        "planner": 0,
        "researcher": 0,
        "expert": 0,
        "critic_planner": 0,
        "critic_researcher": 0,
        "critic_expert": 0,
        "finalizer": 0
    }
    study.enqueue_trial(baseline_params)
    
    # Optimize with remaining trials
    study.optimize(objective, n_trials=n_trials)
    
    return study

def select_best_trial_from_pareto_front(study):
    """Select the best trial from Pareto front, prioritizing factual correctness then composite score"""
    if not study.best_trials:
        return None
    
    # Sort by factual correctness count first (primary objective), then by composite score (secondary objective)
    best_trial = max(study.best_trials, key=lambda t: (t.values[0], t.values[1]))
    
    return best_trial

def get_best_prompts_from_trial(trial, prompt_lists):
    """Extract the best prompts from the selected trial"""
    if trial is None:
        return None
    
    # Extract prompt indices from trial parameters
    planner_idx = trial.params["planner"]
    researcher_idx = trial.params["researcher"]
    expert_idx = trial.params["expert"]
    critic_planner_idx = trial.params["critic_planner"]
    critic_researcher_idx = trial.params["critic_researcher"]
    critic_expert_idx = trial.params["critic_expert"]
    finalizer_idx = trial.params["finalizer"]
    
    # Get the actual prompts
    best_prompts = {
        "planner": prompt_lists["planner"][planner_idx],
        "researcher": prompt_lists["researcher"][researcher_idx],
        "expert": prompt_lists["expert"][expert_idx],
        "critic_planner": prompt_lists["critic_planner"][critic_planner_idx],
        "critic_researcher": prompt_lists["critic_researcher"][critic_researcher_idx],
        "critic_expert": prompt_lists["critic_expert"][critic_expert_idx],
        "finalizer": prompt_lists["finalizer"][finalizer_idx],
    }
    
    return best_prompts

def create_prompt_lists(baseline_prompts, prompt_variations):
    """Create separate lists for each agent with baseline at index 0"""
    prompt_lists = {}
    
    for agent in ["planner", "researcher", "expert", "critic_planner", "critic_researcher", "critic_expert", "finalizer"]:
        # Start with baseline prompt at index 0
        prompt_lists[agent] = [baseline_prompts[f"{agent}_system_prompt.txt"]]
        
        # Add variant prompts from prompt_variations directory
        agent_variants = prompt_variations.get(agent, {})
        for variant_file in sorted(agent_variants.keys()):
            prompt_lists[agent].append(agent_variants[variant_file])
    
    return prompt_lists
```

### Multi-Objective Optimization Strategy

The test harness uses Optuna's multi-objective optimization to balance two key metrics:

#### **Primary Objective: Factual Correctness Count**
- **Goal**: Maximize the number of questions answered correctly
- **Priority**: Highest - getting the right answer is the most important
- **Metric**: Count of questions where the system's answer contains the same facts as the expected answer

#### **Secondary Objective: Composite Score**
- **Goal**: Maximize overall answer quality (factuality + completeness + relevance)
- **Priority**: Secondary - optimize quality once factual correctness is achieved
- **Metric**: Average score from Promptfoo's `llm-rubric` evaluation

#### **Optimization Approach**
1. **Pareto Front Analysis**: Optuna finds all non-dominated solutions
2. **Selection Strategy**: Choose the solution with highest factual correctness count, then highest composite score
3. **Trade-off Handling**: When factual correctness is equal, prefer higher composite scores

## Implementation Patterns

### Prompt Workflow and Operations

#### **Initial Setup Workflow**
1. **Experiment Directory Creation**: Create experiment directory structure including logs subdirectory
   ```bash
   mkdir -p test_harness/experiments/{experiment_name}/{baseline_prompts,optimized_prompts,logs/error_logs}
   ```
2. **Baseline Creation**: Copy current production prompts to experiment's baseline folder
   ```bash
   cp src/prompts/* test_harness/experiments/{experiment_name}/baseline_prompts/
   ```
3. **Variant Preparation**: Ensure prompt variants are ready in `prompt_variations/` directory
4. **Prompt List Creation**: Load all prompts into separate lists for each agent:
   - List[0] = baseline prompt (from experiment's baseline folder)
   - List[1+] = variant prompts from prompt_variations directory
5. **Optuna Configuration**: Configure Optuna with all prompts available for selection via list indices

#### **Optimization Workflow**
1. **Baseline Trial**: Optuna executes baseline prompts as the first trial using `enqueue_trial()`
2. **Baseline Score**: Save baseline performance score for comparison
3. **Trial Execution**: Optuna selects prompt combination from variants (including baseline)
4. **Prompt Injection**: Selected prompts injected into multi-agent system
5. **Evaluation**: Promptfoo evaluates performance using `llm-rubric`
6. **Metrics Aggregation**: Calculate factual correctness count and composite score across all test cases
7. **Multi-Objective Optimization**: Optuna uses both metrics to find Pareto-optimal solutions

#### **Post-Optimization Workflow**
1. **Pareto Front Analysis**: Optuna identifies Pareto-optimal prompt combinations
2. **Best Trial Selection**: Select trial with highest factual correctness count, then highest composite score
3. **Result Storage**: Save best optimized prompts as text files in experiment's optimized_prompts folder
4. **Performance Analysis**: Compare optimized results to baseline
5. **Promotion Decision**: Decide whether to manually promote to production after human review

#### **Manual Promotion and Rollback Operations**
1. **Manual Promotion to Production** (requires human review):
   ```bash
   cp test_harness/experiments/exp_001/optimized_prompts/* src/prompts/
   ```
2. **Manual Rollback to Baseline** (requires human review):
   ```bash
   cp test_harness/experiments/exp_001/baseline_prompts/* src/prompts/
   ```
3. **Manual Rollback to Previous Experiment** (requires human review):
   ```bash
   cp test_harness/experiments/exp_000/optimized_prompts/* src/prompts/
   ```

#### **Version Control Strategy**
- **Production Prompts**: Fully version controlled in Git
- **Baseline Prompts**: Stored locally within each experiment, not version controlled
- **Prompt Variations**: Version controlled for reproducibility
- **Experiment Results**: Stored locally, not version controlled (large files)
- **Experiment Metadata**: Version controlled for tracking

### Test Case File Example
**`test_harness/test_data/optimization/v1.1.0/test_cases.jsonl`**:
```json
{"question": "What is the tallest mountain in Africa?", "files": [], "answer": "Mount Kilimanjaro"}
{"question": "Summarize the main topic of the attached file.", "files": ["context_files/updated_article.txt"], "answer": "The article discusses renewable energy impacts."}
{"question": "What are the key findings in the research data?", "files": ["context_files/new_reference_data.json"], "answer": "The data shows a 15% increase in adoption rates."}
```

### Version Resolution Logic
1. **Default Resolution**: Read `latest_optimization` and `latest_evaluation` from `versions.json`
2. **Override Resolution**: Use CLI parameters if provided
3. **File Path Resolution**: Construct paths like `test_data/optimization/{version}/test_cases.jsonl`
4. **Validation**: Ensure all files exist before proceeding
5. **Logging**: Log version information to MLflow

## Integration Specifications

### Integration Points

#### **Prompt Generation and Injection**
- **INT-001**: Test harness must load original prompts from `src/prompts/` for baseline
- **INT-002**: Test harness must pass prompt indices for each agent to Optuna using the inclusive range [0, N] where N is the total number of prompts (baseline + variants), with dynamic detection of variant count per agent
- **INT-003**: Test harness must convert Optuna trial parameters to actual prompts during optimization
- **INT-004**: Test harness must inject converted prompts into the multi-agent system during trials
- **INT-005**: Test harness must save optimized prompts to `test_harness/experiments/`
- **INT-006**: No direct coupling between production and test harness systems

#### **LangGraph Integration**
- **INT-007**: Test harness must use the same LangGraph system (`src/multi_agent_system.py`)
- **INT-008**: Test harness must inject received prompts during evaluation
- **INT-009**: Production system must use stable prompts during normal operation
- **INT-010**: Both systems must use the same core agent logic
- **INT-011**: Test harness must validate prompt injection before evaluation

#### **Optuna and Optimization Integration**
- **INT-012**: Test harness must configure Optuna to use black-box optimization for prompt combinations
- **INT-013**: Test harness must pass optimization parameters to Optuna study configuration
- **INT-014**: Test harness must pass prompt indices for each agent to Optuna using the inclusive range [0, N] where N is the total number of prompts (baseline + variants), with dynamic detection of variant count per agent
- **INT-015**: Test harness must convert Optuna trial parameters to actual prompts during trials
- **INT-016**: Test harness must capture optimization results from Optuna

### Deployment Strategy

#### **Independent Deployment**
- **DEPLOY-001**: Production system can be deployed independently
- **DEPLOY-002**: Test harness can run optimization experiments independently
- **DEPLOY-003**: Optimized prompts can be manually deployed to production after human review
- **DEPLOY-004**: Production system must not require test harness to function

#### **Prompt Deployment**
- **DEPLOY-005**: Optimized prompts must be manually copied from `test_harness/experiments/` to `src/prompts/` after human review
- **DEPLOY-006**: Production system must use the deployed optimized prompts
- **DEPLOY-007**: Rollback must be possible by reverting to previous prompt versions
- **DEPLOY-008**: Prompt deployment must be manual and require human review

## Workflow Requirements

### Three-Step Test Harness Workflow

#### **Step 1: Baseline Run**
1. **Initial Setup**: Load optimization test cases and copy current production prompts to experiment's baseline folder
2. **Logging Setup**: Initialize experiment-specific logging to `test_harness/experiments/{experiment_name}/logs/baseline_run.log`
3. **MLflow Run Creation**: Create MLflow run with name `<experiment_name>_baseline`
4. **Prompt Loading**: Load baseline prompts from experiment's baseline folder (copied from `src/prompts/`)
5. **System Evaluation**: Run multi-agent system with baseline prompts against optimization test cases
6. **Promptfoo Evaluation**: Use `llm-rubric` to evaluate system performance
7. **Metrics Calculation**: Calculate total factual correctness count and average composite score across all test cases
8. **MLflow Logging**: Log baseline prompts, total factual correctness count, and average composite score to MLflow
9. **Baseline Score Storage**: Save baseline performance metrics for comparison

#### **Step 2: Prompt Optimization with Optuna**
1. **Logging Setup**: Initialize experiment-specific logging to `test_harness/experiments/{experiment_name}/logs/optimization_run.log`
2. **MLflow Run Creation**: Create MLflow run with name `<experiment_name>_optimize`
3. **Optuna Configuration**: Configure Optuna with black-box optimization for 7-dimensional prompt space
4. **Prompt List Creation**: Load all prompts into separate lists for each agent (baseline at index 0, variants at indices 1-3)
5. **Baseline Trial Enqueue**: Use Optuna's `enqueue_trial()` to add baseline as the first trial
6. **Optimization Loop**: Optuna handles optimization loop internally:
   a. **Baseline Trial**: Execute baseline prompts as trial 0 and save baseline score
   b. **Trial Generation**: Optuna suggests prompt combination based on previous trials using TPE sampler
   c. **Prompt Selection**: Select prompts from lists using trial parameters with dynamic range [0, N] where N is the total number of prompts per agent
   d. **Dynamic Config Generation**: Generate Promptfoo configuration dynamically for current trial
   e. **Promptfoo Evaluation**: Run Promptfoo evaluation with selected prompts against optimization test cases
   f. **Metrics Aggregation**: Aggregate factual correctness scores to compute total count and composite scores to compute average
   g. **Trial Reporting**: Report total factual correctness count and average composite score back to Optuna for multi-objective optimization
   h. **Failure Handling**: Halt execution immediately if any trial fails and log detailed error context
7. **Pareto Front Analysis**: Optuna identifies Pareto-optimal prompt combinations
8. **Best Trial Selection**: Select trial with highest total factual correctness count, then highest average composite score
9. **Best Prompts Storage**: Save best optimized prompts as text files in experiment's optimized_prompts folder
10. **MLflow Logging**: Log final Optuna optimization results (best trial, Pareto front, optimization metrics) to MLflow

#### **Step 3: Evaluation Run**
1. **Logging Setup**: Initialize experiment-specific logging to `test_harness/experiments/{experiment_name}/logs/evaluation_run.log`
2. **MLflow Run Creation**: Create MLflow run with name `<experiment_name>_eval`
3. **Best Prompts Loading**: Load best optimized prompts from experiment's optimized_prompts folder
4. **Evaluation Test Cases**: Load separate evaluation test cases (different from optimization test cases)
5. **System Evaluation**: Run multi-agent system with best optimized prompts against evaluation test cases
6. **Promptfoo Evaluation**: Use `llm-rubric` to evaluate system performance
7. **Metrics Calculation**: Calculate total factual correctness count and average composite score across all test cases
8. **MLflow Logging**: Log best optimized prompts, total factual correctness count, and average composite score to MLflow
9. **Performance Comparison**: Compare evaluation results with baseline performance

## Concurrency Constraints

### Single-Threaded Execution Requirements
- **CONC-001**: **CRITICAL**: The system must enforce single-threaded execution - no parallel runs allowed
- **CONC-002**: **CRITICAL**: No concurrent optimization trials - only one trial can run at a time
- **CONC-003**: **CRITICAL**: No concurrent normal operation during optimization mode
- **CONC-004**: **CRITICAL**: No concurrent optimization mode during normal operation
- **CONC-005**: **CRITICAL**: System must prevent any form of parallel graph execution
- **CONC-006**: The system must implement exclusive access control for all operations
- **CONC-007**: The system must implement locks to prevent concurrent mode switching
- **CONC-008**: The system must implement locks to prevent concurrent trial execution
- **CONC-009**: The system must implement locks to prevent concurrent graph execution
- **CONC-010**: The system must provide clear error messages when concurrency violations are detected

### Implementation Requirements
- **CONC-011**: All prompt manager operations must be atomic
- **CONC-012**: All mode switching operations must be atomic
- **CONC-013**: All trial management operations must be atomic
- **CONC-014**: All graph execution operations must be atomic
- **CONC-015**: The system must log all concurrency control events 