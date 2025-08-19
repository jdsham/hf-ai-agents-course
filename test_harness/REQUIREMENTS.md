# Test Harness Requirements

## Overview
A test harness for optimizing prompts used in a LangGraph multi-agent system using a three-step process: baseline evaluation, Optuna optimization, and final evaluation. Each step creates a separate MLflow run for comprehensive tracking.

**Note**: This test harness operates as a **separate system** that generates and injects prompts into the multi-agent system. It uses a three-step process: baseline evaluation, Optuna optimization, and final evaluation, each with its own MLflow run for complete experiment tracking.

## Core Requirements

### 1. Three-Step Test Harness Process
- **REQ-001**: The system must execute a three-step process: baseline run, prompt optimization, and evaluation run
- **REQ-002**: Each step must create a separate MLflow run with naming convention: `<experiment_name>_<step>`
- **REQ-003**: The baseline run must use current source code prompts and evaluate against optimization test cases
- **REQ-004**: The optimization step must use Optuna to find the best prompt combination starting from baseline prompts
- **REQ-005**: The evaluation step must use the best optimized prompts against separate evaluation test cases
- **REQ-006**: The system must log prompts used in each step to MLflow
- **REQ-007**: The system must log Promptfoo aggregate metrics (total factual correctness count and average composite score) to MLflow
- **REQ-008**: The system must store best optimized prompts in a file for the evaluation step
- **REQ-009**: The system must use different test case sets for optimization vs evaluation
- **REQ-010**: The system must ensure each step completes before starting the next step

### 2. Evaluation & Validation
- **REQ-011**: The system must use Promptfoo's native `llm-rubric` evaluation for factuality, completeness, and relevance assessment
- **REQ-012**: The system must return two separate scores per test case: factual correctness (1 for correct, 0 for incorrect) and composite score (factuality + completeness + relevance)
- **REQ-013**: The system must aggregate factual correctness scores across all test cases to compute total number of questions answered correctly
- **REQ-014**: The system must aggregate composite scores across all test cases by computing the average composite score
- **REQ-015**: The system must use different test case sets for optimization vs evaluation to prevent overfitting
- **REQ-016**: The system must use the complete test case set for each evaluation
- **REQ-017**: The system must use optimization test cases to evaluate baseline system performance before starting optimization


### 3. Cost Efficiency
- **REQ-021**: The system must minimize expensive LangGraph system calls through Optuna's intelligent sampling
- **REQ-022**: The system must leverage Promptfoo's built-in caching to avoid redundant evaluations during Optuna trials, baseline and final evaluations.
- **REQ-023**: The system must support early termination if performance degrades during Optuna optimization
- **REQ-024**: The system must leverage Optuna's black-box optimization to reduce total LLM calls compared to grid search

### 4. Prompt Management
- **REQ-025**: The system must load original prompts from production system (`src/prompts/`) for baseline
- **REQ-026**: The system must save optimized prompts to `test_harness/experiments/` after Optuna optimization
- **REQ-027**: The system must support rollback to original prompts if needed
- **REQ-028**: The system must track prompt changes across Optuna optimization trials
- **REQ-029**: The system must manage prompt variants for each agent in `test_harness/prompt_variations/` directory, where each variant represents a different optimization strategy (e.g., role-focused, task-focused, framework-focused)
- **REQ-030**: The system must load all prompts into separate lists for each agent, where the 0th element is the baseline prompt and subsequent elements are the variant prompts
- **REQ-031**: The system must pass prompt indices to Optuna for optimization using the inclusive range [0, N] where N is the total number of prompts (baseline + variants), with the system dynamically detecting the number of variants per agent
- **REQ-032**: The system must convert Optuna trial parameters to actual prompts and inject them into the multi-agent system
- **REQ-033**: The system must dynamically detect the number of prompt variants available for each agent and use this count to determine the inclusive range [0, N] for Optuna's categorical parameter suggestions

