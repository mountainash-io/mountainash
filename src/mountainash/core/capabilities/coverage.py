"""Coverage model for the expression coverage report (spec 2026-08-07 rev 6).

PURE over explicit inputs: no registry imports, no autoload, no wall clock.
Input gathering lives in render_markdown.gather_coverage_inputs().
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from mountainash.core.capabilities.declarations import (
    BoundSegment,
    Domain,
    FactSource,
    QualifiedInformation,
    QualifiedPolicy,
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities.gaps import InventoryGap, gap_order_key
from mountainash.core.capabilities.retired import AssertionChange
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from mountainash.core.capabilities.schema import InformationLayer, PolicyAction, PolicyConsumer


@dataclass(frozen=True)
class OpRecord:
    """One registered operation: the enum member and its enum class name."""

    operation_key: Any
    family: str


@dataclass(frozen=True)
class UnregisteredOp:
    """A key-enum member deliberately absent from the operation registries."""

    family: str
    member: str
    reason: str
    since: str  # YYYY-MM-DD


_UNREGISTERED_OPS: tuple[UnregisteredOp, ...] = (
    # AST-level composition — method body builds ScalarFunctionNode trees from
    # registered primitives (EQUAL / IS_NULL / AND / OR / NOT); the enum
    # member is not itself a ScalarFunction dispatch key.
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_SCALAR_COMPARISON",
        member="EQ_MISSING",
        reason="AST-level composition in api_bldr_ext_ma_scalar_comparison.eq_missing "
        "(composes EQUAL, IS_NULL, AND, OR) — no ScalarFunctionNode dispatch",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_SCALAR_COMPARISON",
        member="NE_MISSING",
        reason="AST-level composition in api_bldr_ext_ma_scalar_comparison.ne_missing "
        "(composes EQUAL, IS_NULL, AND, OR, NOT) — no ScalarFunctionNode dispatch",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_SCALAR_COMPARISON",
        member="IS_CLOSE",
        reason="AST-level composition in api_bldr_ext_ma_scalar_comparison.is_close "
        "(composes SUBTRACT, ABS, MULTIPLY, ADD, LTE) — no ScalarFunctionNode dispatch",
        since="2026-08-07",
    ),
    # Reserved / un-implemented members — defined on the enum but no API
    # builder, no registry def, no source-code usages anywhere in src/.
    UnregisteredOp(
        family="FKEY_MOUNTAINASH_NULL",
        member="ALWAYS_NULL",
        reason="enum member defined with a string value but no API builder method, "
        "no registry entry, and no source-code usages — reserved for a "
        "future null-literal op",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_AGGREGATE",
        member="STRING_AGG",
        reason="enum member defined but no API builder, no registry def, and no "
        "source-code usages — string aggregate not yet wired",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_AGGREGATE",
        member="SUM0",
        reason="enum member referenced only as a fixture in "
        "tests/expressions/argument_types/test_arg_types_aggregate.py — no "
        "API builder, no registry def, no source-code implementation",
        since="2026-08-07",
    ),
    # Duplicate names — the live dispatch key lives on a different family.
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_BOOLEAN",
        member="IS_TRUE",
        reason="duplicate of FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_TRUE, which is the "
        "registered dispatch key; the boolean-family member has no source-code usages",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_BOOLEAN",
        member="IS_FALSE",
        reason="duplicate of FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FALSE, which is the "
        "registered dispatch key; the boolean-family member has no source-code usages",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_SCALAR_STRING",
        member="REGEXP_CONTAINS",
        reason="duplicate of FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS (singular "
        "REGEX), which is the registered mountainash extension; the "
        "substrait-family plural member has no source-code usages",
        since="2026-08-07",
    ),
    # Special node constructors — handled by FieldReferenceNode / LiteralNode
    # rather than ScalarFunctionNode, per the comment in
    # function_mapping/definitions.py ("col and lit are handled specially ...
    # not ScalarFunctionNode. They don't need registry entries.").
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_FIELD_REFERENCE",
        member="COL",
        reason="FieldReferenceNode constructor — col() is a dedicated node type, "
        "not a ScalarFunctionNode dispatch key (per definitions.py line 95)",
        since="2026-08-07",
    ),
    UnregisteredOp(
        family="FKEY_SUBSTRAIT_LITERAL",
        member="CAST",
        reason="LiteralNode constructor — lit() is a dedicated node type, not a "
        "ScalarFunctionNode dispatch key (per definitions.py line 95); the "
        "registered type-cast op is FKEY_SUBSTRAIT_CAST.CAST",
        since="2026-08-07",
    ),
)


def declaration_domain_for(operation_key: Any) -> tuple[FactSource, Domain] | None:
    """Return the source/domain provenance for a registered operation.

    `None` means the enum family has no known declaration classification.  It
    is a report label, not a completeness or support verdict.
    """
    try:
        return (classify_source(operation_key), classify_domain(operation_key))
    except ValueError:
        return None


RENDERED_BACKENDS: tuple[CONST_BACKEND, ...] = (
    CONST_BACKEND.POLARS,
    CONST_BACKEND.NARWHALS,
    CONST_BACKEND.IBIS,
)


class ImplState(Enum):
    IMPLEMENTED = "implemented"
    IMPLEMENTED_VIA_HANDLER = "implemented_via_handler"
    NOT_IMPLEMENTED = "not_implemented"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ImplementationRecord:
    """One cell of the implementation axis (§3.6). Provenance fields
    (method_name, protocol_name) are None iff state is UNKNOWN."""

    operation_key: Any
    backend: CONST_BACKEND
    state: ImplState
    method_name: str | None
    protocol_name: str | None


@dataclass(frozen=True)
class OpCoverage:
    """One implementation cell with independently authored declarations.

    An empty declaration tuple is UNKNOWN: it says nothing about support,
    verification, audit, or the absence of a native behaviour.
    """

    op: OpRecord
    declaration_domain: tuple[FactSource, Domain] | None
    backend: CONST_BACKEND
    impl: ImplState
    impl_method: str | None
    impl_protocol: str | None
    information: tuple[QualifiedInformation, ...]
    policies: tuple[QualifiedPolicy, ...]


@dataclass(frozen=True)
class FamilyCoverage:
    family: str
    declaration_domain: tuple[FactSource, Domain] | None
    ops: tuple[OpCoverage, ...]


@dataclass(frozen=True)
class CoverageStats:
    ops_total: int
    by_impl: Mapping[tuple[CONST_BACKEND, ImplState], int]
    information_by_layer: Mapping[InformationLayer, int]
    policies_by_consumer: Mapping[PolicyConsumer, int]
    policies_by_action: Mapping[PolicyAction, int]
    information_total: int
    policies_total: int


@dataclass(frozen=True)
class CoverageReport:
    families: tuple[FamilyCoverage, ...]
    segments: tuple[BoundSegment, ...]
    information: tuple[QualifiedInformation, ...]
    policies: tuple[QualifiedPolicy, ...]
    gaps: tuple[InventoryGap, ...] | None
    changes: tuple[AssertionChange, ...]
    stats: CoverageStats


def _check_date(value: str, owner: str) -> None:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"invalid calendar date {value!r} on {owner}") from None


def _validate_segments(segments: tuple[BoundSegment, ...]) -> None:
    if type(segments) is not tuple or any(type(segment) is not BoundSegment for segment in segments):
        raise TypeError("segments require immutable BoundSegment captures")
    addresses: set[str] = set()
    for segment in segments:
        if segment.module in addresses:
            raise ValueError(f"duplicate segment address {segment.module!r}")
        addresses.add(segment.module)


def _segment_sort_key(segment: BoundSegment) -> str:
    return segment.module


def _declaration_order(record: QualifiedInformation | QualifiedPolicy) -> tuple:
    key = record.key
    local = key.local
    scope = key.scope
    selector = local.selector
    base = (
        scope.backend.value,
        type(scope.applicability).__name__,
        scope.dialect or "",
        type(local.operation).__name__,
        local.operation.name,
        local.subject,
        selector.kind,
        repr(selector.value),
        local.variant or "",
    )
    if isinstance(record, QualifiedInformation):
        return (*base, record.key.layer.value)
    return (*base, record.assertion.consumer.value, record.assertion.action.value)


def _validate_declarations(
    universe: tuple[OpRecord, ...],
    information: tuple[QualifiedInformation, ...],
    policies: tuple[QualifiedPolicy, ...],
) -> None:
    if type(information) is not tuple or any(type(record) is not QualifiedInformation for record in information):
        raise TypeError("report information requires qualified information records")
    if type(policies) is not tuple or any(type(record) is not QualifiedPolicy for record in policies):
        raise TypeError("report policies requires qualified policy records")
    universe_keys = {record.operation_key for record in universe}
    groups: tuple[tuple[str, tuple[QualifiedInformation | QualifiedPolicy, ...]], ...] = (
        ("information", information),
        ("policy", policies),
    )
    for kind, records in groups:
        seen: set[Any] = set()
        for record in records:
            if record.key in seen:
                raise ValueError(f"duplicate qualified {kind} key {record.key!r}")
            seen.add(record.key)
            if record.key.local.operation not in universe_keys:
                raise ValueError(
                    f"{kind} references op outside the registered universe: {record.key.local.operation!r}"
                )
            if record.key.scope.backend not in RENDERED_BACKENDS:
                raise ValueError(f"{kind} uses non-rendered backend {record.key.scope.backend.value!r}")
            _check_date(record.assertion.since, f"{kind} {record.key!r}")
            if kind == "policy" and record.key.scope.dialect is None:
                raise ValueError("policy requires a concrete dialect scope")


def _validate_changes(changes: tuple[AssertionChange, ...]) -> None:
    if type(changes) is not tuple or any(type(change) is not AssertionChange for change in changes):
        raise TypeError("changes require immutable AssertionChange captures")
    if len({change.change_ref for change in changes}) != len(changes):
        raise ValueError("duplicate change_ref in coverage report")


def _change_sort_key(change: AssertionChange) -> tuple[str, str, str, str]:
    ref = change.change_ref
    return (change.recorded_at, ref.repository, ref.path, ref.entry)


def _validate_implementations(
    universe: tuple[OpRecord, ...],
    implementations: tuple[ImplementationRecord, ...],
) -> None:
    """Require exactly one independent discovery result per operation/backend."""
    expected: Counter[tuple[Any, CONST_BACKEND]] = Counter(
        (record.operation_key, backend) for record in universe for backend in RENDERED_BACKENDS
    )
    actual: Counter[tuple[Any, CONST_BACKEND]] = Counter(
        (record.operation_key, record.backend) for record in implementations
    )
    if actual == expected:
        return

    def cell_key(cell: tuple[Any, CONST_BACKEND]) -> tuple[str, str]:
        return cell[0].name, cell[1].value

    missing = sorted((expected - actual).keys(), key=cell_key)
    duplicates = sorted((cell for cell, count in actual.items() if count > 1), key=cell_key)
    duplicate_cells = set(duplicates)
    extras = sorted(
        (cell for cell in (actual - expected) if cell not in duplicate_cells),
        key=cell_key,
    )
    parts: list[str] = []
    if missing:
        parts.append("missing implementation record for " + ", ".join(_cell_label(*cell) for cell in missing))
    if extras:
        parts.append("unexpected implementation record for " + ", ".join(_cell_label(*cell) for cell in extras))
    if duplicates:
        parts.append("duplicate implementation record for " + ", ".join(_cell_label(*cell) for cell in duplicates))
    raise ValueError("; ".join(parts))


def _cell_label(operation: Any, backend: CONST_BACKEND) -> str:
    return f"{type(operation).__name__}.{operation.name} × {backend.value}"


def build_coverage_report(
    universe: tuple[OpRecord, ...],
    information: tuple[QualifiedInformation, ...],
    policies: tuple[QualifiedPolicy, ...],
    segments: tuple[BoundSegment, ...],
    gaps: tuple[InventoryGap, ...] | None,
    changes: tuple[AssertionChange, ...],
    implementations: tuple[ImplementationRecord, ...],
) -> CoverageReport:
    """Build a descriptive report without turning declarations into evidence.

    Information and policies are preserved as their distinct qualified records.
    No family expansion, policy projection, or absence-derived capability claim
    is performed here.
    """
    _validate_segments(segments)
    _validate_declarations(universe, information, policies)
    _validate_changes(changes)
    _validate_implementations(universe, implementations)
    if gaps is not None and (type(gaps) is not tuple or any(type(gap) is not InventoryGap for gap in gaps)):
        raise TypeError("gaps require immutable InventoryGap captures or None")

    information = tuple(sorted(information, key=_declaration_order))
    policies = tuple(sorted(policies, key=_declaration_order))
    implementations_by_cell = {(record.operation_key, record.backend): record for record in implementations}
    families: dict[str, list[OpRecord]] = {}
    for record in universe:
        families.setdefault(record.family, []).append(record)

    family_coverages: list[FamilyCoverage] = []
    for family_name in sorted(families):
        family_operations = sorted(families[family_name], key=lambda record: record.operation_key.name)
        domain = declaration_domain_for(family_operations[0].operation_key)
        cells: list[OpCoverage] = []
        for record in family_operations:
            for backend in RENDERED_BACKENDS:
                implementation = implementations_by_cell[(record.operation_key, backend)]
                cells.append(
                    OpCoverage(
                        op=record,
                        declaration_domain=domain,
                        backend=backend,
                        impl=implementation.state,
                        impl_method=implementation.method_name,
                        impl_protocol=implementation.protocol_name,
                        information=tuple(
                            item
                            for item in information
                            if item.key.scope.backend is backend and item.key.local.operation is record.operation_key
                        ),
                        policies=tuple(
                            item
                            for item in policies
                            if item.key.scope.backend is backend and item.key.local.operation is record.operation_key
                        ),
                    )
                )
        family_coverages.append(FamilyCoverage(family_name, domain, tuple(cells)))

    by_impl = Counter((record.backend, record.state) for record in implementations)
    return CoverageReport(
        families=tuple(family_coverages),
        segments=tuple(sorted(segments, key=_segment_sort_key)),
        information=information,
        policies=policies,
        gaps=None if gaps is None else tuple(sorted(gaps, key=gap_order_key)),
        changes=tuple(sorted(changes, key=_change_sort_key)),
        stats=CoverageStats(
            ops_total=len(universe),
            by_impl={key: by_impl.get(key, 0) for key in ((b, s) for b in RENDERED_BACKENDS for s in ImplState)},
            information_by_layer=Counter(record.assertion.layer for record in information),
            policies_by_consumer=Counter(record.assertion.consumer for record in policies),
            policies_by_action=Counter(record.assertion.action for record in policies),
            information_total=len(information),
            policies_total=len(policies),
        ),
    )
