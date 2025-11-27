"""Ibis core operations implementation."""

from typing import Any
import ibis

from .base import IbisBaseExpressionSystem
from ....core.protocols import CoreExpressionProtocol


class IbisCoreExpressionSystem(IbisBaseExpressionSystem,
                                 CoreExpressionProtocol):
    """Ibis implementation of core operations."""

    def col(self, name: str, **kwargs) -> Any:
        """Create an Ibis column reference using ibis._[name]."""
        return ibis._[name]

    def lit(self, value: Any) -> Any:
        """Create an Ibis literal value expression."""
        return ibis.literal(value)
