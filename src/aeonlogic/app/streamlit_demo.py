"""
AeonLogic Command Center — Streamlit dashboard.

Structure
---------
* Module-level code: only imports and pure functions.  No `st.*` calls.
  → safe to `import` in tests and from other modules.
* `_render()` contains every Streamlit call and is only invoked when the
  file is executed by `streamlit run` (which sets __name__ == "__main__").
"""
from __future__ import annotations

from typing import Any

from aeonlogic.domain.finding import FindingSeverity, Verdict
from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import CycleStatus, ModelTier
from aeonlogic.models.budgets import get_budget
from aeonlogic.utils.ids import new_ulid

PAGE_TITLE = "AeonLogic Command Center"
DEFAULT_GOAL = "Build a secure API authentication module"

# ---------------------------------------------------------------------------
# CSS — dark futuristic command-center theme
# ---------------------------------------------------------------------------

_CSS = """
<style>
/* ── Base ── */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background-color: #060b16 !important;
    color: #c8d8e8 !important;
}
[data-testid="stHeader"] { background: transparent !important; }
section[data-testid="stSidebar"] { background: #070d1c !important; }
div[data-testid="stToolbar"] { display: none; }

/* ── Typography ── */
* { font-family: 'Courier New', Courier, monospace; }

/* ── Input ── */
input[type="text"], textarea {
    background: #0a1628 !important;
    color: #c8e8ff !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 4px !important;
}
label { color: #4a9abe !important; letter-spacing: 1px; font-size: 0.78em !important; }

/* ── Primary button ── */
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #003d7a, #0077c8) !important;
    color: #00d4ff !important;
    border: 1px solid #00d4ff !important;
    border-radius: 4px !important;
    font-weight: bold !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
}
[data-testid="baseButton-primary"]:hover {
    background: linear-gradient(135deg, #0055aa, #0099e8) !important;
    box-shadow: 0 0 16px #00d4ff55 !important;
}

/* ── Metric ── */
[data-testid="metric-container"] {
    background: #0a1628;
    border: 1px solid #1e3a5f;
    border-left: 3px solid #00d4ff;
    border-radius: 6px;
    padding: 10px 14px !important;
}
[data-testid="stMetricLabel"]  > div { color: #4a9abe !important; font-size: 0.72em; letter-spacing: 1px; }
[data-testid="stMetricValue"]  > div { color: #c8e8ff !important; font-size: 1.4em; }
[data-testid="stMetricDelta"]  > div { font-size: 0.8em; }

/* ── Divider ── */
hr { border-color: #1a3050 !important; }

/* ── Expander ── */
[data-testid="stExpander"] details {
    background: #080f1e !important;
    border: 1px solid #1a3050 !important;
    border-radius: 6px !important;
}
summary { color: #4a9abe !important; font-size: 0.85em; letter-spacing: 1px; }

/* ── Alert boxes ── */
[data-testid="stAlert"] { border-radius: 6px !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: #00d4ff !important; }

/* ── Custom classes ── */
.aeon-logo {
    font-size: 2em;
    font-weight: bold;
    color: #00d4ff;
    letter-spacing: 4px;
    text-shadow: 0 0 24px #00d4ff66;
}
.aeon-sub { color: #2a6a8a; font-size: 0.78em; letter-spacing: 2px; }
.mode-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.72em;
    letter-spacing: 1px;
    font-weight: bold;
}
.badge-mock    { background: #1a2a10; border: 1px solid #4a8a20; color: #88cc44; }
.badge-real    { background: #102a10; border: 1px solid #20aa40; color: #44ee66; }
.card {
    background: #0a1628;
    border: 1px solid #1e3a5f;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.card-red   { border-left: 3px solid #ff3366; }
.card-green { border-left: 3px solid #00ff88; }
.card-amber { border-left: 3px solid #ffaa00; }
.card-cyan  { border-left: 3px solid #00d4ff; }
.sev-critical { color: #ff3366; font-weight: bold; }
.sev-high     { color: #ff6644; font-weight: bold; }
.sev-medium   { color: #ffaa00; }
.sev-low      { color: #00d4ff; }
.sev-info     { color: #667788; }
.verdict-ok {
    text-align: center; padding: 20px;
    background: #071a0f; border: 2px solid #00ff88; border-radius: 8px;
    font-size: 1.6em; color: #00ff88; letter-spacing: 3px;
}
.verdict-fail {
    text-align: center; padding: 20px;
    background: #1a0709; border: 2px solid #ff3366; border-radius: 8px;
    font-size: 1.6em; color: #ff3366; letter-spacing: 3px;
}
</style>
"""

