"""Polars ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Polars backend.
"""

from __future__ import annotations

from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    CALENDAR_COMPONENTS,
    DatetimeComponent,
)
from typing import TYPE_CHECKING, Optional

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarDatetimeExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


class SubstraitPolarsScalarDatetimeExpressionSystem(PolarsBaseExpressionSystem, SubstraitScalarDatetimeExpressionSystemProtocol[pl.Expr]):
    """Polars implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components (20+ component types)
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations:
    - Date arithmetic: add_days, add_months, add_years, etc.
    - Date difference: diff_days, diff_months, diff_years, etc.
    - Truncation: truncate, round, ceil, floor
    - Timezone: to_timezone, assume_timezone
    - Formatting: strftime
    """

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract(
        self,
        x: PolarsExpr,
        /,
        component: str,
        indexing: str = None,
        timezone: str = None,
    ) -> PolarsExpr:
        """Extract a date/time component (Substrait: extract).

        ``indexing`` (ONE/ZERO) applies only to calendar components; the
        builder rejects it otherwise. ``timezone`` converts the value to the
        target IANA zone before the component lookup.
        """
        comp = component.value if isinstance(component, DatetimeComponent) else str(component).upper()

        e = x
        if timezone is not None:
            e = e.dt.convert_time_zone(timezone)

        component_map = {
            "YEAR": lambda d: d.dt.year(),
            "ISO_YEAR": lambda d: d.dt.iso_year(),
            "QUARTER": lambda d: d.dt.quarter(),
            "MONTH": lambda d: d.dt.month(),
            "DAY": lambda d: d.dt.day(),
            "DAY_OF_YEAR": lambda d: d.dt.ordinal_day(),
            "MONDAY_DAY_OF_WEEK": lambda d: d.dt.weekday(),
            "SUNDAY_DAY_OF_WEEK": lambda d: (d.dt.weekday() % 7) + 1,
            "ISO_WEEK": lambda d: d.dt.week(),
            "HOUR": lambda d: d.dt.hour(),
            "MINUTE": lambda d: d.dt.minute(),
            "SECOND": lambda d: d.dt.second(),
            "MILLISECOND": lambda d: d.dt.millisecond(),
            "MICROSECOND": lambda d: d.dt.microsecond() % 1000,
            "NANOSECOND": lambda d: d.dt.nanosecond() % 1000,
            "SUBSECOND": lambda d: d.dt.microsecond(),
            "UNIX_TIME": lambda d: d.dt.epoch("s"),
        }

        if comp not in component_map:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
            raise BackendCapabilityError(
                f"extract component {comp!r} is not supported on polars",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
            )

        result = component_map[comp](e)
        if indexing == "ZERO" and comp in CALENDAR_COMPONENTS:
            result = result - 1
        return result

    def extract_boolean(
        self,
        x: PolarsExpr,
        /,
        component: str,
        timezone: str = None,
    ) -> PolarsExpr:
        """Extract a boolean date/time component (Substrait: extract_boolean)."""
        comp = component.value if isinstance(component, BooleanComponent) else str(component).upper()

        e = x
        if timezone is not None:
            e = e.dt.convert_time_zone(timezone)

        if comp == "IS_LEAP_YEAR":
            year = e.dt.year()
            return ((year % 4 == 0) & (year % 100 != 0)) | (year % 400 == 0)

        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
        raise BackendCapabilityError(
            f"extract_boolean component {comp!r} is not supported on polars",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
        )


    # =========================================================================
    # Substrait Interval Operations
    # =========================================================================

    def add(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add an interval to a date/time value.

        Args:
            x: Datetime expression.
            y: Interval/duration to add.

        Returns:
            Datetime with interval added.
        """
        return x + y

    def subtract(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Subtract an interval from a date/time value.

        Args:
            x: Datetime expression.
            y: Interval/duration to subtract.

        Returns:
            Datetime with interval subtracted.
        """
        return x - y

    def multiply(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Multiply an interval by an integral number.

        Args:
            x: Interval/duration expression.
            y: Multiplier.

        Returns:
            Scaled interval.
        """
        return x * y

    def add_intervals(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
        """Add two intervals together.

        Args:
            x: First interval.
            y: Second interval.

        Returns:
            Combined interval.
        """
        return x + y

    # =========================================================================
    # Substrait Datetime Comparisons
    # =========================================================================

    def lt(
        self,
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        y: PolarsExpr,
        /,
    ) -> PolarsExpr:
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
        x: PolarsExpr,
        /,
        timezone: str,
    ) -> PolarsExpr:
        """Assume the timestamp is in the specified timezone.

        Args:
            x: Datetime expression (timezone-naive).
            timezone: Timezone to assume (IANA format).

        Returns:
            Timezone-aware datetime.
        """
        return x.dt.replace_time_zone(timezone)


    def local_timestamp(
        self,
        x: PolarsExpr,
        /,
        timezone: str,
    ) -> PolarsExpr:
        """Convert UTC-relative timestamp_tz to local timestamp.

        Args:
            x: UTC timestamp expression.
            timezone: Target timezone (IANA format).

        Returns:
            Local timestamp in the given timezone.
        """
        # Convert to timezone then remove timezone info
        return x.dt.convert_time_zone(timezone).dt.replace_time_zone(None)

    # =========================================================================
    # Substrait Parsing Operations
    # =========================================================================

    def strptime_time(
        self,
        x: PolarsExpr,
        /,
        format: str,
    ) -> PolarsExpr:
        """Parse string into time using provided format.

        Args:
            x: String to parse.
            format: strptime format string.

        Returns:
            Parsed time expression.
        """
        return x.str.to_time(format)

    def strptime_date(
        self,
        x: PolarsExpr,
        /,
        format: str,
    ) -> PolarsExpr:
        """Parse string into date using provided format.

        Args:
            x: String to parse.
            format: strptime format string.

        Returns:
            Parsed date expression.
        """
        return x.str.to_date(format)

    def strptime_timestamp(
        self,
        x: PolarsExpr,
        /,
        format: str,
        timezone: Optional[str] = None,
    ) -> PolarsExpr:
        """Parse string into timestamp using provided format.

        Args:
            x: String to parse.
            format: strptime format string.
            timezone: Optional timezone (IANA format).

        Returns:
            Parsed timestamp expression.
        """
        result = x.str.to_datetime(format)
        if timezone is not None:
            result = result.dt.replace_time_zone(timezone)
        return result

    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def strftime(
        self,
        x: PolarsExpr,
        /,
        format: str,
    ) -> PolarsExpr:
        """Format datetime as string.

        Args:
            x: Datetime expression.
            format: strftime format string.

        Returns:
            Formatted string.
        """
        return x.dt.strftime(format)



    # =========================================================================
    # Substrait Rounding Operations
    # =========================================================================

    def round_temporal(
        self,
        x: PolarsExpr,
        /,
        rounding: Optional[str] = None,
        unit: str = "1d",
        multiple: int = 1,
        origin: Optional[str] = None,
    ) -> PolarsExpr:
        """Round datetime to a multiple of a time unit.

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: Time unit string.
            multiple: Multiple of unit (default 1).
            origin: Origin timestamp for rounding.

        Returns:
            Rounded datetime.
        """
        rounding = rounding if rounding else "FLOOR"

        if rounding == "FLOOR":
            return x.dt.truncate(unit)
        elif rounding == "CEIL":
            truncated = x.dt.truncate(unit)
            return pl.when(truncated == x).then(x).otherwise(truncated.dt.offset_by(unit))
        else:
            # ROUND_TIE_DOWN, ROUND_TIE_UP - use round
            return x.dt.round(unit)

    def round_calendar(
        self,
        x: PolarsExpr,
        /,
        rounding: Optional[str] = None,
        unit: str = "1d",
        origin: Optional[str] = None,
        multiple: int = 1,
    ) -> PolarsExpr:
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
        """
        # For Polars, calendar rounding uses the same approach
        return self.round_temporal(x, rounding, unit, multiple, origin)
