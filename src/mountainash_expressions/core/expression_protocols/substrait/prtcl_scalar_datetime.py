"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, Union, TYPE_CHECKING

# Placeholder - use your actual type
SupportedExpressions = Any

if TYPE_CHECKING:
    from ...expression_nodes import ExpressionNode
    from ...expression_api.api_namespaces import BaseExpressionNamespace as BaseNamespace




class ScalarDatetimeExpressionProtocol(Protocol):
    """Protocol for datetime operations.

    Auto-generated from Substrait datetime extension.
    """

    def extract(self, x: SupportedExpressions, component: SupportedExpressions, timezone: SupportedExpressions, /) -> SupportedExpressions:
        """Extract portion of a date/time value. * YEAR Return the year. * ISO_YEAR Return the ISO 8601 week-numbering year. First week of an ISO year has the majority (4 or more) of
  its days in January.
* US_YEAR Return the US epidemiological year. First week of US epidemiological year has the majority (4 or more)
  of its days in January. Last week of US epidemiological year has the year's last Wednesday in it. US
  epidemiological week starts on Sunday.
* QUARTER Return the number of the quarter within the year. January 1 through March 31 map to the first quarter,
  April 1 through June 30 map to the second quarter, etc.
* MONTH Return the number of the month within the year. * DAY Return the number of the day within the month. * DAY_OF_YEAR Return the number of the day within the year. January 1 maps to the first day, February 1 maps to
  the thirty-second day, etc.
* MONDAY_DAY_OF_WEEK Return the number of the day within the week, from Monday (first day) to Sunday (seventh
  day).
* SUNDAY_DAY_OF_WEEK Return the number of the day within the week, from Sunday (first day) to Saturday (seventh
  day).
* MONDAY_WEEK Return the number of the week within the year. First week starts on first Monday of January. * SUNDAY_WEEK Return the number of the week within the year. First week starts on first Sunday of January. * ISO_WEEK Return the number of the ISO week within the ISO year. First ISO week has the majority (4 or more)
  of its days in January. ISO week starts on Monday.
* US_WEEK Return the number of the US week within the US year. First US week has the majority (4 or more) of
  its days in January. US week starts on Sunday.
* HOUR Return the hour (0-23). * MINUTE Return the minute (0-59). * SECOND Return the second (0-59). * MILLISECOND Return number of milliseconds since the last full second. * MICROSECOND Return number of microseconds since the last full millisecond. * NANOSECOND Return number of nanoseconds since the last full microsecond. * PICOSECOND Return number of picoseconds since the last full nanosecond. * SUBSECOND Return number of microseconds since the last full second of the given timestamp. * UNIX_TIME Return number of seconds that have elapsed since 1970-01-01 00:00:00 UTC, ignoring leap seconds. * TIMEZONE_OFFSET Return number of seconds of timezone offset to UTC.
The range of values returned for QUARTER, MONTH, DAY, DAY_OF_YEAR, MONDAY_DAY_OF_WEEK, SUNDAY_DAY_OF_WEEK, MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, and US_WEEK depends on whether counting starts at 1 or 0. This is governed by the indexing option.
When indexing is ONE: * QUARTER returns values in range 1-4 * MONTH returns values in range 1-12 * DAY returns values in range 1-31 * DAY_OF_YEAR returns values in range 1-366 * MONDAY_DAY_OF_WEEK and SUNDAY_DAY_OF_WEEK return values in range 1-7 * MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, and US_WEEK return values in range 1-53
When indexing is ZERO: * QUARTER returns values in range 0-3 * MONTH returns values in range 0-11 * DAY returns values in range 0-30 * DAY_OF_YEAR returns values in range 0-365 * MONDAY_DAY_OF_WEEK and SUNDAY_DAY_OF_WEEK return values in range 0-6 * MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, and US_WEEK return values in range 0-52
The indexing option must be specified when the component is QUARTER, MONTH, DAY, DAY_OF_YEAR, MONDAY_DAY_OF_WEEK, SUNDAY_DAY_OF_WEEK, MONDAY_WEEK, SUNDAY_WEEK, ISO_WEEK, or US_WEEK. The indexing option cannot be specified when the component is YEAR, ISO_YEAR, US_YEAR, HOUR, MINUTE, SECOND, MILLISECOND, MICROSECOND, SUBSECOND, UNIX_TIME, or TIMEZONE_OFFSET.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: extract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def extract_boolean(self, x: SupportedExpressions, /, component: SupportedExpressions,) -> SupportedExpressions:
        """Extract boolean values of a date/time value. * IS_LEAP_YEAR Return true if year of the given value is a leap year and false otherwise. * IS_DST Return true if DST (Daylight Savings Time) is observed at the given value
  in the given timezone.

Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: extract_boolean
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

