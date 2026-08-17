"""Polars ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Polars backend.
"""

from __future__ import annotations

from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    CALENDAR_COMPONENTS,
    DatetimeComponent,
)
from typing import Any, TYPE_CHECKING, Optional

import polars as pl

from ..base import PolarsBaseExpressionSystem
from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarDatetimeExpressionSystemProtocol
if TYPE_CHECKING:
    from mountainash.expressions.types import PolarsExpr


# Substrait canonical unit name -> Polars duration-string suffix. Combined
# with an integer multiplier (e.g. "2d", "3h", "1mo") this is accepted
# natively by Polars' dt.truncate/dt.round/dt.offset_by -- verified against
# polars 1.43.2 (item 74).
_POLARS_UNIT_SUFFIX = {
    "YEAR": "y", "MONTH": "mo", "WEEK": "w", "DAY": "d",
    "HOUR": "h", "MINUTE": "m", "SECOND": "s",
    "MILLISECOND": "ms", "MICROSECOND": "us",
}

# round_temporal's in-scope units (v1): YEAR/MONTH/WEEK are declared
# UNSUPPORTED there (ambiguous fixed-duration length) -- round_calendar
# covers all nine.
_ROUND_TEMPORAL_UNITS = frozenset(
    {"DAY", "HOUR", "MINUTE", "SECOND", "MILLISECOND", "MICROSECOND"}
)


def _round_datetime(x: PolarsExpr, rounding: str, unit: str, multiple: int) -> PolarsExpr:
    """Shared round_temporal/round_calendar implementation.

    FLOOR/CEIL/ROUND_TIE_DOWN are hand-rolled from dt.truncate + dt.offset_by
    (Polars has no native CEIL or tie-down primitive). ROUND_TIE_UP uses
    Polars' native dt.round -- verified empirically (2026-08-16) that its
    tie rule IS tie-up (10:30 -> 11:00, not 10:00) and that it accepts every
    combined multiplier/unit string used here, including calendar units.
    """
    every = f"{multiple}{_POLARS_UNIT_SUFFIX[unit]}"
    floor = x.dt.truncate(every)
    if rounding == "FLOOR":
        return floor
    if rounding == "ROUND_TIE_UP":
        return x.dt.round(every)
    ceiling = pl.when(floor == x).then(x).otherwise(floor.dt.offset_by(every))
    if rounding == "CEIL":
        return ceiling
    # ROUND_TIE_DOWN: nearest, tying to the earlier point on equidistance.
    diff_down = x - floor
    diff_up = ceiling - x
    return pl.when(diff_down <= diff_up).then(floor).otherwise(ceiling)

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
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: Any = None,
    ) -> PolarsExpr:
        """Round datetime to a multiple of a fixed-duration time unit.

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: One of DAY, HOUR, MINUTE, SECOND, MILLISECOND, MICROSECOND.
                YEAR/MONTH/WEEK are declared UNSUPPORTED here (ambiguous
                fixed-duration length; see capabilities/datetime/rounding.py)
                -- the raise below is defence in depth, the real gate is the
                capability fact.
            multiple: Positive multiplier on unit. Defaults to 1.
            origin: Never non-None here -- the API builder rejects it at
                build time (v1 scope; real Substrait origin is an
                arguments-channel value, not a string option).

        Returns:
            Rounded datetime.
        """
        if unit not in _ROUND_TEMPORAL_UNITS:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import (
                FKEY_SUBSTRAIT_SCALAR_DATETIME,
            )

            raise BackendCapabilityError(
                f"round_temporal unit={unit!r} is not supported -- fixed-duration "
                "rounding is ambiguous for YEAR/MONTH/WEEK; use round_calendar",
                backend="polars",
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
            )
        return _round_datetime(x, rounding, unit, multiple)

    def round_calendar(
        self,
        x: PolarsExpr,
        /,
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: Any = None,
    ) -> PolarsExpr:
        """Round datetime to a multiple of a calendar time unit.

        All nine Substrait units are in scope (calendar rounding is
        unambiguous for every one, unlike round_temporal).

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: YEAR, MONTH, WEEK, DAY, HOUR, MINUTE, SECOND, MILLISECOND,
                or MICROSECOND.
            multiple: Positive multiplier on unit. Defaults to 1.
            origin: Never non-None here -- the API builder rejects it at
                build time (v1 scope).

        Returns:
            Rounded datetime.
        """
        return _round_datetime(x, rounding, unit, multiple)
