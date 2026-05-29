from __future__ import annotations

from typing import Any

from aeonlogic.agents.base import BaseAgent
from aeonlogic.domain.artifact import Artifact, ArtifactType
from aeonlogic.domain.task import CycleStatus
from aeonlogic.graph.state import AeonState
from aeonlogic.memory.retrieval import summarize_lessons
from aeonlogic.models.budgets import get_budget
from aeonlogic.models.prompts import generate_prompt
from aeonlogic.models.qwen_client import get_client


class GeneratorAgent(BaseAgent):
    name = "generator"

    def __call__(self, state: AeonState) -> dict[str, Any]:
        active_task = state["active_task"]
        if active_task is None:
            raise ValueError("GeneratorAgent: no active_task in state")

        client = get_client()
        budget = get_budget(state["model_tier"])
        attempt = state.get("generation_attempt", 0) + 1  # type: ignore[call-overload]

        findings_str = "\n".join(
            f"  - [{f.severity}] {f.title}: {f.evidence}"
            for f in state.get("critic_findings", [])  # type: ignore[call-overload]
        )

        memory_context = state.get("memory_context") or {}  # type: ignore[call-overload]
        lessons = memory_context.get("lessons", [])
        memory_hint = summarize_lessons(lessons)

        prompt = generate_prompt(
            task_description=active_task.description,
            findings=findings_str,
        )
        if memory_hint:
            prompt = f"{memory_hint}\n\n{prompt}"

        content = client.complete(budget=budget, prompt=prompt)

        artifact = Artifact(
            task_id=active_task.id,
            artifact_type=ArtifactType.ANALYSIS,
            content=content,
        )

        return {
            "candidate_artifact": artifact,
            "generation_attempt": attempt,
            "critic_verdict": None,
            "critic_findings": [],
            "status": CycleStatus.RUNNING,
            "generator_trace": (
                f"Attempt {attempt}: generated artifact {artifact.id[:8]}...  "
                f"({len(content)} chars, hash {artifact.content_hash[:8]}...)"
                + (f"  [memory: {len(lessons)} lesson(s)]" if lessons else "")
            ),
        }
