"""Expression node classes for building expression trees."""

from .expression_nodes import (
    ExpressionNode,
    NativeBackendExpressionNode,
    SourceExpressionNode,
    LiteralExpressionNode,
    CastExpressionNode,
    LogicalConstantExpressionNode,
    UnaryExpressionNode,
    LogicalExpressionNode,
    ComparisonExpressionNode,
    CollectionExpressionNode,
    ArithmeticExpressionNode,
    ConditionalIfElseExpressionNode,
)

from .boolean_expression_nodes import (
    BooleanExpressionNode,
    BooleanUnaryExpressionNode,
    BooleanLogicalExpressionNode,
    BooleanComparisonExpressionNode,
    BooleanConditionalIfElseExpressionNode,
    BooleanCollectionExpressionNode,
)

__all__ = [
    # Base nodes
    "ExpressionNode",
    "NativeBackendExpressionNode",
    "SourceExpressionNode",
    "LiteralExpressionNode",
    "CastExpressionNode",
    "LogicalConstantExpressionNode",
    "UnaryExpressionNode",
    "LogicalExpressionNode",
    "ComparisonExpressionNode",
    "CollectionExpressionNode",
    "ArithmeticExpressionNode",
    "ConditionalIfElseExpressionNode",
    # Boolean nodes
    "BooleanExpressionNode",
    "BooleanUnaryExpressionNode",
    "BooleanLogicalExpressionNode",
    "BooleanComparisonExpressionNode",
    "BooleanConditionalIfElseExpressionNode",
    "BooleanCollectionExpressionNode",
]
