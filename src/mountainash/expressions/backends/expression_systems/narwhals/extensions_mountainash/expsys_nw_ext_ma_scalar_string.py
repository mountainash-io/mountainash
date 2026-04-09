"""Narwhals MountainAsh string extension implementation.

Implements regex_contains natively using Narwhals str.contains (regex by default).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


class SubstraitNarwhalsScalarStringExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of MountainAsh string extensions."""

    def regex_contains(
        self,
        input: NarwhalsExpr,
        /,
        *,
        pattern: str,
        case_sensitivity: Any = None,
    ) -> NarwhalsExpr:
        """Regex containment via Narwhals str.contains (regex by default).

        Note: narwhals/pandas may return False (not None) for null input.
        """
        return input.str.contains(pattern)
