from __future__ import annotations

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule

from aeonlogic.app.lifecycle import on_shutdown, on_startup
from aeonlogic.domain.finding import Finding, FindingSeverity, Verdict
from aeonlogic.domain.result import ExecutionStatus
from aeonlogic.domain.task import CycleStatus, ModelTier
from aeonlogic.graph.builder import build_graph
from aeonlogic.graph.state import AeonState
from aeonlogic.models.budgets import get_budget
from aeonlogic.utils.ids import new_ulid

app = typer.Typer(
    name="aeonlogic",
    help="AeonLogic -- Recursive Perpetual Evolution multi-agent system.",
    add_completion=False,
)
console = Console(highlight=False, width=90)

_SEV_COLOR: dict[str, str] = {
    "critical": "bold red",
    "high":     "red",
    "medium":   "yellow",
    "low":      "cyan",
    "info":     "dim",
}


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _hdr(label: str, color: str, suffix: str = "") -> None:
    """Print a stage header: [LABEL]  suffix"""
    tail = f"  {suffix}" if suffix else ""
    console.print(f"\n[{color}][{label}][/{color}]{tail}")


def _row(key: str, value: str, key_width: int = 12) -> None:
    console.print(f"  {key:<{key_width}}: {value}")


def _dim(text: str) -> None:
    console.print(f"  [dim]{text}[/dim]")


# ── Stage printers ────────────────────────────────────────────────────────────

def _show_dispatch(update: dict) -> None:
    task   = update.get("active_task")
    tier   = update.get("model_tier", ModelTier.FAST)
    budget = get_budget(tier)
    risk   = task.risk_level.upper() if task else "UNKNOWN"
    rc     = "red" if risk == "HIGH" else "yellow"

    _hdr("DISPATCH", "bold cyan")
    _row("Task",        task.description if task else "n/a")
    _row("Risk level",  f"[bold {rc}]{risk}[/bold {rc}]")
    _row("Model route", f"[bold magenta]{budget.model_name}[/bold magenta]  ({tier.upper()} tier)")


def _show_generate(update: dict, model_tier: ModelTier) -> None:
    attempt  = update.get("generation_attempt", 1)
    artifact = update.get("candidate_artifact")
    budget   = get_budget(model_tier)

    _hdr("GENERATE", "bold blue", f"attempt {attempt}")
    _row("Model",    f"[magenta]{budget.model_name}[/magenta]")
    if artifact:
        lines = len(artifact.content.splitlines())
        _row("Artifact", f"{artifact.id[:16]}...  | {lines} lines | hash {artifact.content_hash[:8]}...")


def _show_critic_rejected(findings: list[Finding]) -> None:
    _hdr("CRITIC", "bold red", f"REJECTED  |  {len(findings)} security finding(s)")
    console.print()
    for f in findings:
        sev   = f.severity.upper()
        color = _SEV_COLOR.get(f.severity, "white")
        console.print(f"  [{color}]{sev:8s}[/{color}]  {escape(f.title)}")
        if f.evidence:
            console.print(f"    Evidence   : [dim]{escape(f.evidence)}[/dim]")
        if f.recommendation:
            rec = f.recommendation if len(f.recommendation) <= 78 else f.recommendation[:75] + "..."
            console.print(f"    Fix        : {rec}")
        console.print()


def _show_critic_approved() -> None:
    _hdr("CRITIC", "bold green", "APPROVED  |  all security checks passed")


def _show_execute_blocked(update: dict, blocking_count: int, top_finding: Finding | None) -> None:
    _hdr("EXECUTE", "bold red", "BLOCKED")
    _row("Reason",   f"{blocking_count} critical/high finding(s) prevent execution")
    if top_finding:
        _row("Top issue", f"{escape(top_finding.title)}")
        _dim(f"Evidence: {escape(top_finding.evidence)}")
    console.print()
    _dim("Initiating repair cycle ...")


def _show_repair(findings: list[Finding], next_attempt: int) -> None:
    _hdr("REPAIR", "bold yellow", f"attempt {next_attempt}")
    _row("Addressing", f"{len(findings)} finding(s)")
    for f in findings:
        color = _SEV_COLOR.get(f.severity, "white")
        console.print(
            f"    [{color}]{f.severity.upper():8s}[/{color}]  {escape(f.title)}"
        )
    console.print()
    _dim("Strategy: regenerating artifact with all findings injected into context")


def _show_execute_success(update: dict) -> None:
    result = update.get("execution_result")
    ms     = result.duration_ms if result else 0
    _hdr("EXECUTE", "bold green", f"SUCCESS  |  {ms} ms")
    if result and result.summary:
        _row("Output", f"[dim]{result.summary}[/dim]")


