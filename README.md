# hf-ai-agents-course
This repository follows the Hugging Face AI Agents course and contains the contents to develop an AI agent to answer GAIA Level 1 questions.

## Synthetic GAIA Test Sets Usage

This project uses two separate sets of synthetic GAIA Level 1 test cases to support robust prompt tuning and unbiased evaluation:

- **`data/synthetic_gaia_testcases.jsonl`**: 
  - **Purpose:** For prompt tuning and development with DSPy.
  - **Usage:** Use this set to optimize prompts, agent logic, and evaluate improvements during development. Do not use for final evaluation to avoid overfitting.

- **`data/synthetic_gaia_evalset.jsonl`**: 
  - **Purpose:** For final evaluation and benchmarking with promptfoo (or other evaluation tools).
  - **Usage:** Use this set only for unbiased, post-tuning evaluation to measure real-world/generalization performance. Do not use for tuning or development.

**Referenced Files:**
- All files referenced in these test sets are located in the `data/` directory and contain the required content for each test case.

**Best Practice:**
- Never use the evaluation set for tuning or prompt optimization. This ensures your evaluation results reflect true generalization and are not biased by the tuning process.
