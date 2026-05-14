from datetime import datetime

from mountainash.pipelines.core.capabilities import ResolvedPredicates
from mountainash.pipelines.core.result import StepMetadata, StepResult


def test_step_metadata():
    meta = StepMetadata(
        step_name="extract_fitbit",
        completed_at=datetime(2026, 5, 13, 10, 0, 0),
        record_count=42,
    )
    assert meta.step_name == "extract_fitbit"
    assert meta.record_count == 42
    assert meta.input_cache_keys == {}


def test_step_metadata_with_predicates():
    predicates = ResolvedPredicates(
        date_start=None,
        date_end=None,
        limit=100,
    )
    meta = StepMetadata(
        step_name="query_data",
        completed_at=datetime(2026, 5, 13, 10, 0, 0),
        resolved_predicates=predicates,
    )
    assert meta.resolved_predicates is not None
    assert meta.resolved_predicates.limit == 100


def test_step_result():
    meta = StepMetadata(
        step_name="test",
        completed_at=datetime(2026, 5, 13, 10, 0, 0),
    )
    result = StepResult(
        data=[{"id": 1}, {"id": 2}],
        metadata=meta,
        cache_key="abc123",
    )
    assert len(result.data) == 2
    assert result.cache_key == "abc123"
    assert result.metadata.step_name == "test"


def test_step_result_is_frozen():
    meta = StepMetadata(step_name="test", completed_at=datetime.now())
    result = StepResult(data=[], metadata=meta, cache_key="x")
    try:
        result.cache_key = "y"
        assert False, "Should raise"
    except AttributeError:
        pass


def test_step_metadata_defaults():
    meta = StepMetadata(
        step_name="step1",
        completed_at=datetime(2026, 5, 13, 10, 0, 0),
    )
    assert meta.record_count is None
    assert meta.input_cache_keys == {}
    assert meta.resolved_predicates is None
