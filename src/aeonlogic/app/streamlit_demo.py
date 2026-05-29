"""
AeonLogic Command Center — Streamlit dashboard (Phase 5B polish).

Structure
---------
* Module-level code: only imports, constants, and pure functions.  No st.* calls.
  → safe to `import` in tests and from other modules.
* `_render()` contains every Streamlit call and is only invoked when the file is
  executed by `streamlit run` (which sets __name__ == "__main__").
"""
from __future__ import annotations

from typing import Any

from aeonlogic.domain.finding import Verdict
from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import CycleStatus, ModelTier
from aeonlogic.models.budgets import get_budget
from aeonlogic.utils.ids import new_ulid

PAGE_TITLE    = "AeonLogic Command Center"
PAGE_SUBTITLE = "Recursive Self-Healing Multi-Agent Engine"
DEFAULT_GOAL  = "Build a secure API authentication module"

# Ordered pipeline stages shown in the timeline
_TIMELINE_NODES = ["DISPATCH", "GENERATE", "CRITIC", "EXECUTE", "REPAIR", "MEMORY", "FINAL"]

# LangGraph node name → timeline label
_NODE_TO_STAGE: dict[str, str] = {
    "dispatch":  "DISPATCH",
    "generate":  "GENERATE",
    "critique":  "CRITIC",
    "execute":   "EXECUTE",
    "synthesize": "MEMORY",
}

# ---------------------------------------------------------------------------
# CSS — dark futuristic command-center theme (Phase 5B)
# ---------------------------------------------------------------------------

