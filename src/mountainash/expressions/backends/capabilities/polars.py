"""Import-safe Polars expression-backend capability declarations (LITERAL_ONLY).

Migrated from ``PolarsBaseExpressionSystem.CAPABILITIES`` in
``mountainash.expressions.backends.expression_systems.polars.base``
(2026-08 capability-architecture PR). Extracted; the class still carries the
inline tuple until Task 11 rewires the class body.
"""
from __future__ import annotations

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


_SINCE = "2026-07-05"

# upstream_ref mapping preserved verbatim from the class body's dict literal.
_UPSTREAM_REF = {
    (FK_STR.REPLACE, "substring"): "PL-STR-01",
    (FK_STR.REGEXP_REPLACE, "pattern"): "PL-STR-02",
    (FK_STR.REPEAT, "count"): "PL-STR-03",
    (FK_STR.CENTER, "length"): "PL-STR-03",
    (FK_STR.CENTER, "character"): "PL-STR-03",
    (FK_STR.REPLACE_SLICE, "start"): "PL-STR-03",
    (FK_STR.REPLACE_SLICE, "length"): "PL-STR-03",
    (FK_STR.LPAD, "characters"): "PL-STR-03",
    (FK_STR.RPAD, "characters"): "PL-STR-03",
}


_POLARS_LITERAL_ONLY_FACTS: tuple[CapabilityFact, ...] = tuple(
    CapabilityFact(
        operation_key=op, param=param,
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.POLARS,
        message=message, workaround=workaround, since=_SINCE,
        upstream_ref=_UPSTREAM_REF.get((op, param)),
    )
    for op, param, message, workaround in [
        (FK_STR.REPLACE, "substring",
         "Polars does not support dynamic column patterns in str.replace",
         "Use a literal string substring; replacement can be a column reference"),
        (FK_STR.REGEXP_REPLACE, "pattern",
         "Polars does not support dynamic column patterns in str.replace_all/str.replace with regex",
         "Use a literal string regex pattern; replacement can be a column reference"),
        (FK_STR.REPEAT, "count",
         "Polars str.repeat() requires a literal integer count, not a column expression",
         "Use a literal integer count value"),
        (FK_STR.CENTER, "length",
         "Polars str.center() requires a literal integer length, not a column expression",
         "Use a literal integer length value"),
        (FK_STR.CENTER, "character",
         "Polars str.center() requires a single literal fill character, not a column expression",
         "Use a literal single-character string"),
        (FK_STR.REPLACE_SLICE, "start",
         "Polars str.replace_slice() requires a literal integer start, not a column expression",
         "Use a literal integer start value"),
        (FK_STR.REPLACE_SLICE, "length",
         "Polars str.replace_slice() requires a literal integer length, not a column expression",
         "Use a literal integer length value"),
        (FK_STR.REPLACE_SLICE, "replacement",
         "Polars str.replace_slice() requires a literal replacement string, not a column expression",
         "Use a literal replacement string"),
        (FK_STR.LPAD, "characters",
         "Polars str.pad_start() requires a single literal fill character, not a column expression",
         "Use a literal single-character string"),
        (FK_STR.RPAD, "characters",
         "Polars str.pad_end() requires a single literal fill character, not a column expression",
         "Use a literal single-character string"),
    ]
) + (
    # LIKE is probe-exempt: with a dynamic arg the native path does NOT
    # raise — the SQL-LIKE→regex conversion runs on str(Expr), yielding a
    # garbage pattern that silently matches nothing. An exception-based
    # probe cannot detect this (verified: dynamic-arg output [False, False]).
    CapabilityFact(
        operation_key=FK_STR.LIKE, param="match",
        level=CapabilityLevel.LITERAL_ONLY,
        backend=CONST_BACKEND.POLARS,
        message="Polars LIKE requires a literal pattern — the SQL-LIKE to regex conversion happens in Python",
        workaround="Use a literal SQL LIKE pattern string",
        since=_SINCE,
        probe_exempt=(
            "dynamic arg silently miscompiles: the SQL-LIKE→regex conversion "
            "runs on str(Expr), producing a pattern that matches nothing rather "
            "than raising — cannot be confirmed by an exception-based probe"
        ),
    ),
)


POLARS_EXPR_CAPABILITIES: tuple[CapabilityFact, ...] = _POLARS_LITERAL_ONLY_FACTS


from mountainash.core.capabilities.declarations import (  # noqa: E402
    CapabilityDeclaration,
    Domain,
    FactSource,
    ProbeEvidence,
)


_EVIDENCE = ProbeEvidence(
    probe_date="2026-07-05",
    library_versions=(),
    fixtures=("polars",),
)


DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS, domain=Domain.STRING,
        source=FactSource.SUBSTRAIT, facts=POLARS_EXPR_CAPABILITIES,
        evidence=_EVIDENCE,
    ),
)
