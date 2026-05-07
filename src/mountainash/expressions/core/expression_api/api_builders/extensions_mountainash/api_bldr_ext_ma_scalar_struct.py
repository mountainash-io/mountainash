"""Struct operations API builder."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder
from mountainash.expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarStructAPIBuilderProtocol
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_STRUCT
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainAshScalarStructAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarStructAPIBuilderProtocol):
    """API builder for the .struct namespace."""

    def field(self, name: str) -> BaseExpressionAPI:
        """Extract a named field from a struct column.

        Args:
            name: Field name to extract.

        Returns:
            Expression containing the extracted field value.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_STRUCT.FIELD,
            arguments=[self._node],
            options={"field_name": name},
        )
        return self._build(node)
