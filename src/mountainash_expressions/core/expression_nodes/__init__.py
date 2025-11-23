"""Expression node classes for building expression trees."""

from .base_expression_node import ExpressionNode

from .core.core_expression_nodes import (
    # ExpressionNode,
    NativeBackendExpressionNode,
    ColumnExpressionNode,
    LiteralExpressionNode,
    # CastExpressionNode,
    # LogicalConstantExpressionNode,
    # UnaryExpressionNode,
    # LogicalExpressionNode,
    # ComparisonExpressionNode,
    # CollectionExpressionNode,
    # ArithmeticExpressionNode,
    # StringExpressionNode,
    # PatternExpressionNode,
    # ConditionalIfElseExpressionNode,
    # TemporalExpressionNode,
)
from .arithmetic_expression_nodes import (
    ArithmeticExpressionNode,
    ArithmeticIterableExpressionNode,
    SupportedArithmeticExpressionNodeTypes
)

from .boolean_expression_nodes import (
    BooleanExpressionNode,
    BooleanUnaryExpressionNode,
    BooleanComparisonExpressionNode,
    BooleanCollectionExpressionNode,
    BooleanIterableExpressionNode,
    SupportedBooleanExpressionNodeTypes
)

from .core_expression_nodes import (
    ExpressionNode,
    ColumnExpressionNode,
    LiteralExpressionNode,
    NativeBackendExpressionNode,
    SupportedCoreExpressionNodeTypes
)


from .null_expression_nodes import (
    NullExpressionNode,
    NullConstantExpressionNode,
    NullConditionalExpressionNode,
    NullLogicalExpressionNode,
    SupportedNullExpresionNodeTypes
}

__all__ = [
    # Base nodes
    "ExpressionNode",
    "ColumnExpressionNode",
    "LiteralExpressionNode",
    "NativeBackendExpressionNode",

    "ArithmeticExpressionNode",
    "ArithmeticIterableExpressionNode",
    "SupportedArithmeticExpressionNodeTypes",

    "ColumnExpressionNode",
    "LiteralExpressionNode",
    "NativeBackendExpressionNode",
    "SupportedCoreExpressionNodeTypes",

    "NullExpressionNode",
    "NullConstantExpressionNode",
    "NullConditionalExpressionNode",
    "NullLogicalExpressionNode",


    # "CastExpressionNode",
    # "LogicalConstantExpressionNode",
    # "UnaryExpressionNode",
    # "LogicalExpressionNode",
    # "ComparisonExpressionNode",
    # "CollectionExpressionNode",
    # "ArithmeticExpressionNode",
    # "StringExpressionNode",
    # "PatternExpressionNode",
    # "ConditionalIfElseExpressionNode",
    # "TemporalExpressionNode",
    # # Boolean nodes
    "BooleanExpressionNode",
    "BooleanUnaryExpressionNode",
    "BooleanComparisonExpressionNode",
    "BooleanCollectionExpressionNode",
    "BooleanIterableExpressionNode",
    "SupportedBooleanExpressionNodeTypes"
]
