"""Narwhals backend base class.

Provides the base ExpressionSystem class for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any

import narwhals as nw

from mountainash.core.capabilities import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
)
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
    FKEY_MOUNTAINASH_SCALAR_TERNARY as FK_MA_TERN,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


_NW_STRING_MSG = (
    "Narwhals string methods require literal values, not column references, "
    "on the pandas backend. The polars-backed narwhals path supports "
    "expression arguments for several methods (declared as dialect-scoped "
    "EXPR_CAPABLE refinements below)."
)
_NW_DT_MSG = "Narwhals datetime offset operations require literal integer values"
_NW_LIST_MSG = (
    "Narwhals (as of 2.19.0) does not accept expression arguments for "
    "list.contains on any native backend — its `item` parameter is typed "
    "`NonNestedLiteral` and rejects Expr."
)
# Native errors the list.contains(Expr) path can raise — preserved verbatim
# from the pre-spine _NW_LIST_CONTAINS_LIMITED. Enrichment coverage (verified
# empirically 2026-07-20, narwhals 2.23.0 / polars 1.42.1):
#   * narwhals-pandas (eager): list.contains(Expr) raises TypeError at the
#     is_in/is_not_in call site, caught by the _call_with_expr_support wrapper.
#   * narwhals-polars (lazy): list.contains(Expr) builds successfully and the
#     TypeError fires at materialize, AFTER the dispatch wrapper has returned.
#     When the expression is embedded in a Relation, that TypeError is caught
#     and enriched to BackendCapabilityError by the relation-collect boundary
#     (core.limitations.enrich_materialization) — this residue fact participates
#     there via boundary=MATERIALIZE. So both the eager and the relation-embedded
#     lazy paths are covered; a *standalone* compiled expression (col.compile(df),
#     user-collected) has no mountainash-controlled materialize boundary and is
#     the only un-enriched case — but that path also mis-compiles is_in-over-a-
#     column entirely (scalar equality, not list.contains); see backlog item 60.
_NW_LIST_NATIVE_ERRORS = (TypeError, AttributeError, ValueError)
_NW_LIST_PROBE_EXEMPT = (
    "MATERIALIZE-boundary, structure-conditioned: the `collection` param takes "
    "a list-typed argument, which the scalar-argument OP_SPECS probe matrix "
    "cannot model. The dynamic list-column path is non-uniform across the "
    "narwhals matrix (narwhals-polars raises TypeError lazily at materialize; "
    "narwhals-pandas raises TypeError eagerly), so no single strict-xfail probe "
    "is well-defined. The errors are enriched via native_errors (integrity "
    "guard #4) at the dispatch wrapper (eager) or the relation-collect boundary "
    "(lazy, when embedded in a Relation); the limitation is not BUILD-gateable."
)


class NarwhalsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Narwhals expression system components.

    Provides common functionality and backend identification for all
    Narwhals protocol implementations.
    """

    BACKEND_NAME: str = "narwhals"

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

    CAPABILITIES: tuple[CapabilityFact, ...] = (
        tuple(
            CapabilityFact(
                operation_key=op, param=param,
                level=CapabilityLevel.LITERAL_ONLY,
                backend=CONST_BACKEND.NARWHALS,
                message=_NW_STRING_MSG,
                workaround="Use a literal string value instead of a column reference",
                since="2026-07-05",
                upstream_ref={
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
                }.get((op, param)),
            )
            for op, param in _STRING_LITERAL_ONLY
        )
        + (
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
            # NOTE: the legacy dict's defensive (REGEX_CONTAINS, "pattern")
            # entry is intentionally NOT migrated: pattern is annotated `str`
            # in the protocol (literal-typed, kw-only), so registration
            # validation rightly rejects LITERAL_ONLY on it — the API builder
            # is the enforcement point (rejects non-str patterns at build
            # time), and a fact the gate can never consult is dead metadata.
            CapabilityFact(
                operation_key=FK_MA_TERN.T_IS_IN, param="collection",
                level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.NARWHALS,
                message=_NW_LIST_MSG,
                workaround="Use a literal collection, the polars backend, or an ibis backend",
                since="2026-07-05",
                # Conditioned: the literal path arrives as a COLLECT_VALUES
                # ExpressionNode, so this must never gate structurally —
                # see the DECIDED note below this block.
                condition="collection compiles to an expression (per-row list-column path); literal collections always work",
                boundary=Boundary.MATERIALIZE,
                native_errors=_NW_LIST_NATIVE_ERRORS,
                probe_exempt=_NW_LIST_PROBE_EXEMPT,
                upstream_ref="NW-LIST-01",
            ),
            CapabilityFact(
                operation_key=FK_MA_TERN.T_IS_NOT_IN, param="collection",
                level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.NARWHALS,
                message=_NW_LIST_MSG,
                workaround="Use a literal collection, the polars backend, or an ibis backend",
                since="2026-07-05",
                condition="collection compiles to an expression (per-row list-column path); literal collections always work",
                boundary=Boundary.MATERIALIZE,
                native_errors=_NW_LIST_NATIVE_ERRORS,
                probe_exempt=_NW_LIST_PROBE_EXEMPT,
                upstream_ref="NW-LIST-01",
            ),
        )
        + tuple(
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
        + tuple(
            CapabilityFact(
                operation_key=op, param=param,
                level=CapabilityLevel.EXPR_CAPABLE,
                backend=CONST_BACKEND.NARWHALS, dialect=dialect,
                message="fixed upstream on the polars-backed narwhals path",
                since="2026-07-05",
                upstream_ref={
                    (FK_STR.CONTAINS, "substring"): "NW-STR-01",
                    (FK_STR.STARTS_WITH, "substring"): "NW-STR-01",
                    (FK_STR.ENDS_WITH, "substring"): "NW-STR-01",
                    (FK_STR.REPLACE, "replacement"): "NW-STR-03",
                    (FK_STR.REGEXP_REPLACE, "replacement"): "NW-STR-05",
                }.get((op, param)),
            )
            for op, param in _POLARS_BACKED_FIXED
            for dialect in ("narwhals-polars", "narwhals-lazy")
        )
    )

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Narwhals backend type identifier."""
        return CONST_BACKEND.NARWHALS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Narwhals expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a nw.Expr instance.
        """
        return isinstance(expr, nw.Expr)


CapabilityRegistry.register_backend(CONST_BACKEND.NARWHALS, NarwhalsBaseExpressionSystem.CAPABILITIES)
