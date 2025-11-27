"""Temporal/datetime operations mixin for ExpressionBuilder."""

from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING

from .base_expression_builder import BaseExpressionBuilder

if TYPE_CHECKING:
    from ..expression_nodes import ExpressionNode

from ..protocols import TemporalBuilderProtocol, ENUM_TEMPORAL_OPERATORS
from ..expression_nodes import (
    TemporalExtractExpressionNode,
    TemporalDiffExpressionNode,
    TemporalAdditionExpressionNode,
    TemporalTruncateExpressionNode,
    TemporalOffsetExpressionNode,
    TemporalSnapshotExpressionNode,
)


class TemporalExpressionBuilder(BaseExpressionBuilder, TemporalBuilderProtocol):
    """
    Mixin providing temporal/datetime operations for ExpressionBuilder.

    Implements all methods from TemporalBuilderProtocol:
    - Date/time extraction: dt_year(), dt_month(), dt_day(), dt_hour(), dt_minute(), dt_second(), dt_weekday(), dt_week(), dt_quarter()
    - Date differences: dt_diff_years(), dt_diff_months(), dt_diff_days(), dt_diff_hours(), dt_diff_minutes(), dt_diff_seconds(), dt_diff_milliseconds()
    - Date addition: dt_add_days(), dt_add_hours(), dt_add_minutes(), dt_add_seconds(), dt_add_months(), dt_add_years()
    - Date manipulation: dt_truncate(), dt_offset_by()
    - Date snapshots: dt_today(), dt_now()
    """


    # ========================================
    # Date/Time Extraction Operations
    # ========================================

    def dt_year(self) -> BaseExpressionBuilder:
        """
        Extract year component from datetime.

        Returns:
            New ExpressionBuilder with year extraction node

        Example:
            >>> col("timestamp").dt_year()  # datetime(2024, 5, 15) -> 2024
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_YEAR,
            self._node
        )
        return self.create(node)

    def dt_month(self) -> BaseExpressionBuilder:
        """
        Extract month component from datetime.

        Returns:
            New ExpressionBuilder with month extraction node

        Example:
            >>> col("timestamp").dt_month()  # datetime(2024, 5, 15) -> 5
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_MONTH,
            self._node
        )
        return self.create(node)

    def dt_day(self) -> BaseExpressionBuilder:
        """
        Extract day component from datetime.

        Returns:
            New ExpressionBuilder with day extraction node

        Example:
            >>> col("timestamp").dt_day()  # datetime(2024, 5, 15) -> 15
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_DAY,
            self._node
        )
        return self.create(node)

    def dt_hour(self) -> BaseExpressionBuilder:
        """
        Extract hour component from datetime.

        Returns:
            New ExpressionBuilder with hour extraction node

        Example:
            >>> col("timestamp").dt_hour()  # datetime(2024, 5, 15, 14, 30) -> 14
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_HOUR,
            self._node
        )
        return self.create(node)

    def dt_minute(self) -> BaseExpressionBuilder:
        """
        Extract minute component from datetime.

        Returns:
            New ExpressionBuilder with minute extraction node

        Example:
            >>> col("timestamp").dt_minute()  # datetime(2024, 5, 15, 14, 30) -> 30
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_MINUTE,
            self._node
        )
        return self.create(node)

    def dt_second(self) -> BaseExpressionBuilder:
        """
        Extract second component from datetime.

        Returns:
            New ExpressionBuilder with second extraction node

        Example:
            >>> col("timestamp").dt_second()  # datetime(2024, 5, 15, 14, 30, 45) -> 45
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_SECOND,
            self._node
        )
        return self.create(node)

    def dt_weekday(self) -> BaseExpressionBuilder:
        """
        Extract day of week from datetime.

        Returns:
            New ExpressionBuilder with weekday extraction node

        Example:
            >>> col("timestamp").dt_weekday()  # Monday = 0, Sunday = 6
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_WEEKDAY,
            self._node
        )
        return self.create(node)

    def dt_week(self) -> BaseExpressionBuilder:
        """
        Extract week number from datetime.

        Returns:
            New ExpressionBuilder with week extraction node

        Example:
            >>> col("timestamp").dt_week()  # Week number (1-53)
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_WEEK,
            self._node
        )
        return self.create(node)

    def dt_quarter(self) -> BaseExpressionBuilder:
        """
        Extract quarter from datetime.

        Returns:
            New ExpressionBuilder with quarter extraction node

        Example:
            >>> col("timestamp").dt_quarter()  # Quarter (1-4)
        """

        node = TemporalExtractExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_QUARTER,
            self._node
        )
        return self.create(node)

    # ========================================
    # Date Difference Operations
    # ========================================

    def dt_diff_years(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in years between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with year difference node

        Example:
            >>> col("end_date").dt_diff_years(col("start_date"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_YEARS,
            self._node,
            other_node
        )
        return self.create(node)

    def dt_diff_months(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in months between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with month difference node

        Example:
            >>> col("end_date").dt_diff_months(col("start_date"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_MONTHS,
            self._node,
            other_node
        )
        return self.create(node)

    def dt_diff_days(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in days between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with day difference node

        Example:
            >>> col("end_date").dt_diff_days(col("start_date"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_DAYS,
            self._node,
            other_node
        )
        return self.create(node)

    def dt_diff_hours(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in hours between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with hour difference node

        Example:
            >>> col("end_time").dt_diff_hours(col("start_time"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_HOURS,
            self._node,
            other_node
        )
        return self.create(node)

    def dt_diff_minutes(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in minutes between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with minute difference node

        Example:
            >>> col("end_time").dt_diff_minutes(col("start_time"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_MINUTES,
            self._node,
            other_node
        )
        return self.create(node)

    def dt_diff_seconds(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in seconds between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with second difference node

        Example:
            >>> col("end_time").dt_diff_seconds(col("start_time"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_SECONDS,
            self._node,
            other_node
        )
        return self.create(node)

    def dt_diff_milliseconds(self, other: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Calculate difference in milliseconds between two datetimes.

        Args:
            other: Other datetime to compare with

        Returns:
            New ExpressionBuilder with millisecond difference node

        Example:
            >>> col("end_time").dt_diff_milliseconds(col("start_time"))
        """

        other_node = self._to_node_or_value(other)
        node = TemporalDiffExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_DIFF_MILLISECONDS,
            self._node,
            other_node
        )
        return self.create(node)

    # ========================================
    # Date Addition Operations
    # ========================================

    def dt_add_days(self, days: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add days to datetime.

        Args:
            days: Number of days to add

        Returns:
            New ExpressionBuilder with day addition node

        Example:
            >>> col("date").dt_add_days(7)  # Add 7 days
        """

        days_node = self._to_node_or_value(days)
        node = TemporalAdditionExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_ADD_DAYS,
            self._node,
            days_node
        )
        return self.create(node)

    def dt_add_hours(self, hours: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add hours to datetime.

        Args:
            hours: Number of hours to add

        Returns:
            New ExpressionBuilder with hour addition node

        Example:
            >>> col("timestamp").dt_add_hours(24)  # Add 24 hours
        """

        hours_node = self._to_node_or_value(hours)
        node = TemporalAdditionExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_ADD_HOURS,
            self._node,
            hours_node
        )
        return self.create(node)

    def dt_add_minutes(self, minutes: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add minutes to datetime.

        Args:
            minutes: Number of minutes to add

        Returns:
            New ExpressionBuilder with minute addition node

        Example:
            >>> col("timestamp").dt_add_minutes(30)  # Add 30 minutes
        """

        minutes_node = self._to_node_or_value(minutes)
        node = TemporalAdditionExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_ADD_MINUTES,
            self._node,
            minutes_node
        )
        return self.create(node)

    def dt_add_seconds(self, seconds: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add seconds to datetime.

        Args:
            seconds: Number of seconds to add

        Returns:
            New ExpressionBuilder with second addition node

        Example:
            >>> col("timestamp").dt_add_seconds(60)  # Add 60 seconds
        """

        seconds_node = self._to_node_or_value(seconds)
        node = TemporalAdditionExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_ADD_SECONDS,
            self._node,
            seconds_node
        )
        return self.create(node)

    def dt_add_months(self, months: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add months to datetime.

        Args:
            months: Number of months to add

        Returns:
            New ExpressionBuilder with month addition node

        Example:
            >>> col("date").dt_add_months(3)  # Add 3 months
        """

        months_node = self._to_node_or_value(months)
        node = TemporalAdditionExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_ADD_MONTHS,
            self._node,
            months_node
        )
        return self.create(node)

    def dt_add_years(self, years: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Add years to datetime.

        Args:
            years: Number of years to add

        Returns:
            New ExpressionBuilder with year addition node

        Example:
            >>> col("date").dt_add_years(1)  # Add 1 year
        """

        years_node = self._to_node_or_value(years)
        node = TemporalAdditionExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_ADD_YEARS,
            self._node,
            years_node
        )
        return self.create(node)

    # ========================================
    # Date Manipulation Operations
    # ========================================

    def dt_truncate(self, unit: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Truncate datetime to specified unit.

        Args:
            unit: Time unit to truncate to (e.g., "day", "hour", "month")

        Returns:
            New ExpressionBuilder with truncate node

        Example:
            >>> col("timestamp").dt_truncate("day")  # 2024-05-15 14:30:45 -> 2024-05-15 00:00:00
        """

        unit_node = self._to_node_or_value(unit)
        node = TemporalTruncateExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_TRUNCATE,
            self._node,
            unit_node
        )
        return self.create(node)

    def dt_offset_by(self, offset: Union[BaseExpressionBuilder, ExpressionNode, Any]) -> BaseExpressionBuilder:
        """
        Offset datetime by a duration string.

        Args:
            offset: Duration string (e.g., "1d", "2h30m", "-3w")

        Returns:
            New ExpressionBuilder with offset node

        Example:
            >>> col("timestamp").dt_offset_by("1d2h")  # Add 1 day and 2 hours
        """

        offset_node = self._to_node_or_value(offset)
        node = TemporalOffsetExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_OFFSET_BY,
            self._node,
            offset_node
        )
        return self.create(node)

    # ========================================
    # Date Snapshot Operations
    # ========================================

    def dt_today(self) -> BaseExpressionBuilder:
        """
        Get today's date (no time component).

        Returns:
            New ExpressionBuilder with today snapshot node

        Example:
            >>> ExpressionBuilder.dt_today()  # Static method usage
        """

        node = TemporalSnapshotExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_TODAY
        )
        return self.create(node)

    def dt_now(self) -> BaseExpressionBuilder:
        """
        Get current datetime (with time component).

        Returns:
            New ExpressionBuilder with now snapshot node

        Example:
            >>> ExpressionBuilder.dt_now()  # Static method usage
        """

        node = TemporalSnapshotExpressionNode(
            ENUM_TEMPORAL_OPERATORS.DT_NOW
        )
        return self.create(node)
