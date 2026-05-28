from __future__ import annotations

from pydantic import BaseModel

from aeonlogic.domain.task import ModelTier


class ModelBudget(BaseModel):
    model_name: str
    max_tokens: int
    temperature: float = 0.7


def get_budget(tier: ModelTier) -> ModelBudget:
    """
    Return a ModelBudget for the given tier.
    Model names are read from settings so they can be overridden via env vars
    (QWEN_FAST_MODEL / QWEN_DEEP_MODEL) without code changes.
    """
    from aeonlogic.config.settings import get_settings

    s = get_settings()
    if tier == ModelTier.STRONG:
        return ModelBudget(model_name=s.qwen_deep_model,  max_tokens=8192, temperature=0.5)
    return ModelBudget(model_name=s.qwen_fast_model, max_tokens=4096, temperature=0.7)
