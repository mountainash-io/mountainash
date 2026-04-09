"""Polars MountainAsh string extension implementation.

Implements regex_contains natively using Polars' str.contains with literal=False.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsScalarStringExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of MountainAsh string extensions."""

    def regex_contains(
        self,
        input: PolarsExpr,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ) -> PolarsExpr:
        """Regex containment via Polars str.contains(literal=False).

        Polars str.contains propagates null on null input, returning a
        true boolean (no extract/null-mismatch hack needed).
        """
        return input.str.contains(pattern, literal=False)