### 5. Experiment Management
- **REQ-034**: The system must track experiments with MLFlow
- **REQ-035**: The system must save Optuna optimization metrics and Promptfoo evaluation data

### 6. User Interface
- **REQ-036**: The system must provide a CLI interface through `test_harness/optimization_runner.py`
- **REQ-037**: The system must accept optimization trial count as a required CLI parameter
- **REQ-038**: The system must pass optimization trial count parameter to Optuna study
- **REQ-039**: The system must provide clear progress feedback during Optuna optimization
- **REQ-040**: The system must enforce single-threaded execution - no parallel runs allowed
- **REQ-041**: The system must prevent concurrent optimization trials
- **REQ-042**: The system must provide exclusive access control for optimization operations

### 7. Test Execution Engine
- **REQ-043**: The system must provide test execution status reporting for Optuna trials
- **REQ-044**: The system must support test execution in different environments (dev, staging)
- **REQ-045**: The system must provide test execution timing and performance metrics from Optuna trials and Promptfoo evaluations

### 8. Test Data Management
- **REQ-046**: The system must support test data versioning and management for Optuna optimization
- **REQ-047**: The system must provide test data validation and sanitization
- **REQ-048**: The system must support independent versioning for optimization and evaluation test data
- **REQ-049**: The system must maintain a version registry that tracks latest versions and metadata for each version
- **REQ-050**: The system must use the latest versions by default when no specific version is specified
- **REQ-051**: The system must support CLI parameters to override the latest version selection
- **REQ-052**: The system must organize test data by version with associated context files
- **REQ-053**: The system must log test data version information to MLflow for experiment reproducibility
- **REQ-054**: The system must validate that all referenced context files exist before experiment execution
- **REQ-055**: The system must provide a test data manager tool for version operations
- **REQ-056**: The test data manager must automatically update latest version indicators when creating new versions
- **REQ-057**: The test data manager must support setting any existing version as the latest version
- **REQ-058**: The test data manager must display all available versions with latest indicators
- **REQ-059**: The test data manager must validate version integrity during creation
- **REQ-060**: The test data manager must copy context files during version creation
- **REQ-061**: The test data manager must record version metadata including creation date, description, and test case count
- **REQ-062**: The system must resolve file paths relative to version directories when loading test data
- **REQ-063**: The test data manager must validate JSONL file format and structure before creating versions
- **REQ-064**: The test data manager must verify that all referenced context files exist in source directories
- **REQ-065**: The test data manager must provide clear error messages for validation failures
- **REQ-066**: The optimization runner must halt execution if specified versions don't exist
- **REQ-067**: The optimization runner must validate file paths before starting experiments
- **REQ-068**: The system must support Git version control for test data
- **REQ-069**: The system must provide clear documentation of version changes and purposes
- **REQ-070**: The system must support rollback operations through version management
- **REQ-071**: The system must maintain version history for audit and compliance purposes

### 9. Logging & Error Handling
- **REQ-049**: The system must provide comprehensive logging at multiple levels (DEBUG, INFO, WARNING, ERROR)
- **REQ-050**: The system must log all Optuna trial execution steps, inputs, outputs, and timing information
- **REQ-051**: The system must log all Promptfoo evaluation steps, inputs, outputs, and timing information
- **REQ-052**: The system must provide detailed error messages with context and stack traces
- **REQ-053**: The system must log all API calls, responses, and performance metrics
- **REQ-054**: The system must store all experiment logs locally within the experiment's directory structure
- **REQ-055**: The system must halt execution immediately upon any failure and ensure logs capture complete error context for debugging
- **REQ-056**: The system must not implement retry mechanisms or error recovery - failures must stop execution

