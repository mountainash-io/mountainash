"""ValidationResultProcessor — unified failure case analysis via mountainash relations."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import mountainash as ma

if TYPE_CHECKING:
    import polars as pl


class ValidationResultProcessor:
    """Processes pandera failure cases using mountainash relations and expressions."""

    def __init__(
        self,
        failure_cases: pl.DataFrame,
        *,
        source_data: pl.DataFrame | None = None,
        natural_key: list[str] | None = None,
        validator_name: str | None = None,
    ) -> None:
        self._failure_cases = failure_cases
        self._source_data = source_data
        self._natural_key = natural_key
        self._validator_name = validator_name
        self._rel = ma.relation(failure_cases)
        self._enriched: pl.DataFrame | None = None

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

    def enriched_failure_cases(self) -> pl.DataFrame:
        """Standardised failure cases with consistent column names and types."""
        if self._enriched is not None:
            return self._enriched

        rel = ma.relation(self._failure_cases)
        enriched = rel.with_columns(
            ma.lit(self._validator_name).alias("validator_name"),
            ma.col("check").alias("rule_id"),
            ma.col("column").alias("column_name"),
            ma.col("index").alias("row_index"),
            ma.col("failure_case").cast("string").alias("value_str"),
        ).select(
            "validator_name", "rule_id", "schema_context",
            "column_name", "row_index", "value_str",
        )

        if self._natural_key is not None:
            enriched = enriched.with_columns(
                ma.col("column_name").is_in(self._natural_key).alias("column_is_natural_key"),
            )

        result = enriched.collect()
        self._enriched = result
        return result

    def _enriched_non_null(self) -> Any:
        """Enriched failure cases filtered to non-null row_index, as a relation."""
        return ma.relation(self.enriched_failure_cases()).filter(
            ma.col("row_index").is_not_null()
        )

    def profiled_failure_count(self) -> pl.DataFrame:
        """Unique failing rows grouped by validator_name."""
        return (
            self._enriched_non_null()
            .group_by("validator_name")
            .agg(ma.col("row_index").n_unique().alias("unique_row_count"))
            .collect()
        )

    def profiled_failure_count_by_column(self) -> pl.DataFrame:
        """Unique failing rows grouped by validator_name + column_name."""
        return (
            self._enriched_non_null()
            .group_by("validator_name", "column_name")
            .agg(ma.col("row_index").n_unique().alias("unique_row_count"))
            .collect()
        )

    def profiled_failure_count_by_value(self) -> pl.DataFrame:
        """Unique failing rows grouped by validator_name + column_name + value_str."""
        return (
            self._enriched_non_null()
            .group_by("validator_name", "column_name", "value_str")
            .agg(ma.col("row_index").n_unique().alias("unique_row_count"))
            .collect()
        )

    def profiled_failure_count_by_rule(self) -> pl.DataFrame:
        """Unique failing rows grouped by validator_name + rule_id."""
        return (
            self._enriched_non_null()
            .group_by("validator_name", "rule_id")
            .agg(ma.col("row_index").n_unique().alias("unique_row_count"))
            .collect()
        )

    def malformed_rules(self) -> pl.DataFrame:
        """Rules where row_index is null — the rule errored instead of returning row-level booleans."""
        return (
            ma.relation(self.enriched_failure_cases())
            .filter(ma.col("row_index").is_null())
            .group_by("rule_id")
            .agg(ma.count_records().alias("null_index_count"))
            .collect()
        )

    def rules_well_formed(self) -> bool:
        """True if no malformed rules detected."""
        return len(self.malformed_rules()) == 0

    def _resolve_source_data(self, source_data: Any | None) -> Any:
        """Resolve source data from parameter or stored value."""
        resolved = source_data if source_data is not None else self._source_data
        if resolved is None:
            raise ValueError(
                "source_data is required for pivot operations. "
                "Pass it to the constructor or to this method."
            )
        return resolved

    def pivot_all_fields(self, source_data: Any | None = None) -> pl.DataFrame:
        """Wide pivot: all field values for failing rows, grouped by rule_id + row_index."""
        resolved = self._resolve_source_data(source_data)
        enriched = self.enriched_failure_cases()
        failures = ma.relation(enriched).filter(
            ma.col("row_index").is_not_null()
        ).with_columns(
            ma.col("row_index").cast("uint32").alias("row_index"),
        ).select("rule_id", "row_index").unique()

        source_rel = ma.relation(resolved).with_row_index(name="_row_idx")
        joined = failures.join(
            source_rel,
            left_on=["row_index"],
            right_on=["_row_idx"],
            how="inner",
        )
        return joined.collect()

    def pivot_key_fields(self, source_data: Any | None = None) -> pl.DataFrame:
        """Wide pivot: natural key field values only for failing rows."""
        if self._natural_key is None:
            raise ValueError(
                "natural_key is required for pivot_key_fields. "
                "Pass it to the constructor."
            )
        resolved = self._resolve_source_data(source_data)
        enriched = self.enriched_failure_cases()
        failures = ma.relation(enriched).filter(
            ma.col("row_index").is_not_null()
        ).with_columns(
            ma.col("row_index").cast("uint32").alias("row_index"),
        ).select("rule_id", "row_index").unique()

        source_rel = ma.relation(resolved).with_row_index(name="_row_idx")
        select_cols = ["_row_idx"] + [c for c in self._natural_key]
        source_rel = source_rel.select(*select_cols)
        joined = failures.join(
            source_rel,
            left_on=["row_index"],
            right_on=["_row_idx"],
            how="inner",
        )
        return joined.collect()

    def passed(self) -> bool:
        return len(self._failure_cases) == 0

    def passed_for_column(self, column: str) -> bool:
        return len(self.failure_cases_for_column(column)) == 0

    def passed_for_rule(self, rule_id: str) -> bool:
        return len(self.failure_cases_for_rule(rule_id)) == 0
