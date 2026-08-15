"""Ibis ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Ibis backend.
"""

from __future__ import annotations

from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    CALENDAR_COMPONENTS,
    DatetimeComponent,
)
from typing import TYPE_CHECKING, Optional

import ibis

from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)
from ..base import IbisBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarDatetimeExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.core.types import IbisValueExpr

_LOCAL_TIMESTAMP_UNSUPPORTED = (
    "local_timestamp is not supported on ibis — it yields the UTC wall clock, "
    "not the target zone wall clock; see capabilities/datetime/value_classes_substrait.py"
)


class SubstraitIbisScalarDatetimeExpressionSystem(IbisBaseExpressionSystem, SubstraitScalarDatetimeExpressionSystemProtocol["IbisValueExpr"]):
    """Ibis implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations.
    """

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract(
        self,
        x: IbisValueExpr,
        /,
        component: str,
        indexing: str = None,
        timezone: str = None,
    ) -> IbisValueExpr:
        """Extract a date/time component (Substrait: extract).

        ``timezone`` is not honored on ibis (no timezone primitives); the
        capability gate raises before this body is reached in production.
        """
        comp = component.value if isinstance(component, DatetimeComponent) else str(component).upper()

        component_map = {
            "YEAR": lambda e: e.year(),
            "ISO_YEAR": lambda e: e.iso_year(),
            "QUARTER": lambda e: e.quarter(),
            "MONTH": lambda e: e.month(),
            "DAY": lambda e: e.day(),
            "DAY_OF_YEAR": lambda e: e.day_of_year(),
            "MONDAY_DAY_OF_WEEK": lambda e: e.day_of_week.index() + ibis.literal(1),
            "SUNDAY_DAY_OF_WEEK": lambda e: (e.day_of_week.index() + ibis.literal(1)) % ibis.literal(7) + ibis.literal(1),
            "ISO_WEEK": lambda e: e.week_of_year(),
            "HOUR": lambda e: e.hour(),
            "MINUTE": lambda e: e.minute(),
            "SECOND": lambda e: e.second(),
            "MILLISECOND": lambda e: e.millisecond(),
            "MICROSECOND": lambda e: e.microsecond() % ibis.literal(1000),
            "SUBSECOND": lambda e: e.microsecond(),
            "UNIX_TIME": lambda e: e.epoch_seconds(),
        }

        if comp not in component_map:
            raise BackendCapabilityError(
                f"extract component {comp!r} is not supported on ibis",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
            )

        result = component_map[comp](x)
        if indexing == "ZERO" and comp in CALENDAR_COMPONENTS:
            result = result - ibis.literal(1)
        return result

    def extract_boolean(
        self,
        x: IbisValueExpr,
        /,
        component: str,
        timezone: str = None,
    ) -> IbisValueExpr:
        """Extract a boolean date/time component (Substrait: extract_boolean)."""
        comp = component.value if isinstance(component, BooleanComponent) else str(component).upper()

        if comp == "IS_LEAP_YEAR":
            year = x.year()
            return ((year % ibis.literal(4) == ibis.literal(0)) &
                    (year % ibis.literal(100) != ibis.literal(0))) | (year % ibis.literal(400) == ibis.literal(0))

        raise BackendCapabilityError(
            f"extract_boolean component {comp!r} is not supported on ibis",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
        )



    # =========================================================================
    # Substrait Interval Operations
    # =========================================================================

    def add(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add an interval to a date/time value.

        Args:
            x: Datetime expression.
            y: Interval/duration to add.

        Returns:
            Datetime with interval added.
        """
        x, y = self._lift_deferred(x, y)
        return x + y

    def subtract(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Subtract an interval from a date/time value.

        Args:
            x: Datetime expression.
            y: Interval/duration to subtract.

        Returns:
            Datetime with interval subtracted.
        """
        x, y = self._lift_deferred(x, y)
        return x - y

    def multiply(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Multiply an interval by an integral number.

        Args:
            x: Interval/duration expression.
            y: Multiplier.

        Returns:
            Scaled interval.
        """
        x, y = self._lift_deferred(x, y)
        return x * y

    def add_intervals(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Add two intervals together.

        Args:
            x: First interval.
            y: Second interval.

        Returns:
            Combined interval.
        """
        x, y = self._lift_deferred(x, y)
        return x + y

    # =========================================================================
    # Substrait Datetime Comparisons
    # =========================================================================

    def lt(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /
    ) -> IbisValueExpr:
        """Less than comparison for datetime/interval.

        Args:
            x: First datetime/interval.
            y: Second datetime/interval.

        Returns:
            Boolean expression.
        """
        return x < y

    def lte(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Less than or equal comparison for datetime/interval.

        Args:
            x: First datetime/interval.
            y: Second datetime/interval.

        Returns:
            Boolean expression.
        """
        return x <= y

    def gt(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Greater than comparison for datetime/interval.

        Args:
            x: First datetime/interval.
            y: Second datetime/interval.

        Returns:
            Boolean expression.
        """
        return x > y

    def gte(
        self,
        x: IbisValueExpr,
        y: IbisValueExpr,
        /,
    ) -> IbisValueExpr:
        """Greater than or equal comparison for datetime/interval.

        Args:
            x: First datetime/interval.
            y: Second datetime/interval.

        Returns:
            Boolean expression.
        """
        return x >= y

    # =========================================================================
    # Substrait Timezone Operations
    # =========================================================================


    def assume_timezone(
        self,
        x: IbisValueExpr,
        /,
        timezone: str,
    ) -> IbisValueExpr:
        """Assume the timestamp is in the specified timezone.

        Args:
            x: Datetime expression (timezone-naive).
            timezone: Timezone to assume (IANA format).

        Returns:
            Timezone-aware datetime.

        Note:
            Ibis may not have timezone assignment. Falls back to input.
        """
        # Ibis doesn't have replace_time_zone - fallback
        return x

    def local_timestamp(
        self,
        x: IbisValueExpr,
        /,
        timezone: str,
    ) -> IbisValueExpr:
        """Convert UTC-relative timestamp_tz to local timestamp.

        Declared UNSUPPORTED on ibis (see
        capabilities/datetime/value_classes_substrait.py) -- the capability gate
        raises before this method is reached. The raise here is defence in depth.
        """
        raise BackendCapabilityError(
            _LOCAL_TIMESTAMP_UNSUPPORTED,
            backend="ibis",
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP,
        )

    # =========================================================================
    # Substrait Parsing Operations
    # =========================================================================

    def strptime_time(
        self,
        x: IbisValueExpr,
        /,
        format: str,
    ) -> IbisValueExpr:
        """Parse string into time using provided format.

        Args:
            time_string: String to parse.
            format: strptime format string.

        Returns:
            Parsed time expression.

        Note:
            Ibis may not have strptime_time. Falls back to cast.
        """
        # Ibis doesn't have strptime for time - fallback
        return x.cast("time")

    def strptime_date(
        self,
        x: IbisValueExpr,
        /,
        format: str,
    ) -> IbisValueExpr:
        """Parse string into date using provided format.

        Args:
            x: String to parse.
            format: strptime format string.

        Returns:
            Parsed date expression.
        """
        # ibis >= 10 honors the strptime format directly; the previous
        # `x.cast("date")` silently discarded it (spec 2026-07-28 section 3).
        return x.as_date(format)

    def strptime_timestamp(
        self,
        x: IbisValueExpr,
        /,
        format: str,
        timezone: str = None,
    ) -> IbisValueExpr:
        """Parse string into timestamp using provided format.

        Args:
            x: String to parse.
            format: strptime format string.
            timezone: Optional timezone (IANA format).

        Returns:
            Parsed timestamp expression.
        """
        # `.as_timestamp()` returns timestamp('UTC'); the recast restores the
        # naive wall-clock dtype the previous `cast("timestamp")` produced, so
        # the fix changes the parse and nothing else. `timezone` is ignored --
        # ibis has no timezone primitives (matches assume_timezone/to_timezone/
        # local_timestamp/extract.timezone); a declared_unsupported fact gates
        # this in production.
        return x.as_timestamp(format).cast("timestamp")

    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def strftime(
        self,
        x: IbisValueExpr,
        /,
        format: str,
    ) -> IbisValueExpr:
        """Format datetime as string.

        Args:
            x: Datetime expression.
            format: strftime format string.

        Returns:
            Formatted string.
        """
        return x.strftime(format)


    # =========================================================================
    # Substrait Rounding Operations
    # =========================================================================

    def round_temporal(
        self,
        x: IbisValueExpr,
        /,
        rounding: Optional[str] = None,
        unit: str = "1d",
        multiple: int = 1,
        origin: Optional[str] = None,
    ) -> IbisValueExpr:
        """Round datetime to a multiple of a time unit.

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: Time unit string.
            multiple: Multiple of unit (default 1).
            origin: Origin timestamp for rounding.

        Returns:
            Rounded datetime.

        Note:
            Ibis only supports truncate. Falls back to truncate for all modes.
        """
        # Ibis only has truncate - use for all rounding modes
        return x.truncate(unit)

    def round_calendar(
        self,
        x: IbisValueExpr,
        /,
        rounding: Optional[str] = None,
        unit: str = "1d",
        origin: Optional[str] = None,
        multiple: int = 1,
    ) -> IbisValueExpr:
        """Round datetime to a calendar unit.

        Similar to round_temporal but for calendar-aware rounding.

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: Calendar unit string.
            origin: Origin timestamp.
            multiple: Multiple of unit.

        Returns:
            Rounded datetime.

        Note:
            Ibis only supports truncate. Falls back to truncate.
        """
        return self.round_temporal(x, rounding, unit, multiple, origin)
