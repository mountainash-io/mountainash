"""Narwhals MountainAsh boolean extension implementation.

Implements xor_parity for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsScalarBooleanExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshScalarBooleanExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of MountainAsh boolean extensions."""


    def xor_parity(self, a: NarwhalsExpr, b: NarwhalsExpr, /) -> NarwhalsExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Note: Narwhals doesn't support the ^ operator directly,
        so we use the logical equivalence: (a | b) & ~(a & b)
        """
        return (a | b) & ~(a & b)
