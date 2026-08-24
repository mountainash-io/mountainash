"""Ibis ScalarDatetimeExpressionProtocol implementation.

Implements datetime operations for the Ibis backend.
"""

from __future__ import annotations

from mountainash.expressions.core.datetime_components import (
    BooleanComponent,
    CALENDAR_COMPONENTS,
    DatetimeComponent,
)
from typing import Any, TYPE_CHECKING

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

# round_temporal's in-scope units (v1): YEAR/MONTH/WEEK are declared
# UNSUPPORTED there (ambiguous fixed-duration length) -- round_calendar
# covers all nine.
_ROUND_TEMPORAL_UNITS = frozenset(
    {"DAY", "HOUR", "MINUTE", "SECOND", "MILLISECOND", "MICROSECOND"}
)

# Substrait canonical unit name -> ibis.interval()/TimestampValue.bucket()
# plural kwarg. x.truncate(unit) accepts the canonical uppercase name
# directly (verified against ibis 12.0.0/duckdb) so no translation is
# needed there.
_IBIS_INTERVAL_KWARGS = {
    "YEAR": "years", "MONTH": "months", "WEEK": "weeks", "DAY": "days",
    "HOUR": "hours", "MINUTE": "minutes", "SECOND": "seconds",
    "MILLISECOND": "milliseconds", "MICROSECOND": "microseconds",
}


def _round_datetime(x: IbisValueExpr, rounding: str, unit: str, multiple: int) -> IbisValueExpr:
    """Shared round_temporal/round_calendar implementation.

    x.truncate(unit) gives FLOOR at multiple=1. For multiple>1,
    TimestampValue.bucket(**{kwarg: multiple}) buckets from the UNIX epoch
    (ibis has no per-op origin parameter honored here; v1 never supplies a
    custom origin). CEIL/tie modes are hand-rolled: ibis rejects Polars-style
    combined multiplier truncate strings (SignatureValidationError, verified
    2026-08-16) and has no native round/ceil primitive at all.
    """
    kwarg = _IBIS_INTERVAL_KWARGS[unit]
    floor = x.truncate(unit) if multiple == 1 else x.bucket(**{kwarg: multiple})
    if rounding == "FLOOR":
        return floor
    ceiling = (floor == x).ifelse(x, floor + ibis.interval(**{kwarg: multiple}))
    if rounding == "CEIL":
        return ceiling
    diff_down = x.epoch_seconds().cast("int64") - floor.epoch_seconds().cast("int64")
    diff_up = ceiling.epoch_seconds().cast("int64") - x.epoch_seconds().cast("int64")
    if rounding == "ROUND_TIE_UP":
        return (diff_up <= diff_down).ifelse(ceiling, floor)
    # ROUND_TIE_DOWN: nearest, tying to the earlier point on equidistance.
    return (diff_down <= diff_up).ifelse(floor, ceiling)


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
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x.cast("time")

    def strptime_date(
        self,
        x: IbisValueExpr,
        /,
        format: str,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x.as_date(format)

    def strptime_timestamp(
        self,
        x: IbisValueExpr,
        /,
        format: str,
        timezone: str = None,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x.as_timestamp(format).cast("timestamp")
    def parse_default(
        self,
        x: IbisValueExpr,
        /,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x.cast("timestamp")

    def parse_xsd_duration(
        self,
        x: IbisValueExpr,
        /,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x

    def parse_xsd_partial_date(
        self,
        x: IbisValueExpr,
        /,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x

    def parse_temporal_any(
        self,
        x: IbisValueExpr,
        /,
        kind: str,
        field_name: str | None = None,
        failure_behavior: str = "throw",
    ) -> IbisValueExpr:
        return x


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
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: Any = None,
    ) -> IbisValueExpr:
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
            raise BackendCapabilityError(
                f"round_temporal unit={unit!r} is not supported -- fixed-duration "
                "rounding is ambiguous for YEAR/MONTH/WEEK; use round_calendar",
                backend="ibis",
                function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.ROUND_TEMPORAL,
            )
        return _round_datetime(x, rounding, unit, multiple)

    def round_calendar(
        self,
        x: IbisValueExpr,
        /,
        rounding: str,
        unit: str,
        multiple: int = 1,
        origin: Any = None,
    ) -> IbisValueExpr:
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
