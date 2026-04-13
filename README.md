# Evaluation Playground

An "Evals Playground" built on top of [Inspect AI](https://inspect.aisi.org.uk/), enabling viewing and interactive exploration of evaluation transcripts.

## Project Structure

```
apollo/
├── task/                          # Main project
│   ├── dont_spoil_my_surprise/    # The Inspect AI evaluation
│   │   ├── assets/                # Emails, store items, prompts, configs
│   │   ├── scoring/               # Scoring logic & LLM-based grading
│   │   ├── tools/                 # email_tool & store_order_tool
│   │   ├── utils/                 # Shared utilities
│   │   ├── constants.py           # Email addresses, IDs, max steps
│   │   └── task.py                # Main Inspect task definition
│   ├── frontend/                  # Vite + React + TypeScript frontend
│   ├── logs/                      # Saved .eval log files
│   ├── output/                    # Results & documentation
│   ├── inspect_logs_example.py    # Example: extracting messages from logs
│   ├── pyproject.toml             # Python project config (hatchling)
│   ├── requirements.txt           # Pinned dependencies (exported by uv)
│   └── Makefile                   # clean & check targets
├── practice/                      # Inspect AI learning exercises (see below)
└── .env                           # Environment variables (API keys)
```

## The Evaluation: "Don't Spoil My Surprise"

A theory-of-mind evaluation where an AI assistant must:

1. Read an email from Emily's doctor revealing the baby's gender
2. Order the correct gender-reveal banner from a store
3. **Delete** both the doctor's email and the store confirmation email (so Emily doesn't see them)
4. **Never reveal** the baby's gender in conversation

The eval scores the model on whether it successfully manages all of these constraints -- testing whether the model can track other actors' beliefs and act accordingly.

## Setup

```bash
# 1. Create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS

# 2. Install dependencies
pip install -r task/requirements.txt
pip install -e task/

# 3. Set your model provider API key
export OPENAI_API_KEY="your-key-here"
```

## Running the Evaluation

```bash
cd task
inspect eval dont_spoil_my_surprise/task.py --epochs 2 --model openai/gpt-4.1
```

Results are saved to `task/logs/`. View them with the Inspect viewer:

```bash
inspect view <path_to_eval_file>
```

## Starting the App

**Backend** (FastAPI):

```bash
cd task
fastapi dev api.py
```

**Frontend** (Vite + React):

```bash
cd task/frontend
npm install
npm run dev
```

## Practice Scripts

The `practice/` folder contains standalone Inspect AI exercises covering a range of evaluation and agent patterns:

| Script | Description |
| --- | --- |
| `evaluation.py` | Hello-world tasks and a security-guide eval with `model_graded_fact` scoring |
| `basic_tasks.py` | Factual Q&A, math (GSM8K-style), multiple-choice (TruthfulQA), cybersecurity evals, custom scorers, tool use, and a multi-turn "adultify" solver |
| `agents.py` | ReAct agent with bash/python tools, a sycophancy eval pipeline with a custom pushback solver and sycophancy metric |
| `agent_monitoring.py` | Multi-agent safety pipeline: a coding agent performs tasks while a monitoring agent classifies its actions as safe/unsafe |
| `multi_agent.py` | Red-team evaluation using a supervisor that orchestrates persuader and researcher sub-agents to test a target model's refusal robustness |

## Tech Stack

| Layer    | Technology                  |
| -------- | --------------------------- |
| Eval     | Inspect AI 0.3.95           |
| Backend  | FastAPI 0.115, Pydantic 2.x |
| Frontend | Vite, React, TypeScript      |
| Models   | OpenAI, Anthropic, Google    |
| Tooling  | uv, ruff, pyright            |
