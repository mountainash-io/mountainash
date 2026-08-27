"""Result model: schemas, builders, containers (spec §8)."""
import polars as pl

import mountainash as ma  # noqa: F401  (import parity with package layout)
from mountainash.validation.identity import RowIdentity
from mountainash.validation.result import (
    CheckSummary,
    DAGValidationResult,
    ValidationResult,
    combine_failure_frames,
    empty_failure_frame,
    failure_case_schema,
    interpolate_message,
    summaries_frame,
)


def test_summary_frame_columns_and_order():
    s = CheckSummary(check_id="r1", check_kind="row", status="passed",
                     pass_count=3, fail_count=0, unknown_count=0, total_rows=3)
    frame = summaries_frame([s])
    assert frame.columns == [
        "check_id", "check_kind", "status", "pass_count", "fail_count",
        "unknown_count", "total_rows", "mostly", "severity", "diagnostic", "error", "elapsed",
    ]
    assert frame["status"].to_list() == ["passed"]


def test_empty_summary_frame_is_typed():
    frame = summaries_frame([])
    assert frame.height == 0
    assert frame["pass_count"].dtype == pl.Int64


def test_empty_failure_frame_keyed():
    frame = empty_failure_frame(RowIdentity("keyed", ("id", "code")))
    assert frame.columns == [
        "check_id", "check_kind", "column", "outcome", "value", "message",
        "instance_path", "schema_path", "validator", "label_declarations",
        "id", "code", "row_number", "row",
    ]
    assert frame["row_number"].dtype == pl.Int64


def test_empty_failure_frame_none_tier_still_has_row_number():
    frame = empty_failure_frame(RowIdentity("none"))
    assert "row_number" in frame.columns  # always present, null outside row_number tier


def test_combine_failure_frames_diagonal():
    identity = RowIdentity("none")
    a = empty_failure_frame(identity)
    b = pl.DataFrame({
        "check_id": ["r1"], "check_kind": ["row"], "column": ["age"],
        "outcome": ["fail"], "value": ["-1"], "message": [None],
        "row_number": [None], "row": [None],
    })
    combined = combine_failure_frames([a, b], identity)
    assert combined.height == 1
    assert combined["check_id"].to_list() == ["r1"]


def test_combine_empty_list_yields_typed_empty(
):
    combined = combine_failure_frames([], RowIdentity("none"))
    assert combined.height == 0
    assert "outcome" in combined.columns


def test_interpolate_message():
    frame = pl.DataFrame({"age": [-1, -2], "value": ["-1", "-2"]})
    out = interpolate_message(frame, "age {age} is negative", ["age"])
    assert out["message"].to_list() == ["age -1 is negative", "age -2 is negative"]


def test_skipped_summary_and_passes_semantics():
    from mountainash.validation.result import passes_from_summaries

    # spec §8: skipped summaries carry check_kind=None (a never-materialised
    # ContextualRule has no classifiable kind)
    skipped = CheckSummary(check_id="tier_gated", check_kind=None, status="skipped",
                           diagnostic="not applicable: batch_tier not in {'C', 'P'}")
    passed = CheckSummary(check_id="r1", check_kind="row", status="passed")
    failed = CheckSummary(check_id="r2", check_kind="row", status="failed")
    errored = CheckSummary(check_id="r3", check_kind="row", status="error", error="boom")

    frame = summaries_frame([skipped, passed])
    assert frame["status"].to_list() == ["skipped", "passed"]
    assert frame["check_kind"][0] is None
    assert frame["diagnostic"][0] == "not applicable: batch_tier not in {'C', 'P'}"

    assert passes_from_summaries([passed, skipped]) is True   # skipped never blocks
    assert passes_from_summaries([passed, failed]) is False
    assert passes_from_summaries([passed, errored]) is False  # an error is a failure
    assert passes_from_summaries([]) is True


def test_severity_blocking_semantics():
    """spec §8 third amendment: error always blocks; failed blocks only at
    'blocking' severity; a failed warning stays status='failed' truthfully."""
    from mountainash.validation.result import is_blocking, passes_from_summaries

    failed_warning = CheckSummary(
        check_id="w1", check_kind="row", status="failed", severity="warning",
        pass_count=2, fail_count=1, unknown_count=0, total_rows=3,
    )
    errored_warning = CheckSummary(
        check_id="w2", check_kind="row", status="error", severity="warning", error="boom",
    )
    passed = CheckSummary(check_id="r1", check_kind="row", status="passed")

    assert is_blocking(failed_warning) is False
    assert is_blocking(errored_warning) is True  # error always blocks
    assert passes_from_summaries([passed, failed_warning]) is True
    assert passes_from_summaries([passed, errored_warning]) is False
    assert failed_warning.status == "failed"  # audit output stays truthful
    frame = summaries_frame([passed, failed_warning])
    assert frame["severity"].to_list() == ["blocking", "warning"]


