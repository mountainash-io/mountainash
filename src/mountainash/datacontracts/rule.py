"""Rule — a named expression for data validation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from mountainash.expressions import BaseExpressionAPI


@dataclass(frozen=True)
class Rule:
    """A named validation rule backed by a mountainash expression.

    The expression may be boolean or ternary. Classification to a row-level
    or scalar check happens by AST inspection (mountainash.validation.classify).
    """

    id: str
    expr: BaseExpressionAPI
    mostly: float | None = None
    booleanizer: str | None = None
    severity: str = "blocking"
    error_message: str | None = None
    fields: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        from mountainash.validation.checks import validate_severity

        validate_severity(self.id, self.severity)


@dataclass(frozen=True)
class ContextualRule:
    """A rule whose expression is built from the run context at resolve time
    (spec §9.6): per-context check values (e.g. version-selected enum sets)
    and `context["as_of"]`-anchored time rules. `RuleRegistry.resolve_detailed`
    materialises it into a concrete Rule via `build(context)`; build failures
    raise CheckDeclarationError (declaration phase, before data)."""

    id: str
    build: Callable[[dict[str, Any]], BaseExpressionAPI]
    mostly: float | None = None
    booleanizer: str | None = None
    severity: str = "blocking"
    error_message: str | None = None
    fields: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        from mountainash.validation.checks import validate_severity

        validate_severity(self.id, self.severity)


def guarded(
    precondition: BaseExpressionAPI,
    test: BaseExpressionAPI,
) -> BaseExpressionAPI:
    """Skip test when precondition is false. Returns (~precondition) | test."""
    return precondition.not_() | test
