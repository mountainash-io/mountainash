"""Mountainash categorical API builder protocol."""
from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING

from ..substrait.prtcl_api_bldr_cast import CaseFailureBehaviour

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI


class MountainAshScalarCategoricalAPIBuilderProtocol(Protocol):
    """User-facing categorical namespace methods."""

    def cast(
        self,
        *,
        value_type: str,
        categories: tuple[Any, ...],
        ordered: bool,
        field_name: str,
        failure_behavior: CaseFailureBehaviour = CaseFailureBehaviour.THROW,
    ) -> BaseExpressionAPI:
        """Cast to the categorical base scalar without encoding categories."""
        ...
