"""Ibis backend base class.

Provides the base ExpressionSystem class for the Ibis backend.
"""

from __future__ import annotations

from typing import Any

import ibis.expr.types as ir

from mountainash.core.capabilities import CapabilityFact
from mountainash.expressions.core.constants import CONST_BACKEND
from mountainash.expressions.backends.expression_systems.base import BaseExpressionSystem
from mountainash.expressions.backends.expression_systems.ibis_capabilities import (
    IBIS_EXPR_CAPABILITIES,
)


class IbisBaseExpressionSystem(BaseExpressionSystem):
    """Base class for Ibis expression system components.

    Provides common functionality and backend identification for all
    Ibis protocol implementations.
    """

    BACKEND_NAME: str = "ibis"

    CAPABILITIES: tuple[CapabilityFact, ...] = IBIS_EXPR_CAPABILITIES

    @property
    def backend_type(self) -> CONST_BACKEND:
        """Return the Ibis backend type identifier."""
        return CONST_BACKEND.IBIS

    def is_native_expression(self, expr: Any) -> bool:
        """Check if the expression is a native Ibis expression.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is an Ibis expression type.
        """
        return isinstance(expr, (ir.Column, ir.Scalar, ir.Expr))

    def _lift_deferred(self, x: Any, y: Any) -> tuple[Any, Any]:
        """Fix the one broken operand ordering: concrete-left ∘ Deferred-right.

        ``col()`` yields a ``Deferred``; ``lit()`` a concrete value. ONLY
        ``concrete ∘ Deferred`` (``lit + col``, ``5 + col``) crashes — the
        concrete literal's arithmetic dunder raises on a right-hand ``Deferred``
        instead of deferring (upstream Ibis #11742 / IB-TYPE-01). Every other
        ordering already works and MUST be left byte-identical, so lift ONLY the
        concrete left operand and ONLY when the right is a ``Deferred``. The
        method body is unchanged and operand order is preserved (safe for
        non-commutative ops).
        """
        from ibis.common.deferred import Deferred, deferred

        if not isinstance(x, Deferred) and isinstance(y, Deferred):
            x = deferred(x)
        return x, y

    def _lift_deferred_receiver(self, receiver: Any, *args: Any) -> Any:
        """Method-call analog of ``_lift_deferred`` for ``receiver.method(*args)``.

        A concrete literal receiver's method RAISES when handed a ``Deferred``
        argument (``lit.str.contains(col)``, ``lit.repeat(col)``) — the same
        concrete-∘-Deferred asymmetry as literal-first arithmetic (item 226b /
        Ibis #11742), here on the string/method-dispatch path (item 226c). Lift
        the receiver into the Deferred world ONLY when it is concrete AND at
        least one argument is a ``Deferred`` (the sole crashing shape); every
        already-working shape (Deferred receiver, all-concrete args) is returned
        unchanged. Arguments are left untouched (order preserved). ``None`` args
        are ignored (never Deferred), so optional params pass through safely.
        """
        from ibis.common.deferred import Deferred, deferred

        if not isinstance(receiver, Deferred) and any(
            isinstance(a, Deferred) for a in args
        ):
            receiver = deferred(receiver)
        return receiver

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
