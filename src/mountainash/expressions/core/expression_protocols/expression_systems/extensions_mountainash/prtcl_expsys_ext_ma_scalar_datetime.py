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

from typing import Optional, Protocol

from mountainash.core.types import ExpressionT


class MountainAshScalarDatetimeExpressionSystemProtocol(Protocol[ExpressionT]):
    """Backend protocol for Mountainash datetime extensions.

    These operations extend Substrait's datetime capabilities with
    additional convenience functions common in DataFrame libraries.
    """

    # =========================================================================
    # Component Extraction - Basic
    # =========================================================================

    def year(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the year component."""
        ...

    def month(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the month component (1-12)."""
        ...

    def day(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the day of month component (1-31)."""
        ...

    def hour(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the hour component (0-23)."""
        ...

    def minute(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the minute component (0-59)."""
        ...

    def second(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the second component (0-59)."""
        ...

    def millisecond(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract milliseconds since last full second."""
        ...

    def microsecond(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract microseconds since last full millisecond."""
        ...

    def nanosecond(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract nanoseconds since last full microsecond."""
        ...

    # =========================================================================
    # Component Extraction - Calendar
    # =========================================================================

    def quarter(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract the quarter (1-4)."""
        ...

    def day_of_year(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract day of year (1-366)."""
        ...

    def day_of_week(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract day of week (Monday=1 to Sunday=7)."""
        ...

    def week_of_year(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract ISO week of year (1-53)."""
        ...

    def iso_year(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract ISO 8601 week-numbering year."""
        ...

    # =========================================================================
    # Component Extraction - Special
    # =========================================================================

    def unix_timestamp(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        ...

    def timezone_offset(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Extract timezone offset to UTC in seconds."""
        ...

    # =========================================================================
    # Boolean Extraction
    # =========================================================================

    def is_leap_year(
        self,
        x: ExpressionT,
        /,
    ) -> ExpressionT:
        """Check if the year is a leap year."""
        ...

    def is_dst(
        self,
        x: ExpressionT,
        /,
        timezone: Optional[str] = None,
    ) -> ExpressionT:
        """Check if DST is observed at this time."""
        ...

    # =========================================================================
    # Date/Time Arithmetic
    # =========================================================================

    def add_years(
        self,
        x: ExpressionT,
        years: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add years to a datetime."""
        ...

    def add_months(
        self,
        x: ExpressionT,
        months: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add months to a datetime."""
        ...

    def add_days(
        self,
        x: ExpressionT,
        days: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add days to a datetime."""
        ...

    def add_hours(
        self,
        x: ExpressionT,
        hours: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add hours to a datetime."""
        ...

    def add_minutes(
        self,
        x: ExpressionT,
        minutes: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add minutes to a datetime."""
        ...

    def add_seconds(
        self,
        x: ExpressionT,
        seconds: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add seconds to a datetime."""
        ...

    def add_milliseconds(
        self,
        x: ExpressionT,
        milliseconds: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add milliseconds to a datetime."""
        ...

    def add_microseconds(
        self,
        x: ExpressionT,
        microseconds: ExpressionT,
        /,
    ) -> ExpressionT:
        """Add microseconds to a datetime."""
        ...

    # =========================================================================
    # Date Difference
    # =========================================================================

    def diff_years(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in years (x - other)."""
        ...

    def diff_months(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in months (x - other)."""
        ...

    def diff_days(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in days (x - other)."""
        ...

    def diff_hours(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in hours (x - other)."""
        ...

    def diff_minutes(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in minutes (x - other)."""
        ...

    def diff_seconds(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in seconds (x - other)."""
        ...

    def diff_milliseconds(
        self,
        x: ExpressionT,
        other: ExpressionT,
        /,
    ) -> ExpressionT:
        """Calculate difference in milliseconds (x - other)."""
        ...

    # =========================================================================
    # Truncation / Rounding
    # =========================================================================

    def truncate(
        self,
        x: ExpressionT,
        /,
        *,
        unit: str,
    ) -> ExpressionT:
        """Truncate datetime to the specified unit (floor)."""
        ...

    def round(
        self,
        x: ExpressionT,
        /,
        *,
        unit: str,
    ) -> ExpressionT:
        """Round datetime to the nearest unit."""
        ...

    def ceil(
        self,
        x: ExpressionT,
        /,
        *,
        unit: str,
    ) -> ExpressionT:
        """Round datetime up to the next unit."""
        ...

    def floor(
        self,
        x: ExpressionT,
        /,
        *,
        unit: str,
    ) -> ExpressionT:
        """Round datetime down to the previous unit."""
        ...

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        x: ExpressionT,
        *,
        offset: str,
    ) -> ExpressionT:
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
    # Core Dispatch Methods (used by visitor)
    # =========================================================================

    def extract(
        self,
        x: ExpressionT,
        component: str,
        timezone: Optional[str] = None,
        /,
    ) -> ExpressionT:
        """Extract a datetime component by name.

        Dispatches to backend-specific extraction (year, month, day, etc.).

        Args:
            x: Datetime expression.
            component: Component identifier.

        Returns:
            Extracted component value.
        """
        ...

    def extract_boolean(
        self,
        x: ExpressionT,
        /,
        component: str,
    ) -> ExpressionT:
        """Extract a boolean datetime property.

        Dispatches to backend-specific boolean extraction (is_leap_year, is_dst).

        Args:
            x: Datetime expression.
            component: Boolean component identifier.

        Returns:
            Boolean expression.
        """
        ...

    # =========================================================================
    # Timezone Operations
    # =========================================================================

    def to_timezone(
        self,
        x: ExpressionT,
        timezone: str,
        /,
    ) -> ExpressionT:
        """Convert to specified timezone."""
        ...

    def assume_timezone(
        self,
        x: ExpressionT,
        timezone: str,
        /,
    ) -> ExpressionT:
        """Assume the timestamp is in the specified timezone."""
        ...

    # =========================================================================
    # Formatting
    # =========================================================================

    def strftime(
        self,
        x: ExpressionT,
        format: str,
        /,
    ) -> ExpressionT:
        """Format datetime as string."""
        ...

    # =========================================================================
    # Snapshot
    # =========================================================================

    def today(self) -> ExpressionT:
        """Return today's date as a literal expression."""
        ...

    def now(self) -> ExpressionT:
        """Return current datetime as a literal expression."""
        ...

    # =========================================================================
    # Component Extraction
    # =========================================================================

    def date(self, input: ExpressionT, /) -> ExpressionT:
        """Extract the date component from a datetime."""
        ...

    def time(self, input: ExpressionT, /) -> ExpressionT:
        """Extract the time component from a datetime."""
        ...

    # =========================================================================
    # Calendar Helpers
    # =========================================================================

    def month_start(self, input: ExpressionT, /) -> ExpressionT:
        """Roll datetime to the first day of its month."""
        ...

    def month_end(self, input: ExpressionT, /) -> ExpressionT:
        """Roll datetime to the last day of its month."""
        ...

    def days_in_month(self, input: ExpressionT, /) -> ExpressionT:
        """Return the number of days in the month of the datetime."""
        ...

    # =========================================================================
    # Duration Extraction
    # =========================================================================

    def total_seconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total seconds in a duration."""
        ...

    def total_minutes(self, x: ExpressionT, /) -> ExpressionT:
        """Total minutes in a duration."""
        ...

    def total_milliseconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total milliseconds in a duration."""
        ...

    def total_microseconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total microseconds in a duration."""
        ...

    def total_days(self, x: ExpressionT, /) -> ExpressionT:
        """Total days in a duration."""
        ...

    def total_hours(self, x: ExpressionT, /) -> ExpressionT:
        """Total hours in a duration."""
        ...

    def total_nanoseconds(self, x: ExpressionT, /) -> ExpressionT:
        """Total nanoseconds in a duration."""
        ...
