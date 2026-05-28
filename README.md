# AeonLogic

> **Recursive Perpetual Evolution** — a LangGraph-orchestrated, self-improving multi-agent AI system.

AeonLogic is a production-grade, recursive multi-agent framework built on LangGraph. Five specialized agents collaborate inside a stateful graph, critique each other's outputs, and continuously synthesize experience into a hybrid memory system (Neo4j + ChromaDB). Model routing automatically selects between a fast tier (`qwen-turbo`) and a strong tier (`qwen-plus`) based on task complexity and risk classification.

---

## Architecture overview

```
User / API
    │
    ▼
┌───────────────────────────────────────────────┐
│                 LangGraph Graph                │
│                                               │
│  Dispatcher ──► Generator ──► Critic          │
│       ▲              │           │            │
│       │              ▼           ▼            │
│  Memory          Executor ◄─────┘            │
│  Synthesizer ◄───────────────────────────────│
└───────────────────────────────────────────────┘
         │                     │
         ▼                     ▼
    Neo4j Graph           ChromaDB Vector
    (knowledge)           (episodic memory)
```

| Agent | Role |
|---|---|
| **Dispatcher** | Decomposes goals, classifies task risk, routes to correct model tier |
| **Generator** | Produces candidate solutions / artefacts |
| **Critic / Adversarial Auditor** | Stress-tests outputs; raises findings |
| **Executor** | Runs validated artefacts in a sandboxed environment |
| **Memory Synthesizer** | Distils experience into persistent long-term memory |

---

## Quick start

### Prerequisites

| Requirement | Version |
|---|---|
| Python | ≥ 3.11 |
| Neo4j | ≥ 5.x (local or AuraDB) |
| ChromaDB server | ≥ 0.5.x (or embedded mode) |
| DashScope API key | Alibaba Cloud |

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd AeonLogic
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys and service URIs
```

### 4. Start backing services (Docker)

```bash
docker-compose up -d
```

### 5. Run

```bash
# CLI
aeonlogic run --task "your task description"

# API server
uvicorn aeonlogic.app.api:app --reload
```

---

## Project layout

```
AeonLogic/
├── src/aeonlogic/
│   ├── agents/          # Dispatcher, Generator, Critic, Executor, MemorySynthesizer
│   ├── app/             # FastAPI app, CLI, lifecycle hooks
│   ├── domain/          # Pure domain models (Task, Artifact, Finding, Result)
│   ├── execution/       # Sandbox runner, artefact validation, result parsing
│   ├── graph/           # LangGraph builder, state schema, edge conditions, checkpoints
│   ├── memory/          # Neo4j store, ChromaDB store, hybrid retrieval
│   ├── models/          # Qwen client, model router, prompt templates, token budgets
│   ├── observability/   # Structured logging, OpenTelemetry tracing, Prometheus metrics
│   ├── security/        # Policies, threat models, validators, adversarial test suite
│   └── utils/           # IDs (ULID), hashing, retry helpers, time utilities
├── configs/
├── data/
├── docs/
│   ├── SYSTEM_DESIGN.md
│   ├── AGENT_SPEC.md
│   ├── STATE_MACHINE.md
│   └── WHITEPAPER_SUMMARY.md
├── tests/
├── scripts/
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

## Documentation

| Document | Description |
|---|---|
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | Architecture decisions, component interactions, data flows |
| [AGENT_SPEC.md](docs/AGENT_SPEC.md) | Per-agent contracts, inputs, outputs, model assignments |
| [STATE_MACHINE.md](docs/STATE_MACHINE.md) | LangGraph state schema and edge transition rules |
| [WHITEPAPER_SUMMARY.md](docs/WHITEPAPER_SUMMARY.md) | Theoretical foundation — Recursive Perpetual Evolution |

---

## Development

```bash
# Lint
ruff check src tests

# Type-check
mypy src

# Tests
pytest
```

---

## License

MIT
