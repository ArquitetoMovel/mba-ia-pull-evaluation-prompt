# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MBA AI course challenge: pull a low-quality prompt from LangSmith Prompt Hub, optimize it using prompt engineering techniques, push it back, and achieve ≥0.9 on all 4 evaluation metrics (Tone Score, Acceptance Criteria Score, User Story Format Score, Completeness Score).

The task is converting bug reports into user stories using the `bug_to_user_story` prompt.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in credentials
```

Required `.env` variables: `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `USERNAME_LANGSMITH_HUB`, and either `OPENAI_API_KEY` or `GOOGLE_API_KEY`. Set `LLM_PROVIDER=google` or `LLM_PROVIDER=openai`.

## Key Commands

```bash
python src/pull_prompts.py   # Pull v1 prompt from LangSmith → prompts/bug_to_user_story_v1.yml
python src/push_prompts.py   # Push optimized v2 prompt to LangSmith
python src/evaluate.py       # Run LLM-as-Judge evaluation (pass threshold: all metrics ≥ 0.9)

pytest tests/test_prompts.py        # Run all tests
pytest tests/test_prompts.py -v     # Verbose output
```

## Architecture

**Pipeline flow:**
1. `pull_prompts.py` → fetches from LangSmith Hub, saves to `prompts/bug_to_user_story_v1.yml`
2. Manually edit/create `prompts/bug_to_user_story_v2.yml` with optimized prompt
3. `push_prompts.py` → reads v2 YAML, pushes to `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`
4. `evaluate.py` → loads `datasets/bug_to_user_story.jsonl` (15 examples), creates LangSmith dataset, runs prompt against up to 10 examples, scores with 4 LLM-as-Judge metrics from `metrics.py`

**Key files:**
- `src/utils.py` — `get_llm()` / `get_eval_llm()` factory (OpenAI or Gemini), `load_yaml()` / `save_yaml()`, `validate_prompt_structure()`
- `src/metrics.py` — 4 scoring functions used by `evaluate.py`: `evaluate_tone_score`, `evaluate_acceptance_criteria_score`, `evaluate_user_story_format_score`, `evaluate_completeness_score`
- `prompts/bug_to_user_story_v1.yml` — serialized LangChain `ChatPromptTemplate` (raw, low-quality)
- `datasets/bug_to_user_story.jsonl` — 15 labeled examples: `inputs.bug_report` → `outputs.reference`

**Prompt YAML format** is a serialized LangChain `ChatPromptTemplate`. The v2 YAML must have `metadata.techniques` listing at least 2 prompt engineering techniques used.

## LangChain Patterns (LCEL)

Use pipe operator for chains:
```python
chain = prompt_template | llm | StrOutputParser()
result = chain.invoke({"bug_report": "..."})
```

Prefer `ChatPromptTemplate`, `StrOutputParser`, and `RunnablePassthrough` over legacy patterns. Use `.invoke()` for single calls, `.batch()` for multiple inputs.

## Required Tests (tests/test_prompts.py)

Six tests must be implemented for `prompts/bug_to_user_story_v2.yml`:
- `test_prompt_has_system_prompt` — system prompt field exists and is non-empty
- `test_prompt_has_role_definition` — defines a persona (e.g., "Você é um Product Manager")
- `test_prompt_mentions_format` — requires Markdown or User Story format
- `test_prompt_has_few_shot_examples` — contains input/output examples
- `test_prompt_no_todos` — no `[TODO]` placeholders remain
- `test_minimum_techniques` — `metadata.techniques` lists at least 2 techniques

## Prompt Optimization Techniques

Apply at least two of: Few-shot Learning, Chain of Thought (CoT), Tree of Thought, Skeleton of Thought, ReAct, Role Prompting. The optimized prompt must include clear instructions, explicit rules, few-shot examples, edge case handling, and proper System vs User prompt separation.

**Do not modify** `datasets/bug_to_user_story.jsonl` or the evaluation metrics in `metrics.py`.
