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
    from mountainash.typespec.spec import FieldConstraints, FieldSpec, TypeSpec
    from mountainash.typespec.universal_types import UniversalType
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(
        TypeSpec(
            fields=[
                FieldSpec(
                    name="payload",
                    type=UniversalType.OBJECT,
                    object_fields=[
                        FieldSpec(
                            name="age",
                            type=UniversalType.INTEGER,
                            constraints=FieldConstraints(required=True, minimum=0),
                        )
                    ],
                )
            ]
        )
    )

    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": [{"age": -1}]}),
        plan=plan,
    )

    nested_summary = result.check_summaries.filter(
        pl.col("check_id") == "payload_nested"
    ).row(0, named=True)
    assert nested_summary["status"] == "failed"


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
