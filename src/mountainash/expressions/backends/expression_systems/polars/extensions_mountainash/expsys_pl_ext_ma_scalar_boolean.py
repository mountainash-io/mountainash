"""Polars MountainAsh boolean extension implementation.

Implements xor_parity for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class MountainAshPolarsScalarBooleanExpressionSystem(PolarsBaseExpressionSystem, MountainAshScalarBooleanExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of MountainAsh boolean extensions."""


    def xor_parity(self, a: PolarsExpr, b: PolarsExpr, /) -> PolarsExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.
        The API builder chains binary pairs for >2 operands.

        Returns null if either input is null.
        """
        return a ^ b
