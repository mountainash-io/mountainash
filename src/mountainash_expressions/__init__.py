from .visitors.boolean import IbisBooleanExpressionVisitor, PolarsBooleanExpressionVisitor, PandasBooleanExpressionVisitor, PyArrowBooleanExpressionVisitor

from .boolean import BooleanExpressionNode, BooleanExpressionBuilder, BooleanExpressionVisitor, BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanLiteralExpressionNode
from .ternary import PolarsTernaryExpressionVisitor, IbisTernaryExpressionVisitor, PandasTernaryExpressionVisitor, PyArrowTernaryExpressionVisitor#, XarrayTernaryExpressionVisitor, NumPyTernaryExpressionVisitor
from .ternary import TernaryExpressionNode, TernaryExpressionBuilder, TernaryExpressionVisitor, TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryLiteralExpressionNode
from .helpers import ExpressionVisitorFactory


import importlib.util

PYSPARK_AVAILABLE = importlib.util.find_spec("pyspark") is not None

__all__ = [
    "IbisBooleanExpressionVisitor",
    "PolarsBooleanExpressionVisitor",
    "PandasBooleanExpressionVisitor",
    "PyArrowBooleanExpressionVisitor",
    # "NumpyExpressionVisitor",

    "BooleanExpressionNode",
    "BooleanExpressionBuilder",
    "BooleanExpressionVisitor",
    "BooleanColumnExpressionNode",
    "BooleanLogicalExpressionNode",
    "BooleanLiteralExpressionNode",

    "TernaryExpressionNode",
    "TernaryExpressionBuilder",
    "TernaryExpressionVisitor",
    "TernaryColumnExpressionNode",
    "TernaryLogicalExpressionNode",
    "TernaryLiteralExpressionNode",

    "PolarsTernaryExpressionVisitor",
    "IbisTernaryExpressionVisitor",
    "PandasTernaryExpressionVisitor",
    "PyArrowTernaryExpressionVisitor",


    "ExpressionVisitorFactory"
    # "XarrayTernaryExpressionVisitor",
    # "NumPyTernaryExpressionVisitor"
    # "IbisExpressionVisitor",
    # "PandasExpressionVisitor",
    # "PyArrowExpressionVisitor",
    # "NumpyExpressionVisitor",

]

# if PYSPARK_AVAILABLE:
#     try:
#         from .boolean_expression_pyspark import PySparkExpressionVisitor  # noqa: F401
#         __all__.append("PySparkExpressionVisitor")
#     except ImportError:
#         PYSPARK_AVAILABLE = False
