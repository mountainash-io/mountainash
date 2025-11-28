"""Visitor pattern implementations for expression evaluation."""

from typing import TYPE_CHECKING

from .expression_visitor import ExpressionVisitor
# from ._boolean_expression_visitor import BooleanExpressionVisitor
from .visitor_factory import ExpressionVisitorFactory

from .arithmetic_visitor import ArithmeticExpressionVisitor
from .boolean_visitor import BooleanExpressionVisitor
from .core_visitor import CoreExpressionVisitor
from .null_visitor import NullExpressionVisitor
from .string_visitor import StringExpressionVisitor

from .native_visitor import NativeExpressionVisitor
from .horizontal_visitor import HorizontalExpressionVisitor
from .temporal_visitor import TemporalExpressionVisitor
from .type_visitor import TypeExpressionVisitor
from .name_visitor import NameExpressionVisitor
from .ternary_visitor import TernaryExpressionVisitor

if TYPE_CHECKING:
    from .types import SupportedExpressionVisitors

__all__ = [
    "ExpressionVisitor",
    # "BooleanExpressionVisitor",
    "ExpressionVisitorFactory",

    "ArithmeticExpressionVisitor",
    "BooleanExpressionVisitor",
    "CoreExpressionVisitor",
    "NullExpressionVisitor",
    "StringExpressionVisitor",

    "NativeExpressionVisitor",
    "HorizontalExpressionVisitor",
    "TemporalExpressionVisitor",
    "TypeExpressionVisitor",
    "NameExpressionVisitor",
    "TernaryExpressionVisitor",

    "SupportedExpressionVisitors"
]
