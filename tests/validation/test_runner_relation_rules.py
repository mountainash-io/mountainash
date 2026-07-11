"""RelationRule execution: failure plans, row-struct failure cases."""
import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.validation import RelationRule, ValidationRunner


def _unique_plan(column):
    """Failure plan for a uniqueness check: rows of duplicated values."""
    def plan(rel):
        return (
            rel.group_by(column)
            .agg(ma.count_records().alias("__ma_n__"))
            .filter(ma.col("__ma_n__").gt(ma.lit(1)))
        )
    return plan


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestRelationRule:
    def test_passes_when_failure_relation_empty(self, backend_name, backend_factory):
        df = backend_factory.create({"id": [1, 2, 3]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df), [RelationRule(id="id_unique", plan=_unique_plan("id"))]
        )
        assert result.passes, f"[{backend_name}]"
        assert result.failure_cases.height == 0

    def test_fails_with_failing_rows_as_struct(self, backend_name, backend_factory):
        df = backend_factory.create({"id": [1, 2, 2, 3, 3, 3]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df), [RelationRule(id="id_unique", plan=_unique_plan("id"))]
        )
        summary = result.check_summaries.row(0, named=True)
        assert summary["status"] == "failed", f"[{backend_name}]"
        assert summary["fail_count"] == 2  # two duplicated key values
        assert result.failure_cases["outcome"].to_list() == ["fail", "fail"]
        assert result.failure_cases["check_kind"].to_list() == ["relation", "relation"]
        # failing source rows are namespaced under the `row` struct
        assert result.failure_cases["row"].dtype == pl.Struct
        assert result.failure_cases["column"].null_count() == 2


def test_failure_sample_caps_relation_rows():
    df = pl.DataFrame({"id": [1, 1, 2, 2, 3, 3]})
    result = ValidationRunner().validate_relation(
        ma.relation(df),
        [RelationRule(id="u", plan=_unique_plan("id"))],
        failure_sample=1,
    )
    assert result.failure_cases.height == 1
    assert result.check_summaries["fail_count"][0] == 3  # count exact, sample caps rows


def test_relation_rule_plan_exception_is_isolated():
    def broken(rel):
        raise RuntimeError("boom")

    df = pl.DataFrame({"id": [1]})
    result = ValidationRunner().validate_relation(
        ma.relation(df), [RelationRule(id="b", plan=broken)]
    )
    assert result.check_summaries["status"][0] == "error"
    assert "boom" in result.check_summaries["error"][0]
