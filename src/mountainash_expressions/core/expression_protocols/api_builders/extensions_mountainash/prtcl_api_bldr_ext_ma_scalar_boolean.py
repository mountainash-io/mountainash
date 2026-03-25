"""Mountainash boolean extension protocol.

Mountainash Extension: Boolean
URI: file://extensions/functions_boolean.yaml

Extensions beyond Substrait standard:
- xor_parity: XOR parity check (odd number of TRUE values)
"""

from __future__ import annotations

from typing import Union, Any,Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_api import BaseExpressionAPI
    from mountainash_expressions.core.expression_nodes import ExpressionNode

class MountainAshScalarBooleanAPIBuilderProtocol(Protocol):
    """Builder protocol for Mountainash boolean extensions.

    These operations extend beyond the Substrait standard boolean
    functions to provide additional boolean operations.
    """

    def always_true(self) -> BaseExpressionAPI:
        """Boolean constant TRUE."""
        ...

    def always_false(self) -> BaseExpressionAPI:
        """Boolean constant FALSE."""
        ...

    def xor_parity(
        self,
        *others: Union[BaseExpressionAPI, ExpressionNode, Any],
    ) -> BaseExpressionAPI:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Returns null if either input is null.

        Args:
            a: First boolean expression.
            b: Second boolean expression.

        Returns:
            Boolean result of parity check.
        """
        ...
