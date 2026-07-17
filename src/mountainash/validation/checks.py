"""Check-type IR for the validation engine (spec §5).

`RowRule`/`ScalarRule` are the classified forms of the public
datacontracts `Rule`; `RelationRule`/`ForeignKeyRule` are declared
explicitly because they are not single expressions. `DistributionRule`
is a reserved slot (Tier B) — constructing it raises.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Union

from mountainash.validation.errors import CheckDeclarationError

if TYPE_CHECKING:
    from datetime import datetime

    from mountainash.expressions import BaseExpressionAPI
    from mountainash.relations import Relation


#: Accepted booleanizer names — the existing compile() vocabulary, verbatim.
BOOLEANIZERS = frozenset(
    {
        "t_is_true",
        "t_maybe_true",
        "t_is_false",
        "t_maybe_false",
        "t_is_unknown",
        "t_is_known",
    }
)

#: Outcomes counted as *passing* under each booleanizer verdict mapping
#: (spec §6.2 — an outcome→verdict mapping, not a compile-time collapse).
VERDICT_PASSING: dict[str, frozenset[str]] = {
    "t_is_true": frozenset({"pass"}),
    "t_maybe_true": frozenset({"pass", "unknown"}),
    "t_is_false": frozenset({"fail"}),
    "t_maybe_false": frozenset({"fail", "unknown"}),
    "t_is_unknown": frozenset({"unknown"}),
    "t_is_known": frozenset({"pass", "fail"}),
}

#: Closed severity vocabulary (spec §5 third amendment). A warning check runs
#: identically but a *failed* warning never blocks the run (spec §8).
SEVERITIES = frozenset({"blocking", "warning"})


def validate_severity(check_id: str, severity: str) -> None:
    """Reject out-of-vocabulary severities at declaration time."""
    if severity not in SEVERITIES:
        raise CheckDeclarationError(
            f"check {check_id!r}: unknown severity {severity!r}; "
            f"expected one of {sorted(SEVERITIES)}"
        )


@dataclass(frozen=True)
class RowRule:
    """Per-row boolean or ternary expression check."""

    id: str
    expr: "BaseExpressionAPI"
    mostly: float | None = None
    booleanizer: str | None = None
    severity: str = "blocking"
    error_message: str | None = None
    fields: list[str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_severity(self.id, self.severity)
        if self.booleanizer is not None and self.booleanizer not in BOOLEANIZERS:
            raise CheckDeclarationError(
                f"check {self.id!r}: unknown booleanizer {self.booleanizer!r}; "
                f"expected one of {sorted(BOOLEANIZERS)}"
            )
        if self.mostly is not None and not (0.0 < self.mostly <= 1.0):
            raise CheckDeclarationError(
                f"check {self.id!r}: mostly must be in (0, 1], got {self.mostly}"
            )
        if self.fields is not None:
            # spec §5: unique, non-empty strings; a field missing from the
            # DATA is an execution error (isolation), not a declaration error
            if not all(isinstance(f, str) and f for f in self.fields):
                raise CheckDeclarationError(
                    f"check {self.id!r}: fields must be non-empty strings, got {self.fields!r}"
                )
            if len(set(self.fields)) != len(self.fields):
                raise CheckDeclarationError(
                    f"check {self.id!r}: duplicate names in fields {self.fields!r}"
                )


@dataclass(frozen=True)
class ScalarRule:
    """Dataset-level scalar boolean expression check."""

    id: str
    expr: "BaseExpressionAPI"
    severity: str = "blocking"
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_severity(self.id, self.severity)


@dataclass(frozen=True)
class RelationRule:
    """Relation plan returning the FAILING rows; passes when empty."""

    id: str
    plan: Callable[["Relation"], "Relation"]
    severity: str = "blocking"
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_severity(self.id, self.severity)


@dataclass(frozen=True)
class ForeignKeyRule:
    """DAG-aware FK row-integrity check; compiled as a relation anti-join."""

    id: str
    child: str
    parent: str
    child_fields: list[str]
    parent_fields: list[str]
    exclude_null_child: bool = True
    severity: str = "blocking"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_severity(self.id, self.severity)
        if not self.child_fields or not self.parent_fields:
            raise CheckDeclarationError(
                f"check {self.id!r}: child_fields and parent_fields must be non-empty"
            )
        if len(self.child_fields) != len(self.parent_fields):
            raise CheckDeclarationError(
                f"check {self.id!r}: FK arity mismatch — "
                f"{len(self.child_fields)} child fields vs {len(self.parent_fields)} parent fields"
            )


class DistributionRule:
    """RESERVED (Tier B) — aggregate + statistical checks. Not implemented."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "DistributionRule is a reserved check type (Tier B); it is not implemented yet."
        )


ValidationCheck = Union[RowRule, ScalarRule, RelationRule, ForeignKeyRule, DistributionRule]

_KIND_BY_TYPE: dict[type, str] = {
    RowRule: "row",
    ScalarRule: "scalar",
    RelationRule: "relation",
    ForeignKeyRule: "foreign_key",
}


def check_kind(check: Any) -> str:
    """The check's kind string; raises for unknown types (closed-by-default)."""
    from mountainash.validation.errors import UnknownCheckTypeError

    try:
        return _KIND_BY_TYPE[type(check)]
    except KeyError:
        raise UnknownCheckTypeError(
            f"unhandled check type {type(check).__name__!r}; "
            f"expected one of {[t.__name__ for t in _KIND_BY_TYPE]}"
        ) from None


