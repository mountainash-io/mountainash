"""Tests for ValidationResult and ValidationResultProcessor."""
from __future__ import annotations

import pytest
import polars as pl

from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor


@pytest.fixture
def sample_failure_cases() -> pl.DataFrame:
    """Failure cases in pandera's format."""
    return pl.DataFrame({
        "failure_case": ["0", "bad_val", "missing"],
        "schema_context": ["Column", "Column", "DataFrameSchema"],
        "column": ["age", "name", "TestContract"],
        "check": ["greater_than_or_equal_to(0)", "str_matches('^[a-z]+$')", "VR01"],
        "check_number": [0, 0, 0],
        "index": [0, 2, 1],
    })


@pytest.fixture
def empty_failure_cases() -> pl.DataFrame:
    return pl.DataFrame({
        "failure_case": [],
        "schema_context": [],
        "column": [],
        "check": [],
        "check_number": [],
        "index": [],
    }).cast({
        "failure_case": pl.Utf8,
        "schema_context": pl.Utf8,
        "column": pl.Utf8,
        "check": pl.Utf8,
        "check_number": pl.Int32,
        "index": pl.Int32,
    })


class TestValidationResult:

    def test_passing_result(self):
        result = ValidationResult(passes=True, validator_name="test")
        assert result.passes is True
        assert result.processor is None

    def test_failing_result_with_processor(self, sample_failure_cases):
        processor = ValidationResultProcessor(sample_failure_cases)
        result = ValidationResult(
            passes=False,
            validator_name="test",
            processor=processor,
        )
        assert result.passes is False
        assert result.processor is not None