### 10. Prompt Integration with LangGraph
- **REQ-057**: The system must inject selected prompts into the LangGraph multi-agent system during optimization trials
- **REQ-058**: The system must ensure prompt injection does not affect production system operation
- **REQ-059**: The system must support manual rollback to baseline prompts when needed
- **REQ-060**: The system must support manual deployment of optimized prompts to production system after human review
- **REQ-061**: The system must convert Optuna trial parameters to actual prompts during optimization trials
- **REQ-062**: The system must maintain prompt isolation between test harness and production environments

### 11. Modular Architecture & Operations
- **REQ-063**: The system must be modular with clearly defined component boundaries
- **REQ-064**: The system must enforce a defined order of operations for all processes
- **REQ-065**: The system must support independent testing of individual modules
- **REQ-066**: The system must provide clear interfaces between modules
- **REQ-067**: The system must operate independently from the production system
- **REQ-068**: The system must receive and inject prompts without affecting production
- **REQ-072**: The system must support future integration of prompt management and versioning capabilities without requiring architectural changes to the core test harness functionality

### 12. MLflow Integration
- **REQ-069**: The system must integrate with MLflow for experiment tracking across all three steps
- **REQ-070**: The system must accept MLflow server URI as a CLI parameter
- **REQ-071**: The system must use the experiment name as the base MLflow experiment name
- **REQ-072**: The system must create separate MLflow runs for each step: `<experiment_name>_baseline`, `<experiment_name>_optimize`, `<experiment_name>_eval`
- **REQ-073**: The system must log the following data to each MLflow run:
  - **Baseline Run**: Prompts used for each agent, Promptfoo metrics (total factual correctness count, average composite score), test data version used
  - **Optimize Run**: Final Optuna optimization results (best trial, Pareto front, optimization metrics), best prompts selected for each agent, Promptfoo metrics from best trial, test data version used
  - **Evaluation Run**: Best optimized prompts for each agent, Promptfoo metrics (total factual correctness count, average composite score), validation data version used, performance comparison with baseline

### 13. Optuna Configuration and Optimization Integration
- **REQ-079**: The system must configure Optuna to use multi-objective black-box optimization for prompt combinations
- **REQ-080**: The system must configure Optuna to test prompt combinations against the LangGraph multi-agent system
- **REQ-081**: The system must use Optuna's TPE (Tree-structured Parzen Estimator) sampler for efficient optimization
- **REQ-082**: The system must accept optimization trial count as a required CLI parameter and pass it to Optuna study
- **REQ-083**: The system must capture and log Optuna optimization results
- **REQ-084**: The system must provide experiment summary reports showing optimization progress, best trial selection, and performance improvements
- **REQ-087**: The system must configure Optuna to optimize prompt variants as categorical parameters using prompt indices (0 for baseline, 1+ for variants), where the system dynamically detects the number of variants per agent and uses the inclusive range [0, N] where N is the total number of prompts (baseline + variants)
- **REQ-088**: The system must convert Optuna trial parameters to actual prompts during optimization trials
- **REQ-089**: The system must use Optuna's `enqueue_trial()` to add baseline prompt combination as the first trial
- **REQ-090**: The system must configure Optuna search space to include baseline prompts as a valid option
- **REQ-091**: The system must handle baseline prompt selection (index 0) in the prompt conversion logic
- **REQ-092**: The system must configure Optuna study with directions ["maximize", "maximize"] for total factual correctness count and average composite score
- **REQ-093**: The system must prioritize total factual correctness count over average composite score in multi-objective optimization
- **REQ-094**: The system must use Pareto front analysis to identify best prompt combinations
- **REQ-095**: The system must select the best trial based on highest total factual correctness count, then highest average composite score

