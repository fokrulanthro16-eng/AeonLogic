# AeonLogic — Demo Script

> **AeonLogic: Recursive Self-Healing Multi-Agent Engine**
> Streamlit Command Center · Qwen Cloud · ChromaDB + Neo4j Hybrid Memory

---

## 30-Second Pitch

> *"AeonLogic is a five-agent AI system that detects security vulnerabilities in its own generated code, triggers an autonomous self-healing repair loop, and writes every failure and success into a hybrid memory system — so the next run starts smarter. It runs on Qwen Cloud, works fully offline for demos, and ships with a Streamlit Command Center dashboard that shows every agent, every finding, and every memory write in real time."*

Key numbers to mention: **five agents · recursive self-healing · 412+ tests · zero external dependencies for the demo**.

---

## 2-Minute Demo Script

### Open with the dashboard (20 s)

```powershell
$env:PYTHONPATH = "src"; streamlit run src/aeonlogic/app/streamlit_demo.py
```

Navigate to [http://localhost:8501](http://localhost:8501).

> *"This is the AeonLogic Streamlit Command Center. It's a live view into the multi-agent pipeline — every agent node, every security finding, every memory write."*

Point at the mode badge: `● MOCK_MODEL_MODE`

> *"Running in mock mode right now — no API key needed. Flip `AEONLOGIC_MODE=real` and add a Qwen Cloud API key and this becomes a live cloud inference run."*

---

### Trigger the one-click security demo (10 s)

Click **⚡ RUN SECURITY DEMO** (or the **🔐 Security Auth Demo** quick-task button).

> *"Five agents just started: Dispatcher classifies the task, Generator writes the code using Qwen Cloud inference, Critic performs adversarial security review, Executor runs it, Memory Synthesizer persists the outcome."*

---

### Show the repair loop (40 s)

When the run completes, point at the **AGENT PIPELINE** timeline:

```
DISPATCH → GENERATE → CRITIC → EXECUTE → REPAIR → GENERATE → CRITIC → EXECUTE → MEMORY → FINAL
```

Walk through each lit node:

- **CRITIC** (red/amber) — *"The Critic found security vulnerabilities: missing JWT validation, plaintext password storage, no rate limiting."*
- **EXECUTE** (blocked) — *"The Executor refused to run. Critical findings block deployment."*
- **REPAIR** (amber) — *"Self-healing triggered. All findings injected back into the Generator's context."*
- Second **CRITIC** → **EXECUTE** — *"Attempt two: hardened artifact, zero findings, execution succeeded."*

> *"This is recursive self-healing. The system found its own failure, diagnosed the cause, repaired it, and verified the fix — without human intervention."*

---

### Show memory and evidence panels (20 s)

Open **🧠 MEMORY WRITES** expander:
- Red `[FAILURE-LESSON]` card — what went wrong on attempt 1
- Green `[SUCCESS-LESSON]` card — what the repair looked like

> *"These lessons are written to ChromaDB as semantic embeddings. The next run on a similar task retrieves them and the Generator starts with that context pre-loaded."*

Point at **MEMORY EVIDENCE** panel:
- `CHROMA: ACTIVE` · `HYBRID: ACTIVE` · `NEO4J: NOT CONFIGURED`
- Written: 2 · Failures: 1 · Successes: 1

Then point at **ARTIFACT PREVIEW** panel — the generated code snippet with session ID.

---

### Close with download (10 s)

Click **⬇ DOWNLOAD DEMO REPORT** — show the plain-text export.

> *"Judges get a shareable artefact with session ID, model, findings summary, memory lesson counts, and final verdict."*

---

## 5-Minute Judge Walkthrough

### Minute 1 — Architecture overview

Draw or point at the pipeline diagram:

```
Dispatcher → Generator → Critic
                  ▲           │ reject
                  └──[REPAIR]─┘
                               │ approve
                            Executor
                               │
                      Memory Synthesizer
                         /           \
                  ChromaDB         Neo4j
               (semantic)       (knowledge graph)
```

> *"Five agents, one LangGraph state machine. The repair loop is enforced by graph edge conditions — not by asking the model to try harder."*

Explain why this matters:

> *"Most AI coding tools are one-shot. AeonLogic closes the feedback loop. Every rejection becomes a repair. Every repair becomes a memory. The system learns from its own failures."*

---

### Minute 2 — Live pipeline run

Run the **Security Auth Demo** from the Streamlit Command Center.

While it runs:
- Point at the spinner: five concurrent agents streaming updates
- Explain the Qwen Cloud integration: `qwen-plus` for generation, `qwen-turbo` for criticism, DashScope `openai`-compatible endpoint
- Mention the Qwen Cloud status panel in the sidebar (mode, model, key status — masked)

---

### Minute 3 — Drill into findings and self-healing

Open **🔍 CRITIC FINDINGS** expander. Show a severity-coloured finding card:

```
[CRITICAL]  Missing JWT validation
Evidence: authenticate() returns True without verifying token signature
↳  Use PyJWT with RS256; reject on expired/invalid tokens
```

> *"The Critic produces structured `Finding` objects with severity, evidence, and recommendation. These aren't just text — they're injected as structured context into the Generator's repair prompt."*

Show the **AGENT PIPELINE** REPAIR node highlighted amber:

> *"Attempt 2 prompt includes all five findings. The Generator must address each one. Attempt 2 produces zero findings. Execution succeeds."*

---

### Minute 4 — Hybrid Memory deep dive

Open **🧠 MEMORY WRITES** expander. Explain each lesson type:

| Type | What it stores | Where it goes |
|---|---|---|
| `failure-lesson` | Task description · failure reason · artifact ID | ChromaDB embeddings + Neo4j node |
| `success-lesson` | Task description · success summary · artifact ID | ChromaDB embeddings + Neo4j node |

Point at **MEMORY EVIDENCE** panel:
- `CHROMA: ACTIVE` — ChromaDB running in embedded mode
- `HYBRID: ACTIVE` — Hybrid Memory coordinating both backends
- `NEO4J: NOT CONFIGURED` — graph store ready; safe no-op in demo

> *"Run a second similar task and the Generator's prompt will include retrieved lessons from ChromaDB. The system starts with prior knowledge. Each run improves the next."*

Show **ARTIFACT PREVIEW** panel — the generated artifact text and session ID.

---

### Minute 5 — Test coverage and production readiness

Open a terminal and run the test suite:

```powershell
$env:PYTHONPATH = "src"; python -m pytest tests/unit -v --tb=short -q
```

> *"412+ passing unit tests. All memory backends tested with mocks — no ChromaDB or Neo4j server required in CI. The dashboard pure helper functions are tested independently of the Streamlit runtime."*

Mention the integration test:

```
tests/integration/test_repair_loop.py
  ✓ attempt 1 → REJECTED (5 findings) → BLOCKED
  ✓ attempt 2 → APPROVED (0 findings) → SUCCESS
```

> *"The repair loop is deterministically tested: attempt 1 always fails with specific findings, attempt 2 always succeeds. This is architecture-level correctness, not probabilistic."*

Close with the download report as a tangible artefact.

---

## Screenshot Checklist

Capture these screens before presenting. Use **Presentation Mode** (sidebar toggle) for clean versions.

- [ ] **Dashboard idle** — hero, mode badge `● MOCK_MODEL_MODE`, quick-task buttons visible
- [ ] **Pipeline running** — spinner active, `⟳ Recursive pipeline executing…`
- [ ] **Agent timeline — full** — all 7 nodes lit, REPAIR highlighted amber
- [ ] **Critic Findings open** — at least one severity-coloured finding card
- [ ] **Memory Writes open** — red `[FAILURE-LESSON]` + green `[SUCCESS-LESSON]` cards
- [ ] **Memory Evidence panel** — `CHROMA: ACTIVE` · lesson counts visible
- [ ] **Artifact Preview panel** — generated code snippet + session ID visible
- [ ] **Final verdict — SUCCESS** — full-width green `✅ SUCCESS` card
- [ ] **Presentation mode** — clean verdict-only view (good for title slides)
- [ ] **Qwen Cloud sidebar** — runtime mode, model, API key status (masked)
- [ ] **Downloaded report** — plain-text `.txt` with session ID and verdict

---

## Q&A Preparation

### What problem does AeonLogic solve?

LLMs generate insecure code. AeonLogic detects vulnerabilities autonomously, repairs them in a recursive self-healing loop, and retains the knowledge of both failure and repair in a Hybrid Memory system — so the same mistake is never made twice on a similar task.

### Does it work without Qwen Cloud?

Yes. `MOCK_MODEL_MODE` uses a deterministic in-process mock that replicates the full repair loop behaviour without any API calls. Full demo from a laptop with no internet connection.

### How is the self-healing different from just "retry with better prompt"?

The repair is **architecture-enforced by LangGraph edge conditions**, not prompt-engineering. The `after_critique` edge function routes back to `generate` with the structured `Finding` objects in graph state when the Critic rejects. The model cannot choose to skip repair. The generation attempt counter enforces a hard cap.

### What is the Hybrid Memory system?

Two backends coordinated by `HybridMemoryStore`:
- **ChromaDB** (authoritative): semantic embeddings of lesson content, retrieved by cosine similarity for the next run's Generator context
- **Neo4j** (best-effort): structured knowledge graph of `Task → Artifact → Lesson` relationships

ChromaDB is always authoritative. Neo4j failures are silently swallowed — the pipeline always completes.

### How many tests? Are they real?

412+ unit tests + integration tests. All memory backends are tested with injected mocks — no ChromaDB server, Neo4j server, or Qwen Cloud API key needed in CI. The Streamlit dashboard's pure helper functions are tested independently of the Streamlit runtime.

### What's next for AeonLogic?

Real-time streaming to the dashboard, multi-task parallel batching, memory retrieval visualisation (show which past lessons influenced the current generation), Neo4j graph explorer panel, and Qwen Cloud model selection from the sidebar.
