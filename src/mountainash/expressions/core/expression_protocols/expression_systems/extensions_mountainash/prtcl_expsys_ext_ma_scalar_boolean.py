"""Mountainash boolean extension protocol.

Mountainash Extension: Boolean
URI: file://extensions/functions_boolean.yaml

Extensions beyond Substrait standard:
- xor_parity: XOR parity check (odd number of TRUE values)
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarBooleanExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash boolean extensions.

    These operations extend beyond the Substrait standard boolean
    functions to provide additional boolean operations.
    """

    def xor_parity(
        self,
        a: ExpressionT,
        b: ExpressionT,
        /,
    ) -> ExpressionT:
        """Binary XOR parity check.

        Returns TRUE if exactly one operand is TRUE.
        The API builder chains binary pairs for >2 operands.

        Returns null if either input is null.
        """
        ...
