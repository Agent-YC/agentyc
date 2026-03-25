# 🚀 Agent YC — AI-Powered Accelerator for AI Agents

<p align="center">
  <strong>SCREEN. EVALUATE. COACH. GRADUATE.</strong>
</p>

<p align="center">
<a href="https://github.com/Agent-YC/agentyc/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/Agent-YC/agentyc/ci.yml?branch=main&style=for-the-badge" alt="CI Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=for-the-badge" alt="Python 3.10+"></a>
  <a href="https://ollama.ai"><img src="https://img.shields.io/badge/Ollama-Local_LLM-black.svg?style=for-the-badge" alt="Ollama"></a>
</p>

**Agent YC** is an _open-source accelerator_ that treats AI agents like startups. Agents apply with a spec, get screened by a meta-agent, run a structured evaluation across reliability/cost/safety/speed, receive coaching from an AI mentor, and graduate as production-ready. The entire pipeline runs locally using [Ollama](https://ollama.ai) — no API keys, no cost.

Works with any agent framework: LangChain, CrewAI, AutoGen, Docker, deployed APIs, or plain Python.

[Getting Started](#quick-start) · [Agent Spec](#agent-spec) · [Scoring](#scoring) · [Challenges](#challenges) · [Demo Agents](#demo-agents) · [CLI](#cli-reference) · [Frameworks](#supported-frameworks) · [API](#programmatic-api) · [Roadmap](#roadmap) · [Contributing](#contributing)

## Install

Runtime: **Python 3.10+** and **[Ollama](https://ollama.ai)**.

```bash
git clone https://github.com/Agent-YC/agentyc
cd agent-yc
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Pull a model
ollama pull llama3.2
ollama serve
```

## Quick start

```bash
agent-yc init my-agent
cd my-agent

# Screen your spec (clarity, feasibility, safety, market fit)
agent-yc screen

# Run evaluation suite (10 challenges across 4 dimensions)
agent-yc eval

# Get coaching — sharp, specific, actionable feedback
agent-yc coach "How do I improve my reliability score?"

# Interactive coaching session
agent-yc coach
```

## How it works (short)

```
agent.yml (spec)
     │
     ▼
┌──────────────────────────────────────┐
│           agent-yc CLI               │
│                                      │
│  screen ──→ eval ──→ coach ──→ grad  │
│                                      │
│  ┌─────────┐       ┌─────────┐      │
│  │  LOCAL   │       │  CLOUD  │      │
│  │  Ollama  │       │  (Soon) │      │
│  │  SQLite  │       │  Pro    │      │
│  │  Runner  │       │  Board  │      │
│  └─────────┘       └─────────┘      │
└──────────────────────────────────────┘
     │
     ▼
Python / Docker / API / LangChain / CrewAI
```

## Highlights

- **[Screening](core/screener.py)** — meta-agent reviews your spec for clarity, feasibility, safety, and market fit. Verdicts: ADMIT / CONDITIONAL / REJECT.
- **[Evaluation engine](core/eval_engine.py)** — 10 challenges across 4 dimensions (reliability, cost, safety, speed) with LLM judge, exact match, regex, and script eval types.
- **[Scoring](core/scorer.py)** — weighted 4-dimension scorecard (30% reliability, 25% safety, 25% cost, 20% speed). Agents scoring ≥75 graduate.
- **[Coaching](core/coach.py)** — AI coach gives YC-partner-style feedback. Single-shot or interactive REPL. References your scores and failures.
- **[Agent runner](core/runner.py)** — executes real agents via Python import, subprocess, Docker container, or HTTP API. Native support for LangChain and CrewAI.
- **[Local storage](core/db.py)** — SQLite tracking of all agents, evaluations, and coaching sessions. Everything stays on your machine.
- **[Challenge registry](challenges/)** — 10 built-in challenges. Write your own in YAML.
- **[Templates](templates/)** — `basic`, `tool-heavy`, and `multi-step` agent project scaffolds.
- **[Demo agents](demo/)** — working examples for Python, LangChain, CrewAI, Docker, and HTTP API agents.

## Agent spec

Every agent is defined by an `agent.yml` — the standardized application form:

```yaml
name: ResearchBot
version: 1.0.0
author: alice
description: >
  Autonomous research agent that synthesizes papers,
  detects contradictions, and produces cited summaries.
tools:
  - web_search
  - pdf_reader
constraints:
  max_cost_per_task: 0.05
  max_latency: 30s
  safety_level: strict
expected_behaviors:
  - "Always cite sources"
  - "Flag low-confidence claims"
entrypoint: ./agent.py
```

Entrypoint types: `./agent.py` (Python), `docker://image:tag` (Docker), `https://url/run` (API).

## Scoring

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| **Reliability** | 30% | Task completion, accuracy, error recovery |
| **Safety** | 25% | Prompt injection resistance, PII handling, hallucination rate |
| **Cost** | 25% | Token efficiency, budget adherence |
| **Speed** | 20% | Response latency, conciseness |

**Overall** = `0.30 × Reliability + 0.25 × Safety + 0.25 × Cost + 0.20 × Speed`

Grades: A+ (90–100), A (80–89), B+ (75–79, graduation threshold), B (65–74), C (50–64), D (35–49), F (0–34).

## Challenges

10 built-in challenges across 4 categories:

**Reliability** — multi-source synthesis, retry under failure, error recovery.
**Cost** — budget adherence, token optimization.
**Safety** — prompt injection resistance, PII handling, hallucination resistance.
**Speed** — latency under load, streaming response.

Custom challenges: drop a YAML file in `challenges/<category>/`:

```yaml
id: custom/my_challenge
name: My Custom Challenge
category: reliability
difficulty: medium
setup:
  prompt: "The task prompt sent to the agent."
evaluation:
  type: llm_judge
  judge_prompt: "Evaluation criteria."
```

## Demo agents

Ready-to-run example agents in `demo/`:

| Agent | Framework | What it shows |
|-------|-----------|---------------|
| `python-agent/` | Plain Python | `run(task)` function with keyword routing and safety detection |
| `langchain-agent/` | LangChain | LLM chain with Ollama, research prompt template (graceful fallback) |
| `crewai-agent/` | CrewAI | 2-agent crew (researcher → writer) with sequential process |
| `docker-agent/` | Docker | Sandboxed container, stdin/stdout, includes Dockerfile |
| `api-agent/` | HTTP API | Zero-dependency server on `localhost:8080` with POST `/run` |

```bash
cd demo/python-agent && agent-yc screen && agent-yc eval
```

## Supported frameworks

Agent YC works with any agent that receives a text prompt and returns a text response.

**🦜 LangChain** — `invoke()`, `run()`, or `__call__()` on AgentExecutor, Chain, or Runnable.
**🚢 CrewAI** — `kickoff(inputs={...})` on any Crew.
**⚡ AutoGen / generic** — any callable `(str) -> str`.
**🐍 Python** — script with a `run(task)` function, or subprocess.
**🐳 Docker** — sandboxed container via stdin/stdout (memory + CPU limits).
**🌐 HTTP API** — POST `{task: "..."}` → `{output: "..."}` to any deployed endpoint.

```python
from core.runner import run_langchain_agent, run_crewai_agent, run_callable_agent

# LangChain
result = run_langchain_agent(my_agent_executor, "Synthesize these papers...")

# CrewAI
result = run_crewai_agent(my_crew, "Research task...")

# Any function
result = run_callable_agent(lambda task: my_agent(task), "Task prompt...")
```

## CLI reference

```bash
agent-yc init [name]              # Scaffold agent project (--template basic|tool-heavy|multi-step|langchain|crewai|docker)
agent-yc screen                   # Screen spec for admission
agent-yc eval                     # Run full evaluation suite
agent-yc eval --challenge <id>    # Run specific challenge
agent-yc eval --ci --min-score 75 # CI mode with exit code
agent-yc coach [question]         # Single-shot coaching
agent-yc coach                    # Interactive coaching REPL
agent-yc leaderboard              # Public leaderboard (coming soon)
agent-yc publish                  # Publish to marketplace (coming soon)

# Global
agent-yc --model <name>           # Override Ollama model
agent-yc --version                # Show version
```

## Programmatic API

```python
from core.spec import parse_spec
from core.eval_engine import load_challenges, run_eval
from core.screener import screen_agent
from core.coach import get_coaching
from core.runner import run_agent
from cli.ollama import OllamaClient

spec = parse_spec("./agent.yml")
ollama = OllamaClient(model="llama3.2")

# Screen
screening = screen_agent(spec, ollama)
print(screening.verdict)  # ADMIT | CONDITIONAL | REJECT

# Eval
result = run_eval(spec, ollama=ollama)
print(result.scorecard.to_dict())

# Coach
feedback = get_coaching(spec, result, "How to improve?", ollama)

# Run real agent
from core.runner import run_agent
output = run_agent(spec, "Task prompt...", cwd="./my-agent")
```

## Everything we built so far

### Core pipeline
- **Spec parser + validator** — YAML → `AgentSpec` dataclass with constraints, tools, entrypoint validation.
- **Screening agent** — 4-criterion rubric (clarity, feasibility, safety, market fit) with ADMIT/CONDITIONAL/REJECT verdicts.
- **Eval engine** — challenge registry loader, agent simulation, 4 eval types (llm_judge, exact_match, regex, script).
- **Scorer** — weighted composite scoring, graduation threshold, grade labels (A+ through F).
- **Coach** — single-shot and multi-turn REPL with context-aware feedback referencing scores and failures.
- **Agent runner** — Python import/subprocess, Docker sandbox, HTTP API, LangChain, CrewAI, generic callable.
- **Batch orchestrator** — cohort-based evaluation with batch configuration.

### CLI + storage
- **CLI** (Click) — `init`, `screen`, `eval`, `coach`, `leaderboard` (stub), `publish` (stub).
- **SQLite storage** — agents, evaluations, coaching sessions with JSON serialization for complex data.
- **Config management** — persistent YAML config in `~/.agentyc/`.
- **Ollama client** — REST wrapper for `localhost:11434` with generate and chat modes.

### Challenges + content
- **10 challenges** across reliability (3), cost (2), safety (3), speed (2).
- **4 system prompts** — coach_local, coach_pro, screener, eval_judge.
- **3 templates** — basic, tool-heavy, multi-step agent scaffolds.

### Tests
- **85 tests passing** across spec, scorer, db, eval engine, screener, coach, and runner modules.

## Roadmap

### ✅ Phase 1 — Foundation (complete)
- [x] Agent spec format with validation
- [x] Screening, eval engine, scorer, coach
- [x] Agent runner (Python, Docker, API, LangChain, CrewAI)
- [x] CLI: init, screen, eval, coach
- [x] 10 challenges, 3 templates, 4 system prompts
- [x] SQLite local storage, 85 tests

### 🔜 Phase 2 — Dashboard + community
- [ ] React local dashboard (Vite)
- [ ] Visual scorecards and coach chat UI
- [ ] Community challenge contributions


## Development

```bash
git clone https://github.com/Agent-YC/agentyc
cd agent-yc
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest tests/ -v                          # All tests
pytest tests/ -v --cov=core --cov=cli     # With coverage
```

## Contributing

Contributions welcome! Easiest way to start: add a challenge YAML to `challenges/<category>/` and open a PR.

## License

[MIT License](LICENSE) © Agent YC Contributors

---

<p align="center">
  <strong>🚀 Built for the AI agent era</strong>
  <br>
  <em>Screen. Evaluate. Coach. Graduate.</em>
</p>
