# AeonLogic — Whitepaper Summary: Recursive Perpetual Evolution

## Abstract

Recursive Perpetual Evolution (RPE) is the theoretical foundation of AeonLogic. It posits that an AI system approaches increasingly capable behaviour not through a single monolithic model, but through a structured cycle of **generation**, **adversarial critique**, **execution**, and **memory synthesis** — repeated recursively across tasks and sessions. Each cycle both solves a problem and strengthens the system's capacity to solve the next one.

---

## 1. The core principle

> *Intelligence is not a state — it is a process. A system that cannot learn from its own outputs is bounded; a system that synthesises experience recursively is unbounded.*

Classical LLM deployments are stateless: the same model responds to similar prompts in roughly the same way regardless of past interactions. RPE rejects this model. In an RPE system:

1. **Every cycle produces knowledge**, not just output.
2. **Knowledge is queryable** — it feeds back into future cycles as structured context.
3. **Failure is first-class data** — rejected artefacts and failed executions are as valuable as successes.

---

## 2. The five-phase cycle

```
┌─────────────────────────────────────────────────────────────┐
│                 Recursive Perpetual Evolution                │
│                                                             │
│  ┌───────────┐                                              │
│  │  Dispatch │  ← Decompose goal; classify risk             │
│  └─────┬─────┘                                              │
│        ▼                                                     │
│  ┌───────────┐                                              │
│  │  Generate │  ← Synthesise candidate artefact             │
│  └─────┬─────┘                                              │
│        ▼                                                     │
│  ┌───────────┐                                              │
│  │  Critique │  ← Adversarial audit; find failure modes     │
│  └─────┬─────┘                                              │
│        ▼                                                     │
│  ┌───────────┐                                              │
│  │  Execute  │  ← Ground truth from the real environment    │
│  └─────┬─────┘                                              │
│        ▼                                                     │
│  ┌───────────┐                                              │
│  │ Synthesise│  ← Compress experience into long-term memory │
│  └─────┬─────┘                                              │
│        │                                                     │
│        └─────────────────────► next cycle                   │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1 — Dispatch
Goal decomposition mirrors human expert planning: large goals are broken into independently solvable sub-tasks. Risk classification ensures computational resources are allocated proportionally (fast tier for routine work; strong tier for high-stakes decisions).

### Phase 2 — Generate
The Generator is not given a blank slate. It receives the compressed result of all prior relevant cycles via the hybrid memory retrieval path. This turns generation into *informed* synthesis rather than pure prior-sampling.

### Phase 3 — Critique
The Critic is deliberately adversarial. Its purpose is not to find solutions but to find the ways a solution fails. This separation of concerns (generator vs. auditor) is inspired by adversarial machine learning and red-team security methodology. A system that only generates is optimistic; one that also critiques becomes robust.

### Phase 4 — Execute
Execution provides a ground-truth signal that no language model can replicate internally: does the artefact actually work in the environment? Execution results — including failures, timeouts, and exceptions — are treated as primary evidence, not secondary metadata.

### Phase 5 — Synthesise
The Memory Synthesizer is the engine of RPE. It extracts structured facts (written to Neo4j as typed nodes and relationships) and episodic summaries (embedded into ChromaDB for semantic recall). The key insight is that synthesis happens *before* the cycle terminates — memory is enriched while the context is hot, not deferred to a separate offline process.

---

## 3. Why recursion?

A single pass through the five phases solves one task. Recursion is what produces evolution:

- The memory written at cycle *n* is retrieved at cycle *n+1*.
- The Critic's findings at cycle *n* become training signal for the Generator's prompts at cycle *n+1*.
- Patterns across many cycles (e.g., "tasks of type X always fail approach Y") emerge as Neo4j relationship patterns and can be surfaced as structured warnings.

Over time, the system accumulates a domain-specific knowledge graph that encodes *what works*, *what fails*, and *under what conditions* — a form of experiential intelligence that neither a static model nor a simple RAG system can provide.

---

## 4. Design invariants

| Invariant | Rationale |
|---|---|
| Failure must be written to memory | A system that only remembers success learns half the truth |
| Critique must be model-independent | The Critic must not share weights or prompts with the Generator |
| Memory writes are synchronous | No background jobs; every cycle completes its synthesis before termination |
| Recursion depth is bounded | Safety cap prevents infinite loops while preserving the recursive learning dynamic |
| All state transitions are auditable | Full deterministic replay must be possible from checkpoints |

---

## 5. Relationship to adjacent paradigms

| Paradigm | Similarity | Key difference |
|---|---|---|
| ReAct (Reason + Act) | Interleaved reasoning and action | RPE adds a dedicated adversarial critique phase and long-term memory |
| Self-RAG | Self-reflection on retrieval quality | RPE externalises critique to a separate agent; adds execution grounding |
| Constitutional AI | Rule-based self-correction | RPE's Critic is dynamic and extensible; not limited to constitutional rules |
| AlphaZero self-play | Generator vs. Critic mirrors self-play | RPE operates on open-ended language tasks, not bounded game trees |
| Reflexion | Stores verbal reflection in memory | RPE stores structured graph knowledge, not free-form reflection strings |

---

## 6. Long-term trajectory

The ultimate aim of Recursive Perpetual Evolution is a system that improves its performance on a class of tasks through lived experience — not fine-tuning, not prompt engineering by humans, but by accumulating a rich, queryable record of what it has attempted, what succeeded, why things failed, and what patterns generalise.

Each session is a small step. The graph that emerges over thousands of sessions is the evolution.

---

## 7. Phase 4 implementation note

As of Phase 4F, the memory substrate described in sections 2–5 is fully implemented:

- **ChromaDB** (`memory/chroma_store.py`) provides the episodic embedding store. Lessons are written and retrieved via semantic similarity search.
- **Neo4j** (`memory/neo4j_store.py`) provides the structured knowledge graph. Failure and success lessons are persisted as typed nodes; artifact-task-lesson relationships are stored as edges.
- **Hybrid memory orchestration** (`memory/hybrid_store.py`) coordinates both stores: Chroma is authoritative (falls back to an in-memory mock if unavailable); Neo4j is best-effort (failures are silently swallowed so the pipeline is never interrupted).
- **Recursive self-healing** is enforced by the repair loop: the Critic's findings are injected back into the Generator prompt on retry, and past lessons retrieved from ChromaDB are prepended as a compact memory hint (Phase 4C).
- **Qwen mock fallback** (`models/qwen_client.py`) ensures the entire engine runs deterministically in CI without any external API dependency.
