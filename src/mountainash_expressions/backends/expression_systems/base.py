"""Base classes for backend expression systems.

This module provides shared base classes and utilities used by all backend
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS


class BaseExpressionSystem(ABC):
    """Abstract base class for all backend expression systems.

    Each backend (Polars, Narwhals, Ibis) should inherit from this class
    and implement the required abstract methods.
    """

    @property
    @abstractmethod
    def backend_type(self) -> "CONST_VISITOR_BACKENDS":
        """Return the backend type identifier."""
        ...

    @abstractmethod
    def is_native_expression(self, expr: Any) -> bool:
        """Check if the given expression is native to this backend.

        Args:
            expr: Any expression object to check.

        Returns:
            True if expr is a native expression type for this backend.
        """
        ...
