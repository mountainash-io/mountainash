from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union
    from . import ArithmeticExpressionVisitor, CoreExpressionVisitor, BooleanExpressionVisitor, NullExpressionVisitor, StringExpressionVisitor, NativeExpressionVisitor  #, TemporalExpressionVisitor

    SupportedExpressionVisitors = Union[ArithmeticExpressionVisitor, CoreExpressionVisitor, BooleanExpressionVisitor, NullExpressionVisitor, StringExpressionVisitor, NativeExpressionVisitor]  #, TemporalExpressionVisitor
