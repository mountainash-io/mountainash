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

    def parse_boolean(
        self,
        x: NarwhalsExpr,
        /,
        *,
        true_values: tuple[str, ...],
        false_values: tuple[str, ...],
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        text = x.cast(nw.String)
        if failure_behavior == "null":
            return (
                nw.when(text.is_in(true_values)).then(nw.lit(True))
                .when(text.is_in(false_values)).then(nw.lit(False))
                .otherwise(nw.lit(None))
            )
        mapped = (
            nw.when(text.is_in(true_values)).then(nw.lit(1))
            .when(text.is_in(false_values)).then(nw.lit(0))
            .when(text.is_null()).then(nw.lit(None))
            .otherwise(nw.lit("__invalid_boolean_token__"))
        )
        return mapped.cast(nw.Int8).cast(nw.Boolean)


    def xor_parity(self, a: NarwhalsExpr, b: NarwhalsExpr, /) -> NarwhalsExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.

        Note: Narwhals doesn't support the ^ operator directly,
        so we use the logical equivalence: (a | b) & ~(a & b)
        """
        return (a | b) & ~(a & b)
