"""Polars backend implementation of ExpressionSystem."""

from typing import Any, List
import polars as pl

from ....core.expression_system import ExpressionSystem
from ....core.constants import CONST_VISITOR_BACKENDS


class IbisBaseExpressionSystem(ExpressionSystem):
    """
    Ibis-specific implementation of ExpressionSystem.

    This class encapsulates all Ibis-specific operations,
    allowing visitors to build expressions without direct knowledge
    of the Ibis API.
    """

    @property
    def backend_type(self) -> CONST_VISITOR_BACKENDS:
        """Return Polars backend type."""
        return CONST_VISITOR_BACKENDS.IBIS

    # ========================================
    # Core Primitives
    # ========================================