### 14. Promptfoo Integration and Evaluation
- **REQ-096**: The system must use Promptfoo as the evaluation service for all evaluation steps (baseline, optimization trials, and final evaluation)
- **REQ-097**: The system must generate Promptfoo configurations dynamically for each optimization trial
- **REQ-098**: The system must integrate Promptfoo with the LangGraph multi-agent system for evaluation
- **REQ-099**: The system must leverage Promptfoo's built-in caching to avoid redundant evaluations
- **REQ-100**: The system must log all Promptfoo evaluation steps, inputs, outputs, and timing information
- **REQ-101**: The system must handle Promptfoo evaluation failures by halting execution and logging detailed error information
- **REQ-102**: The system must configure `llm-rubric` to use ChatGPT (GPT-4) as the grading model
- **REQ-103**: The system must ensure `llm-rubric` returns scores in the 0.0-1.0 range for proper aggregation
- **REQ-104**: The system must configure `llm-rubric` with evaluation criteria for factuality, completeness, and relevance
- **REQ-105**: The system must implement score averaging logic to aggregate `llm-rubric` results across all test cases
- **REQ-106**: The system must handle `llm-rubric` JSON response format with `reason`, `score`, and `pass` fields
- **REQ-107**: The system must evaluate only the `final_answer` field from the multi-agent system's graph state output
- **REQ-108**: The system must use test case expected answers (from the `answer` field) for `llm-rubric` evaluation comparison
- **REQ-109**: The system must evaluate overall system performance, not individual agent outputs
- **REQ-110**: The system must halt execution immediately if Promptfoo evaluation fails completely
- **REQ-111**: The system must log detailed error information before halting execution
- **REQ-112**: The system must not attempt fallback evaluation methods if Promptfoo fails

### 15. Prompt Organization and File Structure
- **REQ-113**: The system must maintain production prompts in `src/prompts/` directory
- **REQ-114**: The system must maintain baseline prompts in `test_harness/experiments/{experiment_name}/baseline_prompts/` directory
- **REQ-115**: The system must store optimized prompts in `test_harness/experiments/{experiment_name}/optimized_prompts/` directory
- **REQ-116**: The system must support manual promotion of optimized prompts from experiments to production after human review
- **REQ-117**: The system must support rollback to baseline prompts when needed
- **REQ-118**: The system must maintain clear separation between production, baseline, and experimental prompts
- **REQ-119**: The system must version control production prompts while keeping experiments isolated
- **REQ-120**: The system must copy production prompts to baseline before starting optimization
- **REQ-121**: The system must provide baseline performance metrics for comparison with optimized results
- **REQ-122**: The system must organize prompt variants by agent type in subdirectories
- **REQ-123**: The system must maintain consistent naming conventions across all prompt directories
- **REQ-124**: The system must ensure baseline prompts are exact copies of production prompts
- **REQ-125**: The system must support easy comparison between baseline, variants, and optimized prompts
- **REQ-126**: The system must maintain prompt metadata and version information in experiment directories
- **REQ-127**: The system must use simplified experiment naming: `exp_001`, `exp_002`, `exp_003`, etc.
- **REQ-128**: Each experiment must represent a complete three-step process: baseline evaluation, optimization, and final evaluation
- **REQ-129**: The system must automatically copy current production prompts from `src/prompts/` to the experiment's baseline folder at the start of each experiment
- **REQ-130**: The system must save the best optimized prompts as text files in the experiment's optimized_prompts folder after optimization is complete
- **REQ-131**: The system must load the optimized prompts from the experiment's optimized_prompts folder for the final evaluation step
- **REQ-132**: The system must support manual rollback by copying baseline prompts to source code folder
- **REQ-133**: The system must not automatically update source code prompts
- **REQ-134**: The system must maintain baseline prompts as exact copies of production prompts
- **REQ-135**: The system must create and maintain a `logs/` directory within each experiment folder to store all experiment-specific logging

## Separated Architecture Design

### Test Data Versioning Architecture

