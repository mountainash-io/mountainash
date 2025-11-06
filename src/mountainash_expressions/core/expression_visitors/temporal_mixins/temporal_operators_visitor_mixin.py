from __future__ import annotations
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from ...constants import CONST_EXPRESSION_TEMPORAL_OPERATORS, CONST_LOGIC_TYPES
from .. import ExpressionVisitor
from ...expression_nodes import ExpressionNode, TemporalExpressionNode
from ...expression_parameters import ExpressionParameter


class TemporalOperatorsExpressionVisitor(ExpressionVisitor):
    """
    Mixin for handling temporal/datetime operations.

    This mixin provides the visitor methods for temporal expressions
    like date/time extraction (YEAR, MONTH, DAY, etc.) and date arithmetic
    (ADD_DAYS, DIFF_DAYS, etc.).

    Temporal operations are universal (no logic prefix) as they work the
    same way regardless of Boolean/Ternary logic system.
    """

    @property
    def logic_type(self) -> CONST_LOGIC_TYPES:
        return CONST_LOGIC_TYPES.BOOLEAN

    # ===============
    # Operations Maps
    # ===============

    @property
    def temporal_ops(self) -> Dict[str, Callable]:
        """Map temporal operators to their implementation methods."""
        return {
            # Date/Time Extraction
            CONST_EXPRESSION_TEMPORAL_OPERATORS.YEAR:       self._temporal_year,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.MONTH:      self._temporal_month,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.DAY:        self._temporal_day,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.HOUR:       self._temporal_hour,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.MINUTE:     self._temporal_minute,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.SECOND:     self._temporal_second,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.WEEKDAY:    self._temporal_weekday,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.WEEK:       self._temporal_week,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.QUARTER:    self._temporal_quarter,
            # Date Arithmetic
            CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_DAYS:   self._temporal_add_days,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_MONTHS: self._temporal_add_months,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.ADD_YEARS:  self._temporal_add_years,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.DIFF_DAYS:  self._temporal_diff_days,
        }

    # ===============
    # Expression Visitor Methods
    # ===============

    def visit_temporal_expression(self, expression_node: TemporalExpressionNode) -> Any:
        """
        Visit a temporal expression node.

        Args:
            expression_node: The temporal expression to visit

        Returns:
            Backend-specific temporal expression
        """
        if expression_node.operator not in self.temporal_ops:
            raise ValueError(f"Unsupported temporal operator: {expression_node.operator}")

        # Resolve the operand (the datetime column/expression)
        operand_param = ExpressionParameter(expression_node.operand)
        operand_resolved = operand_param.resolve_to_expression_node()

        # Check if this is an extraction operation (no args) or arithmetic (has args)
        if expression_node.operator in [
            CONST_EXPRESSION_TEMPORAL_OPERATORS.YEAR,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.MONTH,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.DAY,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.HOUR,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.MINUTE,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.SECOND,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.WEEKDAY,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.WEEK,
            CONST_EXPRESSION_TEMPORAL_OPERATORS.QUARTER,
        ]:
            # Extraction operation - just operand
            return self._process_temporal_extraction(expression_node.operator, operand_resolved)
        else:
            # Arithmetic operation - operand + args
            # Resolve additional arguments
            args_resolved = []
            for arg in expression_node.args:
                arg_param = ExpressionParameter(arg)
                args_resolved.append(arg_param.resolve_to_expression_node())

            return self._process_temporal_arithmetic(
                expression_node.operator,
                operand_resolved,
                args_resolved
            )

    def _process_temporal_extraction(self, operator: str, operand: ExpressionNode) -> Any:
        """
        Process a temporal extraction operation (YEAR, MONTH, DAY, etc.).

        Args:
            operator: Temporal operator
            operand: Datetime expression to extract from

        Returns:
            Backend-specific extraction expression
        """
        op_func = self.temporal_ops[operator]
        return op_func(operand)

    def _process_temporal_arithmetic(
        self,
        operator: str,
        operand: ExpressionNode,
        args: List[ExpressionNode]
    ) -> Any:
        """
        Process a temporal arithmetic operation (ADD_DAYS, DIFF_DAYS, etc.).

        Args:
            operator: Temporal operator
            operand: Datetime expression to operate on
            args: Additional arguments (days, months, other_date, etc.)

        Returns:
            Backend-specific arithmetic expression
        """
        op_func = self.temporal_ops[operator]
        return op_func(operand, *args)

    # ===============
    # Abstract Methods - Date/Time Extraction
    # ===============

    @abstractmethod
    def _temporal_year(self, operand: ExpressionNode) -> Any:
        """Extract year from datetime."""
        pass

    @abstractmethod
    def _temporal_month(self, operand: ExpressionNode) -> Any:
        """Extract month from datetime."""
        pass

    @abstractmethod
    def _temporal_day(self, operand: ExpressionNode) -> Any:
        """Extract day from datetime."""
        pass

    @abstractmethod
    def _temporal_hour(self, operand: ExpressionNode) -> Any:
        """Extract hour from datetime."""
        pass

    @abstractmethod
    def _temporal_minute(self, operand: ExpressionNode) -> Any:
        """Extract minute from datetime."""
        pass

    @abstractmethod
    def _temporal_second(self, operand: ExpressionNode) -> Any:
        """Extract second from datetime."""
        pass

    @abstractmethod
    def _temporal_weekday(self, operand: ExpressionNode) -> Any:
        """Extract day of week from datetime."""
        pass

    @abstractmethod
    def _temporal_week(self, operand: ExpressionNode) -> Any:
        """Extract week number from datetime."""
        pass

    @abstractmethod
    def _temporal_quarter(self, operand: ExpressionNode) -> Any:
        """Extract quarter from datetime."""
        pass

    # ===============
    # Abstract Methods - Date Arithmetic
    # ===============

    @abstractmethod
    def _temporal_add_days(self, operand: ExpressionNode, days: ExpressionNode) -> Any:
        """Add days to a date."""
        pass

    @abstractmethod
    def _temporal_add_months(self, operand: ExpressionNode, months: ExpressionNode) -> Any:
        """Add months to a date."""
        pass

    @abstractmethod
    def _temporal_add_years(self, operand: ExpressionNode, years: ExpressionNode) -> Any:
        """Add years to a date."""
        pass

    @abstractmethod
    def _temporal_diff_days(self, operand: ExpressionNode, other_date: ExpressionNode) -> Any:
        """Calculate difference in days between two dates."""
        pass
