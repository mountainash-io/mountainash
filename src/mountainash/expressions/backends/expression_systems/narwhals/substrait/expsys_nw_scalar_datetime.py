"""Narwhals ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Narwhals backend.
"""

from __future__ import annotations

from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    CALENDAR_COMPONENTS,
    DatetimeComponent,
)
from typing import Any, TYPE_CHECKING

import narwhals as nw

from ..base import NarwhalsBaseExpressionSystem

from mountainash.expressions.core.expression_protocols.expression_systems.substrait import SubstraitScalarDatetimeExpressionSystemProtocol

if TYPE_CHECKING:
    from mountainash.expressions.types import NarwhalsExpr


# round_temporal's in-scope units (v1): YEAR/MONTH/WEEK are declared
# UNSUPPORTED there (ambiguous fixed-duration length) -- round_calendar
# covers YEAR/MONTH but also declares WEEK unsupported (narwhals dt.truncate
# rejects "1w" on both dialects).
_ROUND_TEMPORAL_UNITS = frozenset(
    {"DAY", "HOUR", "MINUTE", "SECOND", "MILLISECOND", "MICROSECOND"}
)

# Substrait canonical unit name -> Polars-style duration-string suffix.
# Narwhals dt.truncate/dt.offset_by use the same combined "<n><suffix>"
# format as Polars (verified against narwhals 2.24.0 on both dialects) --
# bare Substrait names ("YEAR") are NOT accepted, unlike ibis.
_NARWHALS_UNIT_SUFFIX = {
    "YEAR": "y", "MONTH": "mo", "DAY": "d",
    "HOUR": "h", "MINUTE": "m", "SECOND": "s",
    "MILLISECOND": "ms", "MICROSECOND": "us",
}


def _round_datetime(x: NarwhalsExpr, rounding: str, unit: str, multiple: int) -> NarwhalsExpr:
    """Shared round_temporal/round_calendar implementation (unit != WEEK).

    Narwhals has no native round/ceil/tie primitive at all -- every mode
    but FLOOR is hand-rolled from dt.truncate + dt.offset_by + duration
    comparison via total_seconds() (verified against narwhals 2.24.0 on
    both narwhals-polars and narwhals-pandas, including calendar units and
    multiple > 1, e.g. "3mo" for a quarter).
    """
    every = f"{multiple}{_NARWHALS_UNIT_SUFFIX[unit]}"
    floor = x.dt.truncate(every)
    if rounding == "FLOOR":
        return floor
    ceiling = nw.when(floor == x).then(x).otherwise(floor.dt.offset_by(every))
    if rounding == "CEIL":
        return ceiling
    diff_down = (x - floor).dt.total_seconds()
    diff_up = (ceiling - x).dt.total_seconds()
    if rounding == "ROUND_TIE_UP":
        return nw.when(diff_up <= diff_down).then(ceiling).otherwise(floor)
    # ROUND_TIE_DOWN: nearest, tying to the earlier point on equidistance.
    return nw.when(diff_down <= diff_up).then(floor).otherwise(ceiling)

