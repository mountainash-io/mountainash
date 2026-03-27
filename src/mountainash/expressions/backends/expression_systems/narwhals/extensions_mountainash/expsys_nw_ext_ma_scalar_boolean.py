"""Narwhals ScalarBooleanExpressionProtocol implementation.

Implements boolean logical operations for the Narwhals backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsScalarBooleanExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarBooleanExpressionSystemProtocol):
    """Narwhals implementation of ScalarBooleanExpressionProtocol.

    Implements 5 boolean methods using Kleene (three-valued) logic:
    - and_: Boolean AND (returns false if any false, null if any null and no false)
    - or_: Boolean OR (returns true if any true, null if any null and no true)
    - not_: Boolean NOT (negation)
    - xor: Boolean XOR (exclusive or)
    - and_not: Boolean AND of first value with negation of second
    """


    def xor_parity(self, a: NarwhalsExpr, b: NarwhalsExpr, /) -> NarwhalsExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Note: Narwhals doesn't support the ^ operator directly,
        so we use the logical equivalence: (a | b) & ~(a & b)
        """
        return (a | b) & ~(a & b)
