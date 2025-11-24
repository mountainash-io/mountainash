
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Union, Protocol, Any
from typing_extensions import TypeAlias, TypeGuard

if TYPE_CHECKING:
    from . import ArithmeticExpressionVisitor, CoreExpressionVisitor, BooleanExpressionVisitor, NullExpressionVisitor,StringExpressionVisitor, NativeExpressionVisitor#, TemporalExpressionVisitor

SupportedExpressionVisitors = Union[ArithmeticExpressionVisitor, CoreExpressionVisitor, BooleanExpressionVisitor, NullExpressionVisitor,StringExpressionVisitor, NativeExpressionVisitor] #, TemporalExpressionVisitor]
