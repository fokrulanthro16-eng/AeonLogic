from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from aeonlogic.graph.state import AeonState


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def __call__(self, state: AeonState) -> dict[str, Any]:
        """Accept the current graph state; return a partial state update."""
        ...
