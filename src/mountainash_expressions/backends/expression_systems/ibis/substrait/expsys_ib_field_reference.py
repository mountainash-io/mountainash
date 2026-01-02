"""Ibis FieldReferenceExpressionProtocol implementation.

Implements column reference operations for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem
from mountainash_expressions.core.expression_protocols.expression_systems.substrait import SubstraitFieldReferenceExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash_expressions.types import IbisExpr


class SubstraitIbisFieldReferenceExpressionSystem(IbisBaseExpressionSystem, SubstraitFieldReferenceExpressionSystemProtocol):
    """Ibis implementation of FieldReferenceExpressionProtocol."""

    def col(self, x: str) -> IbisExpr:
        """Create a column reference expression.

        Args:
            x: The column name to reference.

        Returns:
            An Ibis expression referencing the named column.
        """
        # Use the deferred expression pattern
        return ibis._[x]
