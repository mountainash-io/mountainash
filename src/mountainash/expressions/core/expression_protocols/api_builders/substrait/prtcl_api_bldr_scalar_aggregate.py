"""Protocol for Substrait scalar aggregate api_builder methods."""
from __future__ import annotations

from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api.api_base import BaseExpressionAPI


class SubstraitScalarAggregateAPIBuilderProtocol(Protocol):
    """Substrait-standard scalar aggregate builder surface."""

    def count(self, *, overflow: Optional[str] = None) -> "BaseExpressionAPI":
        """Count non-null values of this column.

        Corresponds to Substrait ``count(x)``.
        """
        ...
