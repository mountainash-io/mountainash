from __future__ import annotations


from typing import Callable, TYPE_CHECKING, Dict
from enum import Enum




from ..expression_parameters import ExpressionParameter
from .expression_visitor import ExpressionVisitor


from ..protocols import ENUM_TEMPORAL_OPERATORS, TemporalVisitorProtocol

from ...types import SupportedExpressions


if TYPE_CHECKING:
    from ..expression_nodes import (
    TemporalExtractExpressionNode,
    TemporalDiffExpressionNode,
    TemporalAdditionExpressionNode,
    TemporalTruncateExpressionNode,
    TemporalOffsetExpressionNode,
    TemporalSnapshotExpressionNode,
    SupportedTemporalExpressionNodeTypes
)


class TemporalExpressionVisitor(ExpressionVisitor,
                            TemporalVisitorProtocol#, LiteralOperatorProtocol,
):

    # ========================================
    # Temporal Comparison Operations
    # ========================================


    @property
    def _temporal_ops(self) -> Dict[Enum, Callable]:
        return {
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_YEAR: self.dt_year,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_MONTH: self.dt_month,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_DAY: self.dt_day,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_HOUR: self.dt_hour,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_MINUTE: self.dt_minute,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_SECOND: self.dt_second,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_WEEKDAY: self.dt_weekday,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_WEEK: self.dt_week,
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_QUARTER: self.dt_quarter,

            ENUM_TEMPORAL_OPERATORS.DT_DIFF_YEARS: self.dt_diff_years,
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_MONTHS: self.dt_diff_months,
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_DAYS: self.dt_diff_days,
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_HOURS: self.dt_diff_hours,
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_MINUTES: self.dt_diff_minutes,
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_SECONDS: self.dt_diff_seconds,
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_MILLISECONDS: self.dt_diff_milliseconds,

            ENUM_TEMPORAL_OPERATORS.DT_ADD_DAYS: self.dt_add_days,
            ENUM_TEMPORAL_OPERATORS.DT_ADD_HOURS: self.dt_add_hours,
            ENUM_TEMPORAL_OPERATORS.DT_ADD_MINUTES: self.dt_add_minutes,
            ENUM_TEMPORAL_OPERATORS.DT_ADD_SECONDS: self.dt_add_seconds,
            ENUM_TEMPORAL_OPERATORS.DT_ADD_MONTHS: self.dt_add_months,
            ENUM_TEMPORAL_OPERATORS.DT_ADD_YEARS: self.dt_add_years,

            ENUM_TEMPORAL_OPERATORS.DT_TRUNCATE: self.dt_truncate,

            ENUM_TEMPORAL_OPERATORS.DT_OFFSET_BY: self.dt_offset_by,

            ENUM_TEMPORAL_OPERATORS.DT_TODAY: self.dt_today,
            ENUM_TEMPORAL_OPERATORS.DT_NOW: self.dt_now,

        }



    # ========================================
    # Boolean Comparison Operations
    # ========================================


    def visit_expression_node(self, node: SupportedTemporalExpressionNodeTypes) -> SupportedExpressions:
        op_func = self._get_expr_op(self._temporal_ops, node)
        return op_func(node)


    # ========================================
    # Temporal Operations - Extraction
    # ========================================


    def dt_year(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_year(operand_expr)

    def dt_month(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_month(operand_expr)

    def dt_day(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_day(operand_expr)

    def dt_hour(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_hour(operand_expr)

    def dt_minute(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_minute(operand_expr)

    def dt_second(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_second(operand_expr)

    def dt_weekday(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_weekday(operand_expr)

    def dt_week(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_week(operand_expr)

    def dt_quarter(self, node: TemporalExtractExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        return self.backend.dt_quarter(operand_expr)

    # ========================================
    # Temporal Operations - Difference
    # ========================================

    def dt_diff_years(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_years(left_expr, right_expr)

    def dt_diff_months(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_months(left_expr, right_expr)

    def dt_diff_days(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_days(left_expr, right_expr)

    def dt_diff_hours(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_hours(left_expr, right_expr)

    def dt_diff_minutes(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_minutes(left_expr, right_expr)

    def dt_diff_seconds(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_seconds(left_expr, right_expr)

    def dt_diff_milliseconds(self, node: TemporalDiffExpressionNode) -> SupportedExpressions:
        left_expr =  ExpressionParameter(node.left, expression_system=self.backend).to_native_expression()
        right_expr =  ExpressionParameter(node.right, expression_system=self.backend).to_native_expression()
        return self.backend.dt_diff_milliseconds(left_expr, right_expr)


    # ========================================
    # Temporal Operations - data arithmetic
    # ========================================

    def dt_add_days(self, node: TemporalAdditionExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        delta_expr =  ExpressionParameter(node.delta, expression_system=self.backend).to_native_expression()
        return self.backend.dt_add_days(operand_expr, delta_expr)

    def dt_add_hours(self, node: TemporalAdditionExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        delta_expr =  ExpressionParameter(node.delta, expression_system=self.backend).to_native_expression()
        return self.backend.dt_add_hours(operand_expr, delta_expr)

    def dt_add_minutes(self, node: TemporalAdditionExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        delta_expr =  ExpressionParameter(node.delta, expression_system=self.backend).to_native_expression()
        return self.backend.dt_add_minutes(operand_expr, delta_expr)

    def dt_add_seconds(self, node: TemporalAdditionExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        delta_expr =  ExpressionParameter(node.delta, expression_system=self.backend).to_native_expression()
        return self.backend.dt_add_seconds(operand_expr, delta_expr)

    def dt_add_months(self, node: TemporalAdditionExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        delta_expr =  ExpressionParameter(node.delta, expression_system=self.backend).to_native_expression()
        return self.backend.dt_add_months(operand_expr, delta_expr)

    def dt_add_years(self, node: TemporalAdditionExpressionNode) -> SupportedExpressions:
        operand_expr =  ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        delta_expr =  ExpressionParameter(node.delta, expression_system=self.backend).to_native_expression()
        return self.backend.dt_add_years(operand_expr, delta_expr)

    # ========================================
    # Temporal Operations - Modify
    # ========================================


    def dt_truncate(self, node: TemporalTruncateExpressionNode) -> SupportedExpressions:
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        # Pass unit as raw string - backend methods expect string, not expression
        return self.backend.dt_truncate(operand_expr, node.unit)

    def dt_offset_by(self, node: TemporalOffsetExpressionNode) -> SupportedExpressions:
        operand_expr = ExpressionParameter(node.operand, expression_system=self.backend).to_native_expression()
        # Pass offset as raw string - backend methods expect string, not expression
        return self.backend.dt_offset_by(operand_expr, node.offset)


    # ========================================
    # Temporal Operations - Snapshots
    # ========================================

    def dt_today(self, node: TemporalSnapshotExpressionNode) -> SupportedExpressions:
        return self.backend.dt_today()

    def dt_now(self, node: TemporalSnapshotExpressionNode) -> SupportedExpressions:
        return self.backend.dt_now()
