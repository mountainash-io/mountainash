"""Rule — a named expression for data validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mountainash.expressions import BaseExpressionAPI


@dataclass(frozen=True)
class Rule:
    """A named validation rule backed by a mountainash expression.

    The expression must evaluate to a boolean series where True = pass, False = fail.
    """

    id: str
    expr: BaseExpressionAPI
    metadata: dict[str, Any] = field(default_factory=dict)


def guarded(
    precondition: BaseExpressionAPI,
    test: BaseExpressionAPI,
) -> BaseExpressionAPI:
    """Skip test when precondition is false. Returns (~precondition) | test."""
    return precondition.not_() | test
