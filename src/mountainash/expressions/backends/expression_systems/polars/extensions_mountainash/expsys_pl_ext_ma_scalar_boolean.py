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

    def parse_boolean(
        self,
        x: PolarsExpr,
        /,
        *,
        true_values: tuple[str, ...],
        false_values: tuple[str, ...],
        failure_behavior: str = "throw",
    ) -> PolarsExpr:
        text = x.cast(pl.String)
        if failure_behavior == "null":
            return (
                pl.when(text.is_in(true_values)).then(pl.lit(True))
                .when(text.is_in(false_values)).then(pl.lit(False))
                .otherwise(pl.lit(None, dtype=pl.Boolean))
            )
        mapped = (
            pl.when(text.is_in(true_values)).then(pl.lit(1))
            .when(text.is_in(false_values)).then(pl.lit(0))
            .when(text.is_null()).then(pl.lit(None))
            .otherwise(pl.lit("__invalid_boolean_token__"))
        )
        return mapped.cast(pl.Int8, strict=True).cast(pl.Boolean)


    def xor_parity(self, a: PolarsExpr, b: PolarsExpr, /) -> PolarsExpr:
        """XOR parity check (odd number of TRUE values).

        Returns TRUE if an odd number of operands are TRUE.
        For two operands, this is equivalent to XOR.
        The API builder chains binary pairs for >2 operands.

        Returns null if either input is null.
        """
        return a ^ b
