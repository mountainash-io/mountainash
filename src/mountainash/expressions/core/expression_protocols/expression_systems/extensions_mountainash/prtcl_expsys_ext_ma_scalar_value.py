"""Mountainash value classification extension protocol.

Mountainash Extension: Value
URI: file://extensions/functions_value.yaml
"""
from __future__ import annotations

from typing import Literal, Protocol

from mountainash.core.dtypes import CanonicalDtype
from mountainash.core.types import ExpressionT


class MountainAshScalarValueExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for value-domain classification and projection."""

    def value_kind(self, x: ExpressionT, /) -> ExpressionT:
        """Return the admitted scalar-domain label for ``x``."""
        ...

    def boolean_value(
        self,
        x: ExpressionT,
        /,
        *,
        source: Literal["boolean", "binary_number", "finite_number"] = "boolean",
    ) -> ExpressionT:
        """Project one selected Boolean-producing domain from ``x``."""
        ...

    def text_value(self, x: ExpressionT, /) -> ExpressionT:
        """Return text values without stringifying another scalar domain."""
        ...

    def numeric_cast(
        self,
        x: ExpressionT,
        /,
        *,
        dtype: CanonicalDtype,
        rounding: Literal["TIE_TO_EVEN", "TIE_AWAY_FROM_ZERO"],
        failure_behavior: Literal["throw", "null"],
    ) -> ExpressionT:
        """Convert exact numeric/lexical values under explicit operation policies."""
        ...
