"""Ibis ScalarBooleanExpressionProtocol implementation.

Implements boolean logical operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import IbisExpr


class SubstraitIbisScalarBooleanExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarBooleanExpressionSystemProtocol):
    """Ibis implementation of ScalarBooleanExpressionProtocol.

    Implements 5 boolean methods using Kleene (three-valued) logic:
    - and_: Boolean AND (returns false if any false, null if any null and no false)
    - or_: Boolean OR (returns true if any true, null if any null and no true)
    - not_: Boolean NOT (negation)
    - xor: Boolean XOR (exclusive or)
    - and_not: Boolean AND of first value with negation of second
    """


    def xor_parity(self, a: IbisExpr, b: IbisExpr, /) -> IbisExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Returns null if either input is null.
        """
        return a ^ b
