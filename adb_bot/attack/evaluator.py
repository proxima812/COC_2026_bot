from __future__ import annotations

from dataclasses import dataclass

from adb_bot.models import WorldState


@dataclass
class BaseEvaluation:
    score: float
    acceptable: bool
    reason: str


def evaluate_current_base(state: WorldState) -> BaseEvaluation:
    if state.resources.gold is not None and state.resources.gold > 500000:
        return BaseEvaluation(score=0.7, acceptable=True, reason="Gold threshold reached")
    return BaseEvaluation(score=0.1, acceptable=False, reason="Loot information is insufficient")
