"""Outcome-model semantics, cross-backend (spec §6.2/§6.3, §14 fixtures)."""
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.validation import RowRule, ScalarRule, ValidationRunner
from fixtures.capability_gating import xfail_divergence

_VAL01 = [
    pytest.param(b, marks=xfail_divergence("MA-VAL-01", backend=b)) for b in ALL_BACKENDS
]
_SCALARNULL = [
    pytest.param(
        b,
        marks=[xfail_divergence("IB-REL-06", backend=b), xfail_divergence("MA-VAL-02", backend=b)],
    )
    for b in ALL_BACKENDS
]


def _summary(result, check_id):
    frame = result.check_summaries.filter(
        result.check_summaries["check_id"] == check_id
    )
    return frame.row(0, named=True)


@pytest.mark.cross_backend
class TestOutcomeModel:
    @pytest.mark.parametrize("backend_name", _VAL01)
    def test_boolean_rule_nulls_become_unknown_nothing_dropped(
        self, backend_name, backend_factory
    ):
        df = backend_factory.create({"age": [30, -1, None]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df), [RowRule(id="age_ge_0", expr=ma.col("age").ge(0))]
        )
        row = _summary(result, "age_ge_0")
        assert (row["pass_count"], row["fail_count"], row["unknown_count"]) == (1, 1, 1), (
            f"[{backend_name}] {row}"
        )
        assert row["total_rows"] == 3
        assert row["status"] == "failed"
        outcomes = sorted(result.failure_cases["outcome"].to_list())
        assert outcomes == ["fail", "unknown"]

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_ternary_rule_three_way_counts(self, backend_name, backend_factory):
        df = backend_factory.create({"flag": [1, 2, None]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df), [RowRule(id="t_eq_1", expr=ma.col("flag").t_eq(1))]
        )
        row = _summary(result, "t_eq_1")
        assert (row["pass_count"], row["fail_count"], row["unknown_count"]) == (1, 1, 1), (
            f"[{backend_name}] {row}"
        )

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_terminal_ternary_is_boolean_context(self, backend_name, backend_factory):
        """The author's own terminal collapsed the three-way split; respect it."""
        df = backend_factory.create({"flag": [1, 2, None]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="term", expr=ma.col("flag").t_eq(1).t_is_true())],
        )
        row = _summary(result, "term")
        assert row["unknown_count"] == 0, f"[{backend_name}] {row}"
        assert (row["pass_count"], row["fail_count"]) == (1, 2)

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_mostly_denominator_counts_all_rows(self, backend_name, backend_factory):
        df = backend_factory.create({"age": [1, 2, None, 3]}, backend_name)
        checks = [
            RowRule(id="m75", expr=ma.col("age").ge(0), mostly=0.75),
            RowRule(id="m90", expr=ma.col("age").ge(0), mostly=0.9),
        ]
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert _summary(result, "m75")["status"] == "passed"   # 3/4 >= 0.75
        assert _summary(result, "m90")["status"] == "failed"   # 3/4 < 0.9

    @pytest.mark.parametrize("backend_name", _VAL01)
    def test_maybe_true_verdict_flip(self, backend_name, backend_factory):
        df = backend_factory.create({"age": [1, None]}, backend_name)
        checks = [
            RowRule(id="strict", expr=ma.col("age").ge(0)),
            RowRule(id="lenient", expr=ma.col("age").ge(0), booleanizer="t_maybe_true"),
        ]
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert _summary(result, "strict")["status"] == "failed"
        assert _summary(result, "lenient")["status"] == "passed"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_empty_input_passes_vacuously(self, backend_name, backend_factory):
        df = backend_factory.create({"age": []}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="r", expr=ma.col("age").ge(0), mostly=0.9)],
        )
        row = _summary(result, "r")
        assert row["status"] == "passed"
        assert row["total_rows"] == 0

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_scalar_rule_verdict_and_diagnostic(self, backend_name, backend_factory):
        df = backend_factory.create({"age": [10, 20, 30]}, backend_name)
        checks = [
            ScalarRule(id="mean_pos", expr=ma.col("age").mean().gt(0)),
            ScalarRule(id="big", expr=ma.len().gt(10)),
        ]
        result = ValidationRunner().validate_relation(ma.relation(df), checks)
        assert _summary(result, "mean_pos")["status"] == "passed"
        assert _summary(result, "big")["status"] == "failed"
        assert result.failure_cases.height == 0  # scalar rules emit no rows

    @pytest.mark.parametrize("backend_name", _SCALARNULL)
    def test_scalar_null_result_is_unknown_verdict(self, backend_name, backend_factory):
        df = backend_factory.create({"age": [None, None]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df), [ScalarRule(id="mean", expr=ma.col("age").mean().gt(0))]
        )
        assert _summary(result, "mean")["status"] == "failed"

    @pytest.mark.parametrize("backend_name", ALL_BACKENDS)
    def test_multi_field_rule_populates_row_struct(self, backend_name, backend_factory):
        """Spec §8: declared fields -> failing rows carry a `row` struct
        (cross-column failures self-describing without a source join)."""
        df = backend_factory.create({"start": [1, 5], "end": [2, 3]}, backend_name)
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="ordered", expr=ma.col("start").le(ma.col("end")),
                     fields=["start", "end"])],
        )
        assert result.failure_cases.height == 1
        assert result.failure_cases["row"][0] == {"start": 5, "end": 3}
        # multi-field: no single offending column/value
        assert result.failure_cases["column"][0] is None
        assert result.failure_cases["value"][0] is None
