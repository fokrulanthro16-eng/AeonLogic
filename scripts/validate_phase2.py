"""Quick validation script for Phase 2 checkpoint."""
import re
import sys

from aeonlogic.agents.executor import _BLOCKING_SEVERITIES, _EMERGENCY_PATTERNS
from aeonlogic.agents.critic import _RULES
from aeonlogic.domain.finding import Finding
from aeonlogic.models.qwen_client import _WEAK_AUTH_CODE, _SECURE_AUTH_CODE


def get_findings(content: str) -> list[Finding]:
    out = []
    for rule_id, title, severity, category, rec, checker in _RULES:
        matched, evidence = checker(content)
        if matched:
            out.append(Finding(
                artifact_id="validate",
                severity=severity,
                category=category,
                title=f"[{rule_id}] {title}",
                description="validation",
                evidence=evidence,
                recommendation=rec,
            ))
    return out


def main() -> None:
    ok = True

    # 1. Rule coverage
    weak_findings   = get_findings(_WEAK_AUTH_CODE)
    secure_findings = get_findings(_SECURE_AUTH_CODE)

    print(f"[1] Weak code findings   : {len(weak_findings)} (expected 5)")
    print(f"    Secure code findings : {len(secure_findings)} (expected 0)")
    if len(weak_findings) != 5 or len(secure_findings) != 0:
        print("    FAIL")
        ok = False
    else:
        print("    PASS")

    # 2. Executor blocking
    blocking_weak   = [f for f in weak_findings   if f.severity in _BLOCKING_SEVERITIES]
    blocking_secure = [f for f in secure_findings if f.severity in _BLOCKING_SEVERITIES]
    print(f"\n[2] Executor blocks weak code  : {len(blocking_weak) > 0}  ({len(blocking_weak)} blocking)")
    print(f"    Executor passes secure code : {len(blocking_secure) == 0}")
    if not (len(blocking_weak) > 0 and len(blocking_secure) == 0):
        print("    FAIL")
        ok = False
    else:
        print("    PASS")

    # 3. Emergency patterns don't false-positive on secure code
    ep = any(re.search(p, _SECURE_AUTH_CODE, re.IGNORECASE) for p, _ in _EMERGENCY_PATTERNS)
    print(f"\n[3] Emergency scan false-positive on secure code: {ep}  (expected False)")
    if ep:
        print("    FAIL")
        ok = False
    else:
        print("    PASS")

    # 4. Graph loop (full integration)
    print("\n[4] Graph integration loop ...")
    from aeonlogic.graph.builder import build_graph
    from aeonlogic.graph.state import AeonState
    from aeonlogic.domain.task import CycleStatus, ModelTier
    from aeonlogic.utils.ids import new_ulid

    graph = build_graph()
    sid   = new_ulid()
    cfg   = {"configurable": {"thread_id": sid}}
    init: AeonState = {
        "session_id": sid, "cycle_id": "", "generation_attempt": 0,
        "raw_goal": "Build a secure API authentication module",
        "tasks": [], "active_task": None, "model_tier": ModelTier.FAST,
        "memory_context": {}, "memory_write_ids": [], "lessons_written": [],
        "candidate_artifact": None, "critic_verdict": None, "critic_findings": [],
        "execution_result": None, "execution_status": None,
        "status": CycleStatus.RUNNING, "error": None,
        "dispatcher_trace": "", "generator_trace": "", "critic_trace": "",
        "executor_trace": "", "synthesizer_trace": "",
    }

    nodes = []
    exec_statuses = []
    for step in graph.stream(init, config=cfg, stream_mode="updates"):
        for n, u in step.items():
            nodes.append(n)
            if n == "execute":
                exec_statuses.append(str(u.get("execution_status", "?")))

    final   = graph.get_state(cfg).values
    lessons = final.get("lessons_written", [])

    expected_nodes = ["dispatch", "generate", "critique", "execute",
                      "generate", "critique", "execute", "synthesize"]
    print(f"    Node sequence  : {nodes}")
    print(f"    Expected       : {expected_nodes}")
    print(f"    Execute results: {exec_statuses}  (expected ['failure', 'success'])")
    print(f"    Final status   : {final.get('status')}  (expected success)")
    print(f"    Attempts       : {final.get('generation_attempt')}  (expected 2)")
    print(f"    Lessons        : {len(lessons)}  (expected 2)")
    lesson_types = [l["type"] for l in lessons]
    print(f"    Lesson types   : {lesson_types}  (expected failure-lesson, success-lesson)")

    loop_ok = (
        nodes == expected_nodes
        and exec_statuses == ["failure", "success"]
        and final.get("status") == "success"
        and final.get("generation_attempt") == 2
        and len(lessons) == 2
        and "failure-lesson" in lesson_types
        and "success-lesson" in lesson_types
    )
    print("    PASS" if loop_ok else "    FAIL")
    if not loop_ok:
        ok = False

    print()
    print("=" * 50)
    print("CHECKPOINT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
