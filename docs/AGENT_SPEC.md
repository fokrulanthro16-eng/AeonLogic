# AeonLogic — Agent Specification

Each agent is a pure function `(AgentState) -> dict` that returns a partial state update. Agents must not produce side-effects beyond memory writes via designated store interfaces.

---

## 1. Dispatcher

**File:** `src/aeonlogic/agents/dispatcher.py`

### Responsibility

Decomposes the raw user goal into one or more `Task` domain objects, assigns a `RiskLevel`, and selects the model tier for downstream agents.

### Input (from `AgentState`)

| Field | Type | Description |
|---|---|---|
| `raw_goal` | `str` | Unstructured user input |
| `session_id` | `str` | ULID session identifier |
| `memory_context` | `MemoryContext \| None` | Pre-fetched hybrid memory context (may be `None` on first run) |

### Output (partial state update)

| Field | Type | Description |
|---|---|---|
| `tasks` | `list[Task]` | Decomposed, prioritised task queue |
| `active_task` | `Task` | The head task to be processed this cycle |
| `model_tier` | `ModelTier` | `FAST` or `STRONG` |
| `dispatcher_trace` | `str` | Reasoning trace for audit log |

### Model tier

`qwen-turbo` — dispatch logic is structured/classification; low risk.

### Failure modes

- `GoalDecompositionError` — raised if the goal cannot be parsed into valid tasks.
- Returns `status=FAILED` in state; graph routes to termination edge.

---

## 2. Generator

**File:** `src/aeonlogic/agents/generator.py`

### Responsibility

Produces a candidate `Artifact` (code, plan, analysis, or structured data) for the active task. Consumes memory context injected by the Memory Synthesizer retrieval path.

### Input (from `AgentState`)

| Field | Type | Description |
|---|---|---|
| `active_task` | `Task` | Task to solve |
| `model_tier` | `ModelTier` | Routing instruction from Dispatcher |
| `memory_context` | `MemoryContext` | Relevant Neo4j subgraph + ChromaDB top-k |
| `critic_findings` | `list[Finding]` | Populated on retry iterations |
| `generation_attempt` | `int` | 1-indexed retry counter |

### Output (partial state update)

| Field | Type | Description |
|---|---|---|
| `candidate_artifact` | `Artifact` | Proposed solution artefact |
| `generation_attempt` | `int` | Incremented |
| `generator_trace` | `str` | Reasoning trace |

### Model tier

Follows `model_tier` set by Dispatcher — `qwen-turbo` for `FAST`, `qwen-plus` for `STRONG`.

### Failure modes

- `ArtifactGenerationError` — LLM returned unparseable output.
- Exceeding `MAX_RECURSION_DEPTH` retries triggers `status=EXHAUSTED`.

---

## 3. Critic / Adversarial Auditor

**File:** `src/aeonlogic/agents/critic.py`

### Responsibility

Stress-tests the candidate `Artifact` against correctness, safety, and alignment criteria. Produces structured `Finding` objects. Approves or rejects the artefact.

### Input (from `AgentState`)

| Field | Type | Description |
|---|---|---|
| `candidate_artifact` | `Artifact` | Artefact to audit |
| `active_task` | `Task` | Original task context |
| `security_policies` | `list[Policy]` | Active policy set |

### Output (partial state update)

| Field | Type | Description |
|---|---|---|
| `critic_verdict` | `Verdict` | `APPROVED` or `REJECTED` |
| `critic_findings` | `list[Finding]` | Structured issues (empty on approval) |
| `critic_trace` | `str` | Adversarial reasoning trace |

### Model tier

Always `qwen-plus` — critic judgement is high-risk; quality must not be compromised for speed.

### Evaluation axes

1. **Correctness** — Does the artefact solve the task as specified?
2. **Safety** — No harmful content, no prompt injection vectors.
3. **Policy compliance** — Passes all active `Policy` rules.
4. **Hallucination detection** — Claims are grounded in memory context or explicitly flagged as inferred.

