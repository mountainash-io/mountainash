"""Pure helpers for structural operation capability declarations."""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel, Clause, ClauseOp, Predicate
from mountainash.core.constants import CONST_BACKEND

SINCE = "2026-08-24"


def option_predicate(**values: str) -> Predicate:
    return Predicate(tuple(Clause(name, ClauseOp.EQ, value) for name, value in values.items()))


def unsupported(
    operation_key: object,
    backend: CONST_BACKEND,
    dialect: str | None,
    *,
    message: str,
    option: str | None = None,
    value: str | None = None,
    **conditions: str,
) -> CapabilityFact:
    if conditions:
        param = option or next(iter(conditions))
        if value is None:
            value = conditions.get("failure_behavior")
    else:
        param = option or "*"
    return CapabilityFact(
        operation_key=operation_key,
        param=param,
        option_value=value,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=message,
        since=SINCE,
        predicate=option_predicate(**conditions) if conditions else None,
    )
