"""Tests for ValidationResult and ValidationResultProcessor."""
from __future__ import annotations

import pytest
import polars as pl
import pandera.polars as pa
import mountainash as ma

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor


class OrderContract(BaseDataContract):
    order_id: pa.typing.Series[int] = pa.Field(unique=True)
    amount: pa.typing.Series[float] = pa.Field(ge=0)
    status: pa.typing.Series[str] = pa.Field(isin=["open", "closed", "pending"])


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


@pytest.fixture
def source_data() -> pl.DataFrame:
    """Source data that was validated — row indices match failure_cases."""
    return pl.DataFrame({
        "age": [10, 20, 30, 40],
        "name": ["alice", "bad_val", "worse", "dave"],
        "score": [90, 80, 70, 60],
    })


@pytest.fixture
def pivot_failure_cases() -> pl.DataFrame:
    """Failure cases with indices matching source_data fixture."""
    return pl.DataFrame({
        "failure_case": ["10", "bad_val"],
        "schema_context": ["Column", "Column"],
        "column": ["age", "name"],
        "check": ["ge(18)", "str_match"],
        "check_number": [0, 0],
        "index": [0, 1],
    })


class TestPivotReports:

    def test_pivot_all_fields(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        result = proc.pivot_all_fields()
        assert len(result) == 2
        assert "age" in result.columns
        assert "name" in result.columns
        assert "score" in result.columns
        assert "rule_id" in result.columns
        assert "row_index" in result.columns

    def test_pivot_all_fields_with_override(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases, validator_name="v1",
        )
        result = proc.pivot_all_fields(source_data=source_data)
        assert len(result) == 2

    def test_pivot_all_fields_no_source_raises(self, pivot_failure_cases):
        proc = ValidationResultProcessor(
            pivot_failure_cases, validator_name="v1",
        )
        with pytest.raises(ValueError, match="source_data"):
            proc.pivot_all_fields()

    def test_pivot_key_fields(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
            natural_key=["name"],
        )
        result = proc.pivot_key_fields()
        assert len(result) == 2
        assert "name" in result.columns
        assert "rule_id" in result.columns
        assert "score" not in result.columns

    def test_pivot_key_fields_no_natural_key_raises(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        with pytest.raises(ValueError, match="natural_key"):
            proc.pivot_key_fields()

    def test_pivot_excludes_null_row_index(self, source_data):
        fc = pl.DataFrame({
            "failure_case": ["err"],
            "schema_context": ["DataFrameSchema"],
            "column": ["TestContract"],
            "check": ["VR_BAD"],
            "check_number": [0],
            "index": [None],
        })
        proc = ValidationResultProcessor(
            fc, source_data=source_data, validator_name="v1",
        )
        result = proc.pivot_all_fields()
        assert len(result) == 0


class TestInterpolateMessages:

    def test_interpolate_from_dict(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        metadata = {
            "ge(18)": {
                "error_message": "age {age} must be >= 18",
                "fields": ["age"],
            },
            "str_match": {
                "error_message": "name {name} is invalid",
                "fields": ["name"],
            },
        }
        result = proc.interpolate_messages(rule_metadata=metadata)
        assert "error_message_template" in result.columns
        assert "error_message" in result.columns
        msgs = result.sort("row_index")["error_message"].to_list()
        assert msgs[0] == "age 10 must be >= 18"
        assert msgs[1] == "name bad_val is invalid"

    def test_interpolate_from_dataframe(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        metadata_df = pl.DataFrame({
            "rule_id": ["ge(18)", "str_match"],
            "error_message": ["age {age} must be >= 18", "name {name} is invalid"],
            "fields": [["age"], ["name"]],
        })
        result = proc.interpolate_messages(rule_metadata=metadata_df)
        assert len(result) == 2

    def test_interpolate_multi_field(self, source_data):
        fc = pl.DataFrame({
            "failure_case": ["10"],
            "schema_context": ["DataFrameSchema"],
            "column": ["TestContract"],
            "check": ["VR01"],
            "check_number": [0],
            "index": [0],
        })
        proc = ValidationResultProcessor(
            fc, source_data=source_data, validator_name="v1",
        )
        metadata = {
            "VR01": {
                "error_message": "{name} (age {age}) failed",
                "fields": ["name", "age"],
            },
        }
        result = proc.interpolate_messages(rule_metadata=metadata)
        assert result["error_message"][0] == "alice (age 10) failed"

    def test_interpolate_no_source_raises(self, pivot_failure_cases):
        proc = ValidationResultProcessor(
            pivot_failure_cases, validator_name="v1",
        )
        with pytest.raises(ValueError, match="source_data"):
            proc.interpolate_messages(rule_metadata={"ge(18)": {"error_message": "x", "fields": []}})

    def test_interpolate_duplicate_rule_id_raises(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        dup_metadata = pl.DataFrame({
            "rule_id": ["ge(18)", "ge(18)"],
            "error_message": ["msg1", "msg2"],
            "fields": [["age"], ["age"]],
        })
        with pytest.raises(ValueError, match="duplicate"):
            proc.interpolate_messages(rule_metadata=dup_metadata)

    def test_interpolate_unmatched_rules_excluded(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        metadata = {
            "ge(18)": {
                "error_message": "age {age} must be >= 18",
                "fields": ["age"],
            },
        }
        result = proc.interpolate_messages(rule_metadata=metadata)
        assert len(result) == 1  # only ge(18) matched


class TestEndToEndPipeline:

    def test_validator_to_profiling_pipeline(self):
        rules = RuleRegistry([
            Rule("VR01", ma.col("amount").le(ma.col("amount"))),  # always passes
        ])

        validator = Validator(
            name="order_validator",
            contract=OrderContract,
            rules=rules,
            natural_key=["order_id"],
        )

        df = pl.DataFrame({
            "order_id": [1, 2, 3, 3],
            "amount": [100.0, -50.0, 200.0, 300.0],
            "status": ["open", "closed", "invalid", "pending"],
        })

        result = validator.validate(df)
        assert result.passes is False
        proc = result.processor
        assert proc is not None

        enriched = proc.enriched_failure_cases()
        assert "validator_name" in enriched.columns
        assert enriched["validator_name"][0] == "order_validator"

        by_col = proc.profiled_failure_count_by_column()
        assert len(by_col) >= 1

        assert proc.rules_well_formed() is True

        pivot = proc.pivot_all_fields()
        assert len(pivot) >= 1
        assert "order_id" in pivot.columns
