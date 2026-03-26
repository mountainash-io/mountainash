"""DateTime operations APIBuilder.

Substrait-aligned implementation using ScalarFunctionNode.
Implements ScalarDatetimeBuilderProtocol for datetime operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from ..api_builder_base import BaseExpressionAPIBuilder

from mountainash_expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, ExpressionNode
from mountainash_expressions.core.expression_protocols.api_builders.extensions_mountainash import MountainAshScalarDatetimeAPIBuilderProtocol


if TYPE_CHECKING:
    from ...api_base import BaseExpressionAPI
    from ....expression_nodes import ExpressionNode


class MountainAshScalarDatetimeAPIBuilder(BaseExpressionAPIBuilder, MountainAshScalarDatetimeAPIBuilderProtocol):
    """
    DateTime operations APIBuilder (Substrait-aligned).

    Provides datetime manipulation operations.

    Component Extraction:
        year, month, day: Basic date components
        hour, minute, second: Time components
        millisecond, microsecond, nanosecond: Sub-second precision
        quarter, day_of_year, day_of_week, week_of_year: Calendar components
        iso_year, unix_timestamp, timezone_offset: Special extractions

    Boolean Extraction:
        is_leap_year: Check if year is leap year
        is_dst: Check if DST is observed

    Date/Time Arithmetic:
        add_years, add_months, add_days: Add date intervals
        add_hours, add_minutes, add_seconds: Add time intervals
        add_milliseconds, add_microseconds: Add sub-second intervals

    Date Difference:
        diff_years, diff_months, diff_days: Date differences
        diff_hours, diff_minutes, diff_seconds: Time differences

    Truncation/Rounding:
        truncate: Truncate to unit (floor)
        round: Round to nearest unit
        ceil: Round up to unit
        floor: Round down to unit

    Timezone Operations:
        to_timezone: Convert to timezone
        assume_timezone: Assume local timezone

    Formatting:
        strftime: Format as string
    """

    # ========================================
    # Component Extraction - Basic
    # ========================================

    def year(self) -> BaseExpressionAPI:
        """
        Extract the year component.

        Substrait: extract (YEAR)

        Returns:
            New ExpressionAPI with year extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_YEAR,
            arguments=[self._node],
        )
        return self._build(node)

    def month(self) -> BaseExpressionAPI:
        """
        Extract the month component (1-12).

        Substrait: extract (MONTH)

        Returns:
            New ExpressionAPI with month extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MONTH,
            arguments=[self._node],
        )
        return self._build(node)

    def day(self) -> BaseExpressionAPI:
        """
        Extract the day of month component (1-31).

        Substrait: extract (DAY)

        Returns:
            New ExpressionAPI with day extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY,
            arguments=[self._node],
        )
        return self._build(node)

    def hour(self) -> BaseExpressionAPI:
        """
        Extract the hour component (0-23).

        Substrait: extract (HOUR)

        Returns:
            New ExpressionAPI with hour extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_HOUR,
            arguments=[self._node],
        )
        return self._build(node)

    def minute(self) -> BaseExpressionAPI:
        """
        Extract the minute component (0-59).

        Substrait: extract (MINUTE)

        Returns:
            New ExpressionAPI with minute extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MINUTE,
            arguments=[self._node],
        )
        return self._build(node)

    def second(self) -> BaseExpressionAPI:
        """
        Extract the second component (0-59).

        Substrait: extract (SECOND)

        Returns:
            New ExpressionAPI with second extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_SECOND,
            arguments=[self._node],
        )
        return self._build(node)

    def millisecond(self) -> BaseExpressionAPI:
        """
        Extract milliseconds since last full second.

        Substrait: extract (MILLISECOND)

        Returns:
            New ExpressionAPI with millisecond extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MILLISECOND,
            arguments=[self._node],
        )
        return self._build(node)

    def microsecond(self) -> BaseExpressionAPI:
        """
        Extract microseconds since last full millisecond.

        Substrait: extract (MICROSECOND)

        Returns:
            New ExpressionAPI with microsecond extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_MICROSECOND,
            arguments=[self._node],
        )
        return self._build(node)

    def nanosecond(self) -> BaseExpressionAPI:
        """
        Extract nanoseconds since last full microsecond.

        Substrait: extract (NANOSECOND)

        Returns:
            New ExpressionAPI with nanosecond extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_NANOSECOND,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Component Extraction - Calendar
    # ========================================

    def quarter(self) -> BaseExpressionAPI:
        """
        Extract the quarter (1-4).

        Substrait: extract (QUARTER)

        Returns:
            New ExpressionAPI with quarter extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_QUARTER,
            arguments=[self._node],
        )
        return self._build(node)

    def day_of_year(self) -> BaseExpressionAPI:
        """
        Extract day of year (1-366).

        Substrait: extract (DAY_OF_YEAR)

        Returns:
            New ExpressionAPI with day of year extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_DAY_OF_YEAR,
            arguments=[self._node],
        )
        return self._build(node)

    def day_of_week(self) -> BaseExpressionAPI:
        """
        Extract day of week (Monday=1 to Sunday=7).

        Substrait: extract (MONDAY_DAY_OF_WEEK)

        Returns:
            New ExpressionAPI with day of week extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEKDAY,
            arguments=[self._node],
        )
        return self._build(node)

    def week_of_year(self) -> BaseExpressionAPI:
        """
        Extract ISO week of year (1-53).

        Substrait: extract (ISO_WEEK)

        Returns:
            New ExpressionAPI with week of year extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_WEEK,
            arguments=[self._node],
        )
        return self._build(node)

    def iso_year(self) -> BaseExpressionAPI:
        """
        Extract ISO 8601 week-numbering year.

        Substrait: extract (ISO_YEAR)

        Returns:
            New ExpressionAPI with ISO year extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_ISO_YEAR,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Component Extraction - Special
    # ========================================

    def unix_timestamp(self) -> BaseExpressionAPI:
        """
        Extract seconds since 1970-01-01 00:00:00 UTC.

        Substrait: extract (UNIX_TIME)

        Returns:
            New ExpressionAPI with unix timestamp extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_UNIX_TIME,
            arguments=[self._node],
        )
        return self._build(node)

    def timezone_offset(self) -> BaseExpressionAPI:
        """
        Extract timezone offset to UTC in seconds.

        Substrait: extract (TIMEZONE_OFFSET)

        Returns:
            New ExpressionAPI with timezone offset extraction node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_TIMEZONE_OFFSET,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Boolean Extraction
    # ========================================

    def is_leap_year(self) -> BaseExpressionAPI:
        """
        Whether the year is a leap year.

        Substrait: extract_boolean (IS_LEAP_YEAR)

        Returns:
            New ExpressionAPI with is_leap_year node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_LEAP_YEAR,
            arguments=[self._node],
        )
        return self._build(node)

    def is_dst(
        self,
        timezone: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """
        Whether DST is observed at this time.

        Substrait: extract_boolean (IS_DST)

        Args:
            timezone: IANA timezone name (e.g., "America/New_York").

        Returns:
            New ExpressionAPI with is_dst node.
        """
        options = {}
        if timezone is not None:
            options["timezone"] = timezone
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST,
            arguments=[self._node],
            options=options if options else None,
        )
        return self._build(node)

    # ========================================
    # Date/Time Arithmetic
    # ========================================

    def add_years(
        self,
        years: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add years to the datetime.

        Substrait: add

        Args:
            years: Number of years to add (can be negative).

        Returns:
            New ExpressionAPI with add_years node.
        """
        years_node = self._to_substrait_node(years)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_YEARS,
            arguments=[self._node, years_node],
        )
        return self._build(node)

    def add_months(
        self,
        months: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add months to the datetime.

        Substrait: add

        Args:
            months: Number of months to add (can be negative).

        Returns:
            New ExpressionAPI with add_months node.
        """
        months_node = self._to_substrait_node(months)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MONTHS,
            arguments=[self._node, months_node],
        )
        return self._build(node)

    def add_days(
        self,
        days: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add days to the datetime.

        Substrait: add

        Args:
            days: Number of days to add (can be negative).

        Returns:
            New ExpressionAPI with add_days node.
        """
        days_node = self._to_substrait_node(days)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS,
            arguments=[self._node, days_node],
        )
        return self._build(node)

    def add_hours(
        self,
        hours: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add hours to the datetime.

        Substrait: add

        Args:
            hours: Number of hours to add (can be negative).

        Returns:
            New ExpressionAPI with add_hours node.
        """
        hours_node = self._to_substrait_node(hours)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_HOURS,
            arguments=[self._node, hours_node],
        )
        return self._build(node)

    def add_minutes(
        self,
        minutes: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add minutes to the datetime.

        Substrait: add

        Args:
            minutes: Number of minutes to add (can be negative).

        Returns:
            New ExpressionAPI with add_minutes node.
        """
        minutes_node = self._to_substrait_node(minutes)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MINUTES,
            arguments=[self._node, minutes_node],
        )
        return self._build(node)

    def add_seconds(
        self,
        seconds: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add seconds to the datetime.

        Substrait: add

        Args:
            seconds: Number of seconds to add (can be negative).

        Returns:
            New ExpressionAPI with add_seconds node.
        """
        seconds_node = self._to_substrait_node(seconds)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_SECONDS,
            arguments=[self._node, seconds_node],
        )
        return self._build(node)

    def add_milliseconds(
        self,
        milliseconds: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add milliseconds to the datetime.

        Substrait: add

        Args:
            milliseconds: Number of milliseconds to add (can be negative).

        Returns:
            New ExpressionAPI with add_milliseconds node.
        """
        milliseconds_node = self._to_substrait_node(milliseconds)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MILLISECONDS,
            arguments=[self._node, milliseconds_node],
        )
        return self._build(node)

    def add_microseconds(
        self,
        microseconds: Union[BaseExpressionAPI, "ExpressionNode", Any, int],
    ) -> BaseExpressionAPI:
        """
        Add microseconds to the datetime.

        Substrait: add

        Args:
            microseconds: Number of microseconds to add (can be negative).

        Returns:
            New ExpressionAPI with add_microseconds node.
        """
        microseconds_node = self._to_substrait_node(microseconds)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_MICROSECONDS,
            arguments=[self._node, microseconds_node],
        )
        return self._build(node)

    # ========================================
    # Date Difference
    # ========================================

    def diff_years(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in years.

        Substrait: subtract

        Args:
            other: Datetime to compare with.

        Returns:
            New ExpressionAPI with diff_years node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_YEARS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_months(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in months.

        Substrait: subtract

        Args:
            other: Datetime to compare with.

        Returns:
            New ExpressionAPI with diff_months node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MONTHS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_days(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in days.

        Substrait: subtract

        Args:
            other: Datetime to compare with.

        Returns:
            New ExpressionAPI with diff_days node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_DAYS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_hours(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in hours.

        Substrait: subtract

        Args:
            other: Datetime to compare with.

        Returns:
            New ExpressionAPI with diff_hours node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_HOURS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_minutes(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in minutes.

        Substrait: subtract

        Args:
            other: Datetime to compare with.

        Returns:
            New ExpressionAPI with diff_minutes node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_MINUTES,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_seconds(
        self,
        other: Union[BaseExpressionAPI, "ExpressionNode", Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in seconds.

        Substrait: subtract

        Args:
            other: Datetime to compare with.

        Returns:
            New ExpressionAPI with diff_seconds node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DIFF_SECONDS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    # ========================================
    # Truncation / Rounding
    # ========================================

    def truncate(
        self,
        unit: str,
    ) -> BaseExpressionAPI:
        """
        Truncate datetime to the specified unit.

        Substrait: round_temporal (FLOOR)

        Args:
            unit: Time unit (year, quarter, month, week, day, hour, minute, second).

        Returns:
            New ExpressionAPI with truncate node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TRUNCATE,
            arguments=[self._node],
            options={"unit": unit},
        )
        return self._build(node)

    def round(
        self,
        unit: str,
    ) -> BaseExpressionAPI:
        """
        Round datetime to the nearest unit.

        Substrait: round_temporal (ROUND_TIE_UP)

        Args:
            unit: Time unit (year, quarter, month, week, day, hour, minute, second).

        Returns:
            New ExpressionAPI with round node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
            arguments=[self._node],
            options={"unit": unit},
        )
        return self._build(node)

    def ceil(
        self,
        unit: str,
    ) -> BaseExpressionAPI:
        """
        Round datetime up to the next unit.

        Substrait: round_temporal (CEIL)

        Args:
            unit: Time unit (year, quarter, month, week, day, hour, minute, second).

        Returns:
            New ExpressionAPI with ceil node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
            arguments=[self._node],
            options={"unit": unit},
        )
        return self._build(node)

    def floor(
        self,
        unit: str,
    ) -> BaseExpressionAPI:
        """
        Round datetime down to the previous unit.

        Substrait: round_temporal (FLOOR)

        Args:
            unit: Time unit (year, quarter, month, week, day, hour, minute, second).

        Returns:
            New ExpressionAPI with floor node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.FLOOR,
            arguments=[self._node],
            options={"unit": unit},
        )
        return self._build(node)

    # ========================================
    # Timezone Operations
    # ========================================

    def to_timezone(
        self,
        timezone: str,
    ) -> BaseExpressionAPI:
        """
        Convert to specified timezone.

        Substrait: local_timestamp

        Args:
            timezone: IANA timezone name (e.g., "America/New_York", "UTC").

        Returns:
            New ExpressionAPI with to_timezone node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE,
            arguments=[self._node],
            options={"timezone": timezone},
        )
        return self._build(node)

    def assume_timezone(
        self,
        timezone: str,
    ) -> BaseExpressionAPI:
        """
        Assume the timestamp is in the specified timezone.

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

    # ========================================
    # Formatting
    # ========================================

    def strftime(
        self,
        format: str,
    ) -> BaseExpressionAPI:
        """
        Format datetime as string.

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

    # ========================================
    # Flexible Duration Offset
    # ========================================

    def offset_by(
        self,
        offset: str,
    ) -> BaseExpressionAPI:
        """
        Offset datetime by a flexible duration string.

        Supports combined duration formats (e.g., "1d2h", "-3mo", "2h30m").
        Also supports natural language (e.g., "3 days", "2 hours") which is
        automatically converted to Polars format.

        Args:
            offset: Duration string with optional sign and combined units.
                    Examples: "1d", "2h30m", "-3mo", "1y6mo", "3 days"

        Returns:
            New ExpressionAPI with offset node.
        """
        # Convert natural language to Polars format (e.g., "3 days" → "3d")
        # This validates the input early with clear error messages
        if " " in offset:
            from ....utils.temporal import to_offset_string

            offset = to_offset_string(offset)

        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.OFFSET_BY,
            arguments=[self._node],
            options={"offset": offset},
        )
        return self._build(node)

    # ========================================
    # Natural Language Filters
    # ========================================

    def within_last(self, duration: str) -> BaseExpressionAPI:
        """
        Filter for timestamps within the last duration.

        Like journalctl --since, returns records from (now - duration) to now.
        Uses natural language time expressions.

        Args:
            duration: Natural language like "10 minutes", "2 hours", "1 day",
                      or short form like "10m", "2h", "1d".

        Returns:
            New ExpressionAPI with comparison node (timestamp > threshold).

        Example:
            >>> col("created_at").dt.within_last("1 hour")
            >>> # Returns: created_at > (now - 1 hour)
        """
        from ....utils.temporal import time_ago

        threshold = time_ago(duration)
        return self._api.gt(threshold)

    def older_than(self, duration: str) -> BaseExpressionAPI:
        """
        Filter for timestamps older than duration.

        Like find -mtime, returns records before (now - duration).
        Uses natural language time expressions.

        Args:
            duration: Natural language like "7 days", "1 month", "30 minutes",
                      or short form like "7d", "1mo", "30m".

        Returns:
            New ExpressionAPI with comparison node (timestamp < threshold).

        Example:
            >>> col("created_at").dt.older_than("30 days")
            >>> # Returns: created_at < (now - 30 days)
        """
        from ....utils.temporal import time_ago

        threshold = time_ago(duration)
        return self._api.lt(threshold)

    def newer_than(self, duration: str) -> BaseExpressionAPI:
        """
        Filter for timestamps newer than X ago.

        Alias for within_last() for semantic clarity.

        Args:
            duration: Natural language like "1 hour", "30 minutes".

        Returns:
            New ExpressionAPI with comparison node.

        Example:
            >>> col("modified_at").dt.newer_than("3 hours")
        """
        return self.within_last(duration)

    def within_next(self, duration: str) -> BaseExpressionAPI:
        """
        Filter for timestamps within the next duration (future).

        Returns records from now to (now + duration).
        Useful for scheduled events, appointments, deadlines.

        Args:
            duration: Natural language like "2 hours", "1 week", "24h".

        Returns:
            New ExpressionAPI with compound comparison node
            (now <= timestamp < now + duration).

        Example:
            >>> col("scheduled_at").dt.within_next("24 hours")
            >>> # Returns appointments in the next 24 hours
        """
        from datetime import datetime

        from ....utils.temporal import to_timedelta

        delta = to_timedelta(duration)
        now = datetime.now()
        threshold = now + delta
        return self._api.ge(now).and_(self._api.lt(threshold))

    def between_last(
        self,
        older_duration: str,
        newer_duration: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """
        Filter for timestamps between two past time points.

        Returns records between (now - older_duration) and (now - newer_duration).
        If newer_duration is None, uses current time as the end bound.

        Args:
            older_duration: Start of window (further back in time).
                            E.g., "8 hours", "2 days".
            newer_duration: End of window (more recent), defaults to "now".
                            E.g., "2 hours", "30 minutes".

        Returns:
            New ExpressionAPI with compound comparison node
            ((now - older) < timestamp < (now - newer)).

        Example:
            >>> col("timestamp").dt.between_last("8 hours", "2 hours")
            >>> # Returns events from 8 hours ago to 2 hours ago

            >>> col("timestamp").dt.between_last("1 day")
            >>> # Returns events from 1 day ago to now
        """
        from datetime import datetime

        from ....utils.temporal import time_ago

        older_threshold = time_ago(older_duration)
        newer_threshold = time_ago(newer_duration) if newer_duration else datetime.now()

        return self._api.gt(older_threshold).and_(self._api.lt(newer_threshold))

    # ========================================
    # Component Extraction
    # ========================================

    def date(self) -> BaseExpressionAPI:
        """Extract the date component from a datetime."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DATE,
            arguments=[self._node],
        )
        return self._build(node)

    def time(self) -> BaseExpressionAPI:
        """Extract the time component from a datetime."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.TIME,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Calendar Helpers
    # ========================================

    def month_start(self) -> BaseExpressionAPI:
        """Roll datetime to the first day of its month."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_START,
            arguments=[self._node],
        )
        return self._build(node)

    def month_end(self) -> BaseExpressionAPI:
        """Roll datetime to the last day of its month."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.MONTH_END,
            arguments=[self._node],
        )
        return self._build(node)

    def days_in_month(self) -> BaseExpressionAPI:
        """Return the number of days in the month of the datetime."""
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.DAYS_IN_MONTH,
            arguments=[self._node],
        )
        return self._build(node)

    # Polars-compatible aliases
    week = week_of_year
    weekday = day_of_week
    ordinal_day = day_of_year
    convert_time_zone = to_timezone
    replace_time_zone = assume_timezone
    epoch = unix_timestamp
