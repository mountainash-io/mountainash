"""Protocol for Substrait scalar aggregate api_builder methods."""
from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI


class SubstraitScalarAggregateAPIBuilderProtocol(Protocol):
    """Substrait-standard scalar aggregate builder surface."""

    def count(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Count non-null values of this column. Substrait ``count(x)``."""
        ...

    def any_value(self, *, ignore_nulls: Optional[bool] = None) -> "BaseExpressionAPI":
        """Return one representative value from the group. Substrait ``any_value(x)``."""
        ...

    def sum(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Sum a set of values. Returns null for empty input. Substrait ``sum(x)``."""
        ...

    def avg(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Arithmetic mean. Substrait ``avg(x)``."""
        ...

    def min(self) -> "BaseExpressionAPI":
        """Minimum value. Substrait ``min(x)``."""
        ...

    def max(self) -> "BaseExpressionAPI":
        """Maximum value. Substrait ``max(x)``."""
        ...

    def product(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Product of values. Substrait ``product(x)``."""
        ...

    def std_dev(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Standard deviation. Substrait ``std_dev(x)``."""
        ...

    def variance(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Variance. Substrait ``variance(x)``."""
        ...

    def mode(self) -> "BaseExpressionAPI":
        """Most common value. Substrait ``mode(x)``."""
        ...

    def all(self) -> "BaseExpressionAPI":
        """True if all values are true. Substrait ``bool_and(x)``."""
        ...

    def any(self) -> "BaseExpressionAPI":
        """True if any value is true. Substrait ``bool_or(x)``."""
        ...
