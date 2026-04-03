"""Ibis backend base class.

Provides the base ExpressionSystem class for the Ibis backend.
"""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem


class IbisBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Ibis expression system components.

    Provides common functionality and backend identification for all
    Ibis protocol implementations.
    """

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

    def _extract_literal_value(self, expr: Any) -> Any:
        """Extract the literal value from an Ibis literal expression.

        Some operations (like string slice/substring) work better with raw
        Python values than Expr objects. This helper extracts the underlying
        value from ibis.literal() expressions.

        Args:
            expr: An Ibis expression or literal value.

        Returns:
            The underlying Python value if it's a literal expression,
            otherwise returns the expr unchanged.
        """
        # If it's already a raw Python value, return as-is
        if isinstance(expr, (str, int, float, bool, type(None))):
            return expr

        # If it's an Ibis Scalar, try to extract the literal value
        if isinstance(expr, ir.Scalar):
            try:
                # For Ibis literals, we can try to get the value from the op
                op = expr.op()
                if hasattr(op, "value"):
                    return op.value
            except Exception:
                pass

        # If extraction fails, return the original expr
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
