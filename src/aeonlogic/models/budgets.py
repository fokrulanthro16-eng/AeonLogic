from __future__ import annotations

from pydantic import BaseModel

from aeonlogic.domain.task import ModelTier


class ModelBudget(BaseModel):
    model_name: str
    max_tokens: int
    temperature: float = 0.7


_BUDGETS: dict[ModelTier, ModelBudget] = {
    ModelTier.FAST: ModelBudget(
        model_name="qwen-turbo",
        max_tokens=4096,
        temperature=0.7,
    ),
    ModelTier.STRONG: ModelBudget(
        model_name="qwen-plus",
        max_tokens=8192,
        temperature=0.5,
    ),
}


def get_budget(tier: ModelTier) -> ModelBudget:
    return _BUDGETS[tier]