# ---------------------------------------------------------------------------
# Pure engine functions — no Streamlit dependency
# ---------------------------------------------------------------------------

def _make_initial_state(goal: str, session_id: str) -> dict[str, Any]:
    from aeonlogic.graph.state import AeonState  # late import keeps module lightweight
    return {
        "session_id":         session_id,
        "cycle_id":           "",
        "generation_attempt": 0,
        "raw_goal":           goal,
        "tasks":              [],
        "active_task":        None,
        "model_tier":         ModelTier.FAST,
        "memory_context":     {},
        "memory_write_ids":   [],
        "lessons_written":    [],
        "candidate_artifact": None,
        "critic_verdict":     None,
        "critic_findings":    [],
        "execution_result":   None,
        "execution_status":   None,
        "status":             CycleStatus.RUNNING,
        "error":              None,
        "dispatcher_trace":   "",
        "generator_trace":    "",
        "critic_trace":       "",
        "executor_trace":     "",
        "synthesizer_trace":  "",
    }


def _collect_pipeline_events(goal: str) -> dict[str, Any]:
    """Run the AeonLogic pipeline and return structured run data.

    Returns a dict with keys: session_id, runtime_mode, events, final_state.
    No Streamlit calls; safe to test directly.
    """
    from aeonlogic.app.lifecycle import on_shutdown, on_startup
    from aeonlogic.config.settings import get_settings
    from aeonlogic.graph.builder import build_graph

    on_startup()
    settings = get_settings()
    runtime_mode = settings.client_mode_label
    session_id = new_ulid()

    graph = build_graph()
    initial = _make_initial_state(goal, session_id)
    config = {"configurable": {"thread_id": session_id}}

    events: list[dict[str, Any]] = []
    for step in graph.stream(initial, config=config, stream_mode="updates"):
        for node_name, update in step.items():
            events.append({"node": node_name, "update": update})

    final_state = dict(graph.get_state(config).values)
    on_shutdown()

    return {
        "session_id": session_id,
        "runtime_mode": runtime_mode,
        "events": events,
        "final_state": final_state,
    }


