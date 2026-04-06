"""Narwhals MountainashNullExpressionProtocol implementation.

Implements null handling extensions for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNullExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class MountainAshNarwhalsNullExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshNullExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of MountainashNullExpressionProtocol.

    Implements null handling extension methods:
    - fill_null: Replace NULL values with a specified value
    - null_if: Replace values equal to a specified value with NULL
    """

    def fill_null(
        self,
        input: NarwhalsExpr,
        replacement: Any,
        /,
    ) -> NarwhalsExpr:
        """Replace NULL values with the specified replacement value.

        Args:
            input: Expression that may contain NULL values.
            replacement: Value to use in place of NULLs.

        Returns:
            Expression with NULLs replaced by the replacement value.
        """
        return input.fill_null(replacement)

    def null_if(
        self,
        input: NarwhalsExpr,
        condition: Any,
        /,
    ) -> NarwhalsExpr:
        """Replace values equal to condition with NULL.

        SQL NULLIF(input, condition) semantics.
        """
        return nw.when(input == condition).then(None).otherwise(input)

    def fill_nan(
        self,
        input: NarwhalsExpr,
        replacement: Any,
        /,
    ) -> NarwhalsExpr:
        return nw.when(input.is_nan()).then(replacement).otherwise(input)