def require_as_of(context: "dict[str, Any] | None") -> "datetime":
    """The run's reference timestamp from context['as_of'] (spec §6.5).

    Type contract: a timezone-AWARE datetime (UTC recommended). Absent key,
    non-datetime, or naive datetime -> CheckDeclarationError: a bad reference
    time is a misdeclared suite, caught before any data is touched. Intended
    for ContextualRule builders — never call datetime.now() in a rule.
    """
    from datetime import datetime

    value = (context or {}).get("as_of")
    if value is None:
        raise CheckDeclarationError(
            "context['as_of'] is required by a time-relative rule but absent; "
            "pass a timezone-aware datetime in the validation context"
        )
    if not isinstance(value, datetime):
        raise CheckDeclarationError(
            f"context['as_of'] must be a datetime, got {type(value).__name__}"
        )
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise CheckDeclarationError(
            "context['as_of'] must be timezone-aware (UTC recommended); "
            "a naive datetime is ambiguous across backends and runs"
        )
    return value


# --- Rule classification (spec §6.1) -----------------------------------------

from mountainash.expressions.core.expression_nodes import (  # noqa: E402
    ExpressionNode,
    FieldReferenceNode,
    OverNode,
    ScalarFunctionNode,
    WindowFunctionNode,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (  # noqa: E402
    FKEY_MOUNTAINASH_SCALAR_AGGREGATE,
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)
from mountainash.expressions.introspect import iter_child_nodes  # noqa: E402

_AGGREGATE_KEY_TYPES = (FKEY_SUBSTRAIT_SCALAR_AGGREGATE, FKEY_MOUNTAINASH_SCALAR_AGGREGATE)


@dataclass
class _AstProfile:
    has_window: bool = False
    has_reducing_aggregate: bool = False  # aggregate NOT under window context
    has_exposed_field: bool = False       # field ref not beneath a reducing aggregate
    has_field: bool = False


def _walk(
    node: ExpressionNode,
    profile: _AstProfile,
    *,
    under_reducing_agg: bool,
    under_window: bool,
) -> None:
    if isinstance(node, (OverNode, WindowFunctionNode)):
        profile.has_window = True
        under_window = True
    elif isinstance(node, ScalarFunctionNode) and isinstance(
        node.function_key, _AGGREGATE_KEY_TYPES
    ):
        if not under_window:
            profile.has_reducing_aggregate = True
            under_reducing_agg = True
    elif isinstance(node, FieldReferenceNode):
        profile.has_field = True
        if not under_reducing_agg:
            profile.has_exposed_field = True
    for child in iter_child_nodes(node):
        _walk(child, profile, under_reducing_agg=under_reducing_agg, under_window=under_window)


def classify(rule: Any) -> "RowRule | ScalarRule":
    """Route a public Rule declaration to RowRule or ScalarRule by AST shape.

    `rule` is any object with `id` and `expr` attributes (the datacontracts
    `Rule`); `mostly`/`booleanizer`/`severity`/`error_message`/`fields`/
    `metadata` are read when present (severity defaults "blocking"). Typed
    `Any` because `validation` must not import `datacontracts` (dependency
    direction).

    An expression is scalar-valued iff it contains at least one
    aggregate-reducing node outside window context and every field reference
    lies beneath such a node. Window context re-broadcasts the reduction, so
    any OverNode/WindowFunctionNode subtree makes the expression row-valued.
    """
    profile = _AstProfile()
    _walk(rule.expr._node, profile, under_reducing_agg=False, under_window=False)

    if not profile.has_field and not profile.has_reducing_aggregate and not profile.has_window:
        raise CheckDeclarationError(
            f"rule {rule.id!r} is literal-only (no field references, no aggregate); "
            "a constant check is a declaration mistake"
        )

    scalar_valued = (
        not profile.has_window
        and profile.has_reducing_aggregate
        and not profile.has_exposed_field
    )
    mostly = getattr(rule, "mostly", None)
    metadata = dict(getattr(rule, "metadata", None) or {})

    if scalar_valued:
        # spec §6.1: mostly/booleanizer/fields are row-rule concepts; on a
        # scalar-valued expression each is a declaration error, never a
        # silent drop (a single verdict has no pass rate, no outcome mapping
        # to flip, and emits no failure rows)
        for attr, why in (
            ("mostly", "a single verdict has no pass rate"),
            ("booleanizer", "a single verdict has no outcome mapping to flip"),
            ("fields", "scalar rules emit no failure rows"),
        ):
            if getattr(rule, attr, None) is not None:
                raise CheckDeclarationError(
                    f"rule {rule.id!r}: {attr} is meaningless for a "
                    f"scalar-valued expression ({why})"
                )
        return ScalarRule(
            id=rule.id,
            expr=rule.expr,
            severity=getattr(rule, "severity", "blocking"),
            error_message=getattr(rule, "error_message", None),
            metadata=metadata,
        )

    return RowRule(
        id=rule.id,
        expr=rule.expr,
        mostly=mostly,
        booleanizer=getattr(rule, "booleanizer", None),
        severity=getattr(rule, "severity", "blocking"),
        error_message=getattr(rule, "error_message", None),
        fields=getattr(rule, "fields", None),
        metadata=metadata,
    )
