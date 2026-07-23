"""Fact types for the capability spine (spec 2026-07-05, Section 1).

Three fact kinds:
- CapabilityFact  — what a backend can/cannot do per (op, param); gates dispatch.
- DivergenceFact  — same op, different result; never gates; drives xfails + docs.
- KnownGap        — mountainash-side incompleteness; drives verification guards.
"""
from __future__ import annotations

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

    def __post_init__(self) -> None:
        _validate_since(self.since, f"CapabilityFact({self.operation_key}, {self.param})")
        if self.boundary is Boundary.MATERIALIZE and not self.native_errors:
            raise ValueError(
                f"CapabilityFact({self.operation_key}, {self.param}): "
                "MATERIALIZE facts must declare native_errors"
            )
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
