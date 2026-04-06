"""Base classes for backend expression systems.

This module provides shared base classes and utilities used by all backend
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.constants import CONST_VISITOR_BACKENDS
    from mountainash.core.types import KnownLimitation


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

    # Class-level registry for known expression argument limitations.
    KNOWN_EXPR_LIMITATIONS: dict[tuple[str, str], "KnownLimitation"] = {}

    BACKEND_NAME: str = "unknown"

    def _extract_literal_if_possible(self, expr: Any) -> Any:
        """Extract the raw Python value from a literal expression, if possible.

        Some native APIs (e.g., Narwhals/Pandas str methods) require raw Python
        values, not expression objects, even for literal values. This method
        unwraps literal expressions back to raw values. Column references and
        complex expressions pass through unchanged.
        """
        return expr

    def _call_with_expr_support(
        self,
        fn: Any,
        *,
        function_key: str,
        **named_args: Any,
    ) -> Any:
        """Call a native backend function, enriching errors for known limitations.

        Args:
            fn: Zero-arg callable that invokes the native backend operation.
            function_key: The FKEY_* enum value for registry lookup.
            **named_args: Parameter names mapped to their values, used to
                identify which parameter caused the error in registry lookup.
        """
        try:
            return fn()
        except Exception as exc:
            for param_name in named_args:
                key = (function_key, param_name)
                limitation = self.KNOWN_EXPR_LIMITATIONS.get(key)
                if limitation and isinstance(exc, limitation.native_errors):
                    from mountainash.core.types import BackendCapabilityError

                    raise BackendCapabilityError(
                        limitation.message,
                        backend=self.BACKEND_NAME,
                        function_key=function_key,
                        limitation=limitation,
                    ) from exc
            raise
