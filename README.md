# ⚡ AeonLogic

## Recursive Self-Healing Multi-Agent Engine
### CLI + Streamlit Command Center

> A LangGraph-orchestrated, five-agent AI system that detects security failures, triggers an autonomous recursive repair loop, and synthesises every outcome into a persistent hybrid memory (ChromaDB + Neo4j) — so every future run is informed by the past.

**No API key required for demos. No Neo4j server required for tests. Runs fully offline in mock mode.**

---

## Features

| | Feature | Detail |
|---|---|---|
| ⚡ | **Multi-agent pipeline** | Dispatcher · Generator · Critic · Executor · Memory Synthesizer |
| 🔁 | **Recursive self-healing repair loop** | Critic findings injected back into Generator; deterministic attempt-1-fail / attempt-2-repair |
| 🤖 | **Qwen mock / real / fallback mode** | `AEONLOGIC_MODE=auto\|real\|mock` · `REAL_MODEL_MODE`, `MOCK_MODEL_MODE`, `FALLBACK_MODE` · no API key required for mock/demo |
| 🔑 | **Qwen Cloud status panel** | Sidebar shows runtime mode, configured model, base URL, API key presence (masked) — key value never displayed |
| 🧠 | **ChromaDB persistent semantic memory** | Lessons written as embeddings; retrieved via semantic similarity |
| 🕸 | **Neo4j knowledge graph interface** | Failure/success nodes and artifact relationships; safe no-op when unavailable |
| 🔀 | **Hybrid memory orchestration** | Chroma authoritative + Neo4j best-effort; full fallback chain (Chroma → Mock, Neo4j → silent no-op) |
| 🖥 | **Streamlit Command Center dashboard** | Agent timeline · metrics · findings · memory writes · presentation mode · one-click demos |
| 📄 | **Downloadable demo report** | Plain-text export with session ID, model, findings summary, memory lessons, final verdict |
| 🔎 | **Artifact Preview panel** | Displays generated artifact text (truncated) and session ID after each run; graceful fallback when unavailable |

---

## Architecture

```
DISPATCH → GENERATE → CRITIC → EXECUTE → REPAIR → MEMORY → FINAL
```

When the Critic rejects an artifact, the graph automatically routes back to the Generator with findings in context (the **self-healing** repair cycle). After a successful execution the Memory Synthesizer writes structured lessons to both ChromaDB and Neo4j before the session ends.

```
User / CLI / Dashboard
        │
        ▼
┌──────────────────────────────────────────────────┐
│                  LangGraph Graph                  │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │Dispatcher│──►│Generator │──►│Critic        │ │
│  └──────────┘   └──────────┘   └──────┬───────┘ │
│                      ▲  ◄─[REPAIR]────┘ reject  │
│                      │                  approve  │
│                      │            ┌──────────┐  │
│                      │            │ Executor │  │
│                      │            └────┬─────┘  │
│                      │                 │        │
│               ┌──────┴─────────────────┘        │
│               │  Memory Synthesizer              │
│               └──────────────────────────────────│
└──────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
   Neo4j Graph                ChromaDB Vector
   (knowledge)                (episodic memory)
```

| Agent | Role |
|---|---|
| **Dispatcher** | Decomposes goals, classifies task risk, selects model tier |
| **Generator** | Produces candidate artifacts; injects retrieved memory lessons into prompt |
| **Critic / Adversarial Auditor** | Stress-tests outputs; raises structured `Finding` objects |
| **Executor** | Runs approved artifacts; blocks on critical security findings |
| **Memory Synthesizer** | Writes failure/success lessons; retrieves context for next cycle |

---

## Quick start

### Prerequisites

| Requirement | Notes |
|---|---|
| Python ≥ 3.11 | 3.12+ recommended |
| Git | — |
| (Optional) DashScope API key | Only needed for real Qwen inference; mock mode works without it |
| (Optional) `AEONLOGIC_MODE=real` | Set in `.env` alongside `QWEN_API_KEY` to enable real cloud mode |
| (Optional) Neo4j ≥ 5.x | Only needed for graph memory; safe no-op fallback if absent |

### 1 — Clone and install

```bash
git clone <repo-url>
cd AeonLogic
python -m venv .venv
```

