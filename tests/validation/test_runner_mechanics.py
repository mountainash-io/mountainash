"""Runner orchestration mechanics: isolation, fail_fast, sampling, identity, timing.

Polars-only by design: orchestration logic is backend-independent; expression
semantics are covered cross-backend in test_runner_semantics.py.
"""
import polars as pl
import pytest

import mountainash as ma
from mountainash.validation import (
    RowIdentity,
    RowRule,
    ScalarRule,
    ValidationRunner,
)
from mountainash.validation.errors import IdentityInvalidError, UnknownCheckTypeError


def _df():
    return pl.DataFrame({"id": [1, 2, 3], "age": [30, -1, None]})


class TestIsolation:
    def test_erroring_check_isolated(self):
        checks = [
            RowRule(id="broken", expr=ma.col("missing_column").ge(0)),
            RowRule(id="ok", expr=ma.col("age").ge(-100)),
        ]
        result = ValidationRunner().validate_relation(ma.relation(_df()), checks)
        summaries = {r["check_id"]: r for r in result.check_summaries.iter_rows(named=True)}
        assert summaries["broken"]["status"] == "error"
        assert summaries["broken"]["error"]  # captured repr, not raised
        # "ok" runs cleanly (proves isolation from "broken"'s error), but its
        # own status is "failed": age=[30, -1, None] against ge(-100) yields
        # pass=2, fail=0, unknown=1 (the None row) with no `mostly` declared,
        # and the default t_is_true booleanizer only counts "pass" as passing
        # (spec §6.2) — an unknown row keeps a strict, mostly-less check from
        # reaching "passed", exactly as asserted for the structurally
        # identical "strict" case in test_maybe_true_verdict_flip below.
        assert summaries["ok"]["status"] == "failed"
        assert result.passes is False

    def test_elapsed_always_recorded(self):
        result = ValidationRunner().validate_relation(
            ma.relation(_df()), [RowRule(id="r", expr=ma.col("age").ge(0))]
        )
        assert result.check_summaries["elapsed"][0] >= 0.0


class TestFailFast:
    def test_stops_after_first_failure(self):
        checks = [
            RowRule(id="fails", expr=ma.col("age").ge(0)),
            RowRule(id="never_runs", expr=ma.col("age").ge(-100)),
        ]
        result = ValidationRunner().validate_relation(
            ma.relation(_df()), checks, fail_fast=True
        )
        assert result.check_summaries.height == 1
        assert result.passes is False

    def test_error_also_stops_under_fail_fast(self):
        checks = [
            RowRule(id="broken", expr=ma.col("missing").ge(0)),
            RowRule(id="never_runs", expr=ma.col("age").ge(-100)),
        ]
        result = ValidationRunner().validate_relation(
            ma.relation(_df()), checks, fail_fast=True
        )
        assert result.check_summaries.height == 1
        assert result.check_summaries["status"][0] == "error"


class TestFailureSample:
    def test_caps_failure_rows_per_check(self):
        df = pl.DataFrame({"age": [-1, -2, -3, -4]})
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="r", expr=ma.col("age").ge(0))],
            failure_sample=2,
        )
        assert result.failure_cases.height == 2
        assert result.check_summaries["fail_count"][0] == 4  # counts are exact; sampling caps rows


