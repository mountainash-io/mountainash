"""Set operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarSetBuilderProtocol for set membership operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from ....expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_SET
from ....expression_protocols.api_builders.extensions_mountainash import MountainAshScalarSetAPIBuilderProtocol
from ....expression_nodes import ExpressionNode, ScalarFunctionNode

from mountainash.expressions.membership.classify import classify_members
from mountainash.expressions.membership.encode import encode_membership

if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class MountainashScalarSetAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarSetAPIBuilderProtocol):
    """Set operations APIBuilder (Substrait-aligned)."""

    def _build_membership_node(
        self,
        values: tuple,
        function_key: str,
    ) -> BaseExpressionAPI:
        """Shared builder: classify → encode → ScalarFunctionNode."""
        members = classify_members(values)
        arguments, options = encode_membership(self._node, members)
        needle_unknown = getattr(self._node, "unknown_values", None)
        if needle_unknown:
            options["unknown_values"] = frozenset(needle_unknown)
        node = ScalarFunctionNode(
            function_key=function_key,
            arguments=arguments,
            options=options,
        )
        return self._build(node)

    def is_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Check if value is in the given set of values."""
        return self._build_membership_node(values, FKEY_MOUNTAINASH_SCALAR_SET.IS_IN)

    def is_not_in(
        self,
        *values: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Check if value is not in the given set of values."""
        return self._build_membership_node(values, FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN)
