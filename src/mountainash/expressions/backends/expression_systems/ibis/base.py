"""Ibis backend base class.

Provides the base ExpressionSystem class for the Ibis backend.
"""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_DATETIME as FK_DT,
)
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class IbisBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Ibis expression system components.

    Provides common functionality and backend identification for all
    Ibis protocol implementations.
    """

    _IB_DATETIME_OFFSET_LITERAL_ONLY = KnownLimitation(
        message="Ibis datetime offset operations require literal integer values",
        native_errors=(TypeError,),
        workaround="Use a literal integer for the offset amount",
    )

    KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], KnownLimitation] = {
        (FK_DT.ADD_YEARS, "years"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MONTHS, "months"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_DAYS, "days"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_HOURS, "hours"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MINUTES, "minutes"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_SECONDS, "seconds"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MILLISECONDS, "milliseconds"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
        (FK_DT.ADD_MICROSECONDS, "microseconds"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    }

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return the Ibis backend type identifier."""
        return CONST_VISITOR_BACKENDS.IBIS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Ibis expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is an Ibis expression type.
        """
        return isinstance(expr, (ir.Column, ir.Scalar, ir.Expr))

    BACKEND_NAME: str = "ibis"

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract literal value from an Ibis expression.

        Ibis accepts expressions for most operations, but some (like
        ibis.interval) require raw Python values. This extracts literals
        while passing column references through unchanged.
        """
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr
        if isinstance(expr, ir.Scalar):
            try:
                op = expr.op()
                if hasattr(op, "value"):
                    return op.value
            except Exception:
                pass
        return expr

    def _extract_column_name(self, expr: Any) -> str | None:
        """Extract the column name from an Ibis expression.

        Handles various expression types including:
        - Concrete column references (ir.Column)
        - Deferred column references (ibis._['name'])
        - Named expressions

        Args:
            expr: An Ibis expression.

        Returns:
            The column name as a string, or None if extraction fails.
        """
        # Check for Deferred column reference (ibis._['name'])
        # Deferred expressions have a _resolver attribute
        if hasattr(expr, '_resolver'):
            resolver = expr._resolver
            # For Item resolvers (from _['name'] syntax), check indexer.value
            if hasattr(resolver, 'indexer'):
                indexer = resolver.indexer
                # Just objects wrap the actual value
                if hasattr(indexer, 'value'):
                    value = indexer.value
                    if isinstance(value, str):
                        return value
                # Direct string indexer
                elif isinstance(indexer, str):
                    return indexer

        # Try get_name() for concrete expressions (not Deferred)
        # Check that get_name returns a string, not another Deferred
        if hasattr(expr, 'get_name') and not hasattr(expr, '_resolver'):
            try:
                name = expr.get_name()
                if isinstance(name, str):
                    return name
            except Exception:
                pass

        # Try to get name from the operation (for concrete ir.Column)
        if hasattr(expr, 'op'):
            try:
                op = expr.op()
                # Field operations have a 'name' attribute
                if hasattr(op, 'name'):
                    name = op.name
                    if isinstance(name, str):
                        return name
            except Exception:
                pass

        return None
