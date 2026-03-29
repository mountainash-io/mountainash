"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode


class SubstraitScalarComparisonAPIBuilderProtocol(Protocol):
    """Builder protocol for comparison operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseExpressionAPI for chaining.
    """

    def equal(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Equal comparison (==).

        Substrait: equal
        """
        ...


    def not_equal(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Not equal comparison (!=).

        Substrait: not_equal
        """
        ...


    def lt(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Less than comparison (<).

        Substrait: lt
        """
        ...

    def gt(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Greater than comparison (>).

        Substrait: gt
        """
        ...

    def lte(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Less than or equal comparison (<=).

        Substrait: lte
        """
        ...

    def gte(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Greater than or equal comparison (>=).

        Substrait: gte
        """
        ...

    def between(
        self,
        low: Union[BaseExpressionAPI, ExpressionNode, Any],
        high: Union[BaseExpressionAPI, ExpressionNode, Any],
        closed: str
    ) -> BaseExpressionAPI:
        """Whether value is between low and high (inclusive).

        Substrait: between
        """
        ...

    def is_true(self) -> BaseExpressionAPI:
        """Whether value is true.

        Substrait: is_true
        """
        ...

    def is_not_true(self) -> BaseExpressionAPI:
        """Whether value is not true.

        Substrait: is_not_true
        """
        ...

    def is_false(self) -> BaseExpressionAPI:
        """Whether value is false.

        Substrait: is_false
        """
        ...

    def is_not_false(self) -> BaseExpressionAPI:
        """Whether value is not false.

        Substrait: is_not_false
        """
        ...

    def is_null(self) -> BaseExpressionAPI:
        """Whether value is null. NaN is not null.

        Substrait: is_null
        """
        ...

    def is_not_null(self) -> BaseExpressionAPI:
        """Whether value is not null. NaN is not null.

        Substrait: is_not_null
        """
        ...

    def is_nan(self) -> BaseExpressionAPI:
        """Whether value is NaN.

        Substrait: is_nan
        """
        ...

    def is_finite(self) -> BaseExpressionAPI:
        """Whether value is finite (neither infinite nor NaN).

        Substrait: is_finite
        """
        ...

    def is_infinite(self) -> BaseExpressionAPI:
        """Whether value is infinite.

        Substrait: is_infinite
        """
        ...

    def nullif(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Return null if values are equal, otherwise return first value.

        Substrait: nullif
        """
        ...

    def coalesce(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Return first non-null value.

        Substrait: coalesce
        """
        ...

    def least(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Return smallest value. Returns null if any argument is null.

        Substrait: least
        """
        ...

    def least_skip_null(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Return smallest value, skipping nulls.

        Substrait: least_skip_null
        """
        ...

    def greatest(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Return largest value. Returns null if any argument is null.

        Substrait: greatest
        """
        ...

    def greatest_skip_null(self, *others: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
        """Return largest value, skipping nulls.

        Substrait: greatest_skip_null
        """
        ...
