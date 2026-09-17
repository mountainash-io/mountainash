"""Coverage model for the expression coverage report (spec 2026-08-07 rev 6).

PURE over explicit inputs: no registry imports, no autoload, no wall clock.
Input gathering lives in render_markdown.gather_coverage_inputs().
"""

from __future__ import annotations

import builtins
from collections import Counter
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Mapping

from mountainash.core.capabilities.declarations import (
    BoundSegment,
    Domain,
    FactSource,
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities.schema import (
    CapabilityFact,
    CapabilityLevel,
    DivergenceFact,
    Enforcement,
    WILDCARD_PARAM,
    _clause_key,
)
from mountainash.core.constants import CONST_BACKEND

from mountainash.core.capabilities.retired import AssertionChange
from mountainash.core.capabilities.gaps import InventoryGap, gap_order_key


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


def audit_domain_for(operation_key: Any) -> tuple[FactSource, Domain] | None:
    """(source, domain) audit coordinates for an op, or None if unmapped.

    Mirrors the declaration-registration validators exactly (spec §3.2): this
    is the SAME classify_source/classify_domain the registry uses, wrapped to
    be total. None means the enum class has no declaration domain yet and is
    rendered as UNDECLARED, never as an error.
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


_IMPLEMENTED_STATES: frozenset[ImplState] = frozenset({ImplState.IMPLEMENTED, ImplState.IMPLEMENTED_VIA_HANDLER})


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
class SelectorCounts:
    params: int
    option_selectors: int
    metadata_selectors: int
    value_classes: int
    dialects: int


@dataclass(frozen=True)
class OpCoverage:
    op: OpRecord
    audit_domain: tuple[FactSource, Domain] | None
    backend: CONST_BACKEND
    impl: ImplState
    impl_method: str | None
    impl_protocol: str | None
    audited: bool
    whole_op: CapabilityLevel | None
    constraints: tuple[CapabilityFact, ...]
    residue: tuple[CapabilityFact, ...]
    routed: tuple[CapabilityFact, ...]
    refinements: tuple[CapabilityFact, ...]
    selector_counts: SelectorCounts
    segments: tuple[BoundSegment, ...]

    @property
    def constrained(self) -> bool:
        return bool(self.constraints or self.residue)

    @property
    def contradiction(self) -> bool:
        return self.impl is ImplState.NOT_IMPLEMENTED and (
            self.constrained or bool(self.routed) or bool(self.refinements) or self.audited
        )

    @property
    def all_facts(self) -> tuple[CapabilityFact, ...]:
        return self.constraints + self.residue + self.routed + self.refinements


@dataclass(frozen=True)
class FamilyCoverage:
    family: str
    audit_domain: tuple[FactSource, Domain] | None
    ops: tuple[OpCoverage, ...]


@dataclass(frozen=True)
class CoverageStats:
    ops_total: int
    by_impl: Mapping[tuple[CONST_BACKEND, ImplState], int]
    default_capable: Mapping[CONST_BACKEND, int]
    audited_clean: Mapping[CONST_BACKEND, int]
    constrained: Mapping[CONST_BACKEND, int]
    audited_unknown: Mapping[CONST_BACKEND, int]
    contradictions: int
    facts_by_level: Mapping[CapabilityLevel, int]
    facts_by_enforcement: Mapping[Enforcement, int]
    facts_by_backend: Mapping[CONST_BACKEND, int]
    facts_total: int


@dataclass(frozen=True)
class CoverageReport:
    families: tuple[FamilyCoverage, ...]
    segments: tuple[BoundSegment, ...]
    divergences: tuple[DivergenceFact, ...]
    gaps: tuple[InventoryGap, ...] | None
    changes: tuple[AssertionChange, ...]
    stats: CoverageStats


def classify_fact(fact: CapabilityFact) -> str:
    """Partition by enforcement precedence (spec §3.4). Total over legal facts."""
    if fact.enforcement is Enforcement.ROUTER_METADATA:
        return "routed"
    if fact.enforcement is Enforcement.MATERIALIZE_RESIDUE:
        return "residue"
    if fact.level is CapabilityLevel.EXPR_CAPABLE:
        return "refinements"
    return "constraints"


def _check_date(value: str, owner: str) -> None:
    if value == "":
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"invalid calendar date {value!r} on {owner}") from None


def _validate_dates(
    facts: tuple[CapabilityFact, ...],
    segments: tuple[BoundSegment, ...],
    divergences: tuple[DivergenceFact, ...],
    gaps: tuple[InventoryGap, ...] | None,
    changes: tuple[AssertionChange, ...],
) -> None:
    """Reject regex-legal-but-impossible dates at report ingest."""
    for fact in facts:
        _check_date(fact.since, f"fact {fact.operation_key!r}/{fact.param}/{fact.backend}")
    for segment in segments:
        for fact in segment.facts:
            _check_date(fact.since, f"segment {segment.module} fact {fact.operation_key!r}/{fact.param}")
    for divergence in divergences:
        _check_date(divergence.since, f"divergence {divergence.id}")
    for record in gaps or ():
        if type(record) is not InventoryGap:
            raise TypeError("report gaps require inventory-qualified records")
        gap = record.payload
        _check_date(gap.since, f"gap {record.key.inventory}/{record.key.obligation}")
    _validate_changes(changes)


def _validate_changes(changes: tuple[AssertionChange, ...]) -> None:
    if type(changes) is not tuple or any(type(change) is not AssertionChange for change in changes):
        raise TypeError("changes require immutable AssertionChange captures")
    if len({change.change_ref for change in changes}) != len(changes):
        raise ValueError("duplicate change_ref in coverage report")


def _change_sort_key(change: AssertionChange) -> tuple[str, str, str, str, str, str]:
    ref = change.change_ref
    return (
        change.recorded_at,
        ref.repository,
        ref.path,
        ref.entry,
        ref.revision or "",
        ref.artifact.hex() if ref.artifact is not None else "",
    )


def _validate_backends(facts: tuple[CapabilityFact, ...]) -> None:
    """EXECUTE-scope guard (spec §2): str backends are SERIALIZE-side and excluded
    upstream; PANDAS/PYARROW facts mean the report's scope premise broke."""
    for f in facts:
        if isinstance(f.backend, str) and not isinstance(f.backend, CONST_BACKEND):
            raise ValueError(f"SERIALIZE-target fact leaked into coverage inputs: {f!r}")
        if f.backend not in RENDERED_BACKENDS:
            raise ValueError(
                f"fact declares non-rendered backend {f.backend!r} "
                f"({f.operation_key!r}/{f.param}); revisit report scope (spec §2)"
            )


def _validate_native_errors_builtins(
    facts: tuple[CapabilityFact, ...],
    segments: tuple[BoundSegment, ...],
) -> None:
    """Reject non-builtin error captures before their names become ambiguous."""

    def _owner(fact: CapabilityFact) -> str:
        return f"fact {fact.operation_key!r}/{fact.param}/{fact.backend}"

    def _check(fact: CapabilityFact, label: str) -> None:
        for error in fact.native_errors:
            if getattr(builtins, error.__name__, None) is not error:
                raise ValueError(
                    f"native_errors entry {error.__name__!r} on {label} is not a builtin exception class ({error!r})"
                )

    for fact in facts:
        _check(fact, _owner(fact))
    for segment in segments:
        for fact in segment.facts:
            _check(fact, f"segment {segment.module} fact {fact.operation_key!r}/{fact.param}")


def _segment_sort_key(segment: BoundSegment) -> str:
    return segment.module


def _validate_segments(segments: tuple[BoundSegment, ...]) -> None:
    if type(segments) is not tuple or any(type(segment) is not BoundSegment for segment in segments):
        raise TypeError("segments require immutable BoundSegment captures")
    addresses: set[str] = set()
    for segment in segments:
        if segment.module in addresses:
            raise ValueError(f"duplicate segment address {segment.module!r}")
        addresses.add(segment.module)


def _validate_divergences(divergences: tuple[DivergenceFact, ...]) -> None:
    ids: set[str] = set()
    for dv in divergences:
        if dv.id in ids:
            raise ValueError(f"duplicate divergence id {dv.id!r}")
        ids.add(dv.id)


def _cell_label(op: Any, backend: CONST_BACKEND) -> str:
    return f"{type(op).__name__}.{op.name} × {backend.value}"


def _validate_implementations(
    universe: tuple[OpRecord, ...],
    implementations: tuple[ImplementationRecord, ...],
) -> None:
    """Multiset guard (spec §4.1): exactly one record per universe op ×
    rendered backend. Counter-based, NOT set-based, so a missing record and a
    duplicate cannot cancel silently. Reports every missing/extra/duplicate
    cell deterministically (sorted) in a single ValueError."""
    expected: Counter[tuple[Any, CONST_BACKEND]] = Counter(
        (r.operation_key, b) for r in universe for b in RENDERED_BACKENDS
    )
    actual: Counter[tuple[Any, CONST_BACKEND]] = Counter((r.operation_key, r.backend) for r in implementations)
    if actual == expected:
        return
    _cell_key = lambda cell: (cell[0].name, cell[1].value)  # noqa: E731 - enum members are not orderable
    missing = sorted(
        ((op, backend) for (op, backend), n in (expected - actual).items() if n > 0),
        key=_cell_key,
    )
    duplicates = sorted(
        ((op, backend) for (op, backend), n in actual.items() if n > 1),
        key=_cell_key,
    )
    # A cell that is both over-expected and counted >1 is already named as a
    # duplicate; excluding it from `extras` avoids the "unexpected … ; duplicate
    # …" double-diagnostic for one cell (T1 review). Error-path only.
    _dupe_cells = set(duplicates)
    extras = sorted(
        (
            (op, backend)
            for (op, backend), n in (actual - expected).items()
            if n > 0 and (op, backend) not in _dupe_cells
        ),
        key=_cell_key,
    )
    parts: list[str] = []
    if missing:
        parts.append(
            "missing implementation record for " + ", ".join(_cell_label(op, backend) for op, backend in missing)
        )
    if extras:
        parts.append(
            "unexpected implementation record for " + ", ".join(_cell_label(op, backend) for op, backend in extras)
        )
    if duplicates:
        parts.append(
            "duplicate implementation record for " + ", ".join(_cell_label(op, backend) for op, backend in duplicates)
        )
    raise ValueError("; ".join(parts))


def fact_sort_key(f: CapabilityFact) -> tuple:
    """Canonical FULL-identity sort key (spec §4.4): every semantic field
    participates, so distinct facts can never tie and bucket order is
    independent of input order. Used for model bucket order AND every renderer
    fact sequence (Task 4 imports it)."""
    return (
        f.dialect or "",
        f.param,
        f.option_value or "",
        f.value_class.value if f.value_class else "",
        f.level.value,
        f.enforcement.value,
        f.boundary.value,
        f.condition or "",
        f.since,
        f.message,
        f.workaround or "",
        f.upstream_ref or "",
        tuple(e.__name__ for e in f.native_errors),
        f.probe_exempt or "",
        tuple(_clause_key(c) for c in f.predicate.clauses) if f.predicate is not None else (),
    )


def is_whole_op(fact: CapabilityFact) -> bool:
    """True for whole-op GATE facts (spec §3.5): wildcard param, value-agnostic,
    no dialect. Drives the main-doc vs scoped-doc split in renderers."""
    return (
        fact.param == WILDCARD_PARAM and fact.option_value is None and fact.value_class is None and fact.dialect is None
    )


def is_dialect_scoped_whole_op(fact: CapabilityFact) -> bool:
    """True for wildcard-param, value-agnostic, NO value_class, but with a
    dialect set — the dialect-scoped whole-op shape (plan-review M2). The single
    helper the scoped-doc subheading and the I-2b cell predicate share."""
    return (
        fact.param == WILDCARD_PARAM
        and fact.option_value is None
        and fact.value_class is None
        and fact.dialect is not None
    )


def _selector_counts(scoped: tuple[CapabilityFact, ...]) -> SelectorCounts:
    """Exact distinct-key sets (spec §3.5)."""
    from mountainash.core.capabilities.predicates import OPERAND_TYPES_ROOT

    params = {f.param for f in scoped if f.param != WILDCARD_PARAM}
    option_selectors = {(f.param, f.option_value) for f in scoped if f.option_value is not None}
    metadata_selectors = {
        _clause_key(clause)
        for fact in scoped
        if fact.predicate is not None
        for clause in fact.predicate.clauses
        if clause.path.split(".", 1)[0] == OPERAND_TYPES_ROOT
    }
    value_classes = {f.value_class for f in scoped if f.value_class is not None}
    dialects = {f.dialect for f in scoped if f.dialect is not None}
    return SelectorCounts(
        params=len(params),
        option_selectors=len(option_selectors),
        metadata_selectors=len(metadata_selectors),
        value_classes=len(value_classes),
        dialects=len(dialects),
    )


def build_coverage_report(
    universe: tuple[OpRecord, ...],
    facts: tuple[CapabilityFact, ...],
    segments: tuple[BoundSegment, ...],
    divergences: tuple[DivergenceFact, ...],
    gaps: tuple[InventoryGap, ...] | None,
    changes: tuple[AssertionChange, ...],
    implementations: tuple[ImplementationRecord, ...],
) -> CoverageReport:
    _validate_backends(facts)
    _validate_dates(facts, segments, divergences, gaps, changes)
    _validate_segments(segments)
    _validate_divergences(divergences)
    _validate_native_errors_builtins(facts, segments)
    _validate_implementations(universe, implementations)

    # Index facts by (op member, backend); every input fact must attach to a
    # universe op — a fact for an unregistered op is an inconsistency.
    facts_by_cell: dict[tuple[Any, CONST_BACKEND], list[CapabilityFact]] = {}
    universe_keys = {r.operation_key for r in universe}
    for f in facts:
        if f.operation_key not in universe_keys:
            raise ValueError(
                f"fact references op outside the registered universe: {f.operation_key!r} ({f.param}/{f.backend})"
            )
        facts_by_cell.setdefault((f.operation_key, CONST_BACKEND(f.backend)), []).append(f)

    segments_by_coord: dict[tuple[CONST_BACKEND, FactSource, Domain], list[BoundSegment]] = {}
    for segment in segments:
        segments_by_coord.setdefault((segment.scope.backend, segment.source, segment.segment.domain), []).append(
            segment
        )

    # Implementation records joined by (operation_key, backend). Multiset
    # ingest guard has already verified exactly one record per cell.
    impl_by_cell: dict[tuple[Any, CONST_BACKEND], ImplementationRecord] = {
        (r.operation_key, r.backend): r for r in implementations
    }

    families: dict[str, list[OpRecord]] = {}
    for rec in universe:
        families.setdefault(rec.family, []).append(rec)

    family_coverages: list[FamilyCoverage] = []
    for family_name in sorted(families):
        ops_out: list[OpCoverage] = []
        coord = audit_domain_for(families[family_name][0].operation_key)
        for rec in sorted(families[family_name], key=lambda r: r.operation_key.name):
            for backend in RENDERED_BACKENDS:
                cell = facts_by_cell.get((rec.operation_key, backend), [])
                buckets: dict[str, list[CapabilityFact]] = {
                    "routed": [],
                    "residue": [],
                    "refinements": [],
                    "constraints": [],
                }
                for f in cell:
                    buckets[classify_fact(f)].append(f)
                applicable = (
                    tuple(
                        sorted(
                            segments_by_coord.get((backend, coord[0], coord[1]), ()),
                            key=_segment_sort_key,
                        )
                    )
                    if coord is not None
                    else ()
                )
                constraining = buckets["constraints"] + buckets["residue"]
                if constraining and not applicable:
                    raise ValueError(
                        f"constraining fact without applicable segment: {rec.operation_key!r} on {backend} (spec §5)"
                    )
                sorted_constraints = tuple(sorted(buckets["constraints"], key=fact_sort_key))
                whole = next((f.level for f in sorted_constraints if is_whole_op(f)), None)
                scoped = tuple(f for f in constraining if not is_whole_op(f))
                impl_record = impl_by_cell[(rec.operation_key, backend)]
                ops_out.append(
                    OpCoverage(
                        op=rec,
                        audit_domain=coord,
                        backend=backend,
                        impl=impl_record.state,
                        impl_method=impl_record.method_name,
                        impl_protocol=impl_record.protocol_name,
                        audited=bool(applicable),
                        whole_op=whole,
                        constraints=sorted_constraints,
                        residue=tuple(sorted(buckets["residue"], key=fact_sort_key)),
                        routed=tuple(sorted(buckets["routed"], key=fact_sort_key)),
                        refinements=tuple(sorted(buckets["refinements"], key=fact_sort_key)),
                        selector_counts=_selector_counts(scoped),
                        segments=applicable,
                    )
                )
        family_coverages.append(FamilyCoverage(family=family_name, audit_domain=coord, ops=tuple(ops_out)))

    by_impl: dict[tuple[CONST_BACKEND, ImplState], int] = {(b, s): 0 for b in RENDERED_BACKENDS for s in ImplState}
    default_capable: dict[CONST_BACKEND, int] = {b: 0 for b in RENDERED_BACKENDS}
    audited_clean: dict[CONST_BACKEND, int] = {b: 0 for b in RENDERED_BACKENDS}
    constrained: dict[CONST_BACKEND, int] = {b: 0 for b in RENDERED_BACKENDS}
    audited_unknown: dict[CONST_BACKEND, int] = {b: 0 for b in RENDERED_BACKENDS}
    contradictions = 0
    for fc in family_coverages:
        for oc in fc.ops:
            by_impl[(oc.backend, oc.impl)] = by_impl.get((oc.backend, oc.impl), 0) + 1
            if oc.impl is ImplState.UNKNOWN:
                if oc.audited:
                    audited_unknown[oc.backend] = audited_unknown.get(oc.backend, 0) + 1
            elif oc.impl in _IMPLEMENTED_STATES:
                if oc.constrained:
                    constrained[oc.backend] = constrained.get(oc.backend, 0) + 1
                elif oc.audited:
                    audited_clean[oc.backend] = audited_clean.get(oc.backend, 0) + 1
                else:
                    default_capable[oc.backend] = default_capable.get(oc.backend, 0) + 1
            elif oc.impl is ImplState.NOT_IMPLEMENTED:
                if oc.contradiction:
                    contradictions += 1

    by_level: dict[CapabilityLevel, int] = {}
    by_enforcement: dict[Enforcement, int] = {}
    by_backend: dict[CONST_BACKEND, int] = {}
    for f in facts:
        by_level[f.level] = by_level.get(f.level, 0) + 1
        by_enforcement[f.enforcement] = by_enforcement.get(f.enforcement, 0) + 1
        backend = CONST_BACKEND(f.backend)
        by_backend[backend] = by_backend.get(backend, 0) + 1

    return CoverageReport(
        families=tuple(family_coverages),
        segments=tuple(sorted(segments, key=_segment_sort_key)),
        divergences=tuple(sorted(divergences, key=lambda dv: dv.id)),
        gaps=None if gaps is None else tuple(sorted(gaps, key=gap_order_key)),
        changes=tuple(sorted(changes, key=_change_sort_key)),
        stats=CoverageStats(
            ops_total=len(universe),
            by_impl=by_impl,
            default_capable=default_capable,
            audited_clean=audited_clean,
            constrained=constrained,
            audited_unknown=audited_unknown,
            contradictions=contradictions,
            facts_by_level=by_level,
            facts_by_enforcement=by_enforcement,
            facts_by_backend=by_backend,
            facts_total=len(facts),
        ),
    )
