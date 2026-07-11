from __future__ import annotations

from typing import Any


def resolve_step_params(
    step_name: str,
    params: dict[str, Any] | None,
    step_params: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """The effective params for one step: shared params overlaid with the
    step's own entry from ``step_params``.

    Cache keys hash the effective dict, so two instances of a
    parameterised step (same fn, different unit) carry distinct identity,
    and changing one step's entry re-keys only that step — not the whole
    pipeline.
    """
    return {**(params or {}), **((step_params or {}).get(step_name) or {})}