_CSS = """
<style>
/* ── Base ── */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"] {
    background-color: #050c18 !important;
    color: #c0d4e8 !important;
}
[data-testid="stHeader"]  { background: transparent !important; }
[data-testid="stToolbar"] { display: none !important; }
section[data-testid="stSidebar"] { background: #060d1c !important; }

/* ── Typography ── */
* { font-family: 'Courier New', Courier, monospace; }

/* ── Input ── */
input[type="text"], textarea {
    background: #091525 !important;
    color: #b0d0f0 !important;
    border: 1px solid #1b3650 !important;
    border-radius: 4px !important;
}
label { color: #3a8aaa !important; letter-spacing: 1px; font-size: 0.78em !important; }

/* ── Primary button ── */
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #003470, #0068b8) !important;
    color: #00ccff !important;
    border: 1px solid #00ccff !important;
    border-radius: 4px !important;
    font-weight: bold !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    transition: box-shadow 0.2s ease !important;
}
[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 0 18px #00ccff44 !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #091525;
    border: 1px solid #1b3650;
    border-left: 3px solid #00ccff;
    border-radius: 6px;
    padding: 10px 14px !important;
}
[data-testid="stMetricLabel"] > div { color: #3a8aaa !important; font-size: 0.70em; letter-spacing: 1px; }
[data-testid="stMetricValue"] > div { color: #b8e0ff !important; font-size: 1.35em; }
[data-testid="stMetricDelta"] > div { font-size: 0.78em; }

/* ── Divider ── */
hr { border-color: #0e2840 !important; }

/* ── Expander ── */
[data-testid="stExpander"] details {
    background: #070f1c !important;
    border: 1px solid #0e2840 !important;
    border-radius: 6px !important;
}
summary { color: #3a8aaa !important; font-size: 0.83em; letter-spacing: 1px; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: #00ccff !important; }

/* ── Hero ── */
.hero-logo {
    font-size: 2.3em;
    font-weight: 900;
    color: #00ccff;
    letter-spacing: 5px;
    text-shadow: 0 0 28px #00ccff55, 0 0 56px #00ccff22;
    line-height: 1.1;
}
.hero-sub {
    color: #2a6a8a;
    font-size: 0.80em;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 5px;
}
.hero-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #0a3060, transparent);
    margin: 14px 0 10px 0;
}

/* ── Mode badge ── */
.mode-badge {
    display: inline-block;
    padding: 2px 12px;
    border-radius: 12px;
    font-size: 0.72em;
    letter-spacing: 1px;
    font-weight: bold;
}
.badge-mock { background: #141e08; border: 1px solid #3a7010; color: #7ab830; }
.badge-real { background: #081e10; border: 1px solid #10aa38; color: #30ee60; }

/* ── Agent timeline ── */
.timeline-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0;
    padding: 10px 0 6px 0;
}
.tl-node {
    font-size: 0.65em;
    letter-spacing: 1px;
    padding: 4px 11px;
    border: 1px solid #0e2840;
    background: #070f1c;
    color: #1e4060;
    white-space: nowrap;
}
.tl-node-active  { border-color: #00ccff55; background: #071828; color: #4090b8; }
.tl-node-success { border-color: #00ff8866; background: #071a10; color: #00cc66; font-weight: bold; }
.tl-node-repair  { border-color: #ffaa0066; background: #1a1208; color: #cc8800; font-weight: bold; }
.tl-sep { color: #0e2840; font-size: 0.9em; padding: 0 2px; user-select: none; }
.tl-sep-active  { color: #1a4060; }

/* ── Generic cards ── */
.card {
    background: #091525;
    border: 1px solid #1b3650;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.card-red   { border-left: 3px solid #ee2255; }
.card-green { border-left: 3px solid #00ee88; }
.card-amber { border-left: 3px solid #ffaa00; }
.card-cyan  { border-left: 3px solid #00ccff; }
.card-grey  { border-left: 3px solid #1e4060; }

/* ── Severity labels ── */
.sev-critical { color: #ff2255; font-weight: bold; }
.sev-high     { color: #ff5533; font-weight: bold; }
.sev-medium   { color: #ffaa00; }
.sev-low      { color: #00ccff; }
.sev-info     { color: #3a6070; }

/* ── Section headers ── */
.section-hdr {
    font-size: 0.70em;
    letter-spacing: 2px;
    color: #1e5070;
    text-transform: uppercase;
    border-bottom: 1px solid #0a2030;
    padding-bottom: 4px;
    margin: 18px 0 10px 0;
}

/* ── Memory backend chips ── */
.mem-row { display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0; }
.mem-chip {
    display: inline-block;
    font-size: 0.70em;
    padding: 3px 12px;
    border-radius: 10px;
    letter-spacing: 1px;
}
.mem-chip-ok   { background: #081e10; border: 1px solid #00aa44; color: #00cc55; }
.mem-chip-mock { background: #1c1a08; border: 1px solid #aa8800; color: #ccaa00; }
.mem-chip-off  { background: #1a0810; border: 1px solid #662233; color: #995566; }

/* ── Final verdict ── */
.verdict-ok {
    text-align: center;
    padding: 22px 16px;
    background: linear-gradient(180deg, #071e0f, #050c08);
    border: 2px solid #00ee88;
    border-radius: 8px;
    box-shadow: 0 0 24px #00ee8818;
}
.verdict-ok-title  { font-size: 1.8em; color: #00ee88; letter-spacing: 4px; font-weight: bold; }
.verdict-ok-sub    { font-size: 0.72em; color: #007744; letter-spacing: 1px; margin-top: 6px; }
.verdict-fail {
    text-align: center;
    padding: 22px 16px;
    background: linear-gradient(180deg, #1a0710, #0c0408);
    border: 2px solid #ee2255;
    border-radius: 8px;
    box-shadow: 0 0 24px #ee225518;
}
.verdict-fail-title { font-size: 1.8em; color: #ee2255; letter-spacing: 4px; font-weight: bold; }
.verdict-fail-sub   { font-size: 0.72em; color: #882233; letter-spacing: 1px; margin-top: 6px; }

/* ── Export block ── */
.export-wrap {
    background: #040a12;
    border: 1px solid #0e2840;
    border-radius: 6px;
    padding: 14px 16px;
    font-size: 0.78em;
    color: #2a6080;
    white-space: pre;
    overflow-x: auto;
    line-height: 1.5;
}
</style>
"""

# ---------------------------------------------------------------------------
# Pure engine functions — no Streamlit dependency
# ---------------------------------------------------------------------------

