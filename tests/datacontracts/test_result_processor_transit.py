"""Transit-boundary proofs for `ValidationResultProcessor` (Task 9 of the
pandas-transit-elimination plan, backlog slice 5, spec section 13 step 6).

Every internal Polars materialization inside `ValidationResultProcessor`
routes through `transit_call(BoundaryKey.RESULT_PROCESSOR_POLARS_MATERIALIZE,
...)`, whose registry entry declares `route=RouteKey.RESULT_PROCESSING` and
`transit_class=NON_PANDAS_OPERATION`. This file proves every processor
method's conversion trace carries ONLY that route -- never
`RouteKey.NATIVE_MATERIALIZATION` (the generic relation-collection route
used everywhere else) -- and that every source/result type is Polars.
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.core.transit import RouteKey, capture_conversion_trace
from mountainash.datacontracts.result_processor import ValidationResultProcessor
from mountainash.validation.identity import RowIdentity


@pytest.fixture
def failure_cases() -> pl.DataFrame:
    return pl.DataFrame({
        "check_id": ["age__ge", "name__pattern", "age__ge"],
        "check_kind": ["row", "row", "row"],
        "column": ["age", "name", "age"],
        "outcome": ["fail", "fail", "fail"],
        "value": ["0", "bad_val", "-1"],
        "message": [None, None, None],
        "name": ["alice", "bad_val", "carol"],
        "row_number": pl.Series([0, 1, 2], dtype=pl.Int64),
        "row": pl.Series([None, None, None], dtype=pl.Null),
    })


@pytest.fixture
def source_data() -> pl.DataFrame:
    return pl.DataFrame({
        "name": ["alice", "bad_val", "carol"],
        "age": [0, 20, -1],
    })


@pytest.fixture
def rule_metadata() -> dict:
    return {
        "age__ge": {"error_message": "{age} must be >= 0", "fields": ["age"]},
        "name__pattern": {"error_message": "bad name", "fields": []},
    }


def _assert_result_processing_only(trace) -> None:
    assert trace.records, "expected at least one transit_call() record"
    for record in trace.records:
        assert record.route is RouteKey.RESULT_PROCESSING
        assert record.route is not RouteKey.NATIVE_MATERIALIZATION


class TestUnkeyedMethodsRouteResultProcessing:
    def test_failure_cases_for_column(self, failure_cases):
        processor = ValidationResultProcessor(failure_cases)
        with capture_conversion_trace() as trace:
            result = processor.failure_cases_for_column("age")
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_failure_cases_for_rule(self, failure_cases):
        processor = ValidationResultProcessor(failure_cases)
        with capture_conversion_trace() as trace:
            result = processor.failure_cases_for_rule("age__ge")
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_failure_count_by_column(self, failure_cases):
        processor = ValidationResultProcessor(failure_cases)
        with capture_conversion_trace() as trace:
            result = processor.failure_count_by_column()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_failure_count_by_rule(self, failure_cases):
        processor = ValidationResultProcessor(failure_cases)
        with capture_conversion_trace() as trace:
            counts = processor.failure_count_by_rule()
        assert isinstance(counts, pl.DataFrame)
        assert all(record.route is RouteKey.RESULT_PROCESSING for record in trace.records)
        assert not any(record.route is RouteKey.NATIVE_MATERIALIZATION for record in trace.records)

    def test_enriched_failure_cases(self, failure_cases):
        processor = ValidationResultProcessor(failure_cases, validator_name="v1")
        with capture_conversion_trace() as trace:
            result = processor.enriched_failure_cases()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_enriched_failure_cases_second_call_is_cached_no_new_records(self, failure_cases):
        processor = ValidationResultProcessor(failure_cases, validator_name="v1")
        processor.enriched_failure_cases()
        with capture_conversion_trace() as trace:
            processor.enriched_failure_cases()
        assert trace.records == []


class TestProfiledCountsRouteResultProcessing:
    @pytest.fixture
    def processor(self, failure_cases):
        return ValidationResultProcessor(
            failure_cases, validator_name="v1", natural_key=["name"],
        )

    def test_profiled_failure_count(self, processor):
        with capture_conversion_trace() as trace:
            result = processor.profiled_failure_count()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_profiled_failure_count_by_column(self, processor):
        with capture_conversion_trace() as trace:
            result = processor.profiled_failure_count_by_column()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_profiled_failure_count_by_value(self, processor):
        with capture_conversion_trace() as trace:
            result = processor.profiled_failure_count_by_value()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_profiled_failure_count_by_rule(self, processor):
        with capture_conversion_trace() as trace:
            result = processor.profiled_failure_count_by_rule()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)


class TestKeyedMethodsRouteResultProcessing:
    @pytest.fixture
    def processor(self, failure_cases, source_data):
        return ValidationResultProcessor(
            failure_cases,
            source_data=source_data,
            identity=RowIdentity("keyed", ("name",)),
            validator_name="v1",
        )

    def test_pivot_all_fields(self, processor):
        with capture_conversion_trace() as trace:
            result = processor.pivot_all_fields()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_pivot_key_fields(self, processor):
        with capture_conversion_trace() as trace:
            result = processor.pivot_key_fields()
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_interpolate_messages_dict_metadata(self, processor, rule_metadata):
        with capture_conversion_trace() as trace:
            result = processor.interpolate_messages(rule_metadata)
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)

    def test_interpolate_messages_relation_metadata(self, processor):
        """rule_metadata as a raw non-DataFrame, non-dict source (a Polars
        LazyFrame) exercises `_normalise_rule_metadata`'s ma.relation()
        fallback branch, not just the dict/DataFrame fast paths."""
        meta_lazy = pl.DataFrame({
            "rule_id": ["age__ge", "name__pattern"],
            "error_message": ["{age} must be >= 0", "bad name"],
            "fields": [["age"], []],
        }).lazy()
        with capture_conversion_trace() as trace:
            result = processor.interpolate_messages(meta_lazy)
        assert isinstance(result, pl.DataFrame)
        _assert_result_processing_only(trace)
