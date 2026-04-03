"""Substrait DateTime operations APIBuilder.

Substrait-aligned implementation for timezone and formatting operations only.
All other datetime operations (extraction, arithmetic, truncation, etc.)
are in MountainAshScalarDatetimeAPIBuilder (the extension builder).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
    FKEY_MOUNTAINASH_SCALAR_DATETIME,
)
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait import (
    SubstraitScalarDatetimeAPIBuilderProtocol,
)


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI


class SubstraitScalarDatetimeAPIBuilder(
    BaseExpressionAPIBuilder,
    SubstraitScalarDatetimeAPIBuilderProtocol,
):
    """Substrait datetime operations (timezone and formatting only).

    Substrait defines: local_timestamp, assume_timezone, strftime.
    All other datetime operations are in MountainAshScalarDatetimeAPIBuilder.
    """

    def local_timestamp(self, timezone: str) -> BaseExpressionAPI:
        """Get current timestamp in the specified timezone.

        Substrait: local_timestamp

        Args:
            timezone: IANA timezone name (e.g., "America/New_York", "UTC").

        Returns:
            New ExpressionAPI with local_timestamp node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP,
            arguments=[self._node],
            options={"timezone": timezone},
        )
        return self._build(node)

    def assume_timezone(self, timezone: str) -> BaseExpressionAPI:
        """Assume the timestamp is in the specified timezone.

        Converts a local timestamp to UTC-relative timestamp
        using the given timezone.

        Substrait: assume_timezone

        Args:
            timezone: IANA timezone name (e.g., "America/New_York", "UTC").

        Returns:
            New ExpressionAPI with assume_timezone node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ASSUME_TIMEZONE,
            arguments=[self._node],
            options={"timezone": timezone},
        )
        return self._build(node)

    def strftime(self, format: str) -> BaseExpressionAPI:
        """Format datetime as string.

        Uses strftime format codes.

        Substrait: strftime

        Args:
            format: Format string (e.g., "%Y-%m-%d %H:%M:%S").

        Returns:
            New ExpressionAPI with strftime node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.STRFTIME,
            arguments=[self._node],
            options={"format": format},
        )
        return self._build(node)
