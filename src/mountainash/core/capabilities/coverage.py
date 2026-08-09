"""Coverage model for the expression coverage report (spec 2026-08-07 rev 6).

PURE over explicit inputs: no registry imports, no autoload, no wall clock.
Input gathering lives in render_markdown.gather_coverage_inputs().
"""
from __future__ import annotations

import builtins
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from mountainash.core.capabilities.declarations import (
    CapabilityDeclaration,
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
    KnownGap,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND

if TYPE_CHECKING:
    from mountainash.core.capabilities.retired import RetiredFact


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
    be total. None means the op's enum class has no declaration domain yet
    (e.g. SUBSTRAIT_ARITHMETIC_WINDOW) — rendered as UNDECLARED, never an error.
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


_IMPLEMENTED_STATES: frozenset[ImplState] = frozenset(
    {ImplState.IMPLEMENTED, ImplState.IMPLEMENTED_VIA_HANDLER}
)


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
    declarations: tuple[CapabilityDeclaration, ...]

    @property
    def constrained(self) -> bool:
        return bool(self.constraints or self.residue)

    @property
    def contradiction(self) -> bool:
        return self.impl is ImplState.NOT_IMPLEMENTED and (
            self.constrained
            or bool(self.routed)
            or bool(self.refinements)
            or self.audited
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
    declarations: tuple[CapabilityDeclaration, ...]
    divergences: tuple[DivergenceFact, ...]
    gaps: tuple[KnownGap, ...]
    retired: tuple[RetiredFact, ...]
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
    declarations: tuple[CapabilityDeclaration, ...],
    divergences: tuple[DivergenceFact, ...],
    gaps: tuple[KnownGap, ...],
    retired: tuple[RetiredFact, ...],
) -> None:
    """Reject regex-legal-but-impossible dates (e.g. 2026-99-99) at ingest (spec §4.1)."""
    for f in facts:
        _check_date(f.since, f"fact {f.operation_key!r}/{f.param}/{f.backend}")
    for d in declarations:
        owner = f"declaration {d.backend}/{d.domain.value}"
        if d.evidence is not None:
            _check_date(d.evidence.probe_date, owner)
        for nf in d.facts:  # nested facts are independent input surface (spec §4.1)
            _check_date(nf.since, f"{owner} fact {nf.operation_key!r}/{nf.param}")
    for dv in divergences:
        _check_date(dv.since, f"divergence {dv.id}")
    for g in gaps:
        _check_date(g.since, f"gap {g.gap_kind.value}/{g.reason[:40]}")
    for r in retired:
        _check_date(r.since, f"retired {r.operation_key!r}")
        _check_date(r.retired_on, f"retired {r.operation_key!r}")


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
    declarations: tuple[CapabilityDeclaration, ...],
) -> None:
    """native_errors entries must be builtins (review I-4). The fact-sort key and
    the renderer both stringify via `e.__name__`, which collides silently for
    locally-defined exception classes — the report must fail loudly at ingest
    instead. Mirrors `_validate_dates` scope: top-level facts AND nested
    `d.facts` for every declaration (the nested path is an independent input
    surface, per spec §4.1)."""
    def _owner(f: CapabilityFact) -> str:
        return f"fact {f.operation_key!r}/{f.param}/{f.backend}"

    def _check(f: CapabilityFact, label: str) -> None:
        for e in f.native_errors:
            if getattr(builtins, e.__name__, None) is not e:
                raise ValueError(
                    f"native_errors entry {e.__name__!r} on {label} is not a "
                    f"builtin exception class ({e!r})"
                )

    for f in facts:
        _check(f, _owner(f))
    for d in declarations:
        owner = f"declaration {d.backend}/{d.domain.value}"
        for nf in d.facts:
            _check(nf, f"{owner} fact {nf.operation_key!r}/{nf.param}/{nf.backend}")


def _declaration_identity(d: CapabilityDeclaration) -> tuple:
    """Full probe-wave identity AND canonical sort key. probe_date alone is NOT
    unique — at ee8f5058 two narwhals/substrait/string waves share 2026-07-05
    (_EVIDENCE_STRING and _EVIDENCE_POLARS_FIXED in
    expressions/backends/capabilities/narwhals.py) — so the evidence's
    library_versions and fixtures are part of the identity."""
    if d.evidence is None:
        return (str(d.backend), d.source.value, d.domain.value, "", (), ())
    return (
        str(d.backend), d.source.value, d.domain.value,
        d.evidence.probe_date, d.evidence.library_versions, d.evidence.fixtures,
    )


def _validate_declarations(declarations: tuple[CapabilityDeclaration, ...]) -> None:
    seen: set[tuple] = set()
    for d in declarations:
        ident = _declaration_identity(d)
        if ident in seen:
            raise ValueError(f"duplicate declaration identity {ident}")
        seen.add(ident)


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
    actual: Counter[tuple[Any, CONST_BACKEND]] = Counter(
        (r.operation_key, r.backend) for r in implementations
    )
    if actual == expected:
        return
    _cell_key = lambda cell: (cell[0].name, cell[1].value)  # noqa: E731 - enum members are not orderable
    missing = sorted(
        ((op, backend)
         for (op, backend), n in (expected - actual).items()
         if n > 0),
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
        ((op, backend)
         for (op, backend), n in (actual - expected).items()
         if n > 0 and (op, backend) not in _dupe_cells),
        key=_cell_key,
    )
    parts: list[str] = []
    if missing:
        parts.append(
            "missing implementation record for "
            + ", ".join(_cell_label(op, backend) for op, backend in missing)
        )
    if extras:
        parts.append(
            "unexpected implementation record for "
            + ", ".join(_cell_label(op, backend) for op, backend in extras)
        )
    if duplicates:
        parts.append(
            "duplicate implementation record for "
            + ", ".join(_cell_label(op, backend) for op, backend in duplicates)
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
    )