#### File Structure
```
test_harness/
├── test_data/
│   ├── optimization/
│   │   ├── v1.0.0/
│   │   │   ├── test_cases.jsonl
│   │   │   └── context_files/
│   │   │       ├── sample_article.txt
│   │   │       └── reference_data.json
│   │   ├── v1.1.0/
│   │   │   ├── test_cases.jsonl
│   │   │   └── context_files/
│   │   │       ├── updated_article.txt
│   │   │       └── new_reference_data.json
│   │   └── v2.0.0/
│   │       ├── test_cases.jsonl
│   │       └── context_files/
│   │           └── math_problems.json
│   ├── evaluation/
│   │   ├── v1.0.0/
│   │   │   ├── test_cases.jsonl
│   │   │   └── context_files/
│   │   │       ├── validation_article.txt
│   │   │       └── benchmark_data.json
│   │   └── v1.1.0/
│   │       ├── test_cases.jsonl
│   │       └── context_files/
│   │           ├── new_validation_article.txt
│   │           └── updated_benchmark_data.json
│   └── versions.json
```

#### Version Registry Schema
**`test_harness/test_data/versions.json`**:
```json
{
  "latest_optimization": "v2.0.0",
  "latest_evaluation": "v1.1.0",
  "versions": {
    "optimization": {
      "v1.0.0": {
        "created": "2024-01-15",
        "description": "Initial optimization test cases",
        "directory": "optimization/v1.0.0",
        "test_case_count": 50
      },
      "v1.1.0": {
        "created": "2024-02-01",
        "description": "Added more diverse questions",
        "directory": "optimization/v1.1.0",
        "test_case_count": 60
      },
      "v2.0.0": {
        "created": "2024-03-01",
        "description": "Added mathematical reasoning questions",
        "directory": "optimization/v2.0.0",
        "test_case_count": 70
      }
    },
    "evaluation": {
      "v1.0.0": {
        "created": "2024-01-15",
        "description": "Initial evaluation test cases",
        "directory": "evaluation/v1.0.0",
        "test_case_count": 20
      },
      "v1.1.0": {
        "created": "2024-02-15",
        "description": "Updated evaluation cases",
        "directory": "evaluation/v1.1.0",
        "test_case_count": 25
      }
    }
  }
}
```

#### CLI Usage Examples
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

#### Test Case File Example
**`test_harness/test_data/optimization/v1.1.0/test_cases.jsonl`**:
```json
{"question": "What is the tallest mountain in Africa?", "files": [], "answer": "Mount Kilimanjaro"}
{"question": "Summarize the main topic of the attached file.", "files": ["context_files/updated_article.txt"], "answer": "The article discusses renewable energy impacts."}
{"question": "What are the key findings in the research data?", "files": ["context_files/new_reference_data.json"], "answer": "The data shows a 15% increase in adoption rates."}
```

#### Test Data Manager Commands
The test data manager (`test_harness/test_data_manager.py`) provides the following commands:

- **`create-version`**: Create new test data version with automatic latest update
- **`set-latest`**: Set specific version as latest for rollback scenarios
- **`list-versions`**: Display all available versions with latest indicators
- **`validate-version`**: Check version integrity and file existence

#### Version Resolution Logic
1. **Default Resolution**: Read `latest_optimization` and `latest_evaluation` from `versions.json`
2. **Override Resolution**: Use CLI parameters if provided
3. **File Path Resolution**: Construct paths like `test_data/optimization/{version}/test_cases.jsonl`
4. **Validation**: Ensure all files exist before proceeding
5. **Logging**: Log version information to MLflow

