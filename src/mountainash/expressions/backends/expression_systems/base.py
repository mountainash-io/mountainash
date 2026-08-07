"""Base classes for backend expression systems.

This module provides shared base classes and utilities used by all backend
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.constants import CONST_BACKEND


class BaseExpressionSystem(ABC):
    """Abstract base class for all backend expression systems.

    Each backend (Polars, Narwhals, Ibis) should inherit from this class
    and implement the required abstract methods.
    """

    @property
    @abstractmethod
    def backend_type(self) -> "CONST_BACKEND":
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

    BACKEND_NAME: str = "unknown"

    def __init__(self, dialect: str | None = None) -> None:
        self.dialect = dialect

    def _call_with_expr_support(
        self,
        fn: Any,
        *,
        function_key: Any,
        **named_args: Any,
    ) -> Any:
        """Call a native backend op, enriching known-limitation failures.

        Registry-sourced: only MATERIALIZE_RESIDUE facts participate;
        GATE facts gate at the visitor and never reach here.
        """
        from mountainash.core.capabilities import (
            CapabilityRegistry,
            Enforcement,
            WILDCARD_PARAM,
        )
        from mountainash.core.limitations import call_with_limitation_enrichment

        limitations: dict[tuple[Any, str], Any] = {}
        for param in (*named_args, WILDCARD_PARAM):
            fact = CapabilityRegistry.capability_for(
                function_key, param, self.backend_type, self.dialect
            )
            if (
                fact is not None
                and fact.enforcement is Enforcement.MATERIALIZE_RESIDUE
            ):
                limitations[(function_key, param)] = fact
        return call_with_limitation_enrichment(
            fn,
            limitations=limitations,
            backend_name=self.BACKEND_NAME,
            operation_key=function_key,
            named_args=tuple(named_args),
        )
