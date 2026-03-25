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

from typing import Optional, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_expressions.types import SupportedExpressions


class MountainAshScalarDatetimeExpressionSystemProtocol(Protocol):
    """Backend protocol for Mountainash datetime extensions.

    These operations extend Substrait's datetime capabilities with
    additional convenience functions common in DataFrame libraries.
    """

    # =========================================================================
    # Component Extraction - Basic
    # =========================================================================

    def year(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the year component."""
        ...

    def month(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the month component (1-12)."""
        ...

    def day(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the day of month component (1-31)."""
        ...

    def hour(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the hour component (0-23)."""
        ...

    def minute(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the minute component (0-59)."""
        ...

    def second(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the second component (0-59)."""
        ...

    def millisecond(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract milliseconds since last full second."""
        ...

    def microsecond(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract microseconds since last full millisecond."""
        ...

    def nanosecond(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract nanoseconds since last full microsecond."""
        ...

    # =========================================================================
    # Component Extraction - Calendar
    # =========================================================================

    def quarter(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract the quarter (1-4)."""
        ...

    def day_of_year(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract day of year (1-366)."""
        ...

    def day_of_week(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract day of week (Monday=1 to Sunday=7)."""
        ...

    def week_of_year(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract ISO week of year (1-53)."""
        ...

    def iso_year(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract ISO 8601 week-numbering year."""
        ...

    # =========================================================================
    # Component Extraction - Special
    # =========================================================================

    def unix_timestamp(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract seconds since 1970-01-01 00:00:00 UTC."""
        ...

    def timezone_offset(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Extract timezone offset to UTC in seconds."""
        ...

    # =========================================================================
    # Boolean Extraction
    # =========================================================================

    def is_leap_year(
        self,
        x: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Check if the year is a leap year."""
        ...

    def is_dst(
        self,
        x: SupportedExpressions,
        /,
        timezone: Optional[str] = None,
    ) -> SupportedExpressions:
        """Check if DST is observed at this time."""
        ...

    # =========================================================================
    # Date/Time Arithmetic
    # =========================================================================

    def add_years(
        self,
        x: SupportedExpressions,
        years: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add years to a datetime."""
        ...

    def add_months(
        self,
        x: SupportedExpressions,
        months: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add months to a datetime."""
        ...

    def add_days(
        self,
        x: SupportedExpressions,
        days: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add days to a datetime."""
        ...

    def add_hours(
        self,
        x: SupportedExpressions,
        hours: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add hours to a datetime."""
        ...

    def add_minutes(
        self,
        x: SupportedExpressions,
        minutes: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add minutes to a datetime."""
        ...

    def add_seconds(
        self,
        x: SupportedExpressions,
        seconds: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add seconds to a datetime."""
        ...

    def add_milliseconds(
        self,
        x: SupportedExpressions,
        milliseconds: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add milliseconds to a datetime."""
        ...

    def add_microseconds(
        self,
        x: SupportedExpressions,
        microseconds: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Add microseconds to a datetime."""
        ...

    # =========================================================================
    # Date Difference
    # =========================================================================

    def diff_years(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in years (x - other)."""
        ...

    def diff_months(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in months (x - other)."""
        ...

    def diff_days(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in days (x - other)."""
        ...

    def diff_hours(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in hours (x - other)."""
        ...

    def diff_minutes(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in minutes (x - other)."""
        ...

    def diff_seconds(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in seconds (x - other)."""
        ...

    def diff_milliseconds(
        self,
        x: SupportedExpressions,
        other: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Calculate difference in milliseconds (x - other)."""
        ...

    # =========================================================================
    # Truncation / Rounding
    # =========================================================================

    def truncate(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Truncate datetime to the specified unit (floor)."""
        ...

    def round(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Round datetime to the nearest unit."""
        ...

    def ceil(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Round datetime up to the next unit."""
        ...

    def floor(
        self,
        x: SupportedExpressions,
        unit: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Round datetime down to the previous unit."""
        ...

    # =========================================================================
    # Flexible Duration Offset
    # =========================================================================

    def offset_by(
        self,
        x: SupportedExpressions,
        *,
        offset: str,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        component: SupportedExpressions,
        timezone: SupportedExpressions = None,
        /,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        /,
        component: SupportedExpressions,
    ) -> SupportedExpressions:
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
        x: SupportedExpressions,
        timezone: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Convert to specified timezone."""
        ...

    def assume_timezone(
        self,
        x: SupportedExpressions,
        timezone: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Assume the timestamp is in the specified timezone."""
        ...

    # =========================================================================
    # Formatting
    # =========================================================================

    def strftime(
        self,
        x: SupportedExpressions,
        format: SupportedExpressions,
        /,
    ) -> SupportedExpressions:
        """Format datetime as string."""
        ...

    # =========================================================================
    # Snapshot
    # =========================================================================

    def today(self) -> SupportedExpressions:
        """Return today's date as a literal expression."""
        ...

    def now(self) -> SupportedExpressions:
        """Return current datetime as a literal expression."""
        ...
