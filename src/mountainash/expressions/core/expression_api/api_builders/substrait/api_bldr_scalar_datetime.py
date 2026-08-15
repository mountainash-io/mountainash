"""Substrait DateTime operations APIBuilder.

Substrait-aligned implementation for datetime extraction, timezone, and
formatting operations. Arithmetic and truncation live in
MountainAshScalarDatetimeAPIBuilder (the extension builder).
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Union

from ..api_builder_base import BaseExpressionAPIBuilder, _reject_expression

from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)
from mountainash.expressions.core.datetime_components import CALENDAR_COMPONENTS
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
from mountainash.expressions.core.expression_protocols.api_builders.substrait import (
    SubstraitScalarDatetimeAPIBuilderProtocol,
)


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class SubstraitScalarDatetimeAPIBuilder(
    BaseExpressionAPIBuilder,
    SubstraitScalarDatetimeAPIBuilderProtocol,
):
    """Substrait datetime operations (extraction, timezone, formatting).

    Substrait defines: extract, extract_boolean, local_timestamp,
    assume_timezone, strftime. Arithmetic and truncation are in
    MountainAshScalarDatetimeAPIBuilder.
    """

    def extract(
        self,
        component: str,
        indexing: str = None,
        timezone: str = None,
    ) -> BaseExpressionAPI:
        """Extract a date/time component (Substrait: extract).

        Args:
            component: Closed ``DatetimeComponent`` member (e.g. ``"YEAR"``).
            indexing: ``"ONE"``/``"ZERO"`` (calendar components only; ``None``
                is the omission sentinel and is behaviour-preserving).
            timezone: Optional IANA timezone; converts the value before the
                component lookup.
        """
        from mountainash.core.errors import InvalidOptionValueError
        from ._option_domains import validate_option
        from mountainash.core.capabilities.schema import ValueClass
        from ..extensions_mountainash._ma_option_domains import validate_open_value

        _reject_expression("component", component, "extract")
        component = validate_option("extract", "component", component)
        if indexing is not None:
            indexing = validate_option("extract", "indexing", indexing)
            if component.upper() not in CALENDAR_COMPONENTS:
                raise InvalidOptionValueError(
                    f"extract indexing is only valid on calendar components, "
                    f"got {component!r}"
                )
        if timezone is not None:
            _reject_expression("timezone", timezone, "extract")
            timezone = validate_open_value(
                ValueClass.IANA_TIMEZONE, "timezone", timezone, "extract"
            )
        options = {"component": component}
        if indexing is not None:
            options["indexing"] = indexing
        if timezone is not None:
            options["timezone"] = timezone
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
            arguments=[self._node],
            options=options,
        )
        return self._build(node)

    def extract_boolean(
        self,
        component: str,
        timezone: str = None,
    ) -> BaseExpressionAPI:
        """Extract a boolean date/time component (Substrait: extract_boolean).

        Args:
            component: Closed ``BooleanComponent`` member (``IS_LEAP_YEAR`` /
                ``IS_DST``).
            timezone: Optional IANA timezone. Required for ``IS_DST``.
        """
        from mountainash.core.errors import InvalidOptionValueError
        from ._option_domains import validate_option
        from mountainash.core.capabilities.schema import ValueClass
        from ..extensions_mountainash._ma_option_domains import validate_open_value

        _reject_expression("component", component, "extract_boolean")
        component = validate_option("extract_boolean", "component", component)
        if component.upper() == "IS_DST" and timezone is None:
            raise InvalidOptionValueError(
                "extract_boolean(IS_DST) requires a timezone"
            )
        if timezone is not None:
            _reject_expression("timezone", timezone, "extract_boolean")
            timezone = validate_open_value(
                ValueClass.IANA_TIMEZONE, "timezone", timezone, "extract_boolean"
            )
        options = {"component": component}
        if timezone is not None:
            options["timezone"] = timezone
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
            arguments=[self._node],
            options=options,
        )
        return self._build(node)

    def local_timestamp(self, timezone: str) -> BaseExpressionAPI:
        """Get current timestamp in the specified timezone.

        Substrait: local_timestamp

        Args:
            timezone: IANA timezone name (e.g., "America/New_York", "UTC").

        Returns:
            New ExpressionAPI with local_timestamp node.
        """
        _reject_expression("timezone", timezone, "local_timestamp")
        from mountainash.core.capabilities.schema import ValueClass
        from ..extensions_mountainash._ma_option_domains import validate_open_value

        timezone = validate_open_value(
            ValueClass.IANA_TIMEZONE, "timezone", timezone, "local_timestamp"
        )
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
        _reject_expression("timezone", timezone, "assume_timezone")
        from mountainash.core.capabilities.schema import ValueClass
        from ..extensions_mountainash._ma_option_domains import validate_open_value

        timezone = validate_open_value(
            ValueClass.IANA_TIMEZONE, "timezone", timezone, "assume_timezone"
        )
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.ASSUME_TIMEZONE,
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
        _reject_expression("format", format, "strftime")
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.STRFTIME,
            arguments=[self._node],
            options={"format": format},
        )
        return self._build(node)

    def add_intervals(
        self,
        y: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """Add an interval/duration to a datetime expression.

        Args:
            y: Interval or duration expression to add.

        Returns:
            New ExpressionAPI with add_intervals node.
        """
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
        y_node = self._to_substrait_node(y)
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.ADD_INTERVALS,
            arguments=[self._node, y_node],
        )
        return self._build(node)
