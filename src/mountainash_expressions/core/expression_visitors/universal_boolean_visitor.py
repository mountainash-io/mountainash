"""Universal Boolean Expression Visitor using ExpressionSystem.

This module provides a backend-agnostic Boolean logic visitor that works
with any ExpressionSystem implementation through dependency injection.
"""

from __future__ import annotations
from typing import Any, List
from functools import reduce

from ..constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS
from ..expression_system import ExpressionSystem
from ..expression_nodes import ExpressionNode
from .expression_visitor import ExpressionVisitor

from .core.core_visitor import (
    # CastExpressionVisitor,
    CoreExpressionVisitor,
    # ColumnExpressionVisitor
)


class UniversalBooleanExpressionVisitor(
    ExpressionVisitor,
    # CastExpressionVisitor,
    CoreExpressionVisitor,
    # ColumnExpressionVisitor,
    # BooleanCollectionExpressionVisitor,
    # BooleanComparisonExpressionVisitor,
    # BooleanConstantExpressionVisitor,
    # BooleanOperatorsExpressionVisitor,
    # BooleanUnaryExpressionVisitor,
    # ArithmeticOperatorsExpressionVisitor,
    # StringOperatorsExpressionVisitor,
    # PatternOperatorsExpressionVisitor,
    # ConditionalOperatorsExpressionVisitor,
    # TemporalOperatorsExpressionVisitor
):
    """
    Universal Boolean logic visitor that works with any backend.

    This visitor is backend-agnostic and uses ExpressionSystem
    for all backend-specific operations. The same visitor instance
    can work with Narwhals, Polars, Pandas, Ibis, or any other
    backend by injecting the appropriate ExpressionSystem.

    Usage:
        from mountainash_expressions.backends.narwhals import NarwhalsExpressionSystem
        from mountainash_expressions.backends.polars import PolarsExpressionSystem

        # Works with Narwhals
        narwhals_visitor = UniversalBooleanExpressionVisitor(NarwhalsExpressionSystem())

        # Works with Polars
        polars_visitor = UniversalBooleanExpressionVisitor(PolarsExpressionSystem())
    """

    def __init__(self, expression_system: ExpressionSystem):
        """
        Initialize with an ExpressionSystem implementation.

        Args:
            expression_system: Backend-specific ExpressionSystem
        """
        self.backend = expression_system

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return the backend type from the injected ExpressionSystem."""
        return self.backend.backend_type

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        """Return Boolean logic type."""
        return CONST_LOGIC_TYPES.BOOLEAN

    # ========================================
    # Helper Method: Parameter Processing
    # ========================================

    def _process_operand(self, operand: Any) -> Any:
        """
        Process any operand through centralized type dispatch.

        This method handles ExpressionNodes, strings (column names),
        and raw values (literals), converting them to backend-native
        expressions using the ExpressionSystem.

        Args:
            operand: Can be ExpressionNode, string, raw value, or native expression

        Returns:
            Backend-native expression


        """
        # If it's an ExpressionNode, visit it recursively
        # TODO: These should alsways be expression nodes!
        if isinstance(operand, ExpressionNode):
            return operand.accept(self)

        # If it's a string, treat as column reference
        if isinstance(operand, str):
            return self.backend.col(operand)

        # Check if it's already a backend-native expression
        # This is backend-specific, so we do a simple type check
        # If it's not a basic Python type, assume it's already a native expression
        if not isinstance(operand, (int, float, bool, str, type(None), list, tuple, set)):
            return operand

        # Otherwise, treat as literal value
        return self.backend.lit(operand)

    def _process_operands(self, operands: List[Any]) -> List[Any]:
        """Process multiple operands."""
        return [self._process_operand(op) for op in operands]