#     def add(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Add an interval to a date/time type.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: add
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def multiply(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Multiply an interval by an integral number.

#         Substrait: multiply
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def add_intervals(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Add two intervals together.

#         Substrait: add_intervals
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def subtract(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """Subtract an interval from a date/time type.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: subtract
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def lte(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """less than or equal to

#         Substrait: lte
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def lt(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """less than

#         Substrait: lt
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def gte(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """greater than or equal to

#         Substrait: gte
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def gt(self, x: SupportedExpressions, y: SupportedExpressions) -> SupportedExpressions:
#         """greater than

#         Substrait: gt
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def assume_timezone(self, x: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
#         """Convert local timestamp to UTC-relative timestamp_tz using given local time's timezone.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: assume_timezone
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def local_timestamp(self, x: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
#         """Convert UTC-relative timestamp_tz to local timestamp using given local time's timezone.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: local_timestamp
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def strptime_time(self, time_string: SupportedExpressions, format: SupportedExpressions) -> SupportedExpressions:
#         """Parse string into time using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference.

#         Substrait: strptime_time
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def strptime_date(self, date_string: SupportedExpressions, format: SupportedExpressions) -> SupportedExpressions:
#         """Parse string into date using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference.

#         Substrait: strptime_date
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def strptime_timestamp(self, timestamp_string: SupportedExpressions, format: SupportedExpressions, timezone: SupportedExpressions) -> SupportedExpressions:
#         """Parse string into timestamp using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference. If timezone is present in timestamp and provided as parameter an error is thrown.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is supplied as parameter and present in the parsed string the parsed timezone is used. If parameter supplied timezone is invalid an error is thrown.

#         Substrait: strptime_timestamp
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def strftime(self, x: SupportedExpressions, format: SupportedExpressions) -> SupportedExpressions:
#         """Convert timestamp/date/time to string using provided format, see https://man7.org/linux/man-pages/man3/strftime.3.html for reference.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: strftime
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def round_temporal(self, x: SupportedExpressions, rounding: SupportedExpressions, unit: SupportedExpressions, multiple: SupportedExpressions, origin: SupportedExpressions) -> SupportedExpressions:
#         """Round a given timestamp/date/time to a multiple of a time unit. If the given timestamp is not already an exact multiple from the origin in the given timezone, the resulting point is chosen as one of the two nearest multiples. Which of these is chosen is governed by rounding: FLOOR means to use the earlier one, CEIL means to use the later one, ROUND_TIE_DOWN means to choose the nearest and tie to the earlier one if equidistant, ROUND_TIE_UP means to choose the nearest and tie to the later one if equidistant.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: round_temporal
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def round_calendar(self, x: SupportedExpressions, rounding: SupportedExpressions, unit: SupportedExpressions, origin: SupportedExpressions, multiple: SupportedExpressions) -> SupportedExpressions:
#         """Round a given timestamp/date/time to a multiple of a time unit. If the given timestamp is not already an exact multiple from the last origin unit in the given timezone, the resulting point is chosen as one of the two nearest multiples. Which of these is chosen is governed by rounding: FLOOR means to use the earlier one, CEIL means to use the later one, ROUND_TIE_DOWN means to choose the nearest and tie to the earlier one if equidistant, ROUND_TIE_UP means to choose the nearest and tie to the later one if equidistant.
# Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

#         Substrait: round_calendar
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def min(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Min a set of values.

#         Substrait: min
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...

#     def max(self, x: SupportedExpressions) -> SupportedExpressions:
#         """Max a set of values.

#         Substrait: max
#         URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
#         """
#         ...


class ScalarDatetimeBuilderProtocol(Protocol):
    """Builder protocol for datetime operations.

    Defines user-facing fluent API methods that create expression nodes.
    These methods accept flexible inputs and return BaseNamespace for chaining.
    """

    # ============================================================
    # Component Extraction
    # ============================================================

    def year(self) -> "BaseNamespace":
        """Extract the year component.

        Substrait: extract (YEAR)
        """
        ...

    def month(self) -> "BaseNamespace":
        """Extract the month component (1-12).

        Substrait: extract (MONTH)
        """
        ...

    def day(self) -> "BaseNamespace":
        """Extract the day of month component (1-31).

        Substrait: extract (DAY)
        """
        ...

    def hour(self) -> "BaseNamespace":
        """Extract the hour component (0-23).

        Substrait: extract (HOUR)
        """
        ...

    def minute(self) -> "BaseNamespace":
        """Extract the minute component (0-59).

        Substrait: extract (MINUTE)
        """
        ...

    def second(self) -> "BaseNamespace":
        """Extract the second component (0-59).

        Substrait: extract (SECOND)
        """
        ...

    def millisecond(self) -> "BaseNamespace":
        """Extract milliseconds since last full second.

        Substrait: extract (MILLISECOND)
        """
        ...

    def microsecond(self) -> "BaseNamespace":
        """Extract microseconds since last full millisecond.

        Substrait: extract (MICROSECOND)
        """
        ...

    def nanosecond(self) -> "BaseNamespace":
        """Extract nanoseconds since last full microsecond.

        Substrait: extract (NANOSECOND)
        """
        ...

    def quarter(self) -> "BaseNamespace":
        """Extract the quarter (1-4).

        Substrait: extract (QUARTER)
        """
        ...

    def day_of_year(self) -> "BaseNamespace":
        """Extract day of year (1-366).

        Substrait: extract (DAY_OF_YEAR)
        """
        ...

    def day_of_week(self) -> "BaseNamespace":
        """Extract day of week (Monday=1 to Sunday=7).

        Substrait: extract (MONDAY_DAY_OF_WEEK)
        """
        ...

    def week_of_year(self) -> "BaseNamespace":
        """Extract ISO week of year (1-53).

        Substrait: extract (ISO_WEEK)
        """
        ...

    def iso_year(self) -> "BaseNamespace":
        """Extract ISO 8601 week-numbering year.

        Substrait: extract (ISO_YEAR)
        """
        ...

    def unix_timestamp(self) -> "BaseNamespace":
        """Extract seconds since 1970-01-01 00:00:00 UTC.

        Substrait: extract (UNIX_TIME)
        """
        ...

    def timezone_offset(self) -> "BaseNamespace":
        """Extract timezone offset to UTC in seconds.

        Substrait: extract (TIMEZONE_OFFSET)
        """
        ...

    # ============================================================
    # Boolean Extraction
    # ============================================================

    def is_leap_year(self) -> "BaseNamespace":
        """Whether the year is a leap year.

        Substrait: extract_boolean (IS_LEAP_YEAR)
        """
        ...

    def is_dst(self, timezone: Optional[str] = None) -> "BaseNamespace":
        """Whether DST is observed at this time.

        Substrait: extract_boolean (IS_DST)
        """
        ...

    # ============================================================
    # Date/Time Arithmetic
    # ============================================================

    def add_years(
        self,
        years: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add years to the datetime.

        Substrait: add
        """
        ...

    def add_months(
        self,
        months: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add months to the datetime.

        Substrait: add
        """
        ...

    def add_days(
        self,
        days: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add days to the datetime.

        Substrait: add
        """
        ...

    def add_hours(
        self,
        hours: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add hours to the datetime.

        Substrait: add
        """
        ...

    def add_minutes(
        self,
        minutes: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add minutes to the datetime.

        Substrait: add
        """
        ...

    def add_seconds(
        self,
        seconds: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add seconds to the datetime.

        Substrait: add
        """
        ...

    def add_milliseconds(
        self,
        milliseconds: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add milliseconds to the datetime.

        Substrait: add
        """
        ...

    def add_microseconds(
        self,
        microseconds: Union["BaseNamespace", "ExpressionNode", Any, int],
    ) -> "BaseNamespace":
        """Add microseconds to the datetime.

        Substrait: add
        """
        ...

    # ============================================================
    # Date Difference
    # ============================================================

    def diff_years(
        self,
        other: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Calculate difference in years.

        Substrait: subtract
        """
        ...

    def diff_months(
        self,
        other: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Calculate difference in months.

        Substrait: subtract
        """
        ...

    def diff_days(
        self,
        other: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Calculate difference in days.

        Substrait: subtract
        """
        ...

    def diff_hours(
        self,
        other: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Calculate difference in hours.

        Substrait: subtract
        """
        ...

    def diff_minutes(
        self,
        other: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Calculate difference in minutes.

        Substrait: subtract
        """
        ...

    def diff_seconds(
        self,
        other: Union["BaseNamespace", "ExpressionNode", Any],
    ) -> "BaseNamespace":
        """Calculate difference in seconds.

        Substrait: subtract
        """
        ...

    # ============================================================
    # Truncation / Rounding
    # ============================================================

    def truncate(
        self,
        unit: str,
    ) -> "BaseNamespace":
        """Truncate datetime to the specified unit.

        Units: year, quarter, month, week, day, hour, minute, second

        Substrait: round_temporal (FLOOR)
        """
        ...

    def round(
        self,
        unit: str,
    ) -> "BaseNamespace":
        """Round datetime to the nearest unit.

        Units: year, quarter, month, week, day, hour, minute, second

        Substrait: round_temporal (ROUND_TIE_UP)
        """
        ...

    def ceil(
        self,
        unit: str,
    ) -> "BaseNamespace":
        """Round datetime up to the next unit.

        Units: year, quarter, month, week, day, hour, minute, second

        Substrait: round_temporal (CEIL)
        """
        ...

    def floor(
        self,
        unit: str,
    ) -> "BaseNamespace":
        """Round datetime down to the previous unit.

        Units: year, quarter, month, week, day, hour, minute, second

        Substrait: round_temporal (FLOOR)
        """
        ...

    # ============================================================
    # Timezone Operations
    # ============================================================

    def to_timezone(
        self,
        timezone: str,
    ) -> "BaseNamespace":
        """Convert to specified timezone.

        Substrait: local_timestamp
        """
        ...

    def assume_timezone(
        self,
        timezone: str,
    ) -> "BaseNamespace":
        """Assume the timestamp is in the specified timezone.

        Substrait: assume_timezone
        """
        ...

    # ============================================================
    # Formatting / Parsing
    # ============================================================

    def strftime(
        self,
        format: str,
    ) -> "BaseNamespace":
        """Format datetime as string.

        Substrait: strftime
        """
        ...
