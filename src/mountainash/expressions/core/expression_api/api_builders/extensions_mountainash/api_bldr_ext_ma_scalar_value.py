"""Mountainash value classification and projection API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from mountainash.core.value_classification import _validate_boolean_source
from mountainash.expressions.core.expression_api.api_builders.api_builder_base import (
    BaseExpressionAPIBuilder,
)
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import (
    MountainAshScalarValueAPIBuilderProtocol,
)
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_VALUE,
)

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarValueAPIBuilder(
    BaseExpressionAPIBuilder, MountainAshScalarValueAPIBuilderProtocol
):
    """Build backend-agnostic value-domain classification expressions."""

    def value_kind(self) -> BaseExpressionAPI:
        """Return the admitted scalar-domain label for this expression."""
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_VALUE.VALUE_KIND,
                arguments=[self._node],
            )
        )

    def boolean_value(
        self,
        *,
        source: Literal["boolean", "binary_number", "finite_number"] = "boolean",
    ) -> BaseExpressionAPI:
        """Project one selected Boolean-producing domain from this expression."""
        _validate_boolean_source(source)
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_VALUE.BOOLEAN_VALUE,
                arguments=[self._node],
                options={"source": source},
            )
        )

    def text_value(self) -> BaseExpressionAPI:
        """Return text values without stringifying another scalar domain."""
        return self._build(
            ScalarFunctionNode(
                function_key=FKEY_MOUNTAINASH_SCALAR_VALUE.TEXT_VALUE,
                arguments=[self._node],
            )
        )
