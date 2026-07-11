"""Tests for ValidationResult and ValidationResultProcessor.

Fixtures use the unified failure-case schema (spec §8): check_id, check_kind,
column, outcome, value, message, *key_fields, row_number, row. See
tests/datacontracts/test_processor_compat.py for the authoritative
per-method compat matrix this migration mirrors.
"""
from __future__ import annotations

import pytest
import polars as pl
import mountainash as ma

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.datacontracts.field import Field
from mountainash.datacontracts.rule import Rule
from mountainash.datacontracts.registry import RuleRegistry
from mountainash.datacontracts.validator import Validator
from mountainash.datacontracts.result import ValidationResult
from mountainash.datacontracts.result_processor import ValidationResultProcessor
from mountainash.validation.identity import RowIdentity
from mountainash.validation.errors import IdentityRequiredError
from mountainash.validation.result import empty_failure_frame


class OrderContract(BaseDataContract):
    order_id: int = Field(unique=True)
    amount: float = Field(ge=0)
    status: str = Field(isin=["open", "closed", "pending"])


@pytest.fixture
def sample_failure_cases() -> pl.DataFrame:
    """Failure cases in the unified schema (identity tier: none)."""
    return pl.DataFrame({
        "check_id": ["age__ge", "name__pattern", "batch_rule"],
        "check_kind": ["row", "row", "row"],
        "column": ["age", "name", None],
        "outcome": ["fail", "fail", "fail"],
        "value": ["0", "bad_val", "missing"],
        "message": [None, None, None],
        "row_number": pl.Series([0, 2, 1], dtype=pl.Int64),
        "row": pl.Series([None, None, None], dtype=pl.Null),
    })


