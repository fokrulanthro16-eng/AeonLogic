from aeonlogic.domain.task import ModelTier, RiskLevel


def route_model(risk_level: RiskLevel) -> ModelTier:
    if risk_level == RiskLevel.HIGH:
        return ModelTier.STRONG
    return ModelTier.FAST
