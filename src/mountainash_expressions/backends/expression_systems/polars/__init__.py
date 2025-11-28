"""
Polars backend ExpressionSystem implementation.

This module composes all Polars protocol implementations into a single
PolarsExpressionSystem class that can be used by visitors.
"""

from ....core.expression_visitors.visitor_factory import register_expression_system
from ....core.constants import CONST_VISITOR_BACKENDS

from .base import PolarsBaseExpressionSystem
from .core import PolarsCoreExpressionSystem
from .boolean import PolarsBooleanExpressionSystem
from .arithmetic import PolarsArithmeticExpressionSystem
from .string import PolarsStringExpressionSystem
from .temporal import PolarsTemporalExpressionSystem
from .type import PolarsTypeExpressionSystem
from .null import PolarsNullExpressionSystem
from .horizontal import PolarsHorizontalExpressionSystem
from .name import PolarsNameExpressionSystem
from .native import PolarsNativeExpressionSystem
from .conditional import PolarsConditionalExpressionSystem
from .ternary import PolarsTernaryExpressionSystem


@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
class PolarsExpressionSystem(
    PolarsCoreExpressionSystem,
    PolarsBooleanExpressionSystem,
    PolarsArithmeticExpressionSystem,
    PolarsStringExpressionSystem,
    PolarsTemporalExpressionSystem,
    PolarsTypeExpressionSystem,
    PolarsNullExpressionSystem,
    PolarsHorizontalExpressionSystem,
    PolarsNameExpressionSystem,
    PolarsNativeExpressionSystem,
    PolarsConditionalExpressionSystem,
    PolarsTernaryExpressionSystem,
):
    """
    Complete Polars backend ExpressionSystem.

    Composes all protocol implementations:
    - Core: col(), lit()
    - Boolean: eq(), ne(), gt(), lt(), ge(), le(), and_(), or_(), not_(), etc.
    - Arithmetic: add(), subtract(), multiply(), divide(), modulo(), power(), floor_divide()
    - String: str_upper(), str_lower(), str_trim(), str_contains(), etc.
    - Pattern: pat_like(), pat_regex_match(), pat_regex_contains(), pat_regex_replace()
    - Temporal: dt_year(), dt_month(), dt_add_days(), dt_diff_hours(), etc.
    - Type: cast()
    - Null: is_null()
    - Horizontal: coalesce(), greatest(), least()
    - Name: alias(), prefix(), suffix(), to_upper(), to_lower()
    - Native: native() (passthrough for backend-native expressions)

    All operations return pl.Expr objects for use with Polars DataFrames.
    """

    pass  # All functionality inherited from mixins


__all__ = ["PolarsExpressionSystem"]
