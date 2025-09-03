

# Backend visitor imports
from .backends import (
    IbisBooleanExpressionVisitor,
    IbisTernaryExpressionVisitor,
    PandasBooleanExpressionVisitor,
    PandasTernaryExpressionVisitor,
    PolarsBooleanExpressionVisitor,
    PolarsTernaryExpressionVisitor,
    PyArrowBooleanExpressionVisitor,
    PyArrowTernaryExpressionVisitor
)

# Boolean logic imports
from .core.logic.boolean import (
    # BooleanExpressionNode,
    BooleanExpressionBuilder,
    # BooleanColumnExpressionNode,
    # BooleanLogicalExpressionNode,
    # BooleanLiteralExpressionNode
)

# Ternary logic imports
from .core.logic.ternary import (
    # TernaryExpressionNode,
    TernaryExpressionBuilder,
    # TernaryColumnExpressionNode,
    # TernaryLogicalExpressionNode,
    # TernaryLiteralExpressionNode
)

# Constants
from .core.constants import (
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
    CONST_EXPRESSION_LOGIC_OPERATORS,
    CONST_TERNARY_LOGIC_VALUES
)

# Core visitor imports
# from .core.visitor import (
#     ExpressionVisitor,
#     BooleanExpressionVisitor,
#     TernaryExpressionVisitor,
#     ExpressionVisitorFactory
# )

import importlib.util

PYSPARK_AVAILABLE = importlib.util.find_spec("pyspark") is not None

__all__ = [
    # Core visitor classes
    # "ExpressionVisitor",
    # "BooleanExpressionVisitor",
    # "TernaryExpressionVisitor",
    # "ExpressionVisitorFactory",

    # Backend Boolean visitors
    "IbisBooleanExpressionVisitor",
    "PolarsBooleanExpressionVisitor",
    "PandasBooleanExpressionVisitor",
    "PyArrowBooleanExpressionVisitor",

    # Backend Ternary visitors
    "IbisTernaryExpressionVisitor",
    "PolarsTernaryExpressionVisitor",
    "PandasTernaryExpressionVisitor",
    "PyArrowTernaryExpressionVisitor",

    # Boolean expression nodes
    # "BooleanExpressionNode",
    "BooleanExpressionBuilder",
    # "BooleanColumnExpressionNode",
    # "BooleanLogicalExpressionNode",
    # "BooleanLiteralExpressionNode",

    # Ternary expression nodes
    # "TernaryExpressionNode",
    "TernaryExpressionBuilder",
    # "TernaryColumnExpressionNode",
    # "TernaryLogicalExpressionNode",
    # "TernaryLiteralExpressionNode",

    # Constants
    "CONST_VISITOR_BACKENDS",
    "CONST_LOGIC_TYPES",
    "CONST_EXPRESSION_NODE_TYPES",
    "CONST_EXPRESSION_LOGIC_OPERATORS",
    "CONST_TERNARY_LOGIC_VALUES",
]

# if PYSPARK_AVAILABLE:
#     try:
#         from .boolean_expression_pyspark import PySparkExpressionVisitor  # noqa: F401
#         __all__.append("PySparkExpressionVisitor")
#     except ImportError:
#         PYSPARK_AVAILABLE = False
