"""Mountainash boolean extension protocol.

Mountainash Extension: Boolean
URI: file://extensions/functions_boolean.yaml

Extensions beyond Substrait standard:
- xor_parity: XOR parity check (odd number of TRUE values)
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.types import SupportedExpressions


class MountainAshScalarBooleanExpressionSystemProtocol(Protocol):
    """Backend protocol for Mountainash boolean extensions.

    These operations extend beyond the Substrait standard boolean
    functions to provide additional boolean operations.
    """

    def xor_parity(
        self,
        *args: SupportedExpressions
    ) -> SupportedExpressions:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Returns null if either input is null.

        Args:
            a: boolean expressions.

        Returns:
            Boolean result of parity check.
        """
        ...
