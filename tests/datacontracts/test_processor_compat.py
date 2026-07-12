"""ValidationResultProcessor compatibility matrix — pinned BEFORE migration.

Input schema (unified failure cases, spec §8):
    check_id, check_kind, column, outcome, value, message,
    *key_fields (keyed tier), row_number (always present; null outside the
    row_number tier), row (struct; relation/FK checks AND row rules with
    declared fields — multi-field row rules have null column/value and the
    declared fields' values in the struct).

Check-summary statuses include "skipped" (context-excluded rules, spec §9.6):
malformed_rules()/rules_well_formed() consider status=="error" only — skipped
is applicability, not malformation.

Per-method matrix (identity tiers: keyed / row_number / none):

| Method                        | Identity   | Consumes                  | Produces / change vs Pandera era                              |
|-------------------------------|------------|---------------------------|---------------------------------------------------------------|
| failure_cases()               | any        | raw frame                 | raw unified frame (was Pandera 5-column frame)                |
| failure_cases_for_column(c)   | any        | column                    | filter column == c (was schema_context=="Column" AND column)  |
| failure_cases_for_rule(id)    | any        | check_id                  | filter check_id == id (was schema_context=="DataFrameSchema") |
| failure_count()               | any        | —                         | int, unchanged                                                |
| failure_count_by_column()     | any        | column                    | group non-null column -> count                                |
| failure_count_by_rule()       | any        | check_id                  | group check_id -> count (output col renamed check -> check_id)|
| enriched_failure_cases()      | any        | full frame                | validator_name, rule_id (<-check_id), check_kind (REPLACES    |
|                               |            |                           | schema_context — documented breaking change), column_name     |
|                               |            |                           | (<-column), row_index (<-row_number, gate on NULLNESS not     |
|                               |            |                           | absence), value_str (<-value), + key fields, +                |
|                               |            |                           | column_is_natural_key when keyed                              |
| profiled_failure_count[_by_*] | keyed or   | identity cols             | unique failing rows counted over key fields (keyed) or        |
|                               | row_number |                           | row_index (row_number); none -> IdentityRequiredError         |
| malformed_rules()             | any        | check_summaries           | re-expressed over CheckSummary(status=="error") — rule errors |
|                               |            |                           | no longer appear as null-index failure rows                   |
| rules_well_formed()           | any        | ^                         | bool, unchanged semantics                                     |
| pivot_all_fields(source)      | keyed ONLY | key fields + source       | join on key fields (row_number is a diagnostic ordinal, never |
|                               |            |                           | a join key -> IdentityRequiredError otherwise)                |
| pivot_key_fields(source=None) | keyed ONLY | key fields                | rule_id + key values from failure cases; source now optional; |
|                               |            |                           | ValueError -> IdentityRequiredError                           |
| interpolate_messages(meta, s) | keyed ONLY | key fields + source       | join on key fields (was positional row_index)                 |
| passed()/passed_for_rule()    | any        | check_summaries when      | re-expressed over status+severity (is_blocking semantics —    |
|                               |            | supplied, else frame      | error always blocks, failed blocks only at blocking severity; |
|                               |            |                           | scalar/errored checks fail with NO failure rows; row-empti-   |
|                               |            |                           | ness is NOT the verdict); frame fallback only when            |
|                               |            |                           | constructed without summaries                                 |
| passed_for_column(c)          | any        | frame                     | failure-row-based by nature (column verdicts only exist       |
|                               |            |                           | through failure rows); documented as such                     |

Constructor: (failure_cases, *, source_data=None, natural_key=None,
identity=None, check_summaries=None, validator_name=None). `natural_key`
(back-compat) maps to keyed identity when `identity` is not given.
"""
import polars as pl
import pytest

from mountainash.validation.identity import RowIdentity
from mountainash.validation.errors import IdentityRequiredError
from mountainash.datacontracts.result_processor import ValidationResultProcessor


def _keyed_failure_cases() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "check_id": ["age__ge", "age__ge", "email__pattern", "batch_rule"],
            "check_kind": ["row", "row", "row", "row"],
            "column": ["age", "age", "email", None],
            "outcome": ["fail", "unknown", "fail", "fail"],
            "value": ["-1", None, "bad@", None],
            "message": [None, None, None, None],
            "id": [2, 3, 1, 2],
            "row_number": pl.Series([None, None, None, None], dtype=pl.Int64),
            "row": pl.Series([None, None, None, None], dtype=pl.Null),
        }
    )


def _source() -> pl.DataFrame:
    return pl.DataFrame(
        {"id": [1, 2, 3], "age": [30, -1, None], "email": ["bad@", "a@b.c", "c@d.e"]}
    )


def _keyed_processor(**overrides):
    kwargs = dict(
        source_data=_source(),
        identity=RowIdentity("keyed", ("id",)),
        validator_name="users",
    )
    kwargs.update(overrides)
    return ValidationResultProcessor(_keyed_failure_cases(), **kwargs)


