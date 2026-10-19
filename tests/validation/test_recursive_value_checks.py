"""Logical parser, canonical equality, and rendering contracts."""

from decimal import Decimal

import pytest

from mountainash.validation.value import (
    INVALID_VALUE,
    DurationValue,
    PartialDateValue,
    canonical_value_key,
    parse_duration_value,
    parse_partial_date_value,
    render_value,
)


def test_nested_object_fields_apply_child_constraints() -> None:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(TypeSpec(fields={
        "payload": FieldSpec(fields={
            "age": FieldSpec(type=UniversalType.INTEGER, required=True, minimum=0),
        }),
    }))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"age": -1}, {"age": None}, {}]}), plan=plan
    )
    nested_summary = result.check_summaries.filter(
        pl.col("check_id") == "payload_nested"
    ).row(0, named=True)
    assert nested_summary["fail_count"] == 3


def test_nested_container_and_element_constraints_keep_separate_scopes() -> None:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(TypeSpec(fields={
        "values": FieldSpec(
            min_length=2,
            element=FieldSpec(type=UniversalType.INTEGER, minimum=0),
        ),
    }))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"values": [[1, -1], [2], [3, 4]]}), plan=plan
    )
    summary = result.check_summaries.filter(
        pl.col("check_id") == "values_nested"
    ).row(0, named=True)
    assert (summary["pass_count"], summary["fail_count"]) == (2, 1)
    length_summary = result.check_summaries.filter(
        pl.col("check_id") == "values_length"
    ).row(0, named=True)
    assert (length_summary["pass_count"], length_summary["fail_count"]) == (2, 1)


def test_nested_constraints_apply_to_fixed_array_leaves() -> None:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(TypeSpec(fields={
        "matrix": FieldSpec(
            type=UniversalType.ARRAY,
            dimensions=(2, 2),
            element=FieldSpec(type=UniversalType.INTEGER, minimum=0),
        ),
    }))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"matrix": [[[1, -1], [2, 3]], [[4, 5], [6, 7]]]}),
        plan=plan,
    )
    summary = result.check_summaries.filter(
        pl.col("check_id") == "matrix_nested"
    ).row(0, named=True)
    assert (summary["status"], summary["pass_count"], summary["fail_count"]) == ("failed", 1, 1)


def test_nested_child_severity_is_reported_without_blocking() -> None:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(TypeSpec(fields={
        "payload": FieldSpec(
            type=UniversalType.OBJECT,
            fields={
                "age": FieldSpec(
                    type=UniversalType.INTEGER,
                    minimum=0,
                    severity="warning",
                ),
            },
        ),
    }))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"age": -1}, None]}), plan=plan
    )
    warning = result.check_summaries.filter(
        pl.col("check_id") == "payload_nested__warning"
    ).row(0, named=True)
    assert warning["severity"] == "warning"
    assert (warning["pass_count"], warning["fail_count"]) == (1, 1)
    assert result.passes


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(['{"values":[1]}', '{"values":[1,2]}'], id="json-text-object"),
        pytest.param([{"values": [1]}, {"values": [1, 2]}], id="native-struct"),
    ],
)
def test_nested_array_constraints_measure_decoded_values(payload) -> None:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(TypeSpec(fields={
        "payload": FieldSpec(
            type=UniversalType.OBJECT,
            fields={
                "values": FieldSpec(
                    type=UniversalType.ARRAY,
                    min_length=2,
                    element=FieldSpec(type=UniversalType.INTEGER),
                ),
            },
        ),
    }))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": payload}), plan=plan
    )
    nested = result.check_summaries.filter(
        pl.col("check_id") == "payload_nested"
    ).row(0, named=True)
    assert (nested["status"], nested["pass_count"], nested["fail_count"]) == ("failed", 1, 1)


def test_severity_variant_changes_only_its_own_requirement() -> None:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec import FieldSpec, TypeSpec, UniversalType
    from mountainash.validation import ValidationRunner

    age = FieldSpec(type=UniversalType.INTEGER, minimum=0)
    plan = compile_datacontract(TypeSpec(fields={
        "payload": FieldSpec(
            type=UniversalType.OBJECT,
            severity="warning",
            required=True,
            fields={"age": age, "age_soft": age.variant(severity="warning")},
        ),
    }))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"age": -1, "age_soft": 1}, {"age": 1, "age_soft": -1}, None]}),
        plan=plan,
    )
    rows = {
        row["check_id"]: row
        for row in result.check_summaries.iter_rows(named=True)
    }
    outcome = lambda check_id: (  # noqa: E731
        rows[check_id]["severity"], rows[check_id]["status"],
        rows[check_id]["pass_count"], rows[check_id]["fail_count"],
    )
    assert outcome("payload__not_null") == ("warning", "failed", 2, 1)
    assert outcome("payload_nested") == ("blocking", "failed", 2, 1)
    assert outcome("payload_nested__warning") == ("warning", "failed", 2, 1)
    assert age.severity is None
    assert not result.passes

def test_duration_parser_preserves_calendar_months_and_decimal_seconds() -> None:
    """Duration values retain months rather than collapsing to timedeltas."""
    assert parse_duration_value("P1Y2M3DT4H5M6.50S") == DurationValue(
        months=14,
        seconds=Decimal("273906.50"),
    )
    assert parse_duration_value("-P1MT2S") == DurationValue(
        months=-1,
        seconds=Decimal("-2"),
    )


@pytest.mark.parametrize("value", ["P", "PT", "P1YT", "P1X"])
def test_duration_parser_rejects_invalid_lexical_values(value: str) -> None:
    """An invalid semantic string has one explicit internal representation."""
    assert parse_duration_value(value) is INVALID_VALUE


def test_partial_date_parser_supports_arbitrary_years_and_timezones() -> None:
    """Partial dates avoid Python date's bounded year range."""
    assert parse_partial_date_value("12024-11+05:30", kind="yearmonth") == PartialDateValue(
        year=12024,
        month=11,
        timezone_minutes=330,
    )
    assert parse_partial_date_value("-0001Z", kind="year") == PartialDateValue(
        year=-1,
        month=None,
        timezone_minutes=0,
    )
    assert parse_partial_date_value("-0000", kind="year") is INVALID_VALUE


def test_canonical_keys_are_recursive_and_object_order_independent() -> None:
    """Mappings are unordered; arrays retain order at every nesting depth."""
    first = {"items": [True, {"value": Decimal("1.0")}]}
    reordered = {"items": [True, {"value": 1}]}
    changed_array_order = {"items": [{"value": 1}, True]}

    assert canonical_value_key(first) == canonical_value_key(reordered)
    assert canonical_value_key(first) != canonical_value_key(changed_array_order)


def test_canonical_keys_normalize_special_numeric_values() -> None:
    """NaNs and infinities have stable typed equality across numeric inputs."""
    assert canonical_value_key(Decimal("NaN")) == canonical_value_key(float("nan"))
    assert canonical_value_key(Decimal("Infinity")) == canonical_value_key(float("inf"))
    assert canonical_value_key(float("inf")) != canonical_value_key(float("-inf"))


def test_renderer_is_typed_and_deterministic() -> None:
    """Diagnostics distinguish logical types instead of relying on repr()."""
    assert render_value({"value": Decimal("1.0"), "ok": True}) == (
        '{"ok":true,"value":{"$decimal":"1.0"}}'
    )
