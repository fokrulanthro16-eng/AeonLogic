# AeonLogic — Devpost Submission

## Project Title
**AeonLogic: Recursive Self-Healing Multi-Agent Engine**

## Tagline
*An AI system that detects its own security failures, repairs them autonomously, and remembers every outcome — powered by Qwen Cloud.*

---

## The Problem

Large language models generate code that looks correct but contains security vulnerabilities: unsanitised inputs, hardcoded secrets, missing rate limiting, weak authentication. Existing AI coding tools either produce the output and stop, or ask the developer to manually review and retry. There is no closed feedback loop.

The result: developers who trust AI-generated code without adversarial review ship insecure software. The problem compounds — without memory, the same model makes the same mistakes on every new run.

---

## Our Solution

AeonLogic is a five-agent AI system built around one core insight: **failure is as valuable as success**.

The pipeline runs as a stateful LangGraph graph:

1. **Dispatcher** — classifies the task, selects the model tier
2. **Generator** — produces a candidate artifact using Qwen Cloud (or mock fallback)
3. **Critic / Adversarial Auditor** — stress-tests the artifact, raises structured `Finding` objects
4. **Executor** — runs the artifact; blocks on critical findings
5. **Memory Synthesizer** — writes failure and success lessons to hybrid memory

When the Critic rejects an artifact, the system does not stop. It triggers a **recursive self-healing repair loop**: findings are injected back into the Generator's prompt and the cycle retries. Every outcome — rejection, repair, success — is compressed into a persistent **Hybrid Memory** system (ChromaDB semantic store + Neo4j knowledge graph) so future runs start with context.

This is the loop that closes the security feedback gap.

---

## How AeonLogic Uses Qwen Cloud (Alibaba Cloud)

Qwen Cloud is part of the **Alibaba Cloud** ecosystem, delivered via the DashScope API. AeonLogic uses it as the inference backbone for all five agents in three modes:

| Mode | Environment | Behaviour |
|---|---|---|
| `REAL_MODEL_MODE` | `AEONLOGIC_MODE=real` + `QWEN_API_KEY` set | Full Qwen Cloud inference via DashScope |
| `FALLBACK_MODE` | API key set but call fails | Automatic fallback to deterministic mock |
| `MOCK_MODEL_MODE` | No API key (default) | Fully offline deterministic demo |

**In real mode**, the Generator sends structured prompts to `qwen-plus` (or configurable model) via `openai`-compatible DashScope endpoints. The Critic uses the same model to evaluate artifacts with an adversarial system prompt. The Memory Synthesizer uses `qwen-turbo` for fast lesson compression.

**Why Qwen Cloud specifically:**
- DashScope's `openai`-compatible API makes integration clean
- `qwen-plus` handles long structured prompts (code + security context) reliably
- `qwen-turbo` gives fast turnaround for the Critic's structured `Finding` JSON extraction
- The fallback chain means demos never break on transient API errors

The **Qwen Cloud status panel** (Streamlit sidebar) shows runtime mode, configured model, base URL, and API key presence (masked) — the key is never displayed anywhere in the UI or logs.

---

## What Makes It Innovative

### 1 — The repair loop is deterministic, not prompt-based

Self-healing is not implemented by asking the model to "try again." The repair cycle is enforced by LangGraph **edge conditions**: `after_critique` explicitly routes back to `generate` with findings in state when the Critic rejects. The model doesn't decide to repair — the graph structure forces it. This is testable, reproducible, and architecture-first.

### 2 — Memory that compounds over runs

AeonLogic writes structured **Hybrid Memory** after every pipeline execution:
- **ChromaDB** (authoritative): semantic embedding of failure/success lessons, retrieved by similarity for the next run's Generator prompt
- **Neo4j** (best-effort): structured knowledge graph of task → artifact → lesson relationships

Memory retrieval enriches the Generator's context only when relevant lessons exist. First run: same as any LLM. Tenth run on similar tasks: starts with a pre-loaded security checklist derived from past failures and repairs.

### 3 — The Streamlit Command Center

The dashboard is a pure consumer of the same pipeline the CLI runs — no engine logic lives in the UI. It exposes:
- **Agent timeline** — animated pipeline with repair-cycle highlighting
- **Critic Findings panel** — severity-coloured finding cards
- **Memory Writes expander** — failure (red) and success (green) lesson cards
- **Artifact Preview panel** — generated artifact text with session ID
- **Memory Evidence panel** — ChromaDB / Hybrid Memory / Neo4j status + lesson counts
- **Presentation mode** — one toggle to hide telemetry for clean screenshots
- **Downloadable report** — plain-text export for sharing

### 4 — Zero external dependencies for the demo

Qwen mock mode, ChromaDB embedded mode, and Neo4j silent no-op means a complete hackathon demo runs offline, on any laptop, with no API keys or servers required.

---

## Links

| Resource | URL |
|---|---|
| **Live Demo** | *(deploy to Streamlit Community Cloud or Alibaba Cloud ECS — URL TBD)* |
| **Demo Video** | *(Loom / YouTube recording showing real Qwen Cloud run — URL TBD)* |
| **GitHub Repo** | *(public repo URL)* |
| **Architecture Diagram** | [docs/ARCHITECTURE.md](ARCHITECTURE.md) — Mermaid diagram with full component breakdown |
| **Cloud Proof** | [docs/ALIBABA_CLOUD_PROOF.md](ALIBABA_CLOUD_PROOF.md) — Qwen Cloud / Alibaba Cloud integration proof |

