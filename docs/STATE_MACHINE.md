# AeonLogic — LangGraph State Machine

## 1. State schema

The `AgentState` TypedDict (defined in `src/aeonlogic/graph/state.py`) is the single shared envelope passed between all graph nodes. LangGraph merges partial update dicts into this envelope after each node returns.

```python
class AgentState(TypedDict):
    # ── Identity ────────────────────────────────────────────────────────────
    session_id: str                        # ULID — top-level session
    cycle_id: str                          # ULID — current recursion cycle
    generation_attempt: int                # 1-indexed retry counter

    # ── Input ───────────────────────────────────────────────────────────────
    raw_goal: str                          # Original user goal string
    tasks: list[Task]                      # Full decomposed task queue
    active_task: Task | None               # Task being processed this cycle

    # ── Routing ─────────────────────────────────────────────────────────────
    model_tier: ModelTier                  # FAST | STRONG

    # ── Memory ──────────────────────────────────────────────────────────────
    memory_context: MemoryContext | None   # Retrieved context for Generator
    memory_write_ids: list[str]            # IDs written this cycle

    # ── Generation ──────────────────────────────────────────────────────────
    candidate_artifact: Artifact | None

    # ── Critique ────────────────────────────────────────────────────────────
    critic_verdict: Verdict | None         # APPROVED | REJECTED
    critic_findings: list[Finding]

    # ── Execution ───────────────────────────────────────────────────────────
    execution_result: Result | None
    execution_status: ExecutionStatus | None  # SUCCESS | FAILURE | TIMEOUT

    # ── Control flow ────────────────────────────────────────────────────────
    status: CycleStatus                    # RUNNING | SUCCESS | FAILED | EXHAUSTED
    error: str | None

    # ── Traces (for audit log) ───────────────────────────────────────────────
    dispatcher_trace: str
    generator_trace: str
    critic_trace: str
    executor_trace: str
    synthesizer_trace: str
```

---

## 2. Graph nodes

| Node name | Agent called | Description |
|---|---|---|
| `dispatch` | `Dispatcher` | Decomposes goal, classifies risk, sets `model_tier` |
| `generate` | `Generator` | Produces `candidate_artifact` |
| `critique` | `Critic` | Audits artefact, sets `critic_verdict` |
| `execute` | `Executor` | Runs approved artefact, sets `execution_result` |
| `synthesize` | `MemorySynthesizer` | Writes memory, sets `memory_context` for next cycle |

---

## 3. Edge table

| From node | Condition | To node |
|---|---|---|
| `START` | — (always) | `dispatch` |
| `dispatch` | `status == FAILED` | `END` |
| `dispatch` | `status == RUNNING` | `generate` |
| `generate` | `status == FAILED` | `synthesize` |
| `generate` | `status == RUNNING` | `critique` |
| `critique` | `verdict == APPROVED` | `execute` |
| `critique` | `verdict == REJECTED` and `attempt < MAX_RECURSION_DEPTH` | `generate` |
| `critique` | `verdict == REJECTED` and `attempt >= MAX_RECURSION_DEPTH` | `synthesize` |
| `execute` | `execution_status == SUCCESS` | `synthesize` |
| `execute` | `execution_status in {FAILURE, TIMEOUT}` | `synthesize` |
| `synthesize` | `tasks` queue non-empty | `dispatch` (next task) |
| `synthesize` | `tasks` queue empty | `END` |

---

## 4. Edge condition functions (pseudocode)

```python
def after_dispatch(state: AgentState) -> str:
    if state["status"] == CycleStatus.FAILED:
        return "END"
    return "generate"

def after_generate(state: AgentState) -> str:
    if state["status"] == CycleStatus.FAILED:
        return "synthesize"
    return "critique"

def after_critique(state: AgentState) -> str:
    if state["critic_verdict"] == Verdict.APPROVED:
        return "execute"
    if state["generation_attempt"] >= MAX_RECURSION_DEPTH:
        return "synthesize"         # exhausted — still write failure memory
    return "generate"               # retry with findings in context

def after_execute(state: AgentState) -> str:
    return "synthesize"             # always synthesize, success or failure

def after_synthesize(state: AgentState) -> str:
    remaining = [t for t in state["tasks"] if t.id != state["active_task"].id]
    if remaining:
        return "dispatch"           # more tasks in this session
    return "END"
```

---

## 5. State transition diagram

```
START
  │
  ▼
┌──────────┐    FAILED
│ dispatch │──────────────────────────────────────► END
└──────────┘
  │ RUNNING
  ▼
┌──────────┐    FAILED
│ generate │──────────────────────────────────────► synthesize
└──────────┘
  │ RUNNING
  ▼
┌──────────┐    APPROVED
│ critique │──────────────────────────────────────► execute
└──────────┘
  │ REJECTED + attempt < MAX          REJECTED + attempt >= MAX
  │                                         │
  └──────────► generate (retry) ◄───────────┘
                                             │
                                             ▼
                                         synthesize
                                             │
  execute (SUCCESS/FAILURE/TIMEOUT) ────────►│
                                             ▼
                                         ┌────────────┐
                                         │ synthesize │
                                         └─────┬──────┘
                                               │ tasks remaining?
                                    YES ────────┘        └──── NO
                                     │                         │
                                     ▼                         ▼
                                  dispatch                    END
```

---

## 6. Checkpoint strategy

LangGraph persists the full `AgentState` after every node. The persistence backend is selected by `CHECKPOINT_BACKEND` in `.env`:

| Backend | Use case |
|---|---|
| `memory` | Development / unit tests — no durability |
| `sqlite` | Single-process staging — survives restarts |
| `postgres` | Multi-worker production — shared across replicas |

Thread / run isolation: each API request receives a unique `session_id` passed as the LangGraph `thread_id`, ensuring state is never shared across concurrent sessions.

---

## 7. Recursion depth guard

`MAX_RECURSION_DEPTH` (default: 10, configurable via `.env`) is checked in `after_critique`. When the limit is reached the graph routes directly to `synthesize` with `status=EXHAUSTED`, ensuring experience from failed cycles is captured before termination.