class TestFilters:
    def test_failure_cases_for_column(self):
        out = _keyed_processor().failure_cases_for_column("age")
        assert out.height == 2
        assert set(out["check_id"].to_list()) == {"age__ge"}

    def test_failure_cases_for_rule(self):
        out = _keyed_processor().failure_cases_for_rule("batch_rule")
        assert out.height == 1

    def test_failure_count_by_column_ignores_null_column(self):
        out = _keyed_processor().failure_count_by_column()
        assert dict(zip(out["column"].to_list(), out["count"].to_list())) == {
            "age": 2,
            "email": 1,
        }

    def test_failure_count_by_rule(self):
        out = _keyed_processor().failure_count_by_rule()
        assert dict(zip(out["check_id"].to_list(), out["count"].to_list()))["age__ge"] == 2


class TestEnriched:
    def test_enriched_columns(self):
        out = _keyed_processor().enriched_failure_cases()
        for column in (
            "validator_name", "rule_id", "check_kind", "column_name",
            "row_index", "value_str", "id", "column_is_natural_key",
        ):
            assert column in out.columns, column
        assert "schema_context" not in out.columns  # Pandera-ism removed
        assert out["validator_name"].to_list() == ["users"] * 4
        # row_index is present-but-null outside the row_number tier
        assert out["row_index"].null_count() == 4

    def test_enriched_natural_key_flag(self):
        out = _keyed_processor(natural_key=["id"], identity=None).enriched_failure_cases()
        assert out["column_is_natural_key"].any() is False  # no failing column is the key


class TestProfiledGates:
    def test_profiled_counts_unique_rows_by_key(self):
        out = _keyed_processor().profiled_failure_count()
        # failing key ids: {2, 3, 1} -> 3 unique rows
        assert out["unique_row_count"].to_list() == [3]

    def test_profiled_by_column(self):
        out = _keyed_processor().profiled_failure_count_by_column()
        by_col = dict(zip(out["column_name"].to_list(), out["unique_row_count"].to_list()))
        assert by_col["age"] == 2

    def test_profiled_requires_identity(self):
        processor = ValidationResultProcessor(
            _keyed_failure_cases().drop("id"), identity=RowIdentity("none")
        )
        with pytest.raises(IdentityRequiredError):
            processor.profiled_failure_count()


class TestMalformedRules:
    def test_malformed_from_check_summaries(self):
        summaries = pl.DataFrame(
            {
                "check_id": ["ok_rule", "broken_rule"],
                "check_kind": ["row", "row"],
                "status": ["passed", "error"],
                "pass_count": [1, None], "fail_count": [0, None],
                "unknown_count": [0, None], "total_rows": [1, None],
                "mostly": [None, None], "severity": ["blocking", "blocking"],
                "diagnostic": [None, None],
                "error": [None, "ColumnNotFoundError: ghost"],
                "elapsed": [0.001, 0.001],
            }
        )
        processor = _keyed_processor(check_summaries=summaries)
        malformed = processor.malformed_rules()
        assert malformed["rule_id"].to_list() == ["broken_rule"]
        assert processor.rules_well_formed() is False


class TestKeyedOnlyGates:
    def test_pivot_all_fields_joins_on_key(self):
        out = _keyed_processor().pivot_all_fields()
        assert "age" in out.columns  # source columns joined in
        assert set(out["id"].to_list()) <= {1, 2, 3}

    def test_pivot_key_fields_from_failure_cases(self):
        out = _keyed_processor().pivot_key_fields()
        assert "id" in out.columns
        assert "rule_id" in out.columns

    def test_pivots_require_keyed_identity(self):
        processor = ValidationResultProcessor(
            _keyed_failure_cases().drop("id"), identity=RowIdentity("row_number")
        )
        with pytest.raises(IdentityRequiredError):
            processor.pivot_all_fields()
        with pytest.raises(IdentityRequiredError):
            processor.pivot_key_fields()

    def test_interpolate_messages_keyed(self):
        meta = {"age__ge": {"error_message": "age {age} negative", "fields": ["age"]}}
        out = _keyed_processor().interpolate_messages(meta)
        interpolated = out.filter(pl.col("rule_id") == "age__ge")["error_message"].to_list()
        assert "age -1 negative" in interpolated


class TestVerdictHelpers:
    def test_passed_family(self):
        processor = _keyed_processor()
        assert processor.passed() is False
        assert processor.passed_for_column("age") is False
        assert processor.passed_for_rule("nonexistent") is True
        empty = ValidationResultProcessor(
            _keyed_failure_cases().head(0), identity=RowIdentity("none")
        )
        assert empty.passed() is True

    def test_passed_uses_summaries_not_row_emptiness(self):
        """spec §8: the processor is not a second owner of pass semantics.
        A failed scalar rule (or errored rule) emits NO failure rows yet
        fails the run — passed() must say so when summaries are supplied."""
        summaries = pl.DataFrame(
            {
                "check_id": ["row_ok", "mean_bound"],
                "check_kind": ["row", "scalar"],
                "status": ["passed", "failed"],
                "pass_count": [3, None], "fail_count": [0, None],
                "unknown_count": [0, None], "total_rows": [3, None],
                "mostly": [None, None], "severity": ["blocking", "blocking"],
                "diagnostic": [None, "-4.2"],
                "error": [None, None],
                "elapsed": [0.001, 0.001],
            }
        )
        processor = ValidationResultProcessor(
            _keyed_failure_cases().head(0),           # zero failure rows...
            identity=RowIdentity("keyed", ("id",)),
            check_summaries=summaries,                # ...but a failed scalar check
        )
        assert processor.passed() is False
        assert processor.passed_for_rule("mean_bound") is False
        assert processor.passed_for_rule("row_ok") is True
