# Prompt Templates and Variants

This directory contains the template-based prompt system for the multi-agent LangGraph system, designed for joint optimization using Promptfoo.

## Directory Structure

```
src/prompts/
├── templates/                    # Template files with variable placeholders
│   └── planner_template.txt      # Planner agent template
├── variants/                     # Individual variant files for each template variable
│   ├── planner_role_definition_variants.txt
│   ├── planner_task_description_variants.txt
│   ├── planner_research_guidelines_variants.txt
│   ├── planner_expert_guidelines_variants.txt
│   ├── planner_question_analysis_framework_variants.txt
│   └── planner_feedback_handling_variants.txt
├── planner_variants_config.yaml  # YAML configuration with all variants
└── README.md                     # This file
```

## Template Structure

Each agent template follows this structure:

```
## Who you are:
{role_definition}

## What your task is:
{task_description}

## [Agent-specific sections]:
{guidelines_variables}

## Output Format (JSON)
[Fixed JSON output specification]

## Context Variables:
- question: {question}
- [other context variables]
```

## Template Variables

### Planner Agent Variables:
- `role_definition`: How the planner sees itself
- `task_description`: What the planner needs to accomplish
- `research_guidelines`: How to create effective research steps
- `expert_guidelines`: How to create effective expert steps
- `question_analysis_framework`: How to analyze GAIA level 1 questions
- `feedback_handling`: How to respond to critic feedback

## Variants

Each template variable has 5 variants that can be tested:

1. **Basic/Simple**: Straightforward, direct approach
2. **Comprehensive**: Detailed, thorough approach
3. **Strategic**: Focused on efficiency and effectiveness
4. **Systematic**: Methodical, step-by-step approach
5. **Targeted**: Specific, purpose-driven approach

## Joint Optimization

The variants are designed to enable joint optimization across agents:

- **Shared Variables**: Some variables (like role definitions) can be optimized across multiple agents
- **Consistency**: Variants maintain consistency in terminology and approach
- **Compatibility**: Templates are designed to work together in the multi-agent workflow

## Usage with Promptfoo

1. **Template File**: Use `templates/planner_template.txt` as the base template
2. **Variants**: Use `planner_variants_config.yaml` to define all variant combinations
3. **Testing**: Promptfoo will systematically test different combinations of variants
4. **Optimization**: Find the optimal combination for GAIA level 1 questions

## Next Steps

1. Create YAML configuration files for all agents (researcher, expert, critic, finalizer)
2. Configure Promptfoo to test the entire multi-agent system
3. Run joint optimization to find the best prompt combinations
4. Analyze results and deploy optimized prompts

## GAIA Level 1 Considerations

All variants are designed with GAIA level 1 questions in mind:
- Factual accuracy requirements
- Analytical reasoning capabilities
- Synthesis of multiple information sources
- Comprehensive answer generation
- Logical reasoning trace requirements 