@pytest.fixture
def empty_failure_cases() -> pl.DataFrame:
    return empty_failure_frame(RowIdentity("none"))


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
        assert age_failures["check_id"][0] == "age__ge"

    def test_failure_cases_for_rule(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        rule_failures = proc.failure_cases_for_rule("batch_rule")
        assert len(rule_failures) == 1

    def test_failure_count_by_column(self, sample_failure_cases):
        # spec §8: check_kind replaces schema_context — failure_count_by_column
        # now groups every non-null `column` (not only a "Column"-context
        # subset, which no longer exists as a concept).
        proc = ValidationResultProcessor(sample_failure_cases)
        by_col = proc.failure_count_by_column()
        assert isinstance(by_col, pl.DataFrame)
        counts = dict(zip(by_col["column"].to_list(), by_col["count"].to_list()))
        assert counts == {"age": 1, "name": 1}

    def test_failure_count_by_rule(self, sample_failure_cases):
        # spec §8: failure_count_by_rule groups by check_id across ALL check
        # kinds (row + relation) — the legacy Pandera implementation scoped
        # this to DataFrameSchema-level ("VR01") checks only; that scope
        # split no longer exists, so this now covers every check_id.
        proc = ValidationResultProcessor(sample_failure_cases)
        by_rule = proc.failure_count_by_rule()
        assert isinstance(by_rule, pl.DataFrame)
        counts = dict(zip(by_rule["check_id"].to_list(), by_rule["count"].to_list()))
        assert counts == {"age__ge": 1, "name__pattern": 1, "batch_rule": 1}

    def test_passed_for_column_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_column("score") is True

    def test_passed_for_column_false(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_column("age") is False

    def test_passed_for_rule_true(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_rule("nonexistent_rule") is True

    def test_passed_for_rule_false(self, sample_failure_cases):
        proc = ValidationResultProcessor(sample_failure_cases)
        assert proc.passed_for_rule("batch_rule") is False


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


@pytest.fixture
def keyed_failure_cases() -> pl.DataFrame:
    """Unified failure cases carrying a physical `age` key column, so
    natural_key=["age"] is a real keyed identity (spec §7) — not just a
    label. Mirrors test_processor_compat.py::_keyed_failure_cases shape."""
    return pl.DataFrame({
        "check_id": ["age__ge", "name__pattern"],
        "check_kind": ["row", "row"],
        "column": ["age", "name"],
        "outcome": ["fail", "fail"],
        "value": ["0", "bad_val"],
        "message": [None, None],
        "age": [10, 20],
        "row_number": pl.Series([None, None], dtype=pl.Int64),
        "row": pl.Series([None, None], dtype=pl.Null),
    })


class TestEnrichedFailureCases:

    def test_enriched_columns_without_natural_key(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, validator_name="test_validator",
        )
        enriched = proc.enriched_failure_cases()
        # check_kind REPLACES schema_context (spec §8 documented breaking change)
        assert set(enriched.columns) == {
            "validator_name", "rule_id", "check_kind",
            "column_name", "row_index", "value_str",
        }

    def test_enriched_columns_with_natural_key(self, keyed_failure_cases):
        proc = ValidationResultProcessor(
            keyed_failure_cases,
            validator_name="test_validator",
            natural_key=["age"],
        )
        enriched = proc.enriched_failure_cases()
        assert "column_is_natural_key" in enriched.columns
        assert "age" in enriched.columns  # keyed identity's key field is appended

    def test_enriched_values(self, sample_failure_cases):
        proc = ValidationResultProcessor(
            sample_failure_cases, validator_name="v1",
        )
        enriched = proc.enriched_failure_cases()
        assert enriched["validator_name"].to_list() == ["v1", "v1", "v1"]
        assert enriched["rule_id"].to_list() == [
            "age__ge", "name__pattern", "batch_rule",
        ]
        # batch_rule is table-level: column is null (spec §8) — the legacy
        # Pandera contract-name-as-column ("TestContract") placeholder is gone.
        assert enriched["column_name"].to_list() == ["age", "name", None]
        assert enriched["row_index"].to_list() == [0, 2, 1]
        assert enriched["value_str"].to_list() == ["0", "bad_val", "missing"]

    def test_enriched_natural_key_flag(self, keyed_failure_cases):
        proc = ValidationResultProcessor(
            keyed_failure_cases,
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
    """Row-level failures across validators/columns/rules, plus one
    relation-level failure with no single-row attribution — row_number is
    null OUTSIDE the row_number tier (spec §8), not a malformed-rule
    artifact (malformed rules no longer emit failure rows at all)."""
    return pl.DataFrame({
        "check_id": ["age__ge", "name__pattern", "name__pattern", "age__ge", "table_rel_check"],
        "check_kind": ["row", "row", "row", "row", "relation"],
        "column": ["age", "name", "name", "age", None],
        "outcome": ["fail", "fail", "fail", "fail", "fail"],
        "value": ["0", "bad", "worse", "0", None],
        "message": [None, None, None, None, None],
        "row_number": pl.Series([0, 1, 2, 3, None], dtype=pl.Int64),
        "row": pl.Series([None, None, None, None, None], dtype=pl.Null),
    })


class TestProfilingAggregations:
    """Profiled counts are identity-gated (keyed or row_number); the
    Pandera-era implicit positional `index` maps to the row_number tier."""

    def test_profiled_failure_count(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1", identity=RowIdentity("row_number"),
        )
        result = proc.profiled_failure_count()
        assert "validator_name" in result.columns
        assert "unique_row_count" in result.columns
        row = result.filter(pl.col("validator_name") == "v1")
        assert row["unique_row_count"][0] == 4  # rows 0,1,2,3 — null row_number excluded

    def test_profiled_failure_count_by_column(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1", identity=RowIdentity("row_number"),
        )
        result = proc.profiled_failure_count_by_column()
        age_row = result.filter(pl.col("column_name") == "age")
        assert age_row["unique_row_count"][0] == 2  # rows 0, 3
        name_row = result.filter(pl.col("column_name") == "name")
        assert name_row["unique_row_count"][0] == 2  # rows 1, 2

    def test_profiled_failure_count_by_value(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1", identity=RowIdentity("row_number"),
        )
        result = proc.profiled_failure_count_by_value()
        assert "value_str" in result.columns
        assert "unique_row_count" in result.columns
        assert len(result) >= 3

    def test_profiled_failure_count_by_rule(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1", identity=RowIdentity("row_number"),
        )
        result = proc.profiled_failure_count_by_rule()
        ge_row = result.filter(pl.col("rule_id") == "age__ge")
        assert ge_row["unique_row_count"][0] == 2  # rows 0, 3

    def test_profiled_excludes_null_row_index(self, multi_failure_cases):
        proc = ValidationResultProcessor(
            multi_failure_cases, validator_name="v1", identity=RowIdentity("row_number"),
        )
        result = proc.profiled_failure_count()
        total = result["unique_row_count"].sum()
        assert total == 4  # the relation-level, null-row_number failure is excluded


def _check_summaries(*, errored: bool) -> pl.DataFrame:
    if not errored:
        return pl.DataFrame({
            "check_id": ["age__ge"],
            "check_kind": ["row"],
            "status": ["passed"],
            "pass_count": [4], "fail_count": [0],
            "unknown_count": [0], "total_rows": [4],
            "mostly": [None], "severity": ["blocking"],
            "diagnostic": [None], "error": [None], "elapsed": [0.001],
        })
    return pl.DataFrame({
        "check_id": ["age__ge", "broken_rule"],
        "check_kind": ["row", "row"],
        "status": ["passed", "error"],
        "pass_count": [4, None], "fail_count": [0, None],
        "unknown_count": [0, None], "total_rows": [4, None],
        "mostly": [None, None], "severity": ["blocking", "blocking"],
        "diagnostic": [None, None], "error": [None, "ColumnNotFoundError: ghost"],
        "elapsed": [0.001, 0.001],
    })


class TestMalformedRuleDetection:
    """spec §8: malformed_rules() is re-expressed over
    CheckSummary(status=="error") — a rule error no longer surfaces as a
    null-index failure-case row (that mechanism does not exist any more:
    an errored check emits zero failure rows)."""

    def test_malformed_rules_found(self):
        proc = ValidationResultProcessor(
            empty_failure_frame(RowIdentity("none")),
            check_summaries=_check_summaries(errored=True),
            validator_name="v1",
        )
        malformed = proc.malformed_rules()
        assert malformed["rule_id"].to_list() == ["broken_rule"]

    def test_malformed_rules_none(self):
        proc = ValidationResultProcessor(
            empty_failure_frame(RowIdentity("none")),
            check_summaries=_check_summaries(errored=False),
            validator_name="v1",
        )
        malformed = proc.malformed_rules()
        assert len(malformed) == 0

    def test_rules_well_formed_false(self):
        proc = ValidationResultProcessor(
            empty_failure_frame(RowIdentity("none")),
            check_summaries=_check_summaries(errored=True),
            validator_name="v1",
        )
        assert proc.rules_well_formed() is False

    def test_rules_well_formed_true(self):
        proc = ValidationResultProcessor(
            empty_failure_frame(RowIdentity("none")),
            check_summaries=_check_summaries(errored=False),
            validator_name="v1",
        )
        assert proc.rules_well_formed() is True


@pytest.fixture
def source_data() -> pl.DataFrame:
    """Source data joined back via a natural key (`name`) — pivot/interpolate
    are keyed-only now (spec §7/§8): row_number is a diagnostic ordinal and
    never a join key, so the legacy positional-index join has no analogue."""
    return pl.DataFrame({
        "name": ["alice", "bad_val", "worse", "dave"],
        "age": [10, 20, 30, 40],
        "score": [90, 80, 70, 60],
    })


@pytest.fixture
def pivot_failure_cases() -> pl.DataFrame:
    """Failure cases carrying the `name` key field so they join back to
    source_data (keyed identity)."""
    return pl.DataFrame({
        "check_id": ["age__ge", "name__pattern"],
        "check_kind": ["row", "row"],
        "column": ["age", "name"],
        "outcome": ["fail", "fail"],
        "value": ["10", "bad_val"],
        "message": [None, None],
        "name": ["alice", "bad_val"],
        "row_number": pl.Series([None, None], dtype=pl.Int64),
        "row": pl.Series([None, None], dtype=pl.Null),
    })


class TestPivotReports:

    def test_pivot_all_fields(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            identity=RowIdentity("keyed", ("name",)),
            validator_name="v1",
        )
        result = proc.pivot_all_fields()
        assert len(result) == 2
        assert "age" in result.columns
        assert "name" in result.columns
        assert "score" in result.columns
        assert "rule_id" in result.columns
        # NOTE: row_index is no longer part of pivot_all_fields' output (spec
        # §8 compat matrix): the join is on key fields, not a positional
        # ordinal, so there is nothing to carry a row_index for.

    def test_pivot_all_fields_with_override(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases, identity=RowIdentity("keyed", ("name",)), validator_name="v1",
        )
        result = proc.pivot_all_fields(source_data=source_data)
        assert len(result) == 2

    def test_pivot_all_fields_no_source_raises(self, pivot_failure_cases):
        proc = ValidationResultProcessor(
            pivot_failure_cases, identity=RowIdentity("keyed", ("name",)), validator_name="v1",
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

    def test_pivot_key_fields_requires_keyed_identity(self, pivot_failure_cases, source_data):
        # spec §7: keyed-only capabilities raise IdentityRequiredError (not
        # ValueError) when identity is not keyed — the legacy natural_key=None
        # sentinel check is replaced by identity-tier gating.
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            validator_name="v1",
        )
        with pytest.raises(IdentityRequiredError):
            proc.pivot_key_fields()

    def test_pivot_excludes_unresolvable_key(self, source_data):
        """spec §8: a rule error no longer produces a null-index failure row
        (malformed_rules() reads CheckSummary(status="error") instead) — so
        the legacy "null-index row excluded from pivot" scenario has no
        direct analogue. The equivalent native guarantee that survives is
        the SAME underlying mechanism (inner join on key fields): a failure
        case whose key value has no matching source row is dropped from the
        pivot. Exercised here via an unmatched key rather than a null index."""
        fc = pl.DataFrame({
            "check_id": ["ghost_rule"],
            "check_kind": ["row"],
            "column": [None],
            "outcome": ["fail"],
            "value": [None],
            "message": [None],
            "name": ["nobody"],
            "row_number": pl.Series([None], dtype=pl.Int64),
            "row": pl.Series([None], dtype=pl.Null),
        })
        proc = ValidationResultProcessor(
            fc, source_data=source_data,
            identity=RowIdentity("keyed", ("name",)), validator_name="v1",
        )
        result = proc.pivot_all_fields()
        assert len(result) == 0


class TestInterpolateMessages:

    def test_interpolate_from_dict(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            identity=RowIdentity("keyed", ("name",)),
            validator_name="v1",
        )
        metadata = {
            "age__ge": {
                "error_message": "age {age} must be >= 18",
                "fields": ["age"],
            },
            "name__pattern": {
                "error_message": "name {name} is invalid",
                "fields": ["name"],
            },
        }
        result = proc.interpolate_messages(rule_metadata=metadata)
        assert "error_message_template" in result.columns
        assert "error_message" in result.columns
        msgs = result.sort("rule_id")["error_message"].to_list()
        assert msgs[0] == "age 10 must be >= 18"
        assert msgs[1] == "name bad_val is invalid"

    def test_interpolate_from_dataframe(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            identity=RowIdentity("keyed", ("name",)),
            validator_name="v1",
        )
        metadata_df = pl.DataFrame({
            "rule_id": ["age__ge", "name__pattern"],
            "error_message": ["age {age} must be >= 18", "name {name} is invalid"],
            "fields": [["age"], ["name"]],
        })
        result = proc.interpolate_messages(rule_metadata=metadata_df)
        assert len(result) == 2

    def test_interpolate_multi_field(self, source_data):
        fc = pl.DataFrame({
            "check_id": ["batch_rule"],
            "check_kind": ["row"],
            "column": [None],
            "outcome": ["fail"],
            "value": [None],
            "message": [None],
            "name": ["alice"],
            "row_number": pl.Series([None], dtype=pl.Int64),
            "row": pl.Series([None], dtype=pl.Null),
        })
        proc = ValidationResultProcessor(
            fc, source_data=source_data,
            identity=RowIdentity("keyed", ("name",)), validator_name="v1",
        )
        metadata = {
            "batch_rule": {
                "error_message": "{name} (age {age}) failed",
                "fields": ["name", "age"],
            },
        }
        result = proc.interpolate_messages(rule_metadata=metadata)
        assert result["error_message"][0] == "alice (age 10) failed"

    def test_interpolate_no_source_raises(self, pivot_failure_cases):
        proc = ValidationResultProcessor(
            pivot_failure_cases, identity=RowIdentity("keyed", ("name",)), validator_name="v1",
        )
        with pytest.raises(ValueError, match="source_data"):
            proc.interpolate_messages(rule_metadata={"age__ge": {"error_message": "x", "fields": []}})

    def test_interpolate_duplicate_rule_id_raises(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            identity=RowIdentity("keyed", ("name",)),
            validator_name="v1",
        )
        dup_metadata = pl.DataFrame({
            "rule_id": ["age__ge", "age__ge"],
            "error_message": ["msg1", "msg2"],
            "fields": [["age"], ["age"]],
        })
        with pytest.raises(ValueError, match="duplicate"):
            proc.interpolate_messages(rule_metadata=dup_metadata)

    def test_interpolate_unmatched_rules_excluded(self, pivot_failure_cases, source_data):
        proc = ValidationResultProcessor(
            pivot_failure_cases,
            source_data=source_data,
            identity=RowIdentity("keyed", ("name",)),
            validator_name="v1",
        )
        metadata = {
            "age__ge": {
                "error_message": "age {age} must be >= 18",
                "fields": ["age"],
            },
        }
        result = proc.interpolate_messages(rule_metadata=metadata)
        assert len(result) == 1  # only age__ge matched


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

        # spec §7: declared keyed identity (natural_key=["order_id"]) is now
        # validated against the data — a duplicate key tuple raises
        # IdentityInvalidError unless allow_imperfect_key=True. The intent
        # here is to exercise the order_id__unique CONTRACT check's failure
        # reporting (not the identity precondition), so opt in explicitly.
        result = validator.validate(df, allow_imperfect_key=True)
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
