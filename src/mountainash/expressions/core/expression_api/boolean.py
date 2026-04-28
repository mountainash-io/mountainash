"""Boolean logic expression API facade.

Substrait-aligned implementation using new namespace architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from .api_base import BaseExpressionAPI




# Import flat namespaces from new Substrait-aligned core
from .api_builders.substrait import (
    SubstraitCastAPIBuilder,
    SubstraitFieldReferenceAPIBuilder,
    SubstraitLiteralAPIBuilder,
    SubstraitScalarAggregateAPIBuilder,
    SubstraitScalarArithmeticAPIBuilder,
    SubstraitScalarBooleanAPIBuilder,
    SubstraitScalarComparisonAPIBuilder,
    SubstraitScalarLogarithmicAPIBuilder,
    SubstraitScalarRoundingAPIBuilder,
    SubstraitScalarSetAPIBuilder,
    SubstraitWindowArithmeticAPIBuilder,

    SubstraitScalarDatetimeAPIBuilder,
    SubstraitScalarStringAPIBuilder,
)

# Import Mountainash extension builders
from .api_builders.extensions_mountainash import (
    MountainAshNameAPIBuilder,
    MountainAshNativeAPIBuilder,
    MountainAshNullAPIBuilder,
    MountainAshScalarAggregateAPIBuilder,
    MountainAshScalarArithmeticAPIBuilder,
    MountainAshScalarBooleanAPIBuilder,
    MountainAshScalarComparisonAPIBuilder,
    MountainAshScalarDatetimeAPIBuilder,
    MountainAshScalarSetAPIBuilder,
    MountainAshScalarStringAPIBuilder,
    MountainAshScalarStructAPIBuilder,
    MountainAshScalarTernaryAPIBuilder,
)

# Import descriptor for explicit namespaces
from .descriptor import NamespaceDescriptor

if TYPE_CHECKING:
    from .api_builders.api_builder_base import BaseExpressionAPIBuilder
    from ..expression_nodes import ExpressionNode

# Composed datetime builder exposing both Substrait and extension methods
class DatetimeAPIBuilder(
    MountainAshScalarDatetimeAPIBuilder,   # 45+ extension methods
    SubstraitScalarDatetimeAPIBuilder,      # 3 Substrait methods
):
    """Unified datetime builder for the .dt namespace."""
    pass


# Composed string builder exposing both Substrait and extension (Polars alias) methods
class StringAPIBuilder(
    MountainAshScalarStringAPIBuilder,      # Polars-compatible aliases
    SubstraitScalarStringAPIBuilder,        # Standard Substrait string methods
):
    """Unified string builder for the .str namespace."""
    pass


class StructAPIBuilder(MountainAshScalarStructAPIBuilder):
    """Unified struct builder for the .struct namespace."""
    pass


# Import base namespace type for type hints




class BooleanExpressionAPI(BaseExpressionAPI):
    """
    Expression API with standard two-valued boolean logic.

    This is the default facade for building expressions. It provides
    comparison, logical, arithmetic, and other operations that produce
    boolean results for filtering and conditional logic.

    Uses namespace-based composition for clean, organized method access.

    Flat namespaces (methods accessed directly):
    - Ternary: t_eq, t_ne, t_gt, t_lt, t_and, t_or, is_true, is_false, etc.
    - Comparison: eq, ne, gt, lt, ge, le, is_close, between
    - Logical: and_, or_, xor_, not_, is_in, is_not_in, always_true, always_false
    - Null checks: is_null, is_not_null, coalesce, greatest, least
    - Arithmetic: add, subtract, multiply, divide, modulo, power, etc.
    - Rounding: ceil, floor, round
    - Math: log, sqrt, abs, exp (via ScalarLogarithmicNamespace)
    - Type: cast
    - Null handling: fill_null, null_if
    - Native: as_native

    Explicit namespaces (methods accessed via accessor):
    - .str: String operations (upper, lower, contains, etc.)
    - .dt: Date/time operations (year, month, add_days, etc.)
    - .name: Column naming (alias, prefix, suffix, etc.)

    Example:
        >>> import mountainash.expressions as ma
        >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
        >>> result = df.filter(expr.compile(df))
    """

    # Flat namespaces - methods dispatched via __getattr__
    # TernaryNamespace first so ternary-specific methods (is_true, is_false, etc.)
    # take priority when there are conflicts with ScalarComparisonNamespace
    _FLAT_NAMESPACES: ClassVar[tuple[type[BaseExpressionAPIBuilder], ...]] = (
        # Mountainash extensions first (ternary takes priority for is_true etc.)
        MountainAshScalarTernaryAPIBuilder,
        MountainAshNullAPIBuilder,
        MountainAshNameAPIBuilder,
        MountainAshScalarAggregateAPIBuilder,
        MountainAshScalarArithmeticAPIBuilder,
        MountainAshScalarBooleanAPIBuilder,
        MountainAshScalarComparisonAPIBuilder,
        MountainAshNativeAPIBuilder,
        MountainAshScalarSetAPIBuilder,
        # Substrait core
        SubstraitCastAPIBuilder,
        SubstraitFieldReferenceAPIBuilder,
        SubstraitLiteralAPIBuilder,
        SubstraitScalarAggregateAPIBuilder,
        SubstraitScalarArithmeticAPIBuilder,
        SubstraitScalarBooleanAPIBuilder,
        SubstraitScalarComparisonAPIBuilder,
        SubstraitScalarLogarithmicAPIBuilder,
        SubstraitScalarRoundingAPIBuilder,
        SubstraitScalarSetAPIBuilder,
        SubstraitWindowArithmeticAPIBuilder,
    )

    # Explicit namespace descriptors - accessed via .str, .dt, .name, .struct
    str = NamespaceDescriptor(StringAPIBuilder)
    dt = NamespaceDescriptor(DatetimeAPIBuilder)
    name = NamespaceDescriptor(MountainAshNameAPIBuilder)
    struct = NamespaceDescriptor(StructAPIBuilder)

    @classmethod
    def create(cls, node: ExpressionNode) -> BooleanExpressionAPI:
        """Factory method for creating new BooleanExpressionAPI instances."""
        return cls(node)

    # ========================================
    # Python Comparison Operators
    # ========================================

    def __gt__(self, other) -> BooleanExpressionAPI:
        """Python > operator."""
        return self.gt(other)

    def __lt__(self, other) -> BooleanExpressionAPI:
        """Python < operator."""
        return self.lt(other)

    def __ge__(self, other) -> BooleanExpressionAPI:
        """Python >= operator."""
        return self.ge(other)

    def __le__(self, other) -> BooleanExpressionAPI:
        """Python <= operator."""
        return self.le(other)

    def __eq__(self, other) -> BooleanExpressionAPI:
        """Python == operator."""
        return self.eq(other)

    def __ne__(self, other) -> BooleanExpressionAPI:
        """Python != operator."""
        return self.ne(other)

    # ========================================
    # Python Logical Operators
    # ========================================

    def __and__(self, other) -> BooleanExpressionAPI:
        """Python & operator."""
        return self.and_(other)

    def __or__(self, other) -> BooleanExpressionAPI:
        """Python | operator."""
        return self.or_(other)

    def __xor__(self, other) -> BooleanExpressionAPI:
        """Python ^ operator."""
        return self.xor_(other)

    def __invert__(self) -> BooleanExpressionAPI:
        """Python ~ operator (logical NOT)."""
        return self.not_()

    # ========================================
    # Python Arithmetic Operators
    # ========================================

    def __add__(self, other) -> BooleanExpressionAPI:
        """Python + operator."""
        return self.add(other)

    def __radd__(self, other) -> BooleanExpressionAPI:
        """Python + operator (reversed)."""
        return self.add(other)

    def __sub__(self, other) -> BooleanExpressionAPI:
        """Python - operator."""
        return self.subtract(other)

    def __rsub__(self, other) -> BooleanExpressionAPI:
        """Python - operator (reversed): other - self."""
        return self.rsubtract(other)

    def __mul__(self, other) -> BooleanExpressionAPI:
        """Python * operator."""
        return self.multiply(other)

    def __rmul__(self, other) -> BooleanExpressionAPI:
        """Python * operator (reversed)."""
        return self.multiply(other)

    def __truediv__(self, other) -> BooleanExpressionAPI:
        """Python / operator."""
        return self.divide(other)

    def __rtruediv__(self, other) -> BooleanExpressionAPI:
        """Python / operator (reversed): other / self."""
        return self.rdivide(other)

    def __floordiv__(self, other) -> BooleanExpressionAPI:
        """Python // operator."""
        return self.floor_divide(other)

    def __rfloordiv__(self, other) -> BooleanExpressionAPI:
        """Python // operator (reversed): other // self."""
        return self.rfloor_divide(other)

    def __mod__(self, other) -> BooleanExpressionAPI:
        """Python % operator."""
        return self.modulo(other)

    def __rmod__(self, other) -> BooleanExpressionAPI:
        """Python % operator (reversed): other % self."""
        return self.rmodulo(other)

    def __pow__(self, other) -> BooleanExpressionAPI:
        """Python ** operator."""
        return self.power(other)

    def __rpow__(self, other) -> BooleanExpressionAPI:
        """Python ** operator (reversed): other ** self."""
        return self.rpower(other)

    def __neg__(self) -> BooleanExpressionAPI:
        """Python unary - operator."""
        return self.negate()