class SubstraitNarwhalsScalarDatetimeExpressionSystem(NarwhalsBaseExpressionSystem, SubstraitScalarDatetimeExpressionSystemProtocol[nw.Expr]):
    """Narwhals implementation of ScalarDatetimeExpressionProtocol.

    Implements core datetime methods:
    - extract: Extract datetime components
    - extract_boolean: Extract boolean datetime properties

    Plus convenience methods for common operations.

    Note: Narwhals has a more limited datetime API than Polars. Some methods
    use workarounds or simplified implementations.
    """

    # =========================================================================
    # Core Extraction Methods
    # =========================================================================

    def extract(
        self,
        x: NarwhalsExpr,
        /,
        component: str,
        indexing: str = None,
        timezone: str = None,
    ) -> NarwhalsExpr:
        """Extract a date/time component (Substrait: extract)."""
        comp = component.value if isinstance(component, DatetimeComponent) else str(component).upper()

        e = x
        if timezone is not None:
            e = e.dt.convert_time_zone(timezone)

        component_map = {
            "YEAR": lambda d: d.dt.year(),
            "QUARTER": lambda d: (d.dt.month() - nw.lit(1)) // nw.lit(3) + nw.lit(1),
            "MONTH": lambda d: d.dt.month(),
            "DAY": lambda d: d.dt.day(),
            "DAY_OF_YEAR": lambda d: d.dt.ordinal_day(),
            "MONDAY_DAY_OF_WEEK": lambda d: d.dt.weekday(),
            "SUNDAY_DAY_OF_WEEK": lambda d: (d.dt.weekday() % nw.lit(7)) + nw.lit(1),
            "HOUR": lambda d: d.dt.hour(),
            "MINUTE": lambda d: d.dt.minute(),
            "SECOND": lambda d: d.dt.second(),
            "MILLISECOND": lambda d: d.dt.millisecond(),
            "MICROSECOND": lambda d: d.dt.microsecond() % nw.lit(1000),
            "NANOSECOND": lambda d: d.dt.nanosecond() % nw.lit(1000),
            "SUBSECOND": lambda d: d.dt.microsecond(),
        }

        if comp not in component_map:
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
            raise BackendCapabilityError(
                f"extract component {comp!r} is not supported on narwhals",
                backend=self.BACKEND_NAME,
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
            )

        result = component_map[comp](e)
        if indexing == "ZERO" and comp in CALENDAR_COMPONENTS:
            result = result - nw.lit(1)
        return result

    def extract_boolean(
        self,
        x: NarwhalsExpr,
        /,
        component: str,
        timezone: str = None,
    ) -> NarwhalsExpr:
        """Extract a boolean date/time component (Substrait: extract_boolean)."""
        comp = component.value if isinstance(component, BooleanComponent) else str(component).upper()

        e = x
        if timezone is not None:
            e = e.dt.convert_time_zone(timezone)

        if comp == "IS_LEAP_YEAR":
            year = e.dt.year()
            return ((year % nw.lit(4) == nw.lit(0)) & (year % nw.lit(100) != nw.lit(0))) | (year % nw.lit(400) == nw.lit(0))

        from mountainash.core.types import BackendCapabilityError
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
        raise BackendCapabilityError(
            f"extract_boolean component {comp!r} is not supported on narwhals",
            backend=self.BACKEND_NAME,
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
        )



    # =========================================================================
    # Substrait Interval Operations
    # =========================================================================

    def add(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
        """Multiply an interval by an integral number.

        Args:
            x: Interval/duration expression.
            y: Multiplier.

        Returns:
            Scaled interval.

        Note:
            Narwhals may not support interval multiplication.
        """
        return x * y

    def add_intervals(
        self,
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        y: NarwhalsExpr,
        /,
    ) -> NarwhalsExpr:
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
        x: NarwhalsExpr,
        /,
        timezone: str,
    ) -> NarwhalsExpr:
        """Assume the timestamp is in the specified timezone.

        Args:
            x: Datetime expression (timezone-naive).
            timezone: Timezone to assume (IANA format).

        Returns:
            Timezone-aware datetime.

        Note:
            Narwhals may not have timezone assignment. Returns input as fallback.
        """
        # Narwhals doesn't have replace_time_zone - fallback
        return x


    def local_timestamp(
        self,
        x: NarwhalsExpr,
        /,
        timezone: str,
    ) -> NarwhalsExpr:
        """Convert UTC-relative timestamp_tz to local timestamp.

        Args:
            x: UTC timestamp expression.
            timezone: Target timezone (IANA format).

        Returns:
            Local timestamp in the given timezone.
        """
        return x.dt.convert_time_zone(timezone).dt.replace_time_zone(None)

    # =========================================================================
    # Substrait Parsing Operations
    # =========================================================================

    def strptime_time(
        self,
        x: NarwhalsExpr,
        /,
        format: str,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        raise NotImplementedError(
            "strptime_time() is not supported by the Narwhals backend."
        )

    def strptime_date(
        self,
        x: NarwhalsExpr,
        /,
        format: str,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        return x.str.to_date(format=format)

    def strptime_timestamp(
        self,
        x: NarwhalsExpr,
        /,
        format: str,
        timezone: str = None,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        result = x.str.to_datetime(format=format)
        if timezone is not None:
            result = result.dt.replace_time_zone(timezone)
        return result
    def parse_default(
        self,
        x: NarwhalsExpr,
        /,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        return x.str.to_datetime()

    def parse_xsd_duration(
        self,
        x: NarwhalsExpr,
        /,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        return x

    def parse_xsd_partial_date(
        self,
        x: NarwhalsExpr,
        /,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        return x

    def parse_temporal_any(
        self,
        x: NarwhalsExpr,
        /,
        kind: str,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> NarwhalsExpr:
        return x


    # =========================================================================
    # Formatting Methods
    # =========================================================================

    def strftime(
        self,
        x: NarwhalsExpr,
        /,
        format: str,# = "%Y-%m-%d %H:%M:%S",
    ) -> NarwhalsExpr:
        """Format datetime as string."""
        return x.dt.to_string(format)


    # =========================================================================
    # Substrait Rounding Operations
    # =========================================================================

    def round_temporal(
        self,
        x: NarwhalsExpr,
        /,
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: Any = None,
    ) -> NarwhalsExpr:
        """Round datetime to a multiple of a fixed-duration time unit.

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: One of DAY, HOUR, MINUTE, SECOND, MILLISECOND, MICROSECOND.
                YEAR/MONTH/WEEK are declared UNSUPPORTED here (ambiguous
                fixed-duration length; see capabilities/datetime/rounding.py)
                -- the raise below is defence in depth.
            multiple: Positive multiplier on unit. Defaults to 1.
            origin: Never non-None here -- the API builder rejects it at
                build time (v1 scope).

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
                backend="narwhals",
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
            )
        return _round_datetime(x, rounding, unit, multiple)

    def round_calendar(
        self,
        x: NarwhalsExpr,
        /,
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: Any = None,
    ) -> NarwhalsExpr:
        """Round datetime to a multiple of a calendar time unit.

        Args:
            x: Datetime expression.
            rounding: FLOOR, CEIL, ROUND_TIE_DOWN, or ROUND_TIE_UP.
            unit: YEAR, MONTH, DAY, HOUR, MINUTE, SECOND, MILLISECOND, or
                MICROSECOND. WEEK is declared UNSUPPORTED (narwhals'
                ``dt.truncate`` rejects the "1w" duration on both dialects,
                verified 2026-08-16 -- matches the existing MA
                truncate/floor_dt "1w" gap in capabilities/datetime/options.py)
                -- the raise below is defence in depth.
            multiple: Positive multiplier on unit. Defaults to 1.
            origin: Never non-None here -- the API builder rejects it at
                build time (v1 scope).

        Returns:
            Rounded datetime.
        """
        if unit == "WEEK":
            from mountainash.core.types import BackendCapabilityError
            from mountainash.expressions.core.expression_system.function_keys.enums import (
                FKEY_SUBSTRAIT_SCALAR_DATETIME,
            )

            raise BackendCapabilityError(
                "round_calendar unit='WEEK' is not supported on narwhals -- "
                "dt.truncate rejects the '1w' duration on both dialects",
                backend="narwhals",
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_CALENDAR,
            )
        return _round_datetime(x, rounding, unit, multiple)
