"""API-builder protocol for the Mountainash cast surface (``rounding=`` for decimal targets)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Protocol, Union

from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import (
    CaseFailureBehaviour,  # noqa: TC001 - runtime get_type_hints() resolution
)

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshCastAPIBuilderProtocol(Protocol):
    """Fluent API contract for ``.cast`` with an explicit decimal rounding mode."""

    def cast(
        self,
        dtype: Union[str, type, Any],
        *,
        failure_behavior: Optional[CaseFailureBehaviour] = CaseFailureBehaviour.THROW,
        rounding: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """Cast to ``dtype``; ``rounding`` is required for ``DecimalDtype`` targets, rejected otherwise."""
        ...