def _build_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Distil a list of {node, update} events into display-ready data.

    Pure function: no Streamlit, no engine calls.  Easily unit-tested.
    """
    summary: dict[str, Any] = {
        "risk_level":            "UNKNOWN",
        "model_name":            "—",
        "attempts":              0,
        "repaired":              False,
        "findings":              [],
        "memory_lessons":        [],
        "final_status":          "UNKNOWN",
        "total_findings":        0,
        "execution_duration_ms": 0,
        "execution_blocked":     False,
    }

    max_attempt = 0

    for event in events:
        node   = event.get("node", "")
        update = event.get("update", {})

        if node == "dispatch":
            task = update.get("active_task")
            if task:
                rl = getattr(task, "risk_level", "unknown")
                summary["risk_level"] = str(rl).upper()
            tier = update.get("model_tier", ModelTier.FAST)
            try:
                budget = get_budget(tier)
                summary["model_name"] = budget.model_name
            except Exception:
                pass

        elif node == "generate":
            attempt = int(update.get("generation_attempt", 0))
            if attempt > max_attempt:
                max_attempt = attempt

        elif node == "critique":
            verdict  = update.get("critic_verdict")
            findings = update.get("critic_findings", [])
            if verdict == Verdict.REJECTED and findings:
                for f in findings:
                    summary["findings"].append({
                        "severity":       str(getattr(f, "severity", "unknown")),
                        "title":          str(getattr(f, "title", "")),
                        "evidence":       str(getattr(f, "evidence", "")),
                        "recommendation": str(getattr(f, "recommendation", "")),
                    })
                    summary["total_findings"] += 1

        elif node == "execute":
            exec_status = update.get("execution_status")
            result      = update.get("execution_result")
            if exec_status == ExecutionStatus.FAILURE:
                summary["execution_blocked"] = True
            if result:
                summary["execution_duration_ms"] = int(getattr(result, "duration_ms", 0))

        elif node == "synthesize":
            summary["memory_lessons"] = list(update.get("lessons_written", []))
            raw_status = update.get("status")
            if raw_status is not None:
                summary["final_status"] = str(raw_status).upper()

    summary["attempts"] = max_attempt
    summary["repaired"] = max_attempt > 1
    return summary


# ---------------------------------------------------------------------------
# Streamlit rendering — only called when run via `streamlit run`
# ---------------------------------------------------------------------------

def _render() -> None:  # noqa: C901
    import streamlit as st

    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────
    st.markdown('<div class="aeon-logo">⚡ AEONLOGIC COMMAND CENTER</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="aeon-sub">RECURSIVE PERPETUAL EVOLUTION &nbsp;·&nbsp; MULTI-AGENT AI SYSTEM</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Runtime mode badge ────────────────────────────────────────────────
    from aeonlogic.config.settings import get_settings
    runtime_mode = get_settings().client_mode_label
    badge_cls = "badge-real" if runtime_mode == "REAL_QWEN_MODE" else "badge-mock"
    dot = "●"
    st.markdown(
        f'<span class="mode-badge {badge_cls}">{dot} {runtime_mode}</span>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Mission input ─────────────────────────────────────────────────────
    goal = st.text_input(
        "MISSION OBJECTIVE",
        value=DEFAULT_GOAL,
        placeholder="Describe your task in plain language …",
    )
    run_clicked = st.button("▶  EXECUTE PIPELINE", type="primary", use_container_width=True)

    # ── Trigger run ───────────────────────────────────────────────────────
    if run_clicked and goal.strip():
        with st.spinner("⟳  Pipeline executing …"):
            run_data = _collect_pipeline_events(goal.strip())
        st.session_state["aeon_result"] = run_data

    # ── Display results ───────────────────────────────────────────────────
    run_data: dict[str, Any] | None = st.session_state.get("aeon_result")
    if run_data is None:
        st.markdown(
            '<div class="card card-cyan" style="text-align:center;color:#2a6a8a;">'
            'Enter a mission objective and click EXECUTE PIPELINE to begin.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    summary = _build_summary(run_data["events"])

    # Override final_status from full final_state if available
    final_state = run_data.get("final_state", {})
    raw_fs = final_state.get("status")
    if raw_fs is not None:
        summary["final_status"] = str(raw_fs).upper()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top metric row ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RUNTIME MODE",  run_data.get("runtime_mode", "—"))
    c2.metric("MODEL",         summary["model_name"])

    risk = summary["risk_level"]
    risk_delta = "⚠ HIGH RISK" if risk == "HIGH" else ("LOW RISK" if risk == "LOW" else None)
    c3.metric("RISK LEVEL", risk, delta=risk_delta,
              delta_color="inverse" if risk == "HIGH" else "normal")

    c4.metric("ATTEMPTS", summary["attempts"],
              delta="REPAIRED ✓" if summary["repaired"] else "FIRST PASS",
              delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Status row ─────────────────────────────────────────────────────────
    s1, s2, s3 = st.columns(3)
    s1.metric("REPAIR CYCLE",   "YES" if summary["repaired"] else "NO")
    s2.metric("FINDINGS TOTAL", summary["total_findings"])
    s3.metric("EXEC BLOCKED",   "YES" if summary["execution_blocked"] else "NO")

    st.divider()

    # ── Critic findings ────────────────────────────────────────────────────
    findings = summary["findings"]
    label = f"🔍  CRITIC FINDINGS  ({len(findings)} detected)"
    with st.expander(label, expanded=bool(findings)):
        if not findings:
            st.markdown(
                '<div class="card card-green" style="color:#00ff88;">No security findings — artifact approved on first attempt.</div>',
                unsafe_allow_html=True,
            )
        else:
            _SEV_CSS = {
                "critical": "sev-critical",
                "high":     "sev-high",
                "medium":   "sev-medium",
                "low":      "sev-low",
                "info":     "sev-info",
            }
            for f in findings:
                sev = str(f["severity"]).lower()
                css = _SEV_CSS.get(sev, "sev-info")
                ev  = f["evidence"][:120] + "…" if len(f["evidence"]) > 120 else f["evidence"]
                rec = f["recommendation"]
                rec_html = f'<div style="color:#667788;font-size:0.8em;margin-top:4px;">↳ {rec[:120]}</div>' if rec else ""
                st.markdown(
                    f'<div class="card card-red">'
                    f'<span class="{css}">[{sev.upper()}]</span>&nbsp;&nbsp;{f["title"]}<br>'
                    f'<span style="color:#667788;font-size:0.8em;">{ev}</span>'
                    f'{rec_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Memory writes ──────────────────────────────────────────────────────
    lessons = summary["memory_lessons"]
    with st.expander(f"🧠  MEMORY WRITES  ({len(lessons)} lesson(s))", expanded=bool(lessons)):
        if not lessons:
            st.markdown(
                '<div class="card" style="color:#4a6a8a;">No lessons written this cycle.</div>',
                unsafe_allow_html=True,
            )
        else:
            for entry in lessons:
                ltype   = str(entry.get("type", "unknown"))
                content = str(entry.get("content", ""))
                lid     = str(entry.get("id", ""))[:16]
                snippet = content[:100] + "…" if len(content) > 100 else content
                card_cls = "card-red" if "failure" in ltype else "card-green"
                type_color = "#ff6655" if "failure" in ltype else "#00ff88"
                st.markdown(
                    f'<div class="card {card_cls}">'
                    f'<span style="color:{type_color};font-size:0.78em;">[{ltype.upper()}]</span>'
                    f'&nbsp;<span style="color:#2a4a6a;font-size:0.72em;">{lid}…</span><br>'
                    f'<span style="font-size:0.85em;color:#9ab8cc;">{snippet}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Final verdict ──────────────────────────────────────────────────────
    fs = summary["final_status"]
    is_success = "SUCCESS" in fs

    if is_success:
        findings_resolved = (
            f"{summary['total_findings']} finding(s) resolved  ·  "
            if summary["total_findings"] else ""
        )
        repair_note = "1 repair cycle  ·  " if summary["repaired"] else ""
        st.markdown(
            f'<div class="verdict-ok">'
            f'✅ &nbsp; {fs}<br>'
            f'<span style="font-size:0.55em;color:#44aa66;letter-spacing:1px;">'
            f'{repair_note}{findings_resolved}APPROVED BY CRITIC + EXECUTOR'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="verdict-fail">'
            f'✗ &nbsp; {fs}<br>'
            f'<span style="font-size:0.55em;color:#cc3344;letter-spacing:1px;">'
            f'Pipeline did not reach a successful execution state.'
            f'</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Session footer ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="color:#1a3a5a;font-size:0.72em;text-align:center;">'
        f'session · {run_data.get("session_id", "—")}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Entry point — only executed by `streamlit run`, never on plain import
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _render()
