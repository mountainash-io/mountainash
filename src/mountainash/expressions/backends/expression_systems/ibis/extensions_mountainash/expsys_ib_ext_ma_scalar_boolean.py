"""Ibis MountainAsh boolean extension implementation.

Implements xor_parity for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshScalarBooleanExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisBooleanExpr


class MountainAshIbisScalarBooleanExpressionSystem(IbisBaseExpressionSystem, MountainAshScalarBooleanExpressionSystemProtocol["IbisBooleanExpr"]):
    """Ibis implementation of MountainAsh boolean extensions."""

    def parse_boolean(
        self,
        x: IbisBooleanExpr,
        /,
        *,
        true_values: tuple[str, ...],
        false_values: tuple[str, ...],
        failure_behavior: str = "throw",
    ) -> IbisBooleanExpr:
        text = x.cast("string")
        if failure_behavior == "null":
            return ibis.cases(
                (text.isin(true_values), ibis.literal(True)),
                (text.isin(false_values), ibis.literal(False)),
                else_=ibis.null(),
            )
        parsed = ibis.cases(
            (text.isin(true_values), ibis.literal(1)),
            (text.isin(false_values), ibis.literal(0)),
            (text.isnull(), ibis.null()),
            else_=ibis.literal("__invalid_boolean_token__"),
        )
        return parsed.cast("int8").cast("boolean")

    def xor_parity(self, a: IbisBooleanExpr, b: IbisBooleanExpr, /) -> IbisBooleanExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Returns null if either input is null.
        """
        return a ^ b
