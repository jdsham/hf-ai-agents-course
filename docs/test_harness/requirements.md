# Test Harness Requirements

## Overview
A test harness for optimizing prompts used in a LangGraph multi-agent system using a three-step process: baseline evaluation, Optuna optimization, and final evaluation. Each step creates a separate MLflow run for comprehensive tracking.

**Note**: This test harness operates as a **separate system** that generates and injects prompts into the multi-agent system. It uses a three-step process: baseline evaluation, Optuna optimization, and final evaluation, each with its own MLflow run for complete experiment tracking.

## Intentionally Ignored Aspects

This test harness is designed for **research and development purposes only** and intentionally ignores the following production system concerns:

- **Performance Requirements**: No specific performance targets, response times, or throughput requirements
- **Scalability**: No support for distributed execution, load balancing, or horizontal scaling
- **Security**: No authentication, authorization, or data protection mechanisms
- **Reliability**: No fault tolerance, redundancy, or high availability features

These aspects are intentionally excluded to focus the test harness on its core purpose: prompt optimization through systematic experimentation and evaluation.

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
- **REQ-072**: The system must provide comprehensive logging at multiple levels (DEBUG, INFO, WARNING, ERROR)
- **REQ-073**: The system must log all Optuna trial execution steps, inputs, outputs, and timing information
- **REQ-074**: The system must log all Promptfoo evaluation steps, inputs, outputs, and timing information
- **REQ-075**: The system must provide detailed error messages with context and stack traces
- **REQ-076**: The system must log all API calls, responses, and performance metrics
- **REQ-077**: The system must store all experiment logs locally within the experiment's directory structure
- **REQ-078**: The system must halt execution immediately upon any failure and ensure logs capture complete error context for debugging
- **REQ-079**: The system must not implement retry mechanisms or error recovery - failures must stop execution

### 10. Prompt Integration with LangGraph
- **REQ-080**: The system must inject selected prompts into the LangGraph multi-agent system during optimization trials
- **REQ-081**: The system must ensure prompt injection does not affect production system operation
- **REQ-082**: The system must support manual rollback to baseline prompts when needed
- **REQ-083**: The system must support manual deployment of optimized prompts to production system after human review
- **REQ-084**: The system must convert Optuna trial parameters to actual prompts during optimization trials
- **REQ-085**: The system must maintain prompt isolation between test harness and production environments

### 11. Modular Architecture & Operations
- **REQ-086**: The system must be modular with clearly defined component boundaries
- **REQ-087**: The system must enforce a defined order of operations for all processes
- **REQ-088**: The system must support independent testing of individual modules
- **REQ-089**: The system must provide clear interfaces between modules
- **REQ-090**: The system must operate independently from the production system
- **REQ-091**: The system must receive and inject prompts without affecting production
- **REQ-092**: The system must support future integration of prompt management and versioning capabilities without requiring architectural changes to the core test harness functionality

### 12. MLflow Integration
- **REQ-093**: The system must integrate with MLflow for experiment tracking across all three steps
- **REQ-094**: The system must accept MLflow server URI as a CLI parameter
- **REQ-095**: The system must use the experiment name as the base MLflow experiment name
- **REQ-096**: The system must create separate MLflow runs for each step: `<experiment_name>_baseline`, `<experiment_name>_optimize`, `<experiment_name>_eval`
- **REQ-097**: The system must log the following data to each MLflow run:
  - **Baseline Run**: Prompts used for each agent, Promptfoo metrics (total factual correctness count, average composite score), test data version used
  - **Optimize Run**: Final Optuna optimization results (best trial, Pareto front, optimization metrics), best prompts selected for each agent, Promptfoo metrics from best trial, test data version used
  - **Evaluation Run**: Best optimized prompts for each agent, Promptfoo metrics (total factual correctness count, average composite score), validation data version used, performance comparison with baseline
- **REQ-098**: The system must support MLflow model comparison between different experiment runs

### 13. Optuna Configuration and Optimization Integration
- **REQ-099**: The system must configure Optuna to use multi-objective black-box optimization for prompt combinations
- **REQ-100**: The system must configure Optuna to test prompt combinations against the LangGraph multi-agent system
- **REQ-101**: The system must use Optuna's TPE (Tree-structured Parzen Estimator) sampler for efficient optimization
- **REQ-102**: The system must accept optimization trial count as a required CLI parameter and pass it to Optuna study
- **REQ-103**: The system must capture and log Optuna optimization results
- **REQ-104**: The system must provide experiment summary reports showing optimization progress, best trial selection, and performance improvements
- **REQ-105**: The system must configure Optuna to optimize prompt variants as categorical parameters using prompt indices (0 for baseline, 1+ for variants), where the system dynamically detects the number of variants per agent and uses the inclusive range [0, N] where N is the total number of prompts (baseline + variants)
- **REQ-106**: The system must convert Optuna trial parameters to actual prompts during optimization trials
- **REQ-107**: The system must use Optuna's `enqueue_trial()` to add baseline prompt combination as the first trial
- **REQ-108**: The system must configure Optuna search space to include baseline prompts as a valid option
- **REQ-109**: The system must handle baseline prompt selection (index 0) in the prompt conversion logic
- **REQ-110**: The system must configure Optuna study with directions ["maximize", "maximize"] for total factual correctness count and average composite score
- **REQ-111**: The system must prioritize total factual correctness count over average composite score in multi-objective optimization
- **REQ-112**: The system must use Pareto front analysis to identify best prompt combinations
- **REQ-113**: The system must select the best trial based on highest total factual correctness count, then highest average composite score

