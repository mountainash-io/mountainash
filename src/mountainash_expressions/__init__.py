from .visitors.boolean import BooleanExpressionVisitor
from .visitors.boolean import IbisBooleanExpressionVisitor, PolarsBooleanExpressionVisitor, PandasBooleanExpressionVisitor, PyArrowBooleanExpressionVisitor
from .logic.boolean import BooleanExpressionNode, BooleanExpressionBuilder, BooleanColumnExpressionNode, BooleanLogicalExpressionNode, BooleanLiteralExpressionNode
from .logic.boolean import BooleanExpressionBuilder

from .visitors.ternary import TernaryExpressionVisitor
from .visitors.ternary import  PolarsTernaryExpressionVisitor, IbisTernaryExpressionVisitor, PandasTernaryExpressionVisitor, PyArrowTernaryExpressionVisitor
from .logic.ternary import TernaryExpressionNode, TernaryColumnExpressionNode, TernaryLogicalExpressionNode, TernaryLiteralExpressionNode
from .logic.ternary import TernaryExpressionBuilder

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
