"""Import-safe Narwhals expression-backend capability declarations.

Migrated from ``NarwhalsBaseExpressionSystem.CAPABILITIES`` in
``mountainash.expressions.backends.expression_systems.narwhals.base``
(2026-08 capability-architecture PR). Extracted; the class still carries the
inline tuple until Task 11 rewires the class body.

Split per probe wave (per spec): family-LITERAL_ONLY STRING + STRING-character
extras, dialect-scoped polars-backed-fixed EXPR_CAPABLE refinements, DATETIME
LITERAL_ONLY, and LIST LITERAL_ONLY + materialize-residue UNSUPPORTED.
"""
from __future__ import annotations

from typing import Any

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)


_NW_STRING_MSG = (
    "Narwhals string methods require literal values, not column references, "
    "on the pandas backend. The polars-backed narwhals path supports "
    "expression arguments for several methods (declared as dialect-scoped "
    "EXPR_CAPABLE refinements below)."
)
_NW_DT_MSG = "Narwhals datetime offset operations require literal integer values"


_STRING_LITERAL_ONLY: tuple[tuple[Any, str], ...] = (
    (FK_STR.STARTS_WITH, "substring"),
    (FK_STR.ENDS_WITH, "substring"),
    (FK_STR.CONTAINS, "substring"),
    (FK_STR.REPLACE, "substring"),
    (FK_STR.REPLACE, "replacement"),
    (FK_STR.LIKE, "match"),
    (FK_STR.REGEXP_REPLACE, "pattern"),
    (FK_STR.REGEXP_REPLACE, "replacement"),
    (FK_STR.SUBSTRING, "start"),
    (FK_STR.SUBSTRING, "length"),
    (FK_STR.LPAD, "length"),
    (FK_STR.RPAD, "length"),
    (FK_STR.LEFT, "count"),
    (FK_STR.RIGHT, "count"),
    (FK_STR.TRIM, "characters"),
    (FK_STR.LTRIM, "characters"),
    (FK_STR.RTRIM, "characters"),
)
_DT_LITERAL_ONLY: tuple[tuple[Any, str], ...] = (
    (FK_DT.ADD_YEARS, "years"),
    (FK_DT.ADD_MONTHS, "months"),
    (FK_DT.ADD_DAYS, "days"),
    (FK_DT.ADD_HOURS, "hours"),
    (FK_DT.ADD_MINUTES, "minutes"),
    (FK_DT.ADD_SECONDS, "seconds"),
    (FK_DT.ADD_MILLISECONDS, "milliseconds"),
    (FK_DT.ADD_MICROSECONDS, "microseconds"),
)
# Upstream fixed these on the polars-backed narwhals path (str.contains
# at narwhals 2.19.0 et al. — ex-_NW_POLARS_FIXED test allowlist).
# narwhals-lazy is the same polars implementation, lazily evaluated.
# NOTE: LIKE is intentionally NOT listed. mountainash's `like` does a
# Python-side SQL-LIKE -> regex conversion that requires a literal pattern
# string; it cannot accept an nw.Expr on any dialect. So (LIKE, "match")
# stays family-level LITERAL_ONLY (see _STRING_LITERAL_ONLY) — the plan's
# inclusion of it here was based on a false premise about a native method.
_POLARS_BACKED_FIXED: tuple[tuple[Any, str], ...] = (
    (FK_STR.CONTAINS, "substring"),
    (FK_STR.REPLACE, "replacement"),
    (FK_STR.REGEXP_REPLACE, "replacement"),
    (FK_STR.STARTS_WITH, "substring"),
    (FK_STR.ENDS_WITH, "substring"),
)


