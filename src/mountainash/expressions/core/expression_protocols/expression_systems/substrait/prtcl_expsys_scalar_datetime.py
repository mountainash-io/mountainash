"""Protocol stubs auto-generated from Substrait YAMLs.

Auto-generated - regenerate with: python scripts/generate_from_substrait.py

These are STUBS - merge into your existing protocol files.
Adjust type hints and signatures as needed for your implementation.
"""

from __future__ import annotations

from typing import Protocol

from mountainash.core.types import ExpressionT


class SubstraitScalarDatetimeExpressionSystemProtocol(Protocol[ExpressionT]):
    """Protocol for scalar datetime operations.

    Auto-generated from Substrait datetime extension.
    Function type: scalar
    """

    def extract(self, x: ExpressionT, /, component: ExpressionT, timezone: str) -> ExpressionT:
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

    def extract_boolean(self, x: ExpressionT, /, component: ExpressionT) -> ExpressionT:
        """Extract boolean values of a date/time value. * IS_LEAP_YEAR Return true if year of the given value is a leap year and false otherwise. * IS_DST Return true if DST (Daylight Savings Time) is observed at the given value
  in the given timezone.

Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: extract_boolean
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def add(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Add an interval to a date/time type.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: add
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def subtract(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Subtract an interval from a date/time type.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: subtract
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def multiply(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Multiply an interval by an integral number.

        Substrait: multiply
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def add_intervals(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """Add two intervals together.

        Substrait: add_intervals
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...


    def lt(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """less than

        Substrait: lt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def lte(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """less than or equal to

        Substrait: lte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def gt(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """greater than

        Substrait: gt
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...


    def gte(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT:
        """greater than or equal to

        Substrait: gte
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...


    def assume_timezone(self, x: ExpressionT, /, timezone: str) -> ExpressionT:
        """Convert local timestamp to UTC-relative timestamp_tz using given local time's timezone.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: assume_timezone
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def local_timestamp(self, x: ExpressionT, /, timezone: str) -> ExpressionT:
        """Convert UTC-relative timestamp_tz to local timestamp using given local time's timezone.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: local_timestamp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strptime_time(self, x: ExpressionT, /, format: str) -> ExpressionT:
        """Parse string into time using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference.

        Substrait: strptime_time
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strptime_date(self, x: ExpressionT, /, format: str) -> ExpressionT:
        """Parse string into date using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference.

        Substrait: strptime_date
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strptime_timestamp(self, x: ExpressionT, /, format: str, timezone: str) -> ExpressionT:
        """Parse string into timestamp using provided format, see https://man7.org/linux/man-pages/man3/strptime.3.html for reference. If timezone is present in timestamp and provided as parameter an error is thrown.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is supplied as parameter and present in the parsed string the parsed timezone is used. If parameter supplied timezone is invalid an error is thrown.

        Substrait: strptime_timestamp
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def strftime(self, x: ExpressionT, /, format: str) -> ExpressionT:
        """Convert timestamp/date/time to string using provided format, see https://man7.org/linux/man-pages/man3/strftime.3.html for reference.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: strftime
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def round_temporal(self, x: ExpressionT, /, rounding: ExpressionT, unit: ExpressionT, multiple: ExpressionT, origin: ExpressionT) -> ExpressionT:
        """Round a given timestamp/date/time to a multiple of a time unit. If the given timestamp is not already an exact multiple from the origin in the given timezone, the resulting point is chosen as one of the two nearest multiples. Which of these is chosen is governed by rounding: FLOOR means to use the earlier one, CEIL means to use the later one, ROUND_TIE_DOWN means to choose the nearest and tie to the earlier one if equidistant, ROUND_TIE_UP means to choose the nearest and tie to the later one if equidistant.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: round_temporal
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...

    def round_calendar(self, x: ExpressionT, /, rounding: ExpressionT, unit: ExpressionT, origin: ExpressionT, multiple: ExpressionT) -> ExpressionT:
        """Round a given timestamp/date/time to a multiple of a time unit. If the given timestamp is not already an exact multiple from the last origin unit in the given timezone, the resulting point is chosen as one of the two nearest multiples. Which of these is chosen is governed by rounding: FLOOR means to use the earlier one, CEIL means to use the later one, ROUND_TIE_DOWN means to choose the nearest and tie to the earlier one if equidistant, ROUND_TIE_UP means to choose the nearest and tie to the later one if equidistant.
Timezone strings must be as defined by IANA timezone database (https://www.iana.org/time-zones). Examples: "Pacific/Marquesas", "Etc/GMT+1". If timezone is invalid an error is thrown.

        Substrait: round_calendar
        URI: https://raw.githubusercontent.com/substrait-io/substrait/main/extensions/functions_datetime.yaml
        """
        ...