class TestIdentityIntegration:
    def test_keyed_failure_cases_carry_key_fields(self):
        result = ValidationRunner().validate_relation(
            ma.relation(_df()),
            [RowRule(id="r", expr=ma.col("age").ge(0), fields=["age"])],
            identity=RowIdentity("keyed", ("id",)),
        )
        assert "id" in result.failure_cases.columns
        assert set(result.failure_cases["id"].to_list()) == {2, 3}
        assert result.failure_cases["column"].to_list() == ["age", "age"]
        assert "-1" in result.failure_cases["value"].to_list()

    def test_keyed_message_interpolation(self):
        result = ValidationRunner().validate_relation(
            ma.relation(pl.DataFrame({"id": [1], "age": [-5]})),
            [RowRule(id="r", expr=ma.col("age").ge(0), fields=["age"],
                     error_message="age {age} is negative")],
            identity=RowIdentity("keyed", ("id",)),
        )
        assert result.failure_cases["message"].to_list() == ["age -5 is negative"]

    def test_invalid_keyed_identity_raises_before_checks(self):
        df = pl.DataFrame({"id": [1, 1], "age": [1, 2]})
        with pytest.raises(IdentityInvalidError):
            ValidationRunner().validate_relation(
                ma.relation(df),
                [RowRule(id="r", expr=ma.col("age").ge(0))],
                identity=RowIdentity("keyed", ("id",)),
            )

    def test_allow_imperfect_key_records_diagnostics(self):
        df = pl.DataFrame({"id": [1, 1], "age": [-1, 2]})
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="r", expr=ma.col("age").ge(0))],
            identity=RowIdentity("keyed", ("id",)),
            allow_imperfect_key=True,
        )
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1

    def test_row_number_ordinal_assigned_before_rules(self):
        df = pl.DataFrame({"age": [30, -1, -2]})
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="r", expr=ma.col("age").ge(0))],
            identity=RowIdentity("row_number"),
        )
        assert sorted(result.failure_cases["row_number"].to_list()) == [1, 2]

    def test_none_tier_row_number_column_present_but_null(self):
        result = ValidationRunner().validate_relation(
            ma.relation(_df()), [RowRule(id="r", expr=ma.col("age").ge(0))]
        )
        assert "row_number" in result.failure_cases.columns
        assert result.failure_cases["row_number"].null_count() == result.failure_cases.height


class TestClosedByDefault:
    def test_unknown_check_type_raises(self):
        class Mystery:
            id = "m"

        with pytest.raises(UnknownCheckTypeError):
            ValidationRunner().validate_relation(ma.relation(_df()), [Mystery()])

    def test_mostly_passed_check_still_emits_failure_cases(self):
        df = pl.DataFrame({"age": [1, 2, 3, -1]})
        result = ValidationRunner().validate_relation(
            ma.relation(df),
            [RowRule(id="r", expr=ma.col("age").ge(0), mostly=0.7)],
        )
        assert result.check_summaries["status"][0] == "passed"  # 3/4 >= 0.7
        assert result.failure_cases.height == 1                  # failing row still reported


class TestBackendOverride:
    """Guards the backend= path: _compile_and_execute_with_visitor returns
    (result, visitor) — a mis-handled tuple corrupts every override run."""

    def test_explicit_polars_backend_matches_default(self):
        checks = [RowRule(id="r", expr=ma.col("age").ge(0))]
        default = ValidationRunner().validate_relation(ma.relation(_df()), checks)
        forced = ValidationRunner().validate_relation(
            ma.relation(_df()), checks, backend="polars"
        )
        assert forced.passes == default.passes
        assert forced.check_summaries["fail_count"][0] == default.check_summaries["fail_count"][0]

    def test_non_polars_backend_override(self):
        # Narwhals wraps the Polars source: exercises a genuine re-route
        # through a different relation system, not a no-op.
        result = ValidationRunner().validate_relation(
            ma.relation(_df()),
            [RowRule(id="r", expr=ma.col("age").ge(0))],
            backend="narwhals",
        )
        assert result.passes is False
        assert result.check_summaries["fail_count"][0] == 1  # -1 fails; None is unknown


class TestStructuredFailurePolicyMechanics:
    """Task 7 step 2/7: a `coerce`-action structured field with malformed
    JSON reports through the check's own status -- it never degrades the
    run to an unguarded `status="error"` crash (spec 12.2/12.3)."""

    def test_coerce_malformed_json_fails_type_format_not_error(self):
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.validation.checks import ValueRule, ValueValidatorKey

        df = pl.DataFrame({"payload": ['{"a": 1}', "{broken"]})
        spec = TypeSpec(
            fields_match="open", fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)]
        )
        rel = ma.relation(df).conform(spec, contract={"data_type": "coerce"})
        result = ValidationRunner().validate_relation(
            rel,
            checks=[
                ValueRule(
                    id="payload_shape", fields=["payload"],
                    validator=ValueValidatorKey.TYPE_FORMAT, options={"type": "object"},
                )
            ],
        )
        summary = result.check_summaries.filter(pl.col("check_id") == "payload_shape")
        assert summary["status"].item() == "failed"
        assert summary["fail_count"].item() == 1
        assert summary["pass_count"].item() == 1
