# AeonLogic — Showcase

> **Recursive Self-Healing Multi-Agent Engine**
> CLI + Streamlit Command Center · ChromaDB + Neo4j Hybrid Memory · No API key required for demo

---

## Project Pitch (30 seconds)

AeonLogic is a multi-agent AI system built around one insight: **failure is as valuable as success**.

When the Critic agent detects security vulnerabilities in a generated artifact, the system doesn't stop — it triggers an autonomous repair loop, injects the findings back into the Generator, and retries until the artifact passes. Every outcome — failure and success — is compressed into a hybrid memory system (ChromaDB for semantic similarity, Neo4j for structured knowledge graphs) so future runs start smarter.

The full pipeline runs without any external API, database, or cloud service: Qwen mock fallback replaces the real LLM, and ChromaDB/Neo4j have safe in-process fallbacks. **You can run a complete hackathon demo from a laptop with no internet connection.**

---

## Demo Script (5 minutes)

### Step 1 — Launch the dashboard (30 s)

```powershell
$env:PYTHONPATH = "src"; streamlit run src/aeonlogic/app/streamlit_demo.py
```

Open [http://localhost:8501](http://localhost:8501). The Command Center loads with the dark futuristic theme.

**Talking point:** *"This is the AeonLogic Command Center. Every agent node in the pipeline streams its output here in real time."*

---

### Step 2 — One-click Security Auth Demo (20 s)

Click **⚡ RUN SECURITY DEMO** (or the **🔐 Security Auth Demo** quick-task button).

The pipeline spins up. Point at the spinner:
> *"Five agents just started collaborating — Dispatcher, Generator, Critic, Executor, Memory Synthesizer."*

---

### Step 3 — Show the self-healing repair (90 s)

When the run completes, point at the **AGENT PIPELINE** timeline:

```
DISPATCH → GENERATE → CRITIC → EXECUTE → REPAIR → GENERATE → CRITIC → EXECUTE → MEMORY → FINAL
```

Key moments to explain:
- **CRITIC** lights up in red — *"The Critic found 5 security vulnerabilities: no JWT validation, plaintext passwords, missing rate limiting…"*
- **EXECUTE** shows BLOCKED — *"The Executor refused to run the artifact. Critical findings prevent deployment."*
- **REPAIR** fires — *"The system automatically triggered a repair cycle. All 5 findings were injected back into the Generator's prompt."*
- Second **GENERATE** → **CRITIC** → **EXECUTE** — *"Attempt 2: the Generator produced a hardened artifact. Zero findings. Execution succeeded."*

**Talking point:** *"This is recursive self-healing. The system detected its own failure, diagnosed the cause, repaired it, and verified the fix — entirely autonomously."*

---

### Step 4 — Hybrid memory writes (60 s)

Open the **🧠 MEMORY WRITES** expander. Show:
- `[FAILURE-LESSON]` — what went wrong on attempt 1
- `[SUCCESS-LESSON]` — what the successful repair looked like

**Talking point:** *"These lessons are written to ChromaDB as semantic embeddings and attempted on Neo4j as a knowledge graph. The next run on a similar task will retrieve these lessons and start with that context pre-loaded into the Generator prompt."*

Open the **MEMORY BACKENDS** panel:
- `● CHROMADB  ACTIVE` — semantic memory running
- `○ NEO4J  NOT CONFIGURED` — graph store ready to connect; safe no-op in demo mode
- `● LLM  MOCK_MODEL_MODE` — full demo without API costs

---

### Step 5 — Download the report (30 s)

Click **⬇ DOWNLOAD DEMO REPORT**. Show the downloaded `.txt` file:

```
╔══════════════════════════════════════════════════╗
║   AEONLOGIC COMMAND CENTER  —  Demo Run Report   ║
╚══════════════════════════════════════════════════╝
  Session      : 01JXXXXXXXXXXXXXXXXXXXXXXXXX
  Runtime mode : MOCK_MODEL_MODE
  Model        : qwen-turbo
  Risk level   : HIGH
──────────────────────────────────────────────────
  Attempts     : 2
  Repaired     : YES — recursive self-healing triggered
  Findings     : 5 security issues detected
  Exec blocked : YES
──────────────────────────────────────────────────
  Lessons      : 2 written to hybrid memory
    failure    : 1
    success    : 1
──────────────────────────────────────────────────
  Final status : ✅  SUCCESS
```

---

### Step 6 — Presentation mode (30 s)

Open the sidebar (☰) and toggle **Presentation Mode**. The telemetry rows, backend panel, and export block disappear — leaving just:
- Agent timeline
- Critic findings
- Memory writes
- Final verdict card

**Talking point:** *"Clean screenshots for slides or judging sheets — one toggle."*

---

## Screenshot Checklist

Before presenting, capture these screens:

- [ ] **Dashboard idle** — hero, mode badge, quick-task buttons visible
- [ ] **Pipeline running** — spinner active
- [ ] **Agent timeline** — all 7 nodes lit after a successful run (REPAIR highlighted amber)
- [ ] **Critic findings expander open** — severity-colored finding cards visible
- [ ] **Memory writes expander open** — failure-lesson (red) + success-lesson (green) cards
- [ ] **Final verdict — SUCCESS** — green `✅ SUCCESS` card full-width
- [ ] **Presentation mode** — clean verdict-only view (good for title slides)
- [ ] **Downloaded report** — terminal showing the `.txt` content

---

## Judge-Friendly Explanation

| Question | Answer |
|---|---|
| **What problem does it solve?** | LLMs generate insecure code. AeonLogic detects vulnerabilities, repairs them automatically, and remembers what worked — closing the security feedback loop. |
| **What's novel?** | The combination of adversarial critique, recursive repair, and structured long-term memory (not just RAG) in a single stateful pipeline. |
| **Does it work without cloud services?** | Yes. Qwen mock fallback replaces the real LLM. ChromaDB runs embedded. Neo4j is optional (safe no-op). Full demo from a laptop. |
| **What's the memory system?** | Hybrid: ChromaDB (semantic similarity search over past task outcomes) + Neo4j (structured knowledge graph of task–artifact–lesson relationships). |
| **What technology powers it?** | LangGraph for the state machine, Streamlit for the dashboard, ChromaDB for vector memory, Neo4j for graph memory, Qwen/DashScope for inference. |
| **How many tests?** | 267+ passing. Deterministic repair loop covered by integration test. All memory stores tested with mocks — no external services required in CI. |

---

## Technical Highlights

### Self-healing is deterministic, not stochastic

The repair loop is enforced by LangGraph edge conditions — not by prompting the model to "try harder". The `after_critique` edge function explicitly routes back to `generate` with findings in state when the Critic rejects. This is tested in `tests/integration/test_repair_loop.py`:

```
Attempt 1: generate → critique (REJECTED, 5 findings) → execute (BLOCKED)
Attempt 2: generate → critique (APPROVED, 0 findings) → execute (SUCCESS)
```

### Hybrid memory never crashes the pipeline

`HybridMemoryStore` wraps both backends in independent try/except blocks. If ChromaDB raises, the fallback is an in-process dict. If Neo4j raises, the write is silently swallowed. The pipeline always completes — memory is best-effort, not a hard dependency.

### Memory context enriches generation

`summarize_lessons()` converts retrieved `Lesson` objects into a compact hint prepended to the Generator's prompt — only when lessons exist. When the list is empty, the prompt is byte-for-byte identical to a run without memory. Zero behavioral change on first run; incremental improvement thereafter.

### The Streamlit dashboard is a pure consumer

`streamlit_demo.py` calls `build_graph()` and `graph.stream()` — the exact same path as the CLI. No engine logic lives in the dashboard. Pure functions (`_build_summary`, `_build_timeline_stages`, `build_demo_summary_text`) are tested independently without a Streamlit runtime.

---

## Feature Matrix

| Feature | Implementation | Test coverage |
|---|---|---|
| Multi-agent pipeline | `graph/builder.py` + 5 agents | `test_repair_loop.py` |
| Recursive self-healing | `graph/edges.py` `after_critique` | `test_repair_loop.py` |
| Qwen mock fallback | `models/qwen_client.py` | All unit + integration tests |
| ChromaDB memory | `memory/chroma_store.py` | `test_chroma_memory.py` |
| Memory retrieval | `memory/retrieval.py` | `test_memory_retrieval.py` |
| Memory-aware generation | `agents/generator.py` | `test_generator_memory_context.py` |
| Neo4j graph store | `memory/neo4j_store.py` | `test_neo4j_store.py` |
| Hybrid orchestration | `memory/hybrid_store.py` | `test_hybrid_memory.py` |
| Streamlit dashboard | `app/streamlit_demo.py` | `test_streamlit_demo_import.py` |
| Demo report export | `build_demo_summary_text()` | `test_streamlit_demo_import.py` |
