"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace


class ScalarComparisonExpressionProtocol(Protocol):
    """Protocol for comparison operations.

    Auto-generated from Substrait comparison extension.
    """

    def not_equal(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Whether two values are not_equal.
`not_equal(x, y) := (x != y)`
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: not_equal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def equal(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Whether two values are equal.
`equal(x, y) := (x == y)`
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: equal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

#     def is_not_distinct_from(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Whether two values are equal.
# This function treats `null` values as comparable, so
# `is_not_distinct_from(null, null) == True`
# This is in contrast to `equal`, in which `null` values do not compare.


#         Substrait: is_not_distinct_from
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
#         """
#         ...

#     def is_distinct_from(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Whether two values are not equal.
# This function treats `null` values as comparable, so
# `is_distinct_from(null, null) == False`
# This is in contrast to `equal`, in which `null` values do not compare.


#         Substrait: is_distinct_from
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
#         """
#         ...

    def lt(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Less than.
lt(x, y) := (x < y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: lt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def gt(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Greater than.
gt(x, y) := (x > y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: gt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def lte(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Less than or equal to.
lte(x, y) := (x <= y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: lte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def gte(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions:
        """Greater than or equal to.
gte(x, y) := (x >= y)
If either/both of `x` and `y` are `null`, `null` is returned.


        Substrait: gte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def between(self, x: SupportedExpressions, low: SupportedExpressions, high: SupportedExpressions, /) -> SupportedExpressions:
        """Whether the `expression` is greater than or equal to `low` and less than or equal to `high`.
`expression` BETWEEN `low` AND `high`
If `low`, `high`, or `expression` are `null`, `null` is returned.

        Substrait: between
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_true(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is true.

        Substrait: is_true
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_true(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is not true.

        Substrait: is_not_true
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_false(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is false.

        Substrait: is_false
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_false(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is not false.

        Substrait: is_not_false
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_null(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is null. NaN is not null.

        Substrait: is_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_not_null(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is not null. NaN is not null.

        Substrait: is_not_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_nan(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is not a number.
If `x` is `null`, `null` is returned.


        Substrait: is_nan
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_finite(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is finite (neither infinite nor NaN).
If `x` is `null`, `null` is returned.


        Substrait: is_finite
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def is_infinite(self, x: SupportedExpressions, /) -> SupportedExpressions:
        """Whether a value is infinite.
            If `x` is `null`, `null` is returned.


        Substrait: is_infinite
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def nullif(self, x: SupportedExpressions, /, y: SupportedExpressions) -> SupportedExpressions:
        """If two values are equal, return null. Otherwise, return the first value.

        Substrait: nullif
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def coalesce(self, arg: SupportedExpressions, /) -> SupportedExpressions:
        """Evaluate arguments from left to right and return the first argument that is not null. Once a non-null argument is found, the remaining arguments are not evaluated.
If all arguments are null, return null.

        Substrait: coalesce
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def least(self, arg: SupportedExpressions, /) -> SupportedExpressions:
        """Evaluates each argument and returns the smallest one. The function will return null if any argument evaluates to null.

        Substrait: least
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def least_skip_null(self, arg: SupportedExpressions, /) -> SupportedExpressions:
        """Evaluates each argument and returns the smallest one. The function will return null only if all arguments evaluate to null.

        Substrait: least_skip_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def greatest(self, arg: SupportedExpressions, /) -> SupportedExpressions:
        """Evaluates each argument and returns the largest one. The function will return null if any argument evaluates to null.

        Substrait: greatest
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...

    def greatest_skip_null(self, arg: SupportedExpressions, /) -> SupportedExpressions:
        """Evaluates each argument and returns the largest one. The function will return null only if all arguments evaluate to null.

        Substrait: greatest_skip_null
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_comparison.yaml
        """
        ...


class ScalarComparisonBuilderProtocol(Protocol):
    """Builder protocol for comparison operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    def not_equal(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Not equal comparison (!=).

        Substrait: not_equal
        """
        ...

    def equal(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Equal comparison (==).

        Substrait: equal
        """
        ...

    def lt(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Less than comparison (<).

        Substrait: lt
        """
        ...

    def gt(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Greater than comparison (>).

        Substrait: gt
        """
        ...

    def lte(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Less than or equal comparison (<=).

        Substrait: lte
        """
        ...

    def gte(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Greater than or equal comparison (>=).

        Substrait: gte
        """
        ...

    def between(
        self,
        low: Union["BaseNamespace", "ExpressionNode", Any],
        high: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Whether value is between low and high (inclusive).

        Substrait: between
        """
        ...

    def is_true(self) -> "BaseNamespace":
        """Whether value is true.

        Substrait: is_true
        """
        ...

    def is_not_true(self) -> "BaseNamespace":
        """Whether value is not true.

        Substrait: is_not_true
        """
        ...

    def is_false(self) -> "BaseNamespace":
        """Whether value is false.

        Substrait: is_false
        """
        ...

    def is_not_false(self) -> "BaseNamespace":
        """Whether value is not false.

        Substrait: is_not_false
        """
        ...

    def is_null(self) -> "BaseNamespace":
        """Whether value is null. NaN is not null.

        Substrait: is_null
        """
        ...

    def is_not_null(self) -> "BaseNamespace":
        """Whether value is not null. NaN is not null.

        Substrait: is_not_null
        """
        ...

    def is_nan(self) -> "BaseNamespace":
        """Whether value is NaN.

        Substrait: is_nan
        """
        ...

    def is_finite(self) -> "BaseNamespace":
        """Whether value is finite (neither infinite nor NaN).

        Substrait: is_finite
        """
        ...

    def is_infinite(self) -> "BaseNamespace":
        """Whether value is infinite.

        Substrait: is_infinite
        """
        ...

    def nullif(self, other: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return null if values are equal, otherwise return first value.

        Substrait: nullif
        """
        ...

    def coalesce(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return first non-null value.

        Substrait: coalesce
        """
        ...

    def least(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return smallest value. Returns null if any argument is null.

        Substrait: least
        """
        ...

    def least_skip_null(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return smallest value, skipping nulls.

        Substrait: least_skip_null
        """
        ...

    def greatest(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return largest value. Returns null if any argument is null.

        Substrait: greatest
        """
        ...

    def greatest_skip_null(self, *others: Union["BaseNamespace", "ExpressionNode", Any]) -> "BaseNamespace":
        """Return largest value, skipping nulls.

        Substrait: greatest_skip_null
        """
        ...
