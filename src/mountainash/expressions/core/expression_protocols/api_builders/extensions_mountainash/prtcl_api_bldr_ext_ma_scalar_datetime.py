"""Mountainash datetime extension protocol.

Mountainash Extension: DateTime
URI: file://extensions/functions_datetime.yaml

Extensions providing convenient datetime operations beyond Substrait standard:
- Component extraction (year, month, day, hour, etc.) - wrappers for Substrait extract()
- Boolean extraction (is_leap_year, is_dst) - wrappers for Substrait extract_boolean()
- Date arithmetic (add_years, add_months, add_days, etc.) - wrappers for Substrait add()
- Date difference (diff_years, diff_months, diff_days, etc.) - wrappers for Substrait subtract()
- Truncation/rounding (truncate, round, ceil, floor) - wrappers for Substrait round_temporal()
- Flexible duration offset (offset_by) - CUSTOM EXTENSION
- Natural language filtering (within_last, older_than, etc.) - CUSTOM EXTENSION
- Snapshot (today, now) - CUSTOM EXTENSION

Note: Timezone operations (assume_timezone, local_timestamp) and formatting (strftime)
are direct Substrait functions and defined in prtcl_scalar_datetime.py.
"""

from __future__ import annotations

from typing import Union, Any,Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_api import BaseExpressionAPI
    from mountainash.expressions.core.expression_nodes import ExpressionNode

