from __future__ import annotations
from typing import Any, Callable, TYPE_CHECKING
# from ibis.expr.types import s  # Removed - not used and causes import error
from pydantic import Field
from .base_expression_node import ExpressionNode



from ..protocols import ENUM_TEMPORAL_OPERATORS
if TYPE_CHECKING:
    from ..expression_visitors import TemporalExpressionVisitor
    from ...types import SupportedExpressions




class BaseTemporalExpressionNode(ExpressionNode):
    """
    Node representing arithmetic ordered operations (SUBTRACT, DIVIDE, etc.).

    Temporal operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    operator: ENUM_TEMPORAL_OPERATORS = Field()


    def accept(self, visitor: TemporalExpressionVisitor) -> SupportedExpressions:
        return visitor.visit_expression_node(self)

    def eval(self) -> Callable:
        def eval_expr(backend: Any) -> SupportedExpressions:
            from ..expression_visitors import ExpressionVisitorFactory
            visitor: TemporalExpressionVisitor = ExpressionVisitorFactory.get_visitor_for_backend(backend, self.logic_type)
            return visitor.visit_expression_node(self)
        return eval_expr


class TemporalExtractExpressionNode(BaseTemporalExpressionNode):
    """
    Node representing arithmetic ordered operations (SUBTRACT, DIVIDE, etc.).

    Temporal operations return numeric values and can be used with any logic system.
    The logic_type determines how NULL values are handled during arithmetic operations.
    """

    operand : Any = Field()

    def __init__(self, operator: ENUM_TEMPORAL_OPERATORS, operand: Any):
        super().__init__(
            operator=operator,
            operand=operand
        )


class TemporalDiffExpressionNode(BaseTemporalExpressionNode):

    left : Any = Field()
    right : Any = Field()

    def __init__(self, operator: ENUM_TEMPORAL_OPERATORS, left: Any, right: Any):
        super().__init__(
            operator=operator,
            left=left,
            right=right
        )

class TemporalAdditionExpressionNode(BaseTemporalExpressionNode):

    operand : Any = Field()
    delta : Any = Field()

    def __init__(self, operator: ENUM_TEMPORAL_OPERATORS, operand: Any, delta: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            delta=delta
        )

class TemporalTruncateExpressionNode(BaseTemporalExpressionNode):

    operand : Any = Field()
    unit : Any = Field()

    def __init__(self, operator: ENUM_TEMPORAL_OPERATORS, operand: Any, unit: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            unit=unit
        )


class TemporalOffsetExpressionNode(BaseTemporalExpressionNode):

    operand : Any = Field()
    offset : Any = Field()

    def __init__(self, operator: ENUM_TEMPORAL_OPERATORS, operand: Any, offset: Any):
        super().__init__(
            operator=operator,
            operand=operand,
            offset=offset
        )

class TemporalSnapshotExpressionNode(BaseTemporalExpressionNode):

    def __init__(self, operator: ENUM_TEMPORAL_OPERATORS):
        super().__init__(
            operator=operator
        )
