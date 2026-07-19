"""Base classes for backend expression systems.

This module provides shared base classes and utilities used by all backend
implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.constants import CONST_BACKEND
    from mountainash.core.types import KnownLimitation


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

    # Class-level registry for known expression argument limitations.
    # Keys are (function_key_enum_value, param_name) tuples.
    KNOWN_EXPR_LIMITATIONS: dict[tuple[Any, str], "KnownLimitation"] = {}

    BACKEND_NAME: str = "unknown"

    def __init__(self, dialect: str | None = None) -> None:
        self.dialect = dialect

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
        function_key: Any,
        **named_args: Any,
    ) -> Any:
        """Call a native backend op, enriching known-limitation failures.

        Registry-first (migrated backends + conditioned MATERIALIZE facts),
        class-dict fallback (unmigrated backends keep their old enrichment —
        the per-backend-safe-migration invariant). Only facts with
        native_errors participate; BUILD facts gate at the visitor and never
        reach here.
        """
        from mountainash.core.capabilities import CapabilityRegistry
        from mountainash.core.limitations import call_with_limitation_enrichment

        limitations = dict(self.KNOWN_EXPR_LIMITATIONS)
        for param in named_args:
            fact = CapabilityRegistry.capability_for(
                function_key, param, self.backend_type, self.dialect
            )
            if fact is not None and fact.native_errors:
                limitations[(function_key, param)] = fact
        return call_with_limitation_enrichment(
            fn,
            limitations=limitations,
            backend_name=self.BACKEND_NAME,
            operation_key=function_key,
            named_args=tuple(named_args),
        )


from mountainash.core.capabilities.core_facts import (  # noqa: E402
    register_core_polymorphic_facts,
)

register_core_polymorphic_facts()  # noqa: E402