This approach follows [data versioning best practices](https://research.aimultiple.com/data-versioning/) by providing:
- **Preserving working versions** while testing new datasets
- **Measuring performance** across different data versions
- **Compliance and auditing** benefits through version history
- **Semantic versioning** using the three-part version number convention
- **File-based versioning** suitable for small teams and sensitive data

The architecture ensures **reproducibility**, **rollback capability**, and **clear version management** while maintaining simplicity and usability.

### Prompt Folder Structure and Organization

#### **Production Prompts (`src/prompts/`)**
- **Purpose**: Stable, version-controlled production prompts used by the live system
- **Contents**: Current production prompts for all agents
- **File Structure**:
  ```
  src/prompts/
  ├── planner_system_prompt.txt
  ├── researcher_system_prompt.txt
  ├── expert_system_prompt.txt
  ├── critic_planner_system_prompt.txt
  ├── critic_researcher_system_prompt.txt
  ├── critic_expert_system_prompt.txt
  └── finalizer_system_prompt.txt
  ```
- **Version Control**: Fully version controlled and deployed to production
- **Access**: Read by production system, updated only through controlled deployment

#### **Baseline Prompts (`test_harness/experiments/{experiment_name}/baseline_prompts/`)**
- **Purpose**: Exact copy of production prompts for reference and rollback within each experiment
- **Contents**: Snapshot of production prompts at experiment start
- **File Structure**:
  ```
  test_harness/experiments/
  ├── exp_001/
  │   ├── baseline_prompts/
  │   │   ├── planner_system_prompt.txt
  │   │   ├── researcher_system_prompt.txt
  │   │   ├── expert_system_prompt.txt
  │   │   ├── critic_planner_system_prompt.txt
  │   │   ├── critic_researcher_system_prompt.txt
  │   │   ├── critic_expert_system_prompt.txt
  │   │   └── finalizer_system_prompt.txt
  │   └── optimized_prompts/
  └── exp_002/
      ├── baseline_prompts/
      └── optimized_prompts/
  ```
- **Creation**: Copied from `src/prompts/` at the start of each experiment
- **Usage**: Reference point for performance comparison and rollback within the experiment

#### **Prompt Variations (`test_harness/prompt_variations/`)**
- **Purpose**: Prompt variants per agent for systematic optimization, where each variant represents a different optimization strategy
- **Contents**: Experimental prompts representing different optimization strategies (e.g., role-focused, task-focused, framework-focused)
- **File Structure**:
  ```
  test_harness/prompt_variations/
  ├── planner/
  │   ├── variant_0_role_focused.txt
  │   ├── variant_1_task_focused.txt
  │   └── variant_2_framework_focused.txt
  ├── researcher/
  │   ├── variant_0_role_focused.txt
  │   ├── variant_1_task_focused.txt
  │   └── variant_2_framework_focused.txt
  ├── expert/
  │   ├── variant_0_role_focused.txt
  │   ├── variant_1_task_focused.txt
  │   └── variant_2_framework_focused.txt
  ├── critic_planner/
  │   ├── variant_0_role_focused.txt
  │   ├── variant_1_task_focused.txt
  │   └── variant_2_framework_focused.txt
  ├── critic_researcher/
  │   ├── variant_0_role_focused.txt
  │   ├── variant_1_task_focused.txt
  │   └── variant_2_framework_focused.txt
  ├── critic_expert/
  │   ├── variant_0_role_focused.txt
  │   ├── variant_1_task_focused.txt
  │   └── variant_2_framework_focused.txt
  └── finalizer/
      ├── variant_0_role_focused.txt
      ├── variant_1_task_focused.txt
      └── variant_2_framework_focused.txt
  ```
- **Naming Convention**: `variant_{index}_{strategy_name}.txt`
- **Strategies**: Role-focused, Task-focused, Framework-focused (expandable to additional strategies)

#### **Experiment Results (`test_harness/experiments/{experiment_name}/`)**
- **Purpose**: Store optimization results, best-performing prompts, and experiment-specific logs
- **Contents**: Baseline prompts, optimized prompts, experiment data, analysis results, and comprehensive logging
- **File Structure**:
  ```
  test_harness/experiments/
  ├── exp_001/
  │   ├── baseline_prompts/
  │   │   ├── planner_system_prompt.txt
  │   │   ├── researcher_system_prompt.txt
  │   │   ├── expert_system_prompt.txt
  │   │   ├── critic_planner_system_prompt.txt
  │   │   ├── critic_researcher_system_prompt.txt
  │   │   ├── critic_expert_system_prompt.txt
  │   │   └── finalizer_system_prompt.txt
  │   ├── optimized_prompts/
  │   │   ├── planner_system_prompt.txt
  │   │   ├── researcher_system_prompt.txt
  │   │   ├── expert_system_prompt.txt
  │   │   ├── critic_planner_system_prompt.txt
  │   │   ├── critic_researcher_system_prompt.txt
  │   │   ├── critic_expert_system_prompt.txt
  │   │   └── finalizer_system_prompt.txt
  │   ├── logs/
  │   │   ├── baseline_run.log
  │   │   ├── optimization_run.log
  │   │   ├── evaluation_run.log
  │   │   ├── optuna_trials.log
  │   │   ├── promptfoo_evaluations.log
  │   │   └── error_logs/
  │   │       ├── baseline_errors.log
  │   │       ├── optimization_errors.log
  │   │       └── evaluation_errors.log
  │   ├── optuna_study.pkl
  │   ├── promptfoo_results/
  │   ├── mlflow_artifacts/
  │   ├── experiment_summary.json
  │   └── prompt_metadata.yaml
  └── exp_002/
      ├── baseline_prompts/
      ├── optimized_prompts/
      ├── logs/
      └── ...
  ```
- **Baseline Prompts**: Exact copy of production prompts at experiment start
- **Optimized Prompts**: Best-performing prompt combination from Optuna optimization
- **Experiment Data**: Optuna study, Promptfoo results, MLflow artifacts
- **Metadata**: Version information, optimization parameters, performance metrics
- **Logs**: Comprehensive logging for each experiment step with detailed error context

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

### Promptfoo Configuration and Evaluation

#### **Test Case Format**
Test cases must follow the JSONL format with the following structure:
```json
{"question": "What is the tallest mountain in Africa?", "files": [], "answer": "Mount Kilimanjaro"}
{"question": "Summarize the main topic of the attached file.", "files": ["data/sample_article.txt"], "answer": "The article is about the impact of renewable energy, especially solar and wind, on global electricity production."}
```

**Required Fields:**
- `question`: The GAIA Level 1 question to be answered
- `files`: Array of file paths to load for context (can be empty)
- `answer`: Expected answer for evaluation comparison

#### **Promptfoo Configuration Example**
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

#### **Evaluation Process**
1. **System Execution**: Multi-agent system processes each test case
2. **Final Answer Extraction**: Extract `final_answer` from graph state output
3. **Promptfoo Evaluation**: Use `llm-rubric` to compare final answer with expected answer
4. **Score Aggregation**: Calculate average score across all test cases
5. **Optuna Optimization**: Use aggregated score for optimization

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

### Optuna Configuration with Baseline Integration

#### **Optuna Study Configuration Example**
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

### System Boundaries
The test harness operates as a **completely separate system** that generates and injects prompts:

#### **Production System (`src/`)**
- **Entry Point**: `src/main.py` - Production CLI for answering GAIA questions
- **Core Logic**: `src/multi_agent_system.py` - LangGraph multi-agent system
- **Prompts**: `src/prompts/` - Stable production prompts
- **Purpose**: Answer GAIA Level 1 questions efficiently and reliably

#### **Test Harness System (`test_harness/`)**
- **Entry Point**: `test_harness/optimization_runner.py` - Optimization CLI
- **Core Logic**: `test_harness/optimization_workflow.py` - Optimization workflow
- **Configuration**: `test_harness/optuna_config.py` - Optuna configuration for black-box optimization
- **Prompts**: `test_harness/prompt_variations/` - 3 complete prompts per agent for systematic testing
- **Purpose**: Generate and optimize prompts systematically using Optuna black-box optimization

### Entry Point Specifications

#### **Production Entry Point (`src/main.py`)**
```bash
# Usage: Answer a single GAIA question
python src/main.py "What is the capital of France?"

# Usage: Save answer to file
python src/main.py "What is the capital of France?" --output answer.txt
```

**Requirements:**
- **PROD-001**: Must accept a single GAIA Level 1 question as input
- **PROD-002**: Must return the answer to the question
- **PROD-003**: Must support optional output file specification
- **PROD-004**: Must load stable production prompts from `src/prompts/`
- **PROD-005**: Must inject loaded prompts into the multi-agent system
- **PROD-006**: Must handle errors gracefully with clear error messages

#### **Test Harness Entry Point (`test_harness/optimization_runner.py`)**
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



## Non-Functional Requirements

### Performance
- **NFR-001**: System must leverage Optuna's efficient black-box optimization to minimize LangGraph calls
- **NFR-002**: System must use Optuna's TPE sampler for intelligent prompt optimization
- **NFR-003**: System must support configurable optimization trials through CLI parameters

### Reliability
- **NFR-004**: System must handle API failures gracefully with retry mechanisms
- **NFR-005**: System must provide rollback capability for failed optimizations
- **NFR-006**: System must provide comprehensive logging and error tracking
- **NFR-007**: System must support graceful degradation when components fail

### Usability
- **NFR-008**: System must be easy to install and configure with Optuna
- **NFR-009**: System must provide clear error messages with actionable guidance
- **NFR-010**: System must work with existing LangGraph system without modifications

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

## Input/Output Requirements

### Input
- **Optimization test cases** in JSONL format for baseline and optimization steps
- **Evaluation test cases** in JSONL format for final evaluation step (separate from optimization test cases)
- Original prompts for each agent (baseline)
- Prompt variations for each agent (from prompt_variations directory)
- Optuna configuration parameters
- **Optimization trial count** (required CLI parameter: `--optimization-trials`)
- MLflow server URI (optional CLI parameter)
- Experiment name (used for MLflow experiment name)

### Output
- **Three separate MLflow runs**: `<experiment_name>_baseline`, `<experiment_name>_optimize`, `<experiment_name>_eval`
- **Best optimized prompts** stored in file for evaluation step
- **Baseline performance metrics**: total factual correctness count and average composite score
- **Optimization performance metrics**: Final Optuna optimization results (best trial, Pareto front, optimization artifacts)
- **Evaluation performance metrics**: final total factual correctness count and average composite score
- **Promptfoo evaluation results**: `llm-rubric` scores for factuality, completeness, and relevance
- **Performance comparison**: baseline vs optimized vs evaluation results
- **MLflow artifacts**: prompts, metrics, and evaluation data for each step
- **Experiment logs and tracking data** for all three steps
- **Cached evaluation results** for reproducibility

## Constraints
- Must work with existing LangGraph multi-agent system
- Must use Optuna as the primary black-box optimization engine
- Must use Promptfoo as the evaluation service within Optuna trials
- Must use Promptfoo's `llm-rubric` for factuality, completeness, and relevance evaluation
- Must aggregate `llm-rubric` scores across all test cases by calculating the average
- Must generate Promptfoo configurations dynamically for each trial
- Must maintain separate directories for production, baseline, variants, and experiment prompts
- Must support manual prompt promotion from experiments to production after human review
- Must support rollback to baseline prompts when needed
- Must use Optuna's TPE sampler for efficient optimization of 7-dimensional prompt space
- Must support OpenAI API for LLM calls
- Must be compatible with Python 3.8+
- Must run sentence transformers locally (no HuggingFace API)
- Must not use LangSmith or external telemetry services
- Must ensure data privacy through local processing
- Must integrate Optuna with LangGraph system for end-to-end testing
- Must require optimization trial count as a mandatory parameter
- Must halt execution immediately upon any failure with detailed error logging
- Must store all experiment logs locally within experiment directories 