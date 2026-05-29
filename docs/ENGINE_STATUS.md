# AeonLogic — Engine Status

**Last updated:** 2026-05-29
**Current phase:** 4F — Final engine hardening and documentation

---

## Completed phases

| Phase | Description | Status |
|---|---|---|
| 1 | Core MVP: LangGraph graph, five agents, domain models | Done |
| 2 | Recursive self-healing loop: critic-rejection → generator-retry with deterministic repair | Done |
| 3 | Qwen client foundation with Qwen mock fallback for offline testing | Done |
| 4A | ChromaDB persistent memory store: `write_lesson`, `search_lessons`, `clear` | Done |
| 4B | Memory retrieval layer: `MemoryRetriever`, safe empty / backend-failure fallback | Done |
| 4C | Memory-aware generator context: lesson hint prepended to prompt when lessons exist | Done |
| 4D | Neo4j knowledge graph interface: `write_failure_lesson`, `write_success_lesson`, `write_artifact_relationship`, `health_check` | Done |
| 4E | Hybrid memory orchestration: Chroma authoritative + Neo4j best-effort, full fallback chain | Done |
| 4F | Final engine hardening and documentation | Done |

---

## Run command (Windows)

```
.\.venv\Scripts\aeonlogic.exe "Build a secure API authentication module"
```

## Test command (Windows)

```
.\.venv\Scripts\python.exe -m pytest tests -v
```

Or with `PYTHONPATH` set explicitly if running without the installed package:

```
$env:PYTHONPATH = "src"; python -m pytest tests -v
```

---

## Current engine guarantees

| Guarantee | Detail |
|---|---|
| Deterministic repair loop | Attempt 1 intentionally fails, attempt 2 repairs — enforced by integration tests |
| Recursive self-healing | Critic rejections feed findings back into the Generator for guided repair |
| Qwen mock fallback | All tests run without a real DashScope API key; mock client is auto-selected |
| ChromaDB persistent store | `ChromaMemoryStore` backed by the official `chromadb` package; `EphemeralClient` used in tests |
| Hybrid memory orchestration | `HybridMemoryStore` coordinates ChromaDB (authoritative) + Neo4j (best-effort) with full fallback chain |
| Neo4j mock-only tests | No real Neo4j server required; driver is injected for all unit tests |
| Safe memory fallback | ChromaDB unavailable → `MockMemoryStore`; Neo4j unavailable → silent no-op |
| No exception propagation | Every memory write is wrapped; backend failures never interrupt the pipeline |

---

## Memory fallback chain

```
write_failure_lesson / write_success_lesson
    │
    ▼
HybridMemoryStore
    │
    ├──► ChromaMemoryStore (semantic, authoritative)
    │         └── fallback: MockMemoryStore (in-process dict)
    │
    └──► Neo4jMemoryStore (graph, best-effort)
              └── fallback: silent no-op (never raises)
```

---

## Test suite summary

```
tests/
├── unit/
│   ├── test_chroma_memory.py         # ChromaDB store (4A)
│   ├── test_memory_retrieval.py      # MemoryRetriever (4B)
│   ├── test_generator_memory_context.py  # Generator + memory hint (4C)
│   ├── test_neo4j_store.py           # Neo4j store, mock driver only (4D)
│   ├── test_hybrid_memory.py         # Hybrid orchestration (4E)
│   └── test_engine_status_docs.py    # Engine status documentation (4F)
└── integration/
    └── test_repair_loop.py           # Full LangGraph repair loop, deterministic
```

---

## Key module map

| Module | Purpose |
|---|---|
| `memory/chroma_store.py` | ChromaDB semantic memory store |
| `memory/neo4j_store.py` | Neo4j knowledge graph store (lazy import, mock-injectable) |
| `memory/hybrid_store.py` | Orchestrates Chroma + Neo4j with full fallback chain |
| `memory/retrieval.py` | `MemoryRetriever` + `summarize_lessons` for prompt injection |
| `memory/schemas.py` | `Lesson`, `FailureLesson`, `SuccessLesson`, `ArtifactRelationship` |
| `agents/generator.py` | Reads `memory_context.lessons`, prepends hint to prompt |
| `graph/state.py` | `AeonState` TypedDict — single shared envelope for the graph |
| `config/settings.py` | `NEO4J_URI / USERNAME / PASSWORD` fields with safe empty defaults |
