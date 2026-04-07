"""Ibis MountainAsh string extension implementation.

Implements regex_contains natively using Ibis re_search.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarStringExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisBooleanExpr


class SubstraitIbisScalarStringExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarStringExpressionSystemProtocol["IbisBooleanExpr"]):
    """Ibis implementation of MountainAsh string extensions."""

    def regex_contains(
        self,
        input,
        /,
        pattern,
        case_sensitivity: Any = None,
    ):
        """Regex containment via Ibis re_search.

        re_search returns a true boolean and propagates null on null input.
        """
        return input.re_search(pattern)
