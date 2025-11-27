"""Ibis backend ExpressionSystem implementation."""

from ....core.expression_visitors.visitor_factory import register_expression_system
from ....core.constants import CONST_VISITOR_BACKENDS

from .base import IbisBaseExpressionSystem
from .core import IbisCoreExpressionSystem
from .boolean import IbisBooleanExpressionSystem
from .arithmetic import IbisArithmeticExpressionSystem
from .string import IbisStringExpressionSystem
from .temporal import IbisTemporalExpressionSystem
from .type import IbisTypeExpressionSystem
from .null import IbisNullExpressionSystem
from .horizontal import IbisHorizontalExpressionSystem
from .name import IbisNameExpressionSystem
from .native import IbisNativeExpressionSystem
from .conditional import IbisConditionalExpressionSystem


@register_expression_system(CONST_VISITOR_BACKENDS.IBIS)
class IbisExpressionSystem(
    IbisCoreExpressionSystem,
    IbisBooleanExpressionSystem,
    IbisArithmeticExpressionSystem,
    IbisStringExpressionSystem,
    IbisTemporalExpressionSystem,
    IbisTypeExpressionSystem,
    IbisNullExpressionSystem,
    IbisHorizontalExpressionSystem,
    IbisNameExpressionSystem,
    IbisNativeExpressionSystem,
    IbisConditionalExpressionSystem,
):
    """
    Complete Ibis backend ExpressionSystem.

    Composes all protocol implementations for use with Ibis expressions.
    All operations return ibis.expr.types.Expr objects.

    Includes:
    - Core, Boolean, Arithmetic, String, Temporal, Type, Null operations
    - Horizontal: coalesce(), greatest(), least()
    - Name: alias(), prefix(), suffix(), to_upper(), to_lower()
    - Native: native() (passthrough for backend-native expressions)
    """

    pass


__all__ = ["IbisExpressionSystem"]
