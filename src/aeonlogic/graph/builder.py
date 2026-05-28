from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from aeonlogic.agents.critic import CriticAgent
from aeonlogic.agents.dispatcher import DispatcherAgent
from aeonlogic.agents.executor import ExecutorAgent
from aeonlogic.agents.generator import GeneratorAgent
from aeonlogic.agents.memory_synthesizer import MemorySynthesizerAgent
from aeonlogic.graph.checkpoints import create_checkpointer
from aeonlogic.graph.edges import (
    after_critique,
    after_dispatch,
    after_execute,
    after_generate,
    after_synthesize,
)
from aeonlogic.graph.state import AeonState


def build_graph() -> Any:
    builder: StateGraph = StateGraph(AeonState)

    builder.add_node("dispatch", DispatcherAgent())
    builder.add_node("generate", GeneratorAgent())
    builder.add_node("critique", CriticAgent())
    builder.add_node("execute", ExecutorAgent())
    builder.add_node("synthesize", MemorySynthesizerAgent())

    builder.add_edge(START, "dispatch")
    builder.add_conditional_edges("dispatch", after_dispatch)
    builder.add_conditional_edges("generate", after_generate)
    builder.add_conditional_edges("critique", after_critique)
    builder.add_conditional_edges("execute", after_execute)   # was a fixed edge
    builder.add_conditional_edges("synthesize", after_synthesize)

    return builder.compile(checkpointer=create_checkpointer())