# upstream_ref mappings preserved verbatim from the class body's dict literals.
_STRING_UPSTREAM_REF = {
    (FK_STR.STARTS_WITH, "substring"): "NW-STR-01",
    (FK_STR.ENDS_WITH, "substring"): "NW-STR-01",
    (FK_STR.CONTAINS, "substring"): "NW-STR-01",
    (FK_STR.REPLACE, "substring"): "NW-STR-03",
    (FK_STR.REPLACE, "replacement"): "NW-STR-03",
    (FK_STR.LIKE, "match"): "NW-STR-01",
    (FK_STR.REGEXP_REPLACE, "pattern"): "NW-STR-05",
    (FK_STR.REGEXP_REPLACE, "replacement"): "NW-STR-05",
    (FK_STR.SUBSTRING, "start"): "NW-STR-06",
    (FK_STR.SUBSTRING, "length"): "NW-STR-06",
    (FK_STR.LPAD, "length"): "NW-STR-06",
    (FK_STR.RPAD, "length"): "NW-STR-06",
    (FK_STR.LEFT, "count"): "NW-STR-06",
    (FK_STR.RIGHT, "count"): "NW-STR-06",
    (FK_STR.TRIM, "characters"): "NW-STR-07",
    (FK_STR.LTRIM, "characters"): "NW-STR-07",
    (FK_STR.RTRIM, "characters"): "NW-STR-07",
}
_POLARS_FIXED_UPSTREAM_REF = {
    (FK_STR.CONTAINS, "substring"): "NW-STR-01",
    (FK_STR.STARTS_WITH, "substring"): "NW-STR-01",
    (FK_STR.ENDS_WITH, "substring"): "NW-STR-01",
    (FK_STR.REPLACE, "replacement"): "NW-STR-03",
    (FK_STR.REGEXP_REPLACE, "replacement"): "NW-STR-05",
}


# String family-LITERAL_ONLY wave: 16 facts from _STRING_LITERAL_ONLY.
_NW_STRING_ITER_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=op, param=param,
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.NARWHALS,
        message=_NW_STRING_MSG,
        workaround="Use a literal string value instead of a column reference",
        since="2026-07-05",
        upstream_ref=_STRING_UPSTREAM_REF.get((op, param)),
    )
    for op, param in _STRING_LITERAL_ONLY
)


# String LPAD/RPAD `characters` facts (LITERAL_ONLY, family-level): two facts
# that were authored alongside the LIST facts in the class body, kept in the
# same order to preserve tuple equality with the legacy CAPABILITIES tuple.
_NW_STRING_CHAR_FACTS: tuple[CapabilityFact, ...] = (
    CapabilityFact(
        operation_key=FK_STR.LPAD, param="characters",
        level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.NARWHALS,
        message="Narwhals str.lpad() requires a single literal fill character, not a column expression",
        workaround="Use a literal single-character string", since="2026-07-05",
        upstream_ref="NW-STR-06",
    ),
    CapabilityFact(
        operation_key=FK_STR.RPAD, param="characters",
        level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.NARWHALS,
        message="Narwhals str.rpad() requires a single literal fill character, not a column expression",
        workaround="Use a literal single-character string", since="2026-07-05",
        upstream_ref="NW-STR-06",
    ),
)


# LIST facts: NW-LIST-01 (CONTAINS/T_CONTAINS with item LITERAL_ONLY and the
# whole-op narwhals-pandas materialize-residue UNSUPPORTED) and NW-LIST-04
# (narwhals-polars get(index) with index<0 materialize-residue UNSUPPORTED).
_NW_LIST_FACTS: tuple[CapabilityFact, ...] = (
    CapabilityFact(
        operation_key=FK_LIST.CONTAINS, param="item",
        level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.NARWHALS,
        message="Narwhals list.contains() requires a literal item argument, not a column expression",
        workaround="Use a literal value for item or use the Polars/Ibis backend.",
        since="2026-07-05",
        upstream_ref="NW-LIST-01",
        enforcement=Enforcement.GATE,
        boundary=Boundary.BUILD,
    ),
    CapabilityFact(
        operation_key=FK_LIST.CONTAINS, param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-pandas",
        message="Narwhals list operations on pandas require PyArrow-backed list columns.",
        workaround="Convert column to PyArrow list or use the Polars backend.",
        since="2026-07-05",
        upstream_ref="NW-LIST-01",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        native_errors=(TypeError,),
        probe_exempt="whole-op materialize-time storage residue (narwhals-pandas "
        "PyArrow-list requirement); enriched after the visitor, not an arg-type gate",
    ),
    CapabilityFact(
        operation_key=FK_LIST.T_CONTAINS, param="item",
        level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.NARWHALS,
        message="Narwhals list.t_contains() requires a literal item argument, not a column expression",
        workaround="Use a literal value for item or use the Polars/Ibis backend.",
        since="2026-07-05",
        upstream_ref="NW-LIST-01",
        enforcement=Enforcement.GATE,
        boundary=Boundary.BUILD,
    ),
    CapabilityFact(
        operation_key=FK_LIST.T_CONTAINS, param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED, backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-pandas",
        message="Narwhals list operations on pandas require PyArrow-backed list columns.",
        workaround="Convert column to PyArrow list or use the Polars backend.",
        since="2026-07-05",
        upstream_ref="NW-LIST-01",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        boundary=Boundary.MATERIALIZE,
        native_errors=(TypeError,),
        probe_exempt="whole-op materialize-time storage residue (narwhals-pandas "
        "PyArrow-list requirement); enriched after the visitor, not an arg-type gate",
    ),
    CapabilityFact(
        operation_key=FK_LIST.GET,
        param="index",
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-polars",
        boundary=Boundary.MATERIALIZE,
        native_errors=(ValueError,),
        condition="index < 0",
        message="narwhals list.get() (and list.last(), which calls get(-1)) rejects negative "
                "indices on the polars backend.",
        workaround="Use a non-negative index, or the polars/ibis backends.",
        upstream_ref="NW-LIST-04",
        since="2026-08-01",
        probe_exempt="value-conditioned (negative index) — not a structural param gate",
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
    ),
    # NOTE: the legacy dict's defensive (REGEX_CONTAINS, "pattern")
    # entry is intentionally NOT migrated: pattern is annotated `str`
    # in the protocol (literal-typed, kw-only), so registration
    # validation rightly rejects LITERAL_ONLY on it — the API builder
    # is the enforcement point (rejects non-str patterns at build
    # time), and a fact the gate can never consult is dead metadata.
)