def is_whole_op(fact: CapabilityFact) -> bool:
    """True for whole-op GATE facts (spec §3.5): wildcard param, value-agnostic,
    no dialect. Drives the main-doc vs scoped-doc split in renderers."""
    return (
        fact.param == WILDCARD_PARAM
        and fact.option_value is None
        and fact.value_class is None
        and fact.dialect is None
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
    params = {f.param for f in scoped if f.param != WILDCARD_PARAM}
    option_selectors = {
        (f.param, f.option_value) for f in scoped if f.option_value is not None
    }
    value_classes = {f.value_class for f in scoped if f.value_class is not None}
    dialects = {f.dialect for f in scoped if f.dialect is not None}
    return SelectorCounts(
        params=len(params),
        option_selectors=len(option_selectors),
        value_classes=len(value_classes),
        dialects=len(dialects),
    )


def build_coverage_report(
    universe: tuple[OpRecord, ...],
    facts: tuple[CapabilityFact, ...],
    declarations: tuple[CapabilityDeclaration, ...],
    divergences: tuple[DivergenceFact, ...],
    gaps: tuple[KnownGap, ...],
    retired: tuple[RetiredFact, ...],
    implementations: tuple[ImplementationRecord, ...],
) -> CoverageReport:
    _validate_backends(facts)
    _validate_dates(facts, declarations, divergences, gaps, retired)
    _validate_declarations(declarations)
    _validate_divergences(divergences)
    _validate_native_errors_builtins(facts, declarations)
    _validate_implementations(universe, implementations)

    # Canonicalize each declaration's .facts tuple by fact_sort_key at ingest
    # (review I-3). Input declarations are NEVER mutated — dataclasses.replace
    # yields fresh objects, so report.declarations and per-cell `applicable`
    # reference the canonicalized copies, not the caller's originals.
    declarations_canonical: tuple[CapabilityDeclaration, ...] = tuple(
        replace(d, facts=tuple(sorted(d.facts, key=fact_sort_key)))
        for d in declarations
    )

    # Index facts by (op member, backend); every input fact must attach to a
    # universe op — a fact for an unregistered op is an inconsistency.
    facts_by_cell: dict[tuple[Any, CONST_BACKEND], list[CapabilityFact]] = {}
    universe_keys = {r.operation_key for r in universe}
    for f in facts:
        if f.operation_key not in universe_keys:
            raise ValueError(
                f"fact references op outside the registered universe: "
                f"{f.operation_key!r} ({f.param}/{f.backend})"
            )
        facts_by_cell.setdefault(
            (f.operation_key, CONST_BACKEND(f.backend)), []
        ).append(f)

    decls_by_coord: dict[
        tuple[CONST_BACKEND, FactSource, Domain], list[CapabilityDeclaration]
    ] = {}
    for d in declarations_canonical:
        decls_by_coord.setdefault((d.backend, d.source, d.domain), []).append(d)

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
                    "routed": [], "residue": [], "refinements": [], "constraints": []
                }
                for f in cell:
                    buckets[classify_fact(f)].append(f)
                applicable = (
                    tuple(decls_by_coord.get((backend, coord[0], coord[1]), ()))
                    if coord is not None
                    else ()
                )
                constraining = buckets["constraints"] + buckets["residue"]
                if constraining and not applicable:
                    raise ValueError(
                        f"constraining fact without applicable declaration: "
                        f"{rec.operation_key!r} on {backend} (spec §5)"
                    )
                sorted_constraints = tuple(
                    sorted(buckets["constraints"], key=fact_sort_key)
                )
                whole = next(
                    (f.level for f in sorted_constraints if is_whole_op(f)), None
                )
                scoped = tuple(
                    f for f in constraining if not is_whole_op(f)
                )
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
                        refinements=tuple(
                            sorted(buckets["refinements"], key=fact_sort_key)),
                        selector_counts=_selector_counts(scoped),
                        declarations=applicable,
                    )
                )
        family_coverages.append(
            FamilyCoverage(family=family_name, audit_domain=coord, ops=tuple(ops_out))
        )

    by_impl: dict[tuple[CONST_BACKEND, ImplState], int] = {
        (b, s): 0 for b in RENDERED_BACKENDS for s in ImplState
    }
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
        declarations=tuple(sorted(declarations_canonical, key=_declaration_identity)),
        divergences=tuple(sorted(divergences, key=lambda dv: dv.id)),
        gaps=tuple(sorted(gaps, key=lambda g: (g.since, g.gap_kind.value, g.reason))),
        retired=tuple(
            sorted(
                retired,
                key=lambda r: (
                    r.retired_on, r.since, str(r.operation_key), r.param,
                    str(r.backend), r.dialect or "", r.option_value or "",
                    r.value_class.value if r.value_class else "", r.level.value,
                ),
            )
        ),
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
