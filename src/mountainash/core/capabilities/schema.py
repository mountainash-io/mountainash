"""Fact types for the capability spine (spec 2026-07-05, Section 1).

Three fact kinds:
- CapabilityFact  — what a backend can/cannot do per (op, param); gates dispatch.
- DivergenceFact  — same op, different result; never gates; drives xfails + docs.
- KnownGap        — mountainash-side incompleteness; drives verification guards.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND

WILDCARD_PARAM = "*"

_SINCE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_UPSTREAM_REF_RE = re.compile(r"^[A-Z]+-[A-Z]+-\d+$")  # e.g. NW-STR-01, IB-CAST-01
_STALE_AFTER = timedelta(days=183)  # ~6 months (closed-by-default R2)


class CapabilityLevel(Enum):
    EXPR_CAPABLE = "expr_capable"   # implicit default; explicit ONLY as a dialect-scoped refinement
    LITERAL_ONLY = "literal_only"   # literal args → raw value; dynamic args → compile-time error
    POLYMORPHIC = "polymorphic"     # literal collection OR expression (ex-_raw_value_functions)
    UNSUPPORTED = "unsupported"     # op/param unavailable on this backend/dialect entirely


class Boundary(Enum):
    BUILD = "build"                 # gated at visitor dispatch
    MATERIALIZE = "materialize"     # runtime-enrichment residue (value/dtype-dependent)


class Enforcement(Enum):
    """What the system DOES about a limitation (spec 2026-07-28, backlog 66a).

    A separate axis from Boundary, which says WHEN the limitation manifests.
    The two are not orthogonal — each role admits exactly one boundary — but
    Boundary.BUILD admits two roles, so it cannot distinguish a gate from a
    router declaration on its own. The default is the strict role: a fact whose
    author did not think about enforcement gates, rather than silently not
    gating. `condition` is prose and is read by nothing that decides anything.

    enforcement           | legal boundary
    ----------------------|---------------
    GATE                  | BUILD
    ROUTER_METADATA       | BUILD
    MATERIALIZE_RESIDUE   | MATERIALIZE
    """
    GATE = "gate"                                # visitor raises before backend dispatch
    ROUTER_METADATA = "router_metadata"          # a backend router consumes this; never raises
    MATERIALIZE_RESIDUE = "materialize_residue"  # enriches a native error raised during dispatch or materialization (item 88)


class ResidueSignal(Enum):
    EXCEPTION = "exception"
    NON_NULL_TO_NULL = "non_null_to_null"

_LEGAL_BOUNDARY = {
    Enforcement.GATE: Boundary.BUILD,
    Enforcement.ROUTER_METADATA: Boundary.BUILD,
    Enforcement.MATERIALIZE_RESIDUE: Boundary.MATERIALIZE,
}


class TargetKind(Enum):
    """Forward-compat identity axis (spec 2026-07-06 serialization-targets).

    Phase 1 registers only EXECUTE identities; SERIALIZE targets (substrait,
    frictionless-pipeline) arrive with the serialization workstream's
    register_target(). Declared now so the registry schema never migrates.
    """
    EXECUTE = "execute"             # polars/ibis/narwhals — facts feed the dispatch gate
    SERIALIZE = "serialize"         # emit targets — facts feed pre-emit validation


class Fidelity(Enum):
    """How an op serializes to a SERIALIZE target (spec 2026-07-06, Section 5).

    Reserved for SERIALIZE-target facts; EXECUTE facts must leave
    CapabilityFact.fidelity as None (validated at registration).
    """
    NATIVE = "native"               # standard target vocabulary (Substrait catalog fn / standard step)
    EXTENSION = "extension"         # mountainash URN / custom step — foreign consumers need the declaration


class ValueClass(Enum):
    """Unbounded value-space a fact matches by predicate (spec 2026-07-25).

    A value-class fact gates the *entire* class on a backend; register one only
    where a representative slice agrees (see value_classes.REPRESENTATIVE_SLICES
    and the spec's backend-binary agreement rule). A class is usable for gating
    ONLY when the api-builder validates the param to exactly that predicate's
    domain (gate-domain == production-domain, spec §3.2). strftime is open
    (unvalidated) so it has NO value-class — it gates value-agnostically.
    """
    DURATION_MULTIPLIER = "duration_multiplier"   # <int> >= 2 + unit, e.g. 2d, 3h
    IANA_TIMEZONE = "iana_timezone"               # tz-database membership
    POLARS_OFFSET = "polars_offset"               # signed Polars duration string


class ClauseOp(Enum):
    """Closed predicate operator set (spec §4.2). Extending is a spec change."""
    EQ = "eq"                  # resolved value equals a scalar/enum operand
    IN = "in"                  # resolved value is a member of a frozenset
    IS_SET = "is_set"          # resolved value is non-None
    IS_NULL = "is_null"        # resolved value is None
    IS_LITERAL = "is_literal"  # root param's bound value is a LiteralNode
    MATCHES_CLASS = "matches_class"  # value_classes.matches(operand, value)


# Closed, hashable operand union (spec §4.3). ValueClass is an Enum, so EQ
# validation must exclude it explicitly.
Operand = str | int | bool | Enum | frozenset[str | int] | ValueClass | None


def _operand_key(operand: Operand) -> tuple:
    if operand is None:
        return (0,)
    if isinstance(operand, frozenset):
        return (1, tuple(sorted(str(m) for m in operand)))
    if isinstance(operand, ValueClass):
        return (2, operand.value)
    if isinstance(operand, Enum):
        return (3, type(operand).__name__, operand.value)
    return (4, operand)


def _clause_key(clause: "Clause") -> tuple:
    return (clause.path, clause.op.name, _operand_key(clause.operand))


def _validate_clause(clause: "Clause") -> None:
    if not clause.path:
        raise ValueError("Clause path must be non-empty")
    op, operand = clause.op, clause.operand
    if op in (ClauseOp.IS_SET, ClauseOp.IS_NULL, ClauseOp.IS_LITERAL):
        if operand is not None:
            raise ValueError(f"Clause {op.name} takes no operand, got {operand!r}")
    elif op is ClauseOp.EQ:
        if isinstance(operand, ValueClass) or not isinstance(operand, (str, int, bool, Enum)):
            raise ValueError(f"Clause EQ operand must be a scalar/enum, got {operand!r}")
    elif op is ClauseOp.IN:
        if not isinstance(operand, frozenset) or not all(
            isinstance(m, (str, int)) for m in operand
        ):
            raise ValueError(f"Clause IN operand must be frozenset[str|int], got {operand!r}")
    elif op is ClauseOp.MATCHES_CLASS:
        if not isinstance(operand, ValueClass):
            raise ValueError(f"Clause MATCHES_CLASS operand must be a ValueClass, got {operand!r}")
    else:
        raise ValueError(f"unknown ClauseOp {op!r}")


@dataclass(frozen=True)
class Clause:
    path: str
    op: ClauseOp
    operand: Operand = None

    def __post_init__(self) -> None:
        _validate_clause(self)


@dataclass(frozen=True)
class Predicate:
    """Immutable conjunction of clauses; canonical order, order-insensitive eq/hash."""
    clauses: tuple[Clause, ...]

    def __post_init__(self) -> None:
        clauses = self.clauses
        if not clauses:
            raise ValueError("Predicate must have at least one clause")
        if len(set(clauses)) != len(clauses):
            raise ValueError("Predicate must not contain duplicate clauses")
        object.__setattr__(self, "clauses", tuple(sorted(clauses, key=_clause_key)))


def _normalized_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, frozenset):
        normalized = [_normalized_value(item) for item in value]
        return sorted(normalized, key=lambda item: (type(item).__name__, repr(item)))
    if isinstance(value, tuple):
        return [_normalized_value(item) for item in value]
    return value


def _predicate_digest(fact: "CapabilityFact") -> str:
    clauses = (
        [
            (clause.path, clause.op.value, _normalized_value(clause.operand))
            for clause in fact.predicate.clauses
        ]
        if fact.predicate is not None
        else []
    )
    payload = {
        "option_value": _normalized_value(fact.option_value),
        "value_class": _normalized_value(fact.value_class),
        "predicate": clauses,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

def _validate_since(since: str, owner: str) -> None:
    if not _SINCE_RE.match(since):
        raise ValueError(f"{owner}: since must be YYYY-MM-DD, got {since!r}")


@dataclass(frozen=True)
class CapabilityFact:
    operation_key: Any                  # FKEY or RKEY enum member
    param: str                          # param name, or WILDCARD_PARAM
    level: CapabilityLevel
    backend: CONST_BACKEND | str        # str only for SERIALIZE families via register_target
                                        # (spec 2026-07-06; CONST_BACKEND is a StrEnum so mixed
                                        #  keying is well-behaved; register_backend rejects str)
    dialect: str | None = None          # None = whole family; set = dialect-scoped refinement
    message: str = ""
    workaround: str | None = None
    upstream_ref: str | None = None     # typed ID into registry/upstream-issues.yaml
    since: str = ""
    boundary: Boundary = Boundary.BUILD
    native_errors: tuple[type[Exception], ...] = ()
    condition: str | None = None        # human-readable value/option condition; None = unconditional
    option_value: str | None = None     # value-scoped option gate; None = value-agnostic (arg facts)
    probe_exempt: str | None = None     # reason when no probe is possible
    fidelity: Fidelity | None = None    # SERIALIZE targets only; must be None on EXECUTE facts
                                        # (validated in register_backend — spec 2026-07-06)
    value_class: ValueClass | None = None   # value-class fact; option_value MUST be None
    enforcement: Enforcement = Enforcement.GATE  # what the system does; condition is prose only
    predicate: Predicate | None = None     # compound co-value limit (§4); None = param-keyed fact
    residue_signal: ResidueSignal = ResidueSignal.EXCEPTION

    def __post_init__(self) -> None:
        if self.residue_signal is not ResidueSignal.EXCEPTION and (
            self.enforcement is not Enforcement.MATERIALIZE_RESIDUE
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "both materialization residue signals require "
                "MATERIALIZE_RESIDUE enforcement"
            )
        if (
            self.enforcement is Enforcement.MATERIALIZE_RESIDUE
            and self.residue_signal is ResidueSignal.NON_NULL_TO_NULL
            and self.native_errors
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "NON_NULL_TO_NULL residue facts must have empty native_errors"
            )
        if (
            self.enforcement is Enforcement.MATERIALIZE_RESIDUE
            and self.residue_signal is ResidueSignal.EXCEPTION
            and not self.native_errors
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "EXCEPTION residue facts must declare native_errors"
            )
        _validate_since(self.since, f"CapabilityFact({self.operation_key}, {self.param})")
        if self.level is CapabilityLevel.EXPR_CAPABLE and self.dialect is None:
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): explicit "
                "EXPR_CAPABLE is only legal as a dialect-scoped refinement "
                "(family default is already expr-capable)"
            )
        if self.upstream_ref is not None and not _UPSTREAM_REF_RE.match(self.upstream_ref):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): upstream_ref "
                f"{self.upstream_ref!r} does not match PROJ-CAT-NN grammar"
            )
        if self.value_class is not None:
            if self.option_value is not None:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a fact is "
                    "exactly one of exact-value (option_value), value-class "
                    "(value_class), or value-agnostic (neither) — not both "
                    "option_value and value_class"
                )
            if self.param == WILDCARD_PARAM:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): "
                    "value-class facts cannot use WILDCARD_PARAM"
                )
            if self.boundary is not Boundary.BUILD:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): "
                    "value-class facts must use the BUILD boundary"
                )
        if (
            self.param == WILDCARD_PARAM
            and self.enforcement is Enforcement.GATE
            and self.level is CapabilityLevel.LITERAL_ONLY
        ):
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): a GATE WILDCARD_PARAM "
                f"(whole-op) fact may be UNSUPPORTED (whole-op gate), POLYMORPHIC (whole-op "
                f"literal-or-expression args), or a dialect-scoped EXPR_CAPABLE refinement — "
                f"never LITERAL_ONLY, which at the whole-op level means every argument is "
                f"literal-only and must therefore be an option, not an argument "
                f"(arguments-vs-options.md)"
            )
        expected = _LEGAL_BOUNDARY[self.enforcement]
        if self.boundary is not expected:
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                f"{self.enforcement.name} enforcement requires the "
                f"{expected.name} boundary, got {self.boundary.name} — routing "
                "is a build-time path choice and residue is a materialize-time "
                "enrichment; see the 66a compatibility table"
            )

        if self.predicate is not None:
            if self.boundary is not Boundary.BUILD:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): predicate "
                    "facts must use the BUILD boundary (§4.5)"
                )
            if self.value_class is not None:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact cannot also use value_class"
                )
            if self.option_value is not None:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact is value-agnostic and cannot also use option_value"
                )
            if self.param == WILDCARD_PARAM:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact cannot use WILDCARD_PARAM"
                )
            if self.enforcement is not Enforcement.GATE:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact has no consuming path for non-GATE enforcement roles — "
                    "predicate facts gate"
                )
            if self.level not in (CapabilityLevel.UNSUPPORTED, CapabilityLevel.EXPR_CAPABLE):
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param}): a predicate "
                    "fact must be UNSUPPORTED (blocking) or EXPR_CAPABLE (permitting "
                    "refinement) — LITERAL_ONLY/POLYMORPHIC have no predicate enforcement path"
                )
            roots = {c.path.split(".")[0] for c in self.predicate.clauses}
            if self.param not in roots:
                raise ValueError(
                    f"CapabilityFact({self.operation_key}, {self.param!r}): param must "
                    f"be one of the predicate's clause roots {sorted(roots)}"
                )


    @property
    def fact_key(self) -> str:
        operation_type = (
            f"{type(self.operation_key).__module__}."
            f"{type(self.operation_key).__qualname__}"
        )
        operation = getattr(self.operation_key, "name", str(self.operation_key))
        backend = getattr(self.backend, "value", str(self.backend))
        dialect = self.dialect or ""
        return "|".join(
            (
                operation_type,
                str(operation),
                self.param,
                str(backend),
                dialect,
                self.boundary.value,
                self.residue_signal.value,
                _predicate_digest(self),
            )
        )


class DivergenceKind(Enum):
    SEMANTICS = "semantics"
    TYPE_INFERENCE = "type_inference"
    NAMING = "naming"
    PRECISION = "precision"
    ENGINE_LENIENCY = "engine_leniency"


@dataclass(frozen=True)
class DivergenceFact:
    id: str                             # shares the upstream ID grammar: "IB-CAST-01"
    kind: DivergenceKind
    operation_keys: tuple[Any, ...]
    backends: tuple[str, ...]           # family- or dialect-scoped names
    summary: str
    impact: str
    workaround: str | None = None
    upstream_ref: str | None = None
    since: str = ""

    def __post_init__(self) -> None:
        if not _UPSTREAM_REF_RE.match(self.id):
            raise ValueError(f"DivergenceFact: id {self.id!r} does not match PROJ-CAT-NN grammar")
        _validate_since(self.since, f"DivergenceFact({self.id})")


class GapKind(Enum):
    ASPIRATIONAL = "aspirational"
    UNTESTED_OPTION = "untested_option"
    UNTESTED_ARGUMENT = "untested_argument"
    SIGNATURE_DIVERGENCE = "signature_divergence"
    UNRESOLVED_PARAM = "unresolved_param"
    OTHER = "other"


@dataclass(frozen=True)
class KnownGap:
    gap_kind: GapKind
    reason: str
    since: str

    def __post_init__(self) -> None:
        _validate_since(self.since, f"KnownGap({self.reason!r})")

    def is_stale(self, *, today: date | None = None) -> bool:
        """True when the gap is older than ~6 months (closed-by-default R2 warning)."""
        today = today or date.today()
        return date.fromisoformat(self.since) + _STALE_AFTER < today
