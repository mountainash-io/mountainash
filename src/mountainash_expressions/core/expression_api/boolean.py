"""Boolean logic expression API facade.

Substrait-aligned implementation using new namespace architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from .api_base import BaseExpressionAPI

# Import flat namespaces from new Substrait-aligned core
from .api_namespaces.core import (
    # Ternary FIRST for is_true/is_false/is_unknown/is_known priority
    TernaryNamespace,
    # Boolean operations (eq, ne, gt, lt, ge, le, and_, or_, not_, xor_, is_in, etc.)
    ScalarBooleanNamespace,
    # Comparison operations (is_null, is_not_null, coalesce, greatest, least)
    ScalarComparisonNamespace,
    # Arithmetic operations (add, subtract, multiply, divide, etc.)
    ScalarArithmeticNamespace,
    # Rounding operations (ceil, floor, round)
    ScalarRoundingNamespace,
    # Logarithmic operations (log, sqrt, abs, exp)
    ScalarLogarithmicNamespace,
    # Cast operations (cast)
    CastNamespace,
    # Null handling (fill_null, null_if)
    NullNamespace,
    # Native expression passthrough (as_native)
    NativeNamespace,
)

# Import explicit namespaces (accessed via .str, .dt, .name)
from .api_namespaces.core import (
    StringNamespace,
    DateTimeNamespace,
    NameNamespace,
)

# Import base namespace type for type hints
from .api_namespaces.ns_base import BaseExpressionNamespace

# Import descriptor for explicit namespaces
from .descriptor import NamespaceDescriptor

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode


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
        >>> import mountainash_expressions as ma
        >>> expr = ma.col("age").gt(30).and_(ma.col("score").ge(85))
        >>> result = df.filter(expr.compile(df))
    """

    # Flat namespaces - methods dispatched via __getattr__
    # TernaryNamespace first so ternary-specific methods (is_true, is_false, etc.)
    # take priority when there are conflicts with ScalarComparisonNamespace
    _FLAT_NAMESPACES: ClassVar[tuple[type[BaseExpressionNamespace], ...]] = (
        TernaryNamespace,           # t_*, is_true, is_false, is_unknown, is_known, etc.
        ScalarBooleanNamespace,     # eq, ne, gt, lt, ge, le, and_, or_, not_, xor_, is_in
        ScalarComparisonNamespace,  # is_null, is_not_null, coalesce, greatest, least
        ScalarArithmeticNamespace,  # add, subtract, multiply, divide, modulo, power
        ScalarRoundingNamespace,    # ceil, floor, round
        ScalarLogarithmicNamespace, # log, sqrt, abs, exp
        CastNamespace,              # cast
        NullNamespace,              # fill_null, null_if
        NativeNamespace,            # as_native
    )

    # Explicit namespace descriptors - accessed via .str, .dt, .name
    str = NamespaceDescriptor(StringNamespace)
    dt = NamespaceDescriptor(DateTimeNamespace)
    name = NamespaceDescriptor(NameNamespace)

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