def _show_memory(update: dict) -> None:
    lessons: list[dict[str, str]] = update.get("lessons_written", [])
    _hdr("MEMORY", "bold green", f"{len(lessons)} lesson(s) written")
    for entry in lessons:
        lid     = entry.get("id", "")[:16]
        ltype   = entry.get("type", "unknown")
        content = entry.get("content", "")
        snippet = content[:74] + "..." if len(content) > 74 else content
        tc      = "red" if "failure" in ltype else "green"
        console.print(
            f"  [{tc}]{escape(ltype):16s}[/{tc}]  "
            f"[dim]{lid}...[/dim]\n"
            f"    {snippet}"
        )


# ── CLI command ───────────────────────────────────────────────────────────────

@app.command()
def run(
    goal: str = typer.Argument(..., help="Natural-language goal for the agent pipeline."),
) -> None:
    """Run the AeonLogic recursive agent pipeline on a goal."""
    on_startup()

    session_id = new_ulid()

    console.print()
    console.print(
        Panel(
            f"[bold white]{goal}[/bold white]",
            title="[bold cyan]AeonLogic[/bold cyan]  |  Recursive Perpetual Evolution",
            subtitle=f"[dim]session {session_id}[/dim]",
            border_style="cyan",
            padding=(0, 2),
        )
    )

    graph = build_graph()

    initial_state: AeonState = {
        "session_id":        session_id,
        "cycle_id":          "",
        "generation_attempt": 0,
        "raw_goal":          goal,
        "tasks":             [],
        "active_task":       None,
        "model_tier":        ModelTier.FAST,
        "memory_context":    {},
        "memory_write_ids":  [],
        "lessons_written":   [],
        "candidate_artifact": None,
        "critic_verdict":    None,
        "critic_findings":   [],
        "execution_result":  None,
        "execution_status":  None,
        "status":            CycleStatus.RUNNING,
        "error":             None,
        "dispatcher_trace":  "",
        "generator_trace":   "",
        "critic_trace":      "",
        "executor_trace":    "",
        "synthesizer_trace": "",
    }

    config = {"configurable": {"thread_id": session_id}}

    # ── per-run tracking (outside graph state) ────────────────────────────────
    current_model_tier: ModelTier     = ModelTier.FAST
    last_rejection_findings: list[Finding] = []
    total_findings_detected: int      = 0

    for step in graph.stream(initial_state, config=config, stream_mode="updates"):
        for node_name, update in step.items():

            # ── DISPATCH ─────────────────────────────────────────────────────
            if node_name == "dispatch":
                current_model_tier = update.get("model_tier", ModelTier.FAST)
                _show_dispatch(update)

            # ── GENERATE / REPAIR ─────────────────────────────────────────────
            elif node_name == "generate":
                attempt: int = update.get("generation_attempt", 1)
                if attempt > 1:
                    # Show the REPAIR header before the generate details
                    _show_repair(last_rejection_findings, attempt)
                _show_generate(update, current_model_tier)

            # ── CRITIC ────────────────────────────────────────────────────────
            elif node_name == "critique":
                verdict   = update.get("critic_verdict")
                findings: list[Finding] = update.get("critic_findings", [])
                if verdict == Verdict.REJECTED and findings:
                    last_rejection_findings  = findings
                    total_findings_detected += len(findings)
                    _show_critic_rejected(findings)
                else:
                    last_rejection_findings = []
                    _show_critic_approved()

            # ── EXECUTE ───────────────────────────────────────────────────────
            elif node_name == "execute":
                exec_status = update.get("execution_status")
                if exec_status == ExecutionStatus.FAILURE:
                    blocking = [
                        f for f in last_rejection_findings
                        if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH)
                    ]
                    top = blocking[0] if blocking else None
                    _show_execute_blocked(update, len(blocking), top)
                else:
                    _show_execute_success(update)

            # ── MEMORY ────────────────────────────────────────────────────────
            elif node_name == "synthesize":
                _show_memory(update)

    # ── Final summary ─────────────────────────────────────────────────────────
    console.print()
    console.print(Rule(style="dim"))
    console.print()

    snapshot     = graph.get_state(config)
    final        = snapshot.values
    status: CycleStatus = final.get("status", CycleStatus.FAILED)
    attempts: int        = final.get("generation_attempt", 0)
    repaired             = attempts > 1
    sc                   = "green" if status == CycleStatus.SUCCESS else "red"

    summary = "\n".join([
        f"  Status    : [bold {sc}]{status.upper()}[/bold {sc}]",
        f"  Attempts  : {attempts}",
        f"  Repaired  : {'YES  (1 repair cycle)' if repaired else 'NO'}",
        f"  Findings  : {total_findings_detected} detected"
          + (f", {total_findings_detected} resolved" if status == CycleStatus.SUCCESS else ""),
        f"  Verdict   : {'APPROVED by Critic + Executor' if status == CycleStatus.SUCCESS else 'FAILED'}",
        f"  Session   : {session_id}",
    ])
    console.print(
        Panel(summary, title="[bold white]FINAL[/bold white]", border_style=sc, padding=(0, 1))
    )
    console.print()

    on_shutdown()
    raise typer.Exit(0 if status == CycleStatus.SUCCESS else 1)
