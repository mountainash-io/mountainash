"""Ibis MountainashNullExpressionProtocol implementation.

Implements null handling extensions for the Ibis backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import ibis

from ..base import IbisBaseExpressionSystem

if TYPE_CHECKING:
    from mountainash_expressions.core.expression_protocols.mountainash_extensions import (
        MountainashNullExpressionProtocol,
    )

# Type alias for expression type
from mountainash_expressions.types import IbisExpr


class IbisMAExtNullExpressionSystem(IbisBaseExpressionSystem, MountainashNullExpressionProtocol):
    """Ibis implementation of MountainashNullExpressionProtocol.

    Implements null handling extension methods:
    - fill_null: Replace NULL values with a specified value
    - null_if: Replace values equal to a specified value with NULL
    """

    def fill_null(
        self,
        input: IbisExpr,
        replacement: IbisExpr,
        /,
    ) -> IbisExpr:
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
        input: IbisExpr,
        value: IbisExpr,
        /,
    ) -> IbisExpr:
        """Replace values equal to the specified value with NULL.

        Args:
            input: Expression to check.
            value: Value that should become NULL.

        Returns:
            Expression with matching values replaced by NULL.
        """
        return input.nullif(value)
