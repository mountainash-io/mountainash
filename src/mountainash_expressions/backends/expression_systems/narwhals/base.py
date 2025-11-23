"""Polars backend implementation of ExpressionSystem."""

from typing import Any, List
# import polars as pl

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class NarwhalsBaseExpressionSystem(ExpressionSystem):
    """
    Narwhals-specific implementation of ExpressionSystem.

    This class encapsulates all Narwhals-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Narwhals API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Polars backend type."""
        return CONST_VISITOR_BACKENDS.NARWHALS
