# ⚡ AeonLogic

## Recursive Self-Healing Multi-Agent Engine
### CLI + Streamlit Command Center

> A LangGraph-orchestrated, five-agent AI system that detects security failures, triggers an autonomous recursive repair loop, and synthesises every outcome into a persistent hybrid memory (ChromaDB + Neo4j) — so every future run is informed by the past.

**No API key required for demos. No Neo4j server required for tests. Runs fully offline in mock mode.**

> **Hackathon submission** — see [docs/DEVPOST_SUBMISSION.md](docs/DEVPOST_SUBMISSION.md) for the full write-up, [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the live demo script, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the Mermaid architecture diagram, and [docs/ALIBABA_CLOUD_PROOF.md](docs/ALIBABA_CLOUD_PROOF.md) for Alibaba Cloud / Qwen Cloud integration proof.

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
| 🧩 | **Memory Evidence panel** | ChromaDB / Hybrid / Neo4j status · lesson counts (written, failure, success) · retrieved lesson count; never crashes on missing backend |

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

## Qwen Cloud / Alibaba Cloud Integration

AeonLogic uses Qwen Cloud (part of **Alibaba Cloud**, delivered via the DashScope API) as its inference backbone in three modes:

| Mode | How to activate | Behaviour |
|---|---|---|
| `REAL_MODEL_MODE` | `AEONLOGIC_MODE=real` + `QWEN_API_KEY` | Full Qwen Cloud inference |
| `FALLBACK_MODE` | API key set, live call fails | Auto-fallback to deterministic mock |
| `MOCK_MODEL_MODE` | No key (default) | Fully offline — complete demo without API costs |

The **Qwen Cloud status panel** in the Streamlit sidebar shows runtime mode, configured model, base URL, and a masked `QWEN_API_KEY` indicator. The raw key is never logged or displayed anywhere. **No API key is committed to VCS** — only `.env.example` (with empty key) is tracked.

> Mock-mode demo: run with no API key and the full self-healing loop still executes using `MockQwenClient` — no internet connection required.

To enable real mode, create a `.env` file (never commit this file):

```env
AEONLOGIC_MODE=real
QWEN_API_KEY=sk-...
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

---

## Dashboard Features

The Streamlit Command Center (`src/aeonlogic/app/streamlit_demo.py`) exposes the full pipeline through themed panels:

| Panel | What it shows |
|---|---|
| **Agent timeline** | Animated pipeline — DISPATCH → GENERATE → CRITIC → EXECUTE → REPAIR → MEMORY → FINAL |
| **Qwen Cloud status** | Runtime mode · model · base URL · API key presence (masked) |
| **Run telemetry** | Runtime mode · model · risk level · attempt count |
| **Critic Findings** | Severity-coloured finding cards with evidence and recommendation |
| **Memory Writes** | Failure (red) and success (green) lesson cards with content snippets |
| **Memory Evidence** | ChromaDB / Hybrid Memory / Neo4j status · written / failure / success / retrieved counts |
| **Artifact Preview** | Generated artifact text (truncated to 800 chars) + session ID |
| **Final Verdict** | Full-width `✅ SUCCESS` or `✗ FAILED` card |
| **Download Report** | Plain-text export with session ID, model, findings, lessons, verdict |
| **Presentation mode** | One toggle hides telemetry — clean screenshots for slides |

---

## Project Status

| Milestone | Status |
|---|---|
| Phase 1 — Core domain models | ✅ Complete |
| Phase 2 — LangGraph pipeline | ✅ Complete |
| Phase 3 — ChromaDB + Neo4j Hybrid Memory | ✅ Complete |
| Phase 4 — CLI (Typer + Rich) | ✅ Complete |
| Phase 5 — Streamlit Command Center | ✅ Complete |
| Phase 6A — Real Qwen Cloud mode | ✅ Complete |
| Phase 6B — Qwen Cloud proof UI | ✅ Complete |
| Phase 6C — Artifact Preview panel | ✅ Complete |
| Phase 6D — Memory Evidence panel | ✅ Complete |
| Phase 6E — Devpost Submission Pack | ✅ Complete |

**Test suite:** 412+ unit tests passing · zero external services required in CI.

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

> **Expected:** 412+ tests pass. One pre-existing `structlog` import failure is unrelated to engine logic and does not affect the demo.

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

> **Public demo / reproducible judging:** the default `.env` sets `AEONLOGIC_MODE=mock` so the dashboard runs in `MOCK_MODEL_MODE` with no API key — fully deterministic and reproducible.
> Real Qwen Cloud mode is supported through secure environment variables (`QWEN_API_KEY`); API keys must never be committed to GitHub.
> Qwen client code path: `src/aeonlogic/models/qwen_client.py` · Proof docs: [docs/ALIBABA_CLOUD_PROOF.md](docs/ALIBABA_CLOUD_PROOF.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

**Streamlit deploy entry point:** `src/aeonlogic/app/streamlit_demo.py`

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
│   ├── DEVPOST_SUBMISSION.md    # Hackathon submission write-up
│   ├── DEMO_SCRIPT.md           # 30s / 2min / 5min demo scripts + Q&A
│   ├── ARCHITECTURE.md          # Mermaid diagram + Qwen Cloud / Alibaba Cloud component reference
│   ├── ALIBABA_CLOUD_PROOF.md   # Integration proof, env vars, deployment checklist
│   ├── SHOWCASE.md              # Project pitch, screenshot checklist, feature matrix
│   ├── ENGINE_STATUS.md         # Completed phases, run/test commands, guarantees
│   ├── SYSTEM_DESIGN.md         # Architecture decisions, component interactions
│   ├── AGENT_SPEC.md            # Per-agent contracts, inputs, outputs
│   ├── STATE_MACHINE.md         # LangGraph state schema and edge rules
│   └── WHITEPAPER_SUMMARY.md    # Theoretical foundation (Recursive Perpetual Evolution)
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
| [DEVPOST_SUBMISSION.md](docs/DEVPOST_SUBMISSION.md) | **Hackathon submission** — problem, solution, Qwen Cloud usage, architecture, what's next |
| [DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | **Live demo scripts** — 30-second pitch, 2-minute demo, 5-minute judge walkthrough, Q&A |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | **Mermaid architecture diagram** — Streamlit Command Center, engine, Qwen Cloud client, memory |
| [ALIBABA_CLOUD_PROOF.md](docs/ALIBABA_CLOUD_PROOF.md) | **Alibaba Cloud / Qwen Cloud proof** — integration evidence, env vars, deployment checklist |
| [SHOWCASE.md](docs/SHOWCASE.md) | Project pitch, screenshot checklist, judge-friendly explanation, feature matrix |
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
