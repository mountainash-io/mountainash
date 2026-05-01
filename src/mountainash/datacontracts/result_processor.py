"""ValidationResultProcessor — unified failure case analysis via mountainash relations."""
from __future__ import annotations

import polars as pl
import mountainash as ma


class ValidationResultProcessor:
    """Processes pandera failure cases using mountainash relations and expressions."""

    def __init__(self, failure_cases: pl.DataFrame) -> None:
        self._failure_cases = failure_cases
        self._rel = ma.relation(failure_cases)

    def failure_cases(self) -> pl.DataFrame:
        return self._failure_cases

    def failure_cases_for_column(self, column: str) -> pl.DataFrame:
        return (
            self._rel
            .filter(
                ma.col("schema_context").eq(ma.lit("Column"))
                & ma.col("column").eq(ma.lit(column))
            )
            .collect()
        )

    def failure_cases_for_rule(self, rule_id: str) -> pl.DataFrame:
        return (
            self._rel
            .filter(
                ma.col("schema_context").eq(ma.lit("DataFrameSchema"))
                & ma.col("check").eq(ma.lit(rule_id))
            )
            .collect()
        )

    def failure_count(self) -> int:
        return len(self._failure_cases)

    def failure_count_by_column(self) -> pl.DataFrame:
        return (
            self._rel
            .filter(ma.col("schema_context").eq(ma.lit("Column")))
            .group_by("column")
            .agg(ma.count_records().alias("count"))
            .collect()
        )

    def failure_count_by_rule(self) -> pl.DataFrame:
        return (
            self._rel
            .filter(ma.col("schema_context").eq(ma.lit("DataFrameSchema")))
            .group_by("check")
            .agg(ma.count_records().alias("count"))
            .collect()
        )

    def passed(self) -> bool:
        return len(self._failure_cases) == 0

    def passed_for_column(self, column: str) -> bool:
        return len(self.failure_cases_for_column(column)) == 0

    def passed_for_rule(self, rule_id: str) -> bool:
        return len(self.failure_cases_for_rule(rule_id)) == 0
