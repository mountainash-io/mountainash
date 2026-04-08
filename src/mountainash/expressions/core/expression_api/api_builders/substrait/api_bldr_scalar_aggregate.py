"""Substrait scalar aggregate APIBuilder — exposes count() and future sum/min/max/etc."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_AGGREGATE,
)
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_scalar_aggregate import (
    SubstraitScalarAggregateAPIBuilderProtocol,
)

from ..api_builder_base import BaseExpressionAPIBuilder

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class SubstraitScalarAggregateAPIBuilder(
    BaseExpressionAPIBuilder,
    SubstraitScalarAggregateAPIBuilderProtocol,
):
    """Substrait-standard aggregate operations exposed as instance methods on col().

    Extend this class (or add sibling classes) for future Substrait aggregates
    (sum, min, max, mean, first_value, last_value, any_value, etc.).
    """

    def count(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Count non-null values. Corresponds to Substrait ``count(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def any_value(self, *, ignore_nulls: Optional[bool] = None) -> "BaseExpressionAPI":
        """Return one representative value from the group. Substrait ``any_value(x)``.

        Note: nondeterministic — different backends may return different
        representative values across runs.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.ANY_VALUE,
            arguments=[self._node],
            options={"ignore_nulls": ignore_nulls} if ignore_nulls is not None else {},
        )
        return self._build(node)

    def sum(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Sum a set of values. Returns null for empty input. Substrait ``sum(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.SUM,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def avg(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Arithmetic mean. Substrait ``avg(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.AVG,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def min(self) -> "BaseExpressionAPI":
        """Minimum value. Substrait ``min(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MIN,
            arguments=[self._node],
            options={},
        )
        return self._build(node)

    def max(self) -> "BaseExpressionAPI":
        """Maximum value. Substrait ``max(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MAX,
            arguments=[self._node],
            options={},
        )
        return self._build(node)

    def product(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Product of values. Substrait ``product(x)``."""
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.PRODUCT,
            arguments=[self._node],
            options={"overflow": overflow} if overflow is not None else {},
        )
        return self._build(node)

    def std_dev(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Standard deviation. Substrait ``std_dev(x)``."""
        opts: dict = {}
        if rounding is not None:
            opts["rounding"] = rounding
        if distribution is not None:
            opts["distribution"] = distribution
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.STD_DEV,
            arguments=[self._node],
            options=opts,
        )
        return self._build(node)

    def variance(
        self,
        *,
        rounding: Optional[str] = None,
        distribution: Optional[str] = None,
    ) -> "BaseExpressionAPI":
        """Variance. Substrait ``variance(x)``."""
        opts: dict = {}
        if rounding is not None:
            opts["rounding"] = rounding
        if distribution is not None:
            opts["distribution"] = distribution
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.VARIANCE,
            arguments=[self._node],
            options=opts,
        )
        return self._build(node)

    def mode(self) -> "BaseExpressionAPI":
        """Most common value. Substrait ``mode(x)``.

        Note: behaviour on ties varies across backends — see
        ``e.cross-backend/known-divergences.md``.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.MODE,
            arguments=[self._node],
            options={},
        )
        return self._build(node)
