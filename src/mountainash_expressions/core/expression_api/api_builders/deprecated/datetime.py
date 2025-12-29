"""DateTime operations namespace (explicit .dt accessor).

Substrait-aligned implementation using ScalarFunctionNode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Optional

from .base import BaseExpressionNamespace
from ...expression_nodes import ScalarFunctionNode, SUBSTRAIT_DATETIME

if TYPE_CHECKING:
    from ..expression_api.base import BaseExpressionAPI
    from ...expression_nodes import SubstraitNode


class DateTimeNamespace(BaseExpressionNamespace):
    """
    DateTime operations namespace accessed via .dt accessor.

    Provides date/time extraction, arithmetic, and manipulation.
    Method names omit the 'dt_' prefix since the namespace provides
    that context.

    Usage:
        col("timestamp").dt.year()     # Instead of dt_year()
        col("timestamp").dt.add_days() # Instead of dt_add_days()

    Extraction Operations:
        year, month, day, hour, minute, second, weekday, week, quarter

    Difference Operations:
        diff_years, diff_months, diff_days, diff_hours, diff_minutes,
        diff_seconds, diff_milliseconds

    Addition Operations:
        add_years, add_months, add_days, add_hours, add_minutes, add_seconds

    Manipulation Operations:
        truncate, offset_by

    Snapshot Operations:
        today, now
    """

    # ========================================
    # Extraction Operations
    # ========================================

    def year(self) -> BaseExpressionAPI:
        """
        Extract year component from datetime.

        Returns:
            New ExpressionAPI with year extraction node.

        Example:
            >>> col("timestamp").dt.year()  # datetime(2024, 5, 15) -> 2024
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_YEAR,
            arguments=[self._node],
        )
        return self._build(node)

    def month(self) -> BaseExpressionAPI:
        """
        Extract month component from datetime.

        Returns:
            New ExpressionAPI with month extraction node.

        Example:
            >>> col("timestamp").dt.month()  # datetime(2024, 5, 15) -> 5
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_MONTH,
            arguments=[self._node],
        )
        return self._build(node)

    def day(self) -> BaseExpressionAPI:
        """
        Extract day component from datetime.

        Returns:
            New ExpressionAPI with day extraction node.

        Example:
            >>> col("timestamp").dt.day()  # datetime(2024, 5, 15) -> 15
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_DAY,
            arguments=[self._node],
        )
        return self._build(node)

    def hour(self) -> BaseExpressionAPI:
        """
        Extract hour component from datetime.

        Returns:
            New ExpressionAPI with hour extraction node.

        Example:
            >>> col("timestamp").dt.hour()  # datetime(2024, 5, 15, 14) -> 14
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_HOUR,
            arguments=[self._node],
        )
        return self._build(node)

    def minute(self) -> BaseExpressionAPI:
        """
        Extract minute component from datetime.

        Returns:
            New ExpressionAPI with minute extraction node.

        Example:
            >>> col("timestamp").dt.minute()  # datetime(..., 14, 30) -> 30
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_MINUTE,
            arguments=[self._node],
        )
        return self._build(node)

    def second(self) -> BaseExpressionAPI:
        """
        Extract second component from datetime.

        Returns:
            New ExpressionAPI with second extraction node.

        Example:
            >>> col("timestamp").dt.second()  # datetime(..., 30, 45) -> 45
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_SECOND,
            arguments=[self._node],
        )
        return self._build(node)

    def weekday(self) -> BaseExpressionAPI:
        """
        Extract day of week from datetime.

        Returns:
            New ExpressionAPI with weekday extraction node.

        Example:
            >>> col("timestamp").dt.weekday()  # Monday=0, Sunday=6
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_WEEKDAY,
            arguments=[self._node],
        )
        return self._build(node)

    def week(self) -> BaseExpressionAPI:
        """
        Extract week number from datetime.

        Returns:
            New ExpressionAPI with week extraction node.

        Example:
            >>> col("timestamp").dt.week()  # Week number (1-53)
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_WEEK,
            arguments=[self._node],
        )
        return self._build(node)

    def quarter(self) -> BaseExpressionAPI:
        """
        Extract quarter from datetime.

        Returns:
            New ExpressionAPI with quarter extraction node.

        Example:
            >>> col("timestamp").dt.quarter()  # Quarter (1-4)
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.EXTRACT_QUARTER,
            arguments=[self._node],
        )
        return self._build(node)

    # ========================================
    # Difference Operations
    # ========================================

    def diff_years(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in years between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with year difference node.

        Example:
            >>> col("end").dt.diff_years(col("start"))
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_YEARS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_months(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in months between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with month difference node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_MONTHS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_days(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in days between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with day difference node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_DAYS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_hours(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in hours between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with hour difference node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_HOURS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_minutes(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in minutes between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with minute difference node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_MINUTES,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_seconds(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in seconds between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with second difference node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_SECONDS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    def diff_milliseconds(
        self,
        other: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Calculate difference in milliseconds between two datetimes.

        Args:
            other: Other datetime to compare with.

        Returns:
            New ExpressionAPI with millisecond difference node.
        """
        other_node = self._to_substrait_node(other)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.DIFF_MILLISECONDS,
            arguments=[self._node, other_node],
        )
        return self._build(node)

    # ========================================
    # Addition Operations
    # ========================================

    def add_years(
        self,
        years: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add years to datetime.

        Args:
            years: Number of years to add.

        Returns:
            New ExpressionAPI with year addition node.

        Example:
            >>> col("date").dt.add_years(1)
        """
        years_node = self._to_substrait_node(years)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.ADD_YEARS,
            arguments=[self._node, years_node],
        )
        return self._build(node)

    def add_months(
        self,
        months: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add months to datetime.

        Args:
            months: Number of months to add.

        Returns:
            New ExpressionAPI with month addition node.

        Example:
            >>> col("date").dt.add_months(3)
        """
        months_node = self._to_substrait_node(months)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.ADD_MONTHS,
            arguments=[self._node, months_node],
        )
        return self._build(node)

    def add_days(
        self,
        days: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add days to datetime.

        Args:
            days: Number of days to add.

        Returns:
            New ExpressionAPI with day addition node.

        Example:
            >>> col("date").dt.add_days(7)
        """
        days_node = self._to_substrait_node(days)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.ADD_DAYS,
            arguments=[self._node, days_node],
        )
        return self._build(node)

    def add_hours(
        self,
        hours: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add hours to datetime.

        Args:
            hours: Number of hours to add.

        Returns:
            New ExpressionAPI with hour addition node.

        Example:
            >>> col("timestamp").dt.add_hours(24)
        """
        hours_node = self._to_substrait_node(hours)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.ADD_HOURS,
            arguments=[self._node, hours_node],
        )
        return self._build(node)

    def add_minutes(
        self,
        minutes: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add minutes to datetime.

        Args:
            minutes: Number of minutes to add.

        Returns:
            New ExpressionAPI with minute addition node.

        Example:
            >>> col("timestamp").dt.add_minutes(30)
        """
        minutes_node = self._to_substrait_node(minutes)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.ADD_MINUTES,
            arguments=[self._node, minutes_node],
        )
        return self._build(node)

    def add_seconds(
        self,
        seconds: Union[BaseExpressionAPI, SubstraitNode, Any],
    ) -> BaseExpressionAPI:
        """
        Add seconds to datetime.

        Args:
            seconds: Number of seconds to add.

        Returns:
            New ExpressionAPI with second addition node.

        Example:
            >>> col("timestamp").dt.add_seconds(60)
        """
        seconds_node = self._to_substrait_node(seconds)
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.ADD_SECONDS,
            arguments=[self._node, seconds_node],
        )
        return self._build(node)

    # ========================================
    # Manipulation Operations
    # ========================================

    def truncate(
        self,
        unit: str,
    ) -> BaseExpressionAPI:
        """
        Truncate datetime to specified unit.

        Args:
            unit: Time unit ("day", "hour", "month", etc.)

        Returns:
            New ExpressionAPI with truncate node.

        Example:
            >>> col("timestamp").dt.truncate("day")
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.TRUNCATE,
            arguments=[self._node],
            options={"unit": unit},
        )
        return self._build(node)

    def offset_by(
        self,
        offset: str,
    ) -> BaseExpressionAPI:
        """
        Offset datetime by a duration string.

        Args:
            offset: Duration string (e.g., "1d", "2h30m", "-3w")

        Returns:
            New ExpressionAPI with offset node.

        Example:
            >>> col("timestamp").dt.offset_by("1d2h")
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.OFFSET_BY,
            arguments=[self._node],
            options={"offset": offset},
        )
        return self._build(node)

    # ========================================
    # Snapshot Operations
    # ========================================

    def today(self) -> BaseExpressionAPI:
        """
        Get today's date (no time component).

        Returns:
            New ExpressionAPI with today snapshot node.

        Example:
            >>> col("date").dt.today()
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.TODAY,
            arguments=[],
        )
        return self._build(node)

    def now(self) -> BaseExpressionAPI:
        """
        Get current datetime (with time component).

        Returns:
            New ExpressionAPI with now snapshot node.

        Example:
            >>> col("timestamp").dt.now()
        """
        node = ScalarFunctionNode(
            function_key=SUBSTRAIT_DATETIME.NOW,
            arguments=[],
        )
        return self._build(node)

    # ========================================
    # Natural Language Filter Operations
    # ========================================

    def within_last(self, duration: str) -> BaseExpressionAPI:
        """
        Create expression for "within last X time".

        Uses natural language time expressions like journalctl --since.

        Args:
            duration: Time expression like "3 minutes", "2 days", "1h"

        Returns:
            Boolean expression: column > (now - duration)

        Example:
            >>> # Records from last 10 minutes
            >>> col("timestamp").dt.within_last("10 minutes")

            >>> # Filter to recent records
            >>> df.filter(col("timestamp").dt.within_last("1 hour").compile(df))
        """
        from ..utils.temporal import time_ago
        threshold = time_ago(duration)
        return self._api.gt(threshold)

    def within_next(self, duration: str) -> BaseExpressionAPI:
        """
        Create expression for "within next X time".

        Args:
            duration: Time expression like "3 minutes", "2 days", "1h"

        Returns:
            Boolean expression: column < (now + duration)

        Example:
            >>> # Records scheduled in next 2 hours
            >>> col("scheduled_at").dt.within_next("2 hours")
        """
        from datetime import datetime
        from ..utils.temporal import to_timedelta
        delta = to_timedelta(duration)
        threshold = datetime.now() + delta
        return self._api.lt(threshold)

    def older_than(self, duration: str) -> BaseExpressionAPI:
        """
        Create expression for "older than X time".

        Args:
            duration: Time expression like "3 minutes", "2 days", "1h"

        Returns:
            Boolean expression: column < (now - duration)

        Example:
            >>> # Records older than 7 days
            >>> col("created_at").dt.older_than("7 days")

            >>> # Cleanup old logs
            >>> old_logs = df.filter(col("timestamp").dt.older_than("30 days").compile(df))
        """
        from ..utils.temporal import time_ago
        threshold = time_ago(duration)
        return self._api.lt(threshold)

    def newer_than(self, duration: str) -> BaseExpressionAPI:
        """
        Alias for within_last() - create expression for "newer than X time ago".

        Args:
            duration: Time expression like "3 minutes", "2 days", "1h"

        Returns:
            Boolean expression: column > (now - duration)

        Example:
            >>> # Records newer than 3 hours
            >>> col("modified_at").dt.newer_than("3 hours")
        """
        return self.within_last(duration)

    def between_last(
        self,
        start_duration: str,
        end_duration: Optional[str] = None,
    ) -> BaseExpressionAPI:
        """
        Create expression for "between X and Y time ago".

        Args:
            start_duration: Start of range (e.g., "2 hours" = 2 hours ago)
            end_duration: End of range (default: "0 seconds" = now)

        Returns:
            Boolean expression: (now - start) <= column <= (now - end)

        Example:
            >>> # Records between 2 hours ago and 1 hour ago
            >>> col("timestamp").dt.between_last("2 hours", "1 hour")

            >>> # Records between 1 day ago and now
            >>> col("timestamp").dt.between_last("1 day")
        """
        from datetime import datetime
        from ..utils.temporal import time_ago

        start_time = time_ago(start_duration)

        if end_duration is None:
            end_time = datetime.now()
        else:
            end_time = time_ago(end_duration)

        # Note: start_time is older (smaller) than end_time
        return self._api.ge(start_time).and_(self._api.le(end_time))