### 14. Promptfoo Integration and Evaluation
- **REQ-114**: The system must use Promptfoo as the evaluation service for all evaluation steps (baseline, optimization trials, and final evaluation)
- **REQ-115**: The system must generate Promptfoo configurations dynamically for each optimization trial
- **REQ-116**: The system must integrate Promptfoo with the LangGraph multi-agent system for evaluation
- **REQ-117**: The system must leverage Promptfoo's built-in caching to avoid redundant evaluations
- **REQ-118**: The system must log all Promptfoo evaluation steps, inputs, outputs, and timing information
- **REQ-119**: The system must handle Promptfoo evaluation failures by halting execution and logging detailed error information
- **REQ-120**: The system must configure `llm-rubric` to use ChatGPT (GPT-4) as the grading model
- **REQ-121**: The system must ensure `llm-rubric` returns scores in the 0.0-1.0 range for proper aggregation
- **REQ-122**: The system must configure `llm-rubric` with evaluation criteria for factuality, completeness, and relevance
- **REQ-123**: The system must implement score averaging logic to aggregate `llm-rubric` results across all test cases
- **REQ-124**: The system must handle `llm-rubric` JSON response format with `reason`, `score`, and `pass` fields
- **REQ-125**: The system must evaluate only the `final_answer` field from the multi-agent system's graph state output
- **REQ-126**: The system must use test case expected answers (from the `answer` field) for `llm-rubric` evaluation comparison
- **REQ-127**: The system must evaluate overall system performance, not individual agent outputs
- **REQ-128**: The system must halt execution immediately if Promptfoo evaluation fails completely
- **REQ-129**: The system must log detailed error information before halting execution
- **REQ-130**: The system must not attempt fallback evaluation methods if Promptfoo fails

### 15. Prompt Organization and File Structure
- **REQ-131**: The system must maintain production prompts in `src/prompts/` directory
- **REQ-132**: The system must maintain baseline prompts in `test_harness/experiments/{experiment_name}/baseline_prompts/` directory
- **REQ-133**: The system must store optimized prompts in `test_harness/experiments/{experiment_name}/optimized_prompts/` directory
- **REQ-134**: The system must support manual promotion of optimized prompts from experiments to production after human review
- **REQ-135**: The system must support rollback to baseline prompts when needed
- **REQ-136**: The system must maintain clear separation between production, baseline, and experimental prompts
- **REQ-137**: The system must version control production prompts while keeping experiments isolated
- **REQ-138**: The system must copy production prompts to baseline before starting optimization
- **REQ-139**: The system must provide baseline performance metrics for comparison with optimized results
- **REQ-140**: The system must organize prompt variants by agent type in subdirectories
- **REQ-141**: The system must maintain consistent naming conventions across all prompt directories
- **REQ-142**: The system must ensure baseline prompts are exact copies of production prompts
- **REQ-143**: The system must support easy comparison between baseline, variants, and optimized prompts
- **REQ-144**: The system must maintain prompt metadata and version information in experiment directories
- **REQ-145**: The system must use simplified experiment naming: `exp_001`, `exp_002`, `exp_003`, etc.
- **REQ-146**: Each experiment must represent a complete three-step process: baseline evaluation, optimization, and final evaluation
- **REQ-147**: The system must automatically copy current production prompts from `src/prompts/` to the experiment's baseline folder at the start of each experiment
- **REQ-148**: The system must save the best optimized prompts as text files in the experiment's optimized_prompts folder after optimization is complete
- **REQ-149**: The system must load the optimized prompts from the experiment's optimized_prompts folder for the final evaluation step
- **REQ-150**: The system must support manual rollback by copying baseline prompts to source code folder
- **REQ-151**: The system must not automatically update source code prompts
- **REQ-152**: The system must maintain baseline prompts as exact copies of production prompts
- **REQ-153**: The system must create and maintain a `logs/` directory within each experiment folder to store all experiment-specific logging

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

## Production System Requirements

### Production System Behavior
- **PROD-REQ-001**: The production system (`src/main.py`) must iterate through all GAIA Level 1 questions
- **PROD-REQ-002**: The production system must generate a JSONL file containing answers and reasoning traces for each question
- **PROD-REQ-003**: The production system must support optional input questions file specification
- **PROD-REQ-004**: The production system must support optional output file specification
- **PROD-REQ-005**: The production system must include reasoning traces in the output JSONL format
- **PROD-REQ-006**: The production system must load stable production prompts from `src/prompts/`
- **PROD-REQ-007**: The production system must inject loaded prompts into the multi-agent system
- **PROD-REQ-008**: The production system must handle errors gracefully with clear error messages

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