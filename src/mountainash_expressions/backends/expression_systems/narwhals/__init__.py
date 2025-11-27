"""Narwhals backend ExpressionSystem implementation."""

from ....core.expression_visitors.visitor_factory import register_expression_system
from ....core.constants import CONST_VISITOR_BACKENDS

from .base import NarwhalsBaseExpressionSystem
from .core import NarwhalsCoreExpressionSystem
from .boolean import NarwhalsBooleanExpressionSystem
from .arithmetic import NarwhalsArithmeticExpressionSystem
from .string import NarwhalsStringExpressionSystem
from .temporal import NarwhalsTemporalExpressionSystem
from .type import NarwhalsTypeExpressionSystem
from .null import NarwhalsNullExpressionSystem
from .horizontal import NarwhalsHorizontalExpressionSystem
from .name import NarwhalsNameExpressionSystem
from .native import NarwhalsNativeExpressionSystem
from .conditional import NarwhalsConditionalExpressionSystem


@register_expression_system(CONST_VISITOR_BACKENDS.NARWHALS)
class NarwhalsExpressionSystem(
    NarwhalsCoreExpressionSystem,
    NarwhalsBooleanExpressionSystem,
    NarwhalsArithmeticExpressionSystem,
    NarwhalsStringExpressionSystem,
    NarwhalsTemporalExpressionSystem,
    NarwhalsTypeExpressionSystem,
    NarwhalsNullExpressionSystem,
    NarwhalsHorizontalExpressionSystem,
    NarwhalsNameExpressionSystem,
    NarwhalsNativeExpressionSystem,
    NarwhalsConditionalExpressionSystem,
):
    """
    Complete Narwhals backend ExpressionSystem.

    Composes all protocol implementations for use with Narwhals DataFrames.
    All operations return nw.Expr objects.

    Includes:
    - Core, Boolean, Arithmetic, String, Temporal, Type, Null operations
    - Horizontal: coalesce(), greatest(), least()
    - Name: alias(), prefix(), suffix(), to_upper(), to_lower()
    - Native: native() (passthrough for backend-native expressions)
    """

    pass


__all__ = ["NarwhalsExpressionSystem"]