```powershell
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

```bash
# macOS / Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### 2 — Run the test suite

```powershell
# Windows (.venv)
.\.venv\Scripts\python.exe -m pytest tests -v

# Any platform (no install required — set PYTHONPATH)
$env:PYTHONPATH = "src"; python -m pytest tests -v
```

> **Expected:** 267+ tests pass. One pre-existing `structlog` import failure is unrelated to engine logic and does not affect the demo.

### 3 — Run the CLI demo

```powershell
.\.venv\Scripts\aeonlogic.exe "Build a secure API authentication module"
```

Watch the recursive repair loop in real time: attempt 1 fails with security findings, attempt 2 repairs all issues and passes.

### 4 — Run the Streamlit dashboard

```powershell
$env:PYTHONPATH = "src"; streamlit run src/aeonlogic/app/streamlit_demo.py
```

Or with `.venv`:

```powershell
.\.venv\Scripts\streamlit.exe run src/aeonlogic/app/streamlit_demo.py
```

Open [http://localhost:8501](http://localhost:8501) — click **🔐 Security Auth Demo** for a one-click walkthrough.

---

## Project layout

```
AeonLogic/
├── src/aeonlogic/
│   ├── agents/          # Dispatcher, Generator, Critic, Executor, MemorySynthesizer
│   ├── app/             # CLI (Typer + Rich), Streamlit dashboard, lifecycle hooks
│   ├── domain/          # Pure domain models: Task, Artifact, Finding, Result
│   ├── execution/       # Sandbox runner, artifact validation, result parsing
│   ├── graph/           # LangGraph builder, AeonState schema, edge conditions, checkpoints
│   ├── memory/          # ChromaDB store, Neo4j store, HybridMemoryStore, retrieval layer
│   ├── models/          # Qwen client (+ mock fallback), model router, prompt templates
│   ├── observability/   # Structured logging, OpenTelemetry tracing, Prometheus metrics
│   ├── security/        # Policies, threat models, validators, adversarial test suite
│   └── utils/           # ULID IDs, hashing, retry helpers
├── docs/
│   ├── SHOWCASE.md          # Project pitch, demo script, screenshot checklist
│   ├── ENGINE_STATUS.md     # Completed phases, run/test commands, guarantees
│   ├── SYSTEM_DESIGN.md     # Architecture decisions, component interactions
│   ├── AGENT_SPEC.md        # Per-agent contracts, inputs, outputs
│   ├── STATE_MACHINE.md     # LangGraph state schema and edge rules
│   └── WHITEPAPER_SUMMARY.md  # Theoretical foundation (Recursive Perpetual Evolution)
├── tests/
│   ├── unit/            # ChromaDB, Neo4j, hybrid memory, generator, dashboard
│   └── integration/     # Full repair-loop LangGraph test
├── pyproject.toml
├── requirements.txt
└── .env.example
```

---

## Documentation

| Document | Description |
|---|---|
| [SHOWCASE.md](docs/SHOWCASE.md) | Project pitch, demo script, screenshot checklist, judge-friendly explanation |
| [ENGINE_STATUS.md](docs/ENGINE_STATUS.md) | Completed phases, run/test commands, current guarantees |
| [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) | Architecture decisions, component interactions, data flows |
| [AGENT_SPEC.md](docs/AGENT_SPEC.md) | Per-agent contracts, inputs, outputs, model assignments |
| [STATE_MACHINE.md](docs/STATE_MACHINE.md) | LangGraph `AeonState` schema and edge transition rules |
| [WHITEPAPER_SUMMARY.md](docs/WHITEPAPER_SUMMARY.md) | Theoretical foundation — Recursive Perpetual Evolution |
| [streamlit_demo.py](src/aeonlogic/app/streamlit_demo.py) | Streamlit Command Center source |

---

## Development

```powershell
# Lint
ruff check src tests

# Type-check
mypy src

# Tests (Windows .venv)
.\.venv\Scripts\python.exe -m pytest tests -v

# Tests (PYTHONPATH, no install required)
$env:PYTHONPATH = "src"; python -m pytest tests -v

# Dashboard
$env:PYTHONPATH = "src"; streamlit run src/aeonlogic/app/streamlit_demo.py
```

---

## License

MIT
