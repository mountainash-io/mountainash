"""Coverage model for the expression coverage report (spec 2026-08-07 rev 3).

PURE over explicit inputs: no registry imports, no autoload, no wall clock.
Input gathering lives in render_markdown.gather_coverage_inputs().
"""
from __future__ import annotations

from dataclasses import dataclass
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


class CoverageState(Enum):
    DECLARED_CLEAN = "declared_clean"
    CONSTRAINED = "constrained"
    UNDECLARED = "undeclared"


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
    state: CoverageState
    whole_op: CapabilityLevel | None
    constraints: tuple[CapabilityFact, ...]
    residue: tuple[CapabilityFact, ...]
    routed: tuple[CapabilityFact, ...]
    refinements: tuple[CapabilityFact, ...]
    selector_counts: SelectorCounts
    declarations: tuple[CapabilityDeclaration, ...]

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
    by_state: Mapping[tuple[CONST_BACKEND, CoverageState], int]
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