def test_status_vocabulary_closed():
    import pytest

    with pytest.raises(ValueError):
        CheckSummary(check_id="r", check_kind="row", status="pased")  # typo must not pass silently
    with pytest.raises(ValueError):
        CheckSummary(check_id="r", check_kind="row", status="failed", severity="warn")


def test_runner_and_skipped_summaries_concat():
    """The Validator appends skipped summaries to the runner's frame (spec §9.4);
    the concat of a normal frame and a check_kind=None skipped frame must work."""
    ran = summaries_frame([
        CheckSummary(check_id="r1", check_kind="row", status="passed",
                     pass_count=3, fail_count=0, unknown_count=0, total_rows=3),
    ])
    skipped = summaries_frame([
        CheckSummary(check_id="gated", check_kind=None, status="skipped",
                     diagnostic="not applicable: context key 'tier' absent"),
    ])
    combined = pl.concat([ran, skipped])
    assert combined["status"].to_list() == ["passed", "skipped"]
    assert combined["check_kind"].to_list() == ["row", None]


def test_combine_heterogeneous_row_structs():
    """spec §8: different checks contribute different row-struct field sets;
    the combined frame has ONE union-struct row dtype (missing fields null)."""
    identity = RowIdentity("none")
    a = pl.DataFrame({
        "check_id": ["r1"], "check_kind": ["row"], "column": [None],
        "outcome": ["fail"], "value": [None], "message": [None],
        "row_number": pl.Series([None], dtype=pl.Int64),
        "row": [{"start": 5, "end": 3}],
    })
    b = pl.DataFrame({
        "check_id": ["r2"], "check_kind": ["row"], "column": [None],
        "outcome": ["fail"], "value": [None], "message": [None],
        "row_number": pl.Series([None], dtype=pl.Int64),
        "row": [{"amount": 12.5, "end": 9}],
    })
    combined = combine_failure_frames([a, b], identity)
    assert combined.height == 2
    struct_fields = {f.name for f in combined.schema["row"].fields}
    assert struct_fields == {"start", "end", "amount"}
    rows = combined["row"].to_list()
    assert rows[0]["start"] == 5 and rows[0]["amount"] is None
    assert rows[1]["amount"] == 12.5 and rows[1]["start"] is None


def test_validation_result_defaults():
    result = ValidationResult(passes=True, validator_name="v")
    assert result.datacontract_name is None
    assert result.context == {}
    assert result.check_summaries.height == 0
    assert result.failure_cases.height == 0
    assert result.identity == RowIdentity("none")
    assert result.processor is None


def test_dag_validation_result_shape():
    inner = ValidationResult(passes=True, validator_name="users")
    fk = ValidationResult(passes=True, validator_name="__fk__")
    dag_result = DAGValidationResult(passes=True, results={"users": inner}, fk_result=fk)
    assert dag_result.results["users"].passes


def test_private_materialized_source_is_not_public_result_state():
    """The processor handoff cannot leak into equality, repr, or diagnostics."""
    base = {
        "passes": True,
        "validator_name": "unit-d",
        "check_summaries": summaries_frame([]),
        "failure_cases": empty_failure_frame(RowIdentity("none")),
        "identity": RowIdentity("none"),
    }
    result = ValidationResult(**base, _materialized_source=pl.DataFrame({"id": [1]}))
    same = ValidationResult(**base, _materialized_source=pl.DataFrame({"id": [2]}))

    assert result == same
    assert "_materialized_source" not in repr(result)
    assert "_materialized_source" not in result.check_summaries.columns
    assert "_materialized_source" not in result.failure_cases.columns


def test_failure_schema_exposes_structured_validator_paths():
    """All failure outputs reserve deterministic fields for value diagnostics."""
    frame = empty_failure_frame(RowIdentity("none"))

    assert {"instance_path", "schema_path", "validator", "label_declarations"} <= set(
        frame.columns
    )