class MountainAshScalarDatetimeAPIBuilderProtocol(Protocol):
    """Backend protocol for Mountainash datetime extensions.

    These operations extend Substrait's datetime capabilities with
    additional convenience functions common in DataFrame libraries.
    """

    # =========================================================================
    # Component Extraction - Basic
    # =========================================================================

    def year(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the year component."""
        ...

    def month(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the month component (1-12)."""
        ...

    def day(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the day of month component (1-31)."""
        ...

    def hour(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the hour component (0-23)."""
        ...

    def minute(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the minute component (0-59)."""
        ...

    def second(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the second component (0-59)."""
        ...

    def millisecond(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract milliseconds since last full second."""
        ...

    def microsecond(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract microseconds since last full millisecond."""
        ...

    def nanosecond(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract nanoseconds since last full microsecond."""
        ...

    # =========================================================================
    # Component Extraction - Calendar
    # =========================================================================

    def quarter(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract the quarter (1-4)."""
        ...

    def day_of_year(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract day of year (1-366)."""
        ...

    def day_of_week(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract day of week (Monday=1 to Sunday=7)."""
        ...

    def week_of_year(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract ISO week of year (1-53)."""
        ...

    def iso_year(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract ISO 8601 week-numbering year."""
        ...

    # =========================================================================
    # Component Extraction - Special
    # =========================================================================

    def unix_timestamp(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        ...

    def timezone_offset(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Extract timezone offset to UTC in seconds."""
        ...

    # =========================================================================
    # Boolean Extraction
    # =========================================================================

    def is_leap_year(
        self,
        /,
    ) -> BaseExpressionAPI:
        """Check if the year is a leap year."""
        ...

    def is_dst(
        self,
        /,
        timezone: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """Check if DST is observed at this time."""
        ...

    # =========================================================================
    # Date/Time Arithmetic
    # =========================================================================

    def add_years(
        self,
        years: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add years to a datetime."""
        ...

    def add_months(
        self,
        months: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add months to a datetime."""
        ...

    def add_days(
        self,
        days: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add days to a datetime."""
        ...

    def add_hours(
        self,
        hours: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add hours to a datetime."""
        ...

    def add_minutes(
        self,
        minutes: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add minutes to a datetime."""
        ...

    def add_seconds(
        self,
        seconds: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add seconds to a datetime."""
        ...

    def add_milliseconds(
        self,
        milliseconds: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add milliseconds to a datetime."""
        ...

    def add_microseconds(
        self,
        microseconds: Union[BaseExpressionAPI, ExpressionNode, Any, int],
        /,
    ) -> BaseExpressionAPI:
        """Add microseconds to a datetime."""
        ...

    # =========================================================================
    # Date Difference
    # =========================================================================

    def diff_years(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in years (x - other)."""
        ...

    def diff_months(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in months (x - other)."""
        ...

    def diff_days(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in days (x - other)."""
        ...

    def diff_hours(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in hours (x - other)."""
        ...

    def diff_minutes(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in minutes (x - other)."""
        ...

    def diff_seconds(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in seconds (x - other)."""
        ...

    def diff_milliseconds(
        self,
        other: Union[BaseExpressionAPI, ExpressionNode, Any],
        /,
    ) -> BaseExpressionAPI:
        """Calculate difference in milliseconds (x - other)."""
        ...

    # =========================================================================
    # Truncation / Rounding
    # =========================================================================

    def truncate(
        self,
        unit: str,
        /,
    ) -> BaseExpressionAPI:
        """Truncate datetime to the specified unit (floor)."""
        ...

    def round(
        self,
        unit: str,
        /,
    ) -> BaseExpressionAPI:
        """Round datetime to the nearest unit."""
        ...

    def ceil(
        self,
        unit: str,
        /,
    ) -> BaseExpressionAPI:
        """Round datetime up to the next unit."""
        ...

    def floor(
        self,
        unit: str,
        /,
    ) -> BaseExpressionAPI:
        """Round datetime down to the previous unit."""
        ...

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        offset: str,
    ) -> BaseExpressionAPI:
        """Add/subtract flexible duration from datetime.

        Supports combined duration formats (e.g., "1d2h", "-3mo").

        Args:
            x: Datetime expression.
            offset: Duration string.

        Returns:
            Datetime with offset applied.
        """
        ...

    # =========================================================================
    # Natural Language Filtering
    # =========================================================================

    def within_last(
        self,
        duration: str,
        /,
    ) -> BaseExpressionAPI:
        """Filter for timestamps within the last duration.

        Like journalctl --since, returns records from (now - duration) to now.

        Args:
            x: Datetime expression.
            duration: Natural language like "10 minutes", "2 hours", "1 day".

        Returns:
            Boolean expression for filtering.
        """
        ...

    def older_than(
        self,
        duration: str,
        /,
    ) -> BaseExpressionAPI:
        """Filter for timestamps older than duration.

        Like find -mtime, returns records before (now - duration).

        Args:
            x: Datetime expression.
            duration: Natural language like "7 days", "1 month", "30 minutes".

        Returns:
            Boolean expression for filtering.
        """
        ...

    def newer_than(
        self,
        duration: str,
        /,
    ) -> BaseExpressionAPI:
        """Filter for timestamps newer than X ago.

        Alias for within_last() for semantic clarity.

        Args:
            x: Datetime expression.
            duration: Natural language duration.

        Returns:
            Boolean expression for filtering.
        """
        ...

    def within_next(
        self,
        duration: str,
        /,
    ) -> BaseExpressionAPI:
        """Filter for timestamps within the next duration (future).

        Returns records from now to (now + duration).

        Args:
            x: Datetime expression.
            duration: Natural language like "2 hours", "1 week".

        Returns:
            Boolean expression for filtering.
        """
        ...

    def between_last(
        self,
        older_duration: str,
        /,
        newer_duration: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """Filter for timestamps between two past time points.

        Args:
            x: Datetime expression.
            older_duration: Start of window (further back in time).
            newer_duration: End of window (more recent), defaults to "now".

        Returns:
            Boolean expression for filtering.

        Example:
            between_last("8 hours", "2 hours")
            # Returns: (now - 8h) < timestamp < (now - 2h)
        """
        ...

    # =========================================================================
    # Snapshot
    # =========================================================================

    def today(self) -> BaseExpressionAPI:
        """Return today's date as a literal expression."""
        ...

    def now(self) -> BaseExpressionAPI:
        """Return current datetime as a literal expression."""
        ...

    # =========================================================================
    # Timezone Operations
    # =========================================================================

    def to_timezone(self, timezone: str) -> BaseExpressionAPI:
        """Convert to specified timezone."""
        ...

    def assume_timezone(self, timezone: str) -> BaseExpressionAPI:
        """Assume the timestamp is in the specified timezone."""
        ...

    # =========================================================================
    # Formatting
    # =========================================================================

    def strftime(self, format: str) -> BaseExpressionAPI:
        """Format datetime as string using strftime format codes."""
        ...

    # Polars-compatible aliases
    def week(self, /) -> BaseExpressionAPI:
        """Alias for week_of_year() — Polars compatibility."""
        ...

    def weekday(self, /) -> BaseExpressionAPI:
        """Alias for day_of_week() — Polars compatibility."""
        ...

    def ordinal_day(self, /) -> BaseExpressionAPI:
        """Alias for day_of_year() — Polars compatibility."""
        ...

    def convert_time_zone(self, timezone: str, /) -> BaseExpressionAPI:
        """Alias for to_timezone() — Polars compatibility."""
        ...

    def replace_time_zone(self, timezone: str, /) -> BaseExpressionAPI:
        """Alias for assume_timezone() — Polars compatibility."""
        ...

    def epoch(self, /) -> BaseExpressionAPI:
        """Alias for unix_timestamp() — Polars compatibility."""
        ...

    # Component extraction
    def date(self) -> BaseExpressionAPI:
        """Extract the date component from a datetime."""
        ...

    def time(self) -> BaseExpressionAPI:
        """Extract the time component from a datetime."""
        ...

    # Calendar helpers
    def month_start(self) -> BaseExpressionAPI:
        """Roll datetime to the first day of its month."""
        ...

    def month_end(self) -> BaseExpressionAPI:
        """Roll datetime to the last day of its month."""
        ...

    def days_in_month(self) -> BaseExpressionAPI:
        """Return the number of days in the month of the datetime."""
        ...

    # Duration extraction
    def total_seconds(self) -> BaseExpressionAPI:
        """Total seconds in a duration."""
        ...

    def total_minutes(self) -> BaseExpressionAPI:
        """Total minutes in a duration."""
        ...

    def total_milliseconds(self) -> BaseExpressionAPI:
        """Total milliseconds in a duration."""
        ...

    def total_microseconds(self) -> BaseExpressionAPI:
        """Total microseconds in a duration."""
        ...