# Datetime family-LITERAL_ONLY wave.
_NW_DT_ITER_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=op, param=param,
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.NARWHALS,
        message=_NW_DT_MSG,
        workaround="Use a literal integer for the offset amount",
        since="2026-07-05",
        upstream_ref="NW-DT-01",
    )
    for op, param in _DT_LITERAL_ONLY
)


# String polars-backed-fixed EXPR_CAPABLE wave: the dialect-scoped refinements
# that override the family-LITERAL_ONLY declaration for narwhals-polars and
# narwhals-lazy. Carries its own ProbeEvidence with the upstream-fix version.
_NW_POLARS_FIXED_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=op, param=param,
        level=CapabilityLevel.EXPR_CAPABLE,
        backend=CONST_BACKEND.NARWHALS, dialect=dialect,
        message="fixed upstream on the polars-backed narwhals path",
        since="2026-07-05",
        upstream_ref=_POLARS_FIXED_UPSTREAM_REF.get((op, param)),
    )
    for op, param in _POLARS_BACKED_FIXED
    for dialect in ("narwhals-polars", "narwhals-lazy")
)


# NARWHALS_EXPR_CAPABILITIES preserves the legacy tuple's element order:
# 16 string iter + 2 string chars + 5 list + 8 dt iter + 10 polars-fixed = 41.
NARWHALS_EXPR_CAPABILITIES: tuple[CapabilityFact, ...] = (
    _NW_STRING_ITER_FACTS
    + _NW_STRING_CHAR_FACTS
    + _NW_LIST_FACTS
    + _NW_DT_ITER_FACTS
    + _NW_POLARS_FIXED_FACTS
)


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)


_EVIDENCE_STRING = ProbeEvidence(
    probe_date="2026-07-05",
    library_versions=(),
    fixtures=(),
)
_EVIDENCE_DT = ProbeEvidence(
    probe_date="2026-07-05",
    library_versions=(),
    fixtures=(),
)
_EVIDENCE_LIST = ProbeEvidence(
    probe_date="2026-07-05",
    library_versions=(),
    fixtures=(),
)
_EVIDENCE_POLARS_FIXED = ProbeEvidence(
    probe_date="2026-07-05",
    library_versions=(("narwhals", "2.19.0"),),
    fixtures=(),
)


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_NW_STRING_ITER_FACTS + _NW_STRING_CHAR_FACTS,
        evidence=_EVIDENCE_STRING,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.DATETIME,
        source=FactSource.MOUNTAINASH,
        facts=_NW_DT_ITER_FACTS,
        evidence=_EVIDENCE_DT,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.LIST,
        source=FactSource.MOUNTAINASH,
        facts=_NW_LIST_FACTS,
        evidence=_EVIDENCE_LIST,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT,
        facts=_NW_POLARS_FIXED_FACTS,
        evidence=_EVIDENCE_POLARS_FIXED,
    ),
)
