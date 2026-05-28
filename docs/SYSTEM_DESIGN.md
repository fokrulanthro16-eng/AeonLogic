# AeonLogic — System Design

## 1. Purpose

AeonLogic is a recursive, self-improving multi-agent system. Its core premise is that intelligence compounds: each task cycle not only produces an output but also enriches a persistent memory graph that future cycles draw from. The architecture is designed for low latency, observable behaviour, and safe autonomous execution.

---

## 2. High-level architecture

```
                          ┌─────────────────────────────┐
                          │      Client (CLI / API)      │
                          └──────────────┬──────────────┘
                                         │ Task
                                         ▼
                          ┌─────────────────────────────┐
                          │      LangGraph Graph         │
                          │                             │
                          │  ┌──────────┐               │
                          │  │Dispatcher│               │
                          │  └─────┬────┘               │
                          │        │ routed task         │
                          │  ┌─────▼────┐               │
                          │  │Generator │               │
                          │  └─────┬────┘               │
                          │        │ candidate artefact  │
                          │  ┌─────▼──────────────────┐ │
                          │  │  Critic / Adversarial  │ │
                          │  │       Auditor          │ │
                          │  └─────┬──────────────────┘ │
                          │        │ approved / rejected │
                          │  ┌─────▼────┐               │
                          │  │ Executor │               │
                          │  └─────┬────┘               │
                          │        │ execution result    │
                          │  ┌─────▼──────────────┐     │
                          │  │ Memory Synthesizer │     │
                          │  └─────┬──────────────┘     │
                          │        │                     │
                          └────────┼────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              Neo4j Graph    ChromaDB         Checkpoint
              (relations)    (embeddings)     (state)
```

---

## 3. Components

### 3.1 LangGraph graph (`src/aeonlogic/graph/`)

| File | Responsibility |
|---|---|
| `state.py` | Typed `AgentState` TypedDict — the shared mutable envelope passed between nodes |
| `builder.py` | Compiles the `StateGraph`, wires nodes and edges, attaches a checkpointer |
| `edges.py` | Conditional edge functions — decide next node based on state flags |
| `checkpoints.py` | Configures the persistence backend (in-memory / SQLite / Postgres) |

The graph is compiled once at process start and reused across all requests via a shared `CompiledGraph` instance.

### 3.2 Agents (`src/aeonlogic/agents/`)

Each agent is a callable that accepts `AgentState` and returns a partial state update. Agents never mutate state directly; they return `dict` deltas that LangGraph merges.

### 3.3 Model router (`src/aeonlogic/models/router.py`)

Selects between `qwen-turbo` and `qwen-plus` based on a `RiskLevel` enum attached to every `Task`. The router enforces per-model token budgets defined in `budgets.py` and applies prompt templates from `prompts.py`.

### 3.4 Memory layer (`src/aeonlogic/memory/`)

| Store | Technology | Access pattern |
|---|---|---|
| **Knowledge graph** | Neo4j | Cypher queries; stores entities, relationships, provenance chains |
| **Vector store** | ChromaDB | Approximate nearest-neighbour search; stores episodic memories as embeddings |
| **Hybrid retrieval** | `hybrid_store.py` | Fuses graph traversal with vector similarity before injecting context into prompts |

### 3.5 Execution layer (`src/aeonlogic/execution/`)

`runner.py` wraps artefact execution in a configurable sandbox. Every run is bounded by `SANDBOX_TIMEOUT_SECONDS`. `result_parser.py` normalises raw output into a `Result` domain object. `artifact_validator.py` enforces schema invariants before execution.

### 3.6 Observability (`src/aeonlogic/observability/`)

- **Structured logging** — `structlog` with JSON rendering in production, console renderer in development.
- **Distributed tracing** — OpenTelemetry spans are emitted per agent invocation. The OTLP exporter ships traces to any compatible backend (Jaeger, Grafana Tempo, etc.).
- **Metrics** — Prometheus counters and histograms track task throughput, model latency, memory hit rate, and critic rejection rate.
- **Audit log** — immutable append-only log of every state transition, written in `audit_log.py`.

### 3.7 Security (`src/aeonlogic/security/`)

| Module | Purpose |
|---|---|
| `policies.py` | Declarative allow/deny rules evaluated before execution |
| `threat_models.py` | Enumerated threat categories (prompt injection, data exfiltration, etc.) |
| `validators.py` | Input and output schema validation |
| `sandbox.py` | Process isolation configuration |
| `adversarial_suite.py` | Automated red-team prompts run against the Critic agent during CI |

---

## 4. Data flows

### 4.1 Happy path

```
Client ──► Dispatcher ──► Generator ──► Critic ──► Executor ──► Memory Synthesizer ──► Client
```

### 4.2 Critic rejection (retry loop)

```
Generator ──► Critic ──[rejected]──► Generator (with findings in context)
                                        └── up to MAX_RECURSION_DEPTH iterations
```

### 4.3 Memory retrieval enrichment

Before each Generator call, the Memory Synthesizer's retrieval path injects:
1. Relevant Neo4j subgraph (entity context, past decisions)
2. Top-k ChromaDB embeddings (similar past tasks and outcomes)

---

## 5. Deployment topology

| Mode | Description |
|---|---|
| **Local dev** | Embedded ChromaDB, Neo4j via Docker, in-memory checkpointer |
| **Staging** | ChromaDB HTTP server, Neo4j AuraDB Free, SQLite checkpointer |
| **Production** | ChromaDB HTTP server, Neo4j AuraDB Enterprise, Postgres checkpointer |

---

## 6. Key design decisions

| Decision | Rationale |
|---|---|
| LangGraph over raw LangChain agents | Explicit state machine semantics; deterministic edge conditions; built-in checkpointing |
| Pydantic v2 throughout | Fast validation, JSON schema generation, first-class `TypedDict` support |
| Two-tier model routing | Balances cost and quality; `qwen-turbo` handles ≥80% of tokens |
| Neo4j + ChromaDB hybrid | Graph handles relational reasoning; vector store handles semantic similarity — neither alone is sufficient |
| Structlog + OTEL | Correlatable logs and traces without coupling agent code to a specific backend |
| ULID identifiers | Time-sortable, URL-safe, globally unique — better than UUID v4 for time-series audit logs |
