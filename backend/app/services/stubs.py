"""Phase 3+ orchestration placeholders."""

from __future__ import annotations

from app.core.errors import NotImplementedFeatureError


def not_implemented(feature: str, *, phase: str = "3") -> None:
    raise NotImplementedFeatureError(f"{feature} is not implemented yet (Phase {phase}).")
