"""Narwhals MountainashNullExpressionProtocol implementation.

Implements null handling extensions for the Narwhals backend.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash_expressions.core.expression_protocols.expression_systems.extensions_mountainash import MountainAshNullExpressionSystemProtocol


if TYPE_CHECKING:
    from mountainash_expressions.types import NarwhalsExpr


class MountainAshNarwhalsNullExpressionSystem(NarwhalsBaseExpressionSystem, MountainAshNullExpressionSystemProtocol):
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
        # Narwhals fill_null expects a scalar value, not an Expr
        # Extract literal value if possible
        fill_value = self._extract_literal_value(replacement)
        return input.fill_null(fill_value)

    def null_if(
        self,
        input: NarwhalsExpr,
        condition: Any,
        /,
    ) -> NarwhalsExpr:
        """Replace values equal to condition with NULL.

        SQL NULLIF(input, condition) semantics.
        """
        fill_value = self._extract_literal_value(condition)
        return nw.when(input == fill_value).then(None).otherwise(input)

    def fill_nan(
        self,
        input: NarwhalsExpr,
        replacement: Any,
        /,
    ) -> NarwhalsExpr:
        fill_value = self._extract_literal_value(replacement)
        return nw.when(input.is_nan()).then(fill_value).otherwise(input)

