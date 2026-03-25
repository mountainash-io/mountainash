"""Polars ScalarBooleanExpressionProtocol implementation.

Implements boolean logical operations for the Polars backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import PolarsExpr


# Type alias for expression type

class SubstraitPolarsScalarBooleanExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarBooleanExpressionSystemProtocol):
    """Polars implementation of ScalarBooleanExpressionProtocol.

    Implements 5 boolean methods using Kleene (three-valued) logic:
    - and_: Boolean AND (returns false if any false, null if any null and no false)
    - or_: Boolean OR (returns true if any true, null if any null and no true)
    - not_: Boolean NOT (negation)
    - xor: Boolean XOR (exclusive or)
    - and_not: Boolean AND of first value with negation of second
    """


    def xor_parity(self, a: PolarsExpr, b: PolarsExpr, /) -> PolarsExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.
        The API builder chains binary pairs for >2 operands.

        Returns null if either input is null.
        """
        return a ^ b
