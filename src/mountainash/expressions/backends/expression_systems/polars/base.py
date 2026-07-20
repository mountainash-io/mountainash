"""Polars backend base class.

Provides the base ExpressionSystem class for the Polars backend.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from mountainash.core.capabilities import CapabilityFact, CapabilityLevel, CapabilityRegistry
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class PolarsBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Polars expression system components.

    Provides common functionality and backend identification for all
    Polars protocol implementations.
    """

    BACKEND_NAME: str = "polars"

    # Capability spine declarations (spec 2026-07-05). All Polars string
    # limitations are BUILD-gated: dynamic args rejected at compile time,
    # literal args delivered as raw values by the visitor gate.
    CAPABILITIES: tuple[CapabilityFact, ...] = tuple(
        CapabilityFact(
            operation_key=op, param=param,
            level=CapabilityLevel.LITERAL_ONLY,
            backend=CONST_BACKEND.POLARS,
            message=message, workaround=workaround, since="2026-07-05",
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
            since="2026-07-05",
            probe_exempt=(
                "dynamic arg silently miscompiles: the SQL-LIKE→regex conversion "
                "runs on str(Expr), producing a pattern that matches nothing rather "
                "than raising — cannot be confirmed by an exception-based probe"
            ),
        ),
    )

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Polars backend type identifier."""
        return CONST_BACKEND.POLARS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Polars expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a pl.Expr instance.
        """
        return isinstance(expr, pl.Expr)


CapabilityRegistry.register_backend(CONST_BACKEND.POLARS, PolarsBaseExpressionSystem.CAPABILITIES)