---

## Technical Architecture

See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for the full Mermaid architecture diagram, component reference, and Qwen Cloud / Alibaba Cloud deployment guide.

**Key code paths:**
- Qwen Cloud client: `src/aeonlogic/models/qwen_client.py` — `QwenClient.complete()` posts to DashScope
- Dashboard: `src/aeonlogic/app/streamlit_demo.py` — `build_qwen_cloud_status()` shows live Alibaba Cloud status
- Env template: `.env.example` — `QWEN_API_KEY=` empty; no API key is committed to VCS

```
User / CLI / Streamlit Command Center
              │
              ▼
    ┌─────────────────────────────────┐
    │         LangGraph Graph          │
    │                                 │
    │  Dispatcher → Generator → Critic │
    │                  ▲   └──[REPAIR]─┘ reject
    │                  │       approve
    │               Executor           │
    │                  │               │
    │          Memory Synthesizer       │
    └─────────────────────────────────┘
              │                │
              ▼                ▼
       Neo4j Graph        ChromaDB Vector
       (knowledge)        (episodic memory)
```

**Stack:**
- **Orchestration**: LangGraph (stateful graph, checkpointing, streaming)
- **Inference**: Qwen Cloud via DashScope / `openai`-compatible SDK
- **Semantic memory**: ChromaDB (persistent embedded, or in-process mock)
- **Knowledge graph**: Neo4j (optional; full silent no-op fallback)
- **Dashboard**: Streamlit with custom dark CSS theme
- **CLI**: Typer + Rich
- **Domain models**: Pydantic v2
- **IDs**: ULID (monotonic, sortable, URL-safe)
- **Tests**: pytest, 412+ passing, zero external services required

---

## Challenges We Ran Into

**1 — Making the repair loop deterministic**
Getting LangGraph to route correctly on rejection required careful edge condition design. The `after_critique` edge reads `critic_verdict` from state — if `REJECTED`, route back to `generate`; if `APPROVED`, proceed to `execute`. A generation attempt counter prevents infinite loops.

**2 — Hybrid memory without crashes**
ChromaDB and Neo4j have different failure modes. ChromaDB failing mid-write corrupts nothing (each write is transactional). Neo4j being unavailable should not fail the pipeline. The solution: independent try/except blocks, with ChromaDB authoritative and Neo4j best-effort. The `HybridMemoryStore` exposes `backend` and `neo4j_available` introspection properties for the Memory Evidence panel.

**3 — Keeping the dashboard pure**
The Streamlit dashboard started accumulating engine logic in event handlers. We refactored all display logic into pure helper functions (`_build_summary`, `build_artifact_preview_html`, `build_memory_evidence_html`, etc.) that are importable and testable without a Streamlit runtime. This means every dashboard panel is covered by unit tests.

**4 — Qwen Cloud fallback transparency**
When a real Qwen Cloud call fails, the system must fall back gracefully but also tell the user. `get_client_mode_label()` reads the actual post-run mode (which may differ from the configured mode if a live call failed) and the dashboard reflects this in the mode badge and Qwen Cloud status panel.

---

## Accomplishments We're Proud Of

- A fully working recursive self-healing loop that is **architecture-enforced**, not prompt-engineered
- **412+ passing tests** with zero external service requirements in CI
- A Streamlit Command Center that is a **pure consumer** of the engine — tested independently from the UI runtime
- **Hybrid Memory** that gracefully degrades from ChromaDB → in-process mock → no-op Neo4j without ever crashing the pipeline
- The **Artifact Preview panel** and **Memory Evidence panel** (Phases 6C and 6D) give judges a live view of what the system generated and how memory performed
- Complete offline demo: Qwen mock mode + ChromaDB embedded + Neo4j no-op = zero dependencies for a live walkthrough

---

## What We Learned

- LangGraph's state machine model forces explicit reasoning about all transition paths, which surfaces edge cases early
- ChromaDB's embedded mode is genuinely production-ready for single-process use
- Separating pure UI helper functions from the Streamlit rendering path makes dashboard testing straightforward
- The Qwen Cloud DashScope API's `openai`-compatible interface made switching between mock and real modes a one-line change

---

## What's Next

- **Real-time streaming**: pipe LangGraph `stream_mode="updates"` events live to the dashboard via WebSockets instead of waiting for the full run
- **Multi-task batching**: run multiple Dispatcher tasks in parallel with a fan-out graph pattern
- **Memory retrieval visualisation**: show the specific past lessons the Generator used in its context, and how similar they were (cosine distance from ChromaDB)
- **Neo4j graph explorer**: embed a read-only Cypher query panel in the dashboard to browse the knowledge graph live
- **Qwen Cloud model selection UI**: let judges switch between `qwen-turbo`, `qwen-plus`, `qwen-max` from the sidebar without restarting
- **Export to CI**: generate a machine-readable security report (JSON/SARIF) the pipeline can commit back as a PR artefact