class TestValidationResultProcessor:

    def test_failure_count(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.failure_count() == 3

    def test_passed_when_no_failures(self, empty_failure_cases):
        proc = ValidationResultProcessor(empty_failure_cases)
        assert proc.passed() is True

    def test_not_passed_when_failures(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed() is False

    def test_failure_cases_returns_all(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert len(proc.failure_cases()) == 3

    def test_failure_cases_for_column(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        age_failures = proc.failure_cases_for_column("age")
        assert len(age_failures) == 1
        assert age_failures["check"][0] == "greater_than_or_equal_to(0)"

    def test_failure_cases_for_rule(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        rule_failures = proc.failure_cases_for_rule("VR01")
        assert len(rule_failures) == 1

    def test_failure_count_by_column(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        by_col = proc.failure_count_by_column()
        assert isinstance(by_col, pl.DataFrame)
        assert len(by_col) >= 1

    def test_failure_count_by_rule(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        by_rule = proc.failure_count_by_rule()
        assert isinstance(by_rule, pl.DataFrame)
        assert len(by_rule) == 1

    def test_passed_for_column_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_column("score") is True

    def test_passed_for_column_false(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_column("age") is False

    def test_passed_for_rule_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_rule("VR99") is True

    def test_passed_for_rule_false(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_rule("VR01") is False


class TestConstructorParams:

    def test_default_params_unchanged(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.failure_count() == 3

    def test_source_data_stored(self, sample_failure_cases):
        source = pl.DataFrame({"age": [10, 20, 30], "name": ["a", "b", "c"]})
        proc = ValidationResultProcessor(
            sample_failure_cases, source_data=source, validator_name="v1",
        )
        assert proc._source_data is not None
        assert proc._validator_name == "v1"

    def test_natural_key_stored(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, natural_key=["age"],
        )
        assert proc._natural_key == ["age"]

    def test_no_natural_key_default(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc._natural_key is None


class TestEnrichedFailureCases:

    def test_enriched_columns_without_natural_key(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, validator_name="test_validator",
        )
        enriched = proc.enriched_failure_cases()
        assert set(enriched.columns) == {
            "validator_name", "rule_id", "schema_context",
            "column_name", "row_index", "value_str",
        }

    def test_enriched_columns_with_natural_key(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases,
            validator_name="test_validator",
            natural_key=["age"],
        )
        enriched = proc.enriched_failure_cases()
        assert "column_is_natural_key" in enriched.columns

    def test_enriched_values(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, validator_name="v1",
        )
        enriched = proc.enriched_failure_cases()
        assert enriched["validator_name"].to_list() == ["v1", "v1", "v1"]
        assert enriched["rule_id"].to_list() == [
            "greater_than_or_equal_to(0)", "str_matches('^[a-z]+$')", "VR01",
        ]
        assert enriched["column_name"].to_list() == ["age", "name", "TestContract"]
        assert enriched["row_index"].to_list() == [0, 2, 1]
        assert enriched["value_str"].to_list() == ["0", "bad_val", "missing"]

    def test_enriched_natural_key_flag(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases,
            validator_name="v1",
            natural_key=["age"],
        )
        enriched = proc.enriched_failure_cases()
        nk = enriched.select("column_name", "column_is_natural_key")
        age_row = nk.filter(pl.col("column_name") == "age")
        assert age_row["column_is_natural_key"][0] is True
        name_row = nk.filter(pl.col("column_name") == "name")
        assert name_row["column_is_natural_key"][0] is False

    def test_enriched_null_validator_name(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        enriched = proc.enriched_failure_cases()
        assert enriched["validator_name"].null_count() == 3

    def test_enriched_caching(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases, validator_name="v1")
        first = proc.enriched_failure_cases()
        second = proc.enriched_failure_cases()
        assert first is second


@pytest.fixture
def multi_failure_cases() -> pl.DataFrame:
    """Multiple failures across validators, columns, rules — with a null index for malformed rule."""
    return pl.DataFrame({
        "failure_case": ["0", "bad", "worse", "err", "0"],
        "schema_context": ["Column", "Column", "Column", "DataFrameSchema", "Column"],
        "column": ["age", "name", "name", "TestContract", "age"],
        "check": ["ge(0)", "str_match", "str_match", "VR_BAD", "ge(0)"],
        "check_number": [0, 0, 0, 0, 0],
        "index": [0, 1, 2, None, 3],
    })


class TestProfilingAggregations:

    def test_profiled_failure_count(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        result = proc.profiled_failure_count()
        assert "validator_name" in result.columns
        assert "unique_row_count" in result.columns
        row = result.filter(pl.col("validator_name") == "v1")
        assert row["unique_row_count"][0] == 4  # rows 0,1,2,3 — null excluded

    def test_profiled_failure_count_by_column(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        result = proc.profiled_failure_count_by_column()
        age_row = result.filter(pl.col("column_name") == "age")
        assert age_row["unique_row_count"][0] == 2  # rows 0, 3
        name_row = result.filter(pl.col("column_name") == "name")
        assert name_row["unique_row_count"][0] == 2  # rows 1, 2

    def test_profiled_failure_count_by_value(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        result = proc.profiled_failure_count_by_value()
        assert "value_str" in result.columns
        assert "unique_row_count" in result.columns
        assert len(result) >= 3

    def test_profiled_failure_count_by_rule(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        result = proc.profiled_failure_count_by_rule()
        ge_row = result.filter(pl.col("rule_id") == "ge(0)")
        assert ge_row["unique_row_count"][0] == 2  # rows 0, 3

    def test_profiled_excludes_null_row_index(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        result = proc.profiled_failure_count()
        total = result["unique_row_count"].sum()
        assert total == 4  # null-index row excluded


class TestMalformedRuleDetection:

    def test_malformed_rules_found(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        malformed = proc.malformed_rules()
        assert len(malformed) == 1
        assert malformed["rule_id"][0] == "VR_BAD"
        assert malformed["null_index_count"][0] == 1

    def test_malformed_rules_none(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, validator_name="v1",
        )
        malformed = proc.malformed_rules()
        assert len(malformed) == 0

    def test_rules_well_formed_false(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1",
        )
        assert proc.rules_well_formed() is False

    def test_rules_well_formed_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, validator_name="v1",
        )
        assert proc.rules_well_formed() is True
