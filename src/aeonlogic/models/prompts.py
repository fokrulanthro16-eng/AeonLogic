from __future__ import annotations


def dispatch_prompt(raw_goal: str, memory_context: str = "") -> str:
    ctx = f"\nMemory context:\n{memory_context}" if memory_context else ""
    return f"Decompose and classify the following goal:{ctx}\nGoal: {raw_goal}"


def generate_prompt(
    task_description: str,
    findings: str = "",
    memory_context: str = "",
) -> str:
    retry_note = f"\nPrevious critique findings to address:\n{findings}" if findings else ""
    ctx = f"\nMemory context:\n{memory_context}" if memory_context else ""
    return (
        f"Generate a solution for the following task:{ctx}{retry_note}\n"
        f"Task: {task_description}"
    )


def critique_prompt(task_description: str, artifact_content: str) -> str:
    return (
        f"Audit the following solution against correctness, safety, and completeness.\n"
        f"Task: {task_description}\n"
        f"Solution:\n{artifact_content}"
    )


def synthesize_prompt(task_description: str, result_summary: str) -> str:
    return (
        f"Extract and synthesize key learnings from the following completed task.\n"
        f"Task: {task_description}\n"
        f"Outcome: {result_summary}"
    )
