"""ValidationResultProcessor — unified failure case analysis."""
from __future__ import annotations

import polars as pl


class ValidationResultProcessor:
    """Processes pandera failure cases from a validation run."""

    def __init__(self, failure_cases: pl.DataFrame) -> None:
        self._failure_cases = failure_cases

    def failure_cases(self) -> pl.DataFrame:
        return self._failure_cases

    def failure_cases_for_column(self, column: str) -> pl.DataFrame:
        return self._failure_cases.filter(
            (pl.col("schema_context") == "Column") & (pl.col("column") == column)
        )

    def failure_cases_for_rule(self, rule_id: str) -> pl.DataFrame:
        return self._failure_cases.filter(
            (pl.col("schema_context") == "DataFrameSchema") & (pl.col("check") == rule_id)
        )

    def failure_count(self) -> int:
        return len(self._failure_cases)

    def failure_count_by_column(self) -> pl.DataFrame:
        return (
            self._failure_cases.filter(pl.col("schema_context") == "Column")
            .group_by("column")
            .agg(pl.len().alias("count"))
        )

    def failure_count_by_rule(self) -> pl.DataFrame:
        return (
            self._failure_cases.filter(pl.col("schema_context") == "DataFrameSchema")
            .group_by("check")
            .agg(pl.len().alias("count"))
        )

    def passed(self) -> bool:
        return len(self._failure_cases) == 0

    def passed_for_column(self, column: str) -> bool:
        return len(self.failure_cases_for_column(column)) == 0

    def passed_for_rule(self, rule_id: str) -> bool:
        return len(self.failure_cases_for_rule(rule_id)) == 0
