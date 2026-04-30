"""Ibis MountainAsh boolean extension implementation.

Implements xor_parity for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisBooleanExpr


class MountainAshIbisScalarBooleanExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarBooleanExpressionSystemProtocol["IbisBooleanExpr"]):
    """Ibis implementation of MountainAsh boolean extensions."""


    def xor_parity(self, a: IbisBooleanExpr, b: IbisBooleanExpr, /) -> IbisBooleanExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Returns null if either input is null.
        """
        return a ^ b