### Failure modes

- `CriticTimeoutError` — model response exceeded `LLM_REQUEST_TIMEOUT`.
- On timeout: verdict defaults to `REJECTED` with a `TIMEOUT` finding.

---

## 4. Executor

**File:** `src/aeonlogic/agents/executor.py`

### Responsibility

Runs an approved `Artifact` in a sandboxed environment, captures the execution `Result`, and validates it against the task's success criteria.

### Input (from `AgentState`)

| Field | Type | Description |
|---|---|---|
| `candidate_artifact` | `Artifact` | Approved artefact (passed Critic) |
| `active_task` | `Task` | Provides success criteria |

### Output (partial state update)

| Field | Type | Description |
|---|---|---|
| `execution_result` | `Result` | Structured execution output |
| `execution_status` | `ExecutionStatus` | `SUCCESS`, `FAILURE`, or `TIMEOUT` |
| `executor_trace` | `str` | Execution log summary |

### Model tier

N/A — Executor is a deterministic runner, not an LLM call. Uses `runner.py` from the execution layer.

### Sandbox constraints

- Process isolated; timeout enforced by `SANDBOX_TIMEOUT_SECONDS`.
- No network access unless explicitly allowed by `Policy`.
- All file I/O limited to the `data/` scratch directory.

### Failure modes

- `SandboxTimeoutError` — execution exceeded wall-clock limit.
- `ArtifactValidationError` — artefact failed pre-run schema check.
- Both cases result in `execution_status=FAILURE` and graph routes to Memory Synthesizer for failure experience capture.

---

## 5. Memory Synthesizer

**File:** `src/aeonlogic/agents/memory_synthesizer.py`

### Responsibility

Distils the completed task cycle into durable long-term memory. Writes structured knowledge to Neo4j and episodic embeddings to ChromaDB. Also performs retrieval to enrich future Generator calls.

### Input (from `AgentState`)

| Field | Type | Description |
|---|---|---|
| `active_task` | `Task` | Completed task |
| `candidate_artifact` | `Artifact` | The final artefact (approved or failed) |
| `execution_result` | `Result` | Outcome |
| `critic_findings` | `list[Finding]` | Audit findings from this cycle |
| `generation_attempt` | `int` | How many retries were needed |

### Output (partial state update)

| Field | Type | Description |
|---|---|---|
| `memory_context` | `MemoryContext` | Retrieved context for the *next* Generator call |
| `memory_write_ids` | `list[str]` | IDs of nodes/documents written this cycle |
| `synthesizer_trace` | `str` | Summary of what was learned |

### Model tier

`qwen-turbo` — extraction of memory units from structured state is a classification/summarisation task.

### Memory write schema

**Neo4j nodes written per cycle:**
- `(:Task {id, description, risk_level, status, timestamp})`
- `(:Artifact {id, type, content_hash, timestamp})`
- `(:Result {id, status, summary, timestamp})`

**Neo4j relationships:**
- `(Task)-[:PRODUCED]->(Artifact)`
- `(Artifact)-[:YIELDED]->(Result)`
- `(Task)-[:INFORMED_BY]->(Task)` (cross-cycle learning links)

**ChromaDB documents:**
- One document per `Finding` (for critic pattern recognition)
- One document per `Result` summary (for outcome similarity search)

---

## Agent interaction summary

```
Dispatcher
  │  assigns: active_task, model_tier
  ▼
Generator ◄──────────────────────── Memory Synthesizer (retrieval)
  │  produces: candidate_artifact   │
  ▼                                 │
Critic                             │
  │  verdict: APPROVED / REJECTED   │
  ├──[REJECTED]──► Generator (retry, up to MAX_RECURSION_DEPTH)
  │
  ▼ [APPROVED]
Executor
  │  produces: execution_result
  ▼
Memory Synthesizer (write + retrieve for next cycle)
```