def _make_initial_state(goal: str, session_id: str) -> dict[str, Any]:
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
        "session_id":   session_id,
        "runtime_mode": runtime_mode,
        "events":       events,
        "final_state":  final_state,
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


def _build_timeline_stages(events: list[dict[str, Any]]) -> list[str]:
    """Return ordered list of timeline stage labels that were activated.

    Pure function — no Streamlit, no engine calls.
    """
    visited: set[str] = set()
    max_attempt = 0

    for event in events:
        node   = event.get("node", "")
        update = event.get("update", {})
        label  = _NODE_TO_STAGE.get(node)
        if label:
            visited.add(label)
        if node == "generate":
            attempt = int(update.get("generation_attempt", 0))
            if attempt > max_attempt:
                max_attempt = attempt

    if max_attempt > 1:
        visited.add("REPAIR")
    if "MEMORY" in visited:
        visited.add("FINAL")

    return [s for s in _TIMELINE_NODES if s in visited]


def build_demo_summary_text(
    session_id: str,
    runtime_mode: str,
    summary: dict[str, Any],
) -> str:
    """Generate a copyable plain-text summary for sharing after a demo run.

    Pure function — no Streamlit calls.
    """
    lessons       = summary.get("memory_lessons", [])
    lesson_types  = [str(l.get("type", "")) for l in lessons]
    failure_count = sum(1 for t in lesson_types if "failure" in t)
    success_count = sum(1 for t in lesson_types if "success" in t)
    repair_str    = (
        "YES — recursive self-healing triggered"
        if summary.get("repaired")
        else "NO  — first-pass success"
    )
    verdict = summary.get("final_status", "UNKNOWN")
    verdict_icon = "✅" if "SUCCESS" in verdict else "✗"

    lines = [
        "╔══════════════════════════════════════════════════╗",
        "║   AEONLOGIC COMMAND CENTER  —  Demo Run Report   ║",
        "╚══════════════════════════════════════════════════╝",
        f"  Session      : {session_id}",
        f"  Runtime mode : {runtime_mode}",
        f"  Model        : {summary.get('model_name', '—')}",
        f"  Risk level   : {summary.get('risk_level', '—')}",
        "──────────────────────────────────────────────────",
        f"  Attempts     : {summary.get('attempts', 0)}",
        f"  Repaired     : {repair_str}",
        f"  Findings     : {summary.get('total_findings', 0)} security issues detected",
        f"  Exec blocked : {'YES' if summary.get('execution_blocked') else 'NO'}",
        "──────────────────────────────────────────────────",
        f"  Lessons      : {len(lessons)} written to hybrid memory",
        f"    failure    : {failure_count}",
        f"    success    : {success_count}",
        "──────────────────────────────────────────────────",
        f"  Final status : {verdict_icon}  {verdict}",
        "══════════════════════════════════════════════════",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Streamlit rendering helpers (called only from _render)
# ---------------------------------------------------------------------------

def _timeline_html(active_stages: list[str], final_success: bool) -> str:
    parts: list[str] = []
    for i, stage in enumerate(_TIMELINE_NODES):
        is_active  = stage in active_stages
        is_repair  = stage == "REPAIR" and is_active
        is_final   = stage == "FINAL"  and is_active and final_success
        is_success = is_active and (is_final or (stage not in ("REPAIR", "FINAL") and final_success))

        if is_repair:
            node_cls = "tl-node tl-node-repair"
        elif is_success:
            node_cls = "tl-node tl-node-success"
        elif is_active:
            node_cls = "tl-node tl-node-active"
        else:
            node_cls = "tl-node"

        parts.append(f'<span class="{node_cls}">{stage}</span>')
        if i < len(_TIMELINE_NODES) - 1:
            sep_cls = "tl-sep tl-sep-active" if is_active else "tl-sep"
            parts.append(f'<span class="{sep_cls}">›</span>')

    return f'<div class="timeline-wrap">{"".join(parts)}</div>'


def _severity_css(sev: str) -> str:
    return {
        "critical": "sev-critical",
        "high":     "sev-high",
        "medium":   "sev-medium",
        "low":      "sev-low",
    }.get(sev.lower(), "sev-info")


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

    # ── Hero ─────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="hero-logo">⚡ &nbsp; AEONLOGIC &nbsp; COMMAND CENTER</div>'
        f'<div class="hero-sub">{PAGE_SUBTITLE}</div>'
        f'<div class="hero-divider"></div>',
        unsafe_allow_html=True,
    )

    # ── Mode badge + session info ─────────────────────────────────────────
    from aeonlogic.config.settings import get_settings
    runtime_mode = get_settings().client_mode_label
    badge_cls    = "badge-real" if runtime_mode == "REAL_QWEN_MODE" else "badge-mock"
    st.markdown(
        f'<span class="mode-badge {badge_cls}">● &nbsp;{runtime_mode}</span>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Mission input ─────────────────────────────────────────────────────
    goal = st.text_input(
        "MISSION OBJECTIVE",
        value=DEFAULT_GOAL,
        placeholder="Describe the task in plain language …",
    )
    run_clicked = st.button("▶  EXECUTE PIPELINE", type="primary", use_container_width=True)

    if run_clicked and goal.strip():
        with st.spinner("⟳  Recursive pipeline executing …"):
            run_data = _collect_pipeline_events(goal.strip())
        st.session_state["aeon_result"] = run_data

    # ── Idle state ────────────────────────────────────────────────────────
    run_data: dict[str, Any] | None = st.session_state.get("aeon_result")
    if run_data is None:
        st.markdown(
            '<div class="card card-cyan" '
            'style="text-align:center;color:#1e5070;margin-top:24px;">'
            'Enter a mission objective and press EXECUTE PIPELINE to begin.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    events      = run_data["events"]
    summary     = _build_summary(events)

    # Authoritative final status from complete state
    final_state = run_data.get("final_state", {})
    raw_fs = final_state.get("status")
    if raw_fs is not None:
        summary["final_status"] = str(raw_fs).upper()
    is_success = "SUCCESS" in summary["final_status"]

    # ── Agent timeline ────────────────────────────────────────────────────
    active_stages = _build_timeline_stages(events)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">AGENT PIPELINE</div>', unsafe_allow_html=True)
    st.markdown(_timeline_html(active_stages, is_success), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Top metrics row ───────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">RUN TELEMETRY</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("RUNTIME MODE", run_data.get("runtime_mode", "—"))
    c2.metric("MODEL",        summary["model_name"])

    risk = summary["risk_level"]
    c3.metric(
        "RISK LEVEL", risk,
        delta="⚠ HIGH RISK"  if risk == "HIGH"
              else ("LOW RISK" if risk == "LOW" else None),
        delta_color="inverse" if risk == "HIGH" else "normal",
    )
    c4.metric(
        "ATTEMPTS", summary["attempts"],
        delta="REPAIRED ✓" if summary["repaired"] else "FIRST PASS",
        delta_color="normal",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.metric("REPAIR CYCLE",   "YES" if summary["repaired"] else "NO")
    s2.metric("FINDINGS TOTAL", summary["total_findings"])
    s3.metric("EXEC BLOCKED",   "YES" if summary["execution_blocked"] else "NO")

    st.divider()

    # ── Critic findings ───────────────────────────────────────────────────
    findings = summary["findings"]
    with st.expander(f"🔍  CRITIC FINDINGS  ─  {len(findings)} issue(s) detected", expanded=bool(findings)):
        if not findings:
            st.markdown(
                '<div class="card card-green" style="color:#00cc66;">'
                '✓ &nbsp;No security findings — artifact approved on first attempt.</div>',
                unsafe_allow_html=True,
            )
        else:
            for f in findings:
                sev      = str(f["severity"]).lower()
                css      = _severity_css(sev)
                ev       = f["evidence"]
                ev_trunc = ev[:140] + "…" if len(ev) > 140 else ev
                rec      = f["recommendation"]
                rec_html = (
                    f'<div style="color:#2a5560;font-size:0.80em;margin-top:5px;">'
                    f'↳ &nbsp;{rec[:140]}</div>'
                    if rec else ""
                )
                st.markdown(
                    f'<div class="card card-red">'
                    f'<span class="{css}">[{sev.upper()}]</span>'
                    f'&nbsp;&nbsp;<strong style="color:#c0d0e0;">{f["title"]}</strong><br>'
                    f'<span style="color:#3a5560;font-size:0.82em;">{ev_trunc}</span>'
                    f'{rec_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Memory writes ─────────────────────────────────────────────────────
    lessons = summary["memory_lessons"]
    with st.expander(f"🧠  MEMORY WRITES  ─  {len(lessons)} lesson(s)", expanded=bool(lessons)):
        if not lessons:
            st.markdown(
                '<div class="card card-grey" style="color:#2a5060;">'
                'No lessons written this cycle.</div>',
                unsafe_allow_html=True,
            )
        else:
            for entry in lessons:
                ltype      = str(entry.get("type", "unknown"))
                content    = str(entry.get("content", ""))
                lid        = str(entry.get("id", ""))[:16]
                snippet    = content[:120] + "…" if len(content) > 120 else content
                card_cls   = "card-red"   if "failure" in ltype else "card-green"
                type_color = "#ee4433" if "failure" in ltype else "#00cc66"
                st.markdown(
                    f'<div class="card {card_cls}">'
                    f'<span style="color:{type_color};font-size:0.75em;">[{ltype.upper()}]</span>'
                    f'&nbsp;&nbsp;<span style="color:#1a4060;font-size:0.70em;">{lid}…</span><br>'
                    f'<span style="font-size:0.83em;color:#6090b0;">{snippet}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ── Memory backend status ─────────────────────────────────────────────
    st.markdown('<div class="section-hdr">MEMORY BACKENDS</div>', unsafe_allow_html=True)
    chroma_cls  = "mem-chip mem-chip-ok"   if lessons else "mem-chip mem-chip-mock"
    chroma_txt  = "● CHROMADB  ACTIVE"     if lessons else "● CHROMADB  MOCK FALLBACK"
    neo4j_cls   = "mem-chip mem-chip-off"
    neo4j_txt   = "○ NEO4J  NOT CONFIGURED"
    llm_cls     = "mem-chip mem-chip-ok"   if runtime_mode == "REAL_QWEN_MODE" else "mem-chip mem-chip-mock"
    llm_txt     = f"● LLM  {runtime_mode}"
    st.markdown(
        f'<div class="mem-row">'
        f'<span class="{chroma_cls}">{chroma_txt}</span>'
        f'<span class="{neo4j_cls}">{neo4j_txt}</span>'
        f'<span class="{llm_cls}">{llm_txt}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Final verdict ─────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">FINAL VERDICT</div>', unsafe_allow_html=True)
    fs = summary["final_status"]

    if is_success:
        f_count  = summary["total_findings"]
        rep_note = "&nbsp;·&nbsp; recursive self-healing triggered" if summary["repaired"] else ""
        fin_note = (
            f"{f_count} finding(s) resolved{rep_note}&nbsp;·&nbsp; "
            if f_count else ""
        ) + "APPROVED BY CRITIC + EXECUTOR"
        st.markdown(
            f'<div class="verdict-ok">'
            f'<div class="verdict-ok-title">✅ &nbsp; {fs}</div>'
            f'<div class="verdict-ok-sub">{fin_note}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="verdict-fail">'
            f'<div class="verdict-fail-title">✗ &nbsp; {fs}</div>'
            f'<div class="verdict-fail-sub">Pipeline did not reach a successful execution state.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Exportable demo summary ───────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">EXPORT · DEMO SUMMARY</div>', unsafe_allow_html=True)
    export_text = build_demo_summary_text(
        session_id   = run_data.get("session_id", "—"),
        runtime_mode = run_data.get("runtime_mode", "—"),
        summary      = summary,
    )
    st.code(export_text, language=None)

    # ── Session footer ────────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:#0e2840;font-size:0.70em;text-align:center;margin-top:16px;">'
        f'session &nbsp;·&nbsp; {run_data.get("session_id", "—")}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Entry point — only executed by `streamlit run`, never on plain import
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _render()
