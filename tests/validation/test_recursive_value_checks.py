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


def _nested_status(definition, values, dtype) -> str:
    import polars as pl

    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.typespec.spec import TableSchema
    from mountainash.validation import ValidationRunner

    plan = compile_datacontract(TableSchema(fields={"payload": definition}))
    result = ValidationRunner().validate_relation(
        pl.DataFrame({"payload": pl.Series("payload", values, dtype=dtype)}),
        plan=plan,
    )
    return result.check_summaries.filter(
        pl.col("check_id") == "payload_nested"
    ).row(0, named=True)["status"]


def _record(**members):
    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    return FieldDefinition(type=UniversalType.OBJECT, fields=members)


def test_nested_object_fields_apply_child_constraints() -> None:
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    definition = _record(
        age=FieldDefinition(type=UniversalType.INTEGER, required=True, minimum=0)
    )
    dtype = pl.Struct({"age": pl.Int64})

    assert _nested_status(definition, [{"age": -1}], dtype) == "failed"
    assert _nested_status(definition, [{"age": 5}], dtype) == "passed"
    # a required member is a member requirement, not a container requirement
    assert _nested_status(definition, [{"age": None}], dtype) == "failed"


def test_nested_member_applies_extended_constraints() -> None:
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    definition = _record(
        code=FieldDefinition(
            type=UniversalType.STRING,
            str_startswith="a",
            ne="abad",
            notin=["aout"],
        )
    )
    dtype = pl.Struct({"code": pl.String})

    assert _nested_status(definition, [{"code": "agood"}], dtype) == "passed"
    assert _nested_status(definition, [{"code": "bgood"}], dtype) == "failed"
    assert _nested_status(definition, [{"code": "abad"}], dtype) == "failed"
    assert _nested_status(definition, [{"code": "aout"}], dtype) == "failed"


def test_nested_member_applies_string_format_and_categories() -> None:
    """A member keeps every requirement its definition declares, as a top-level field does."""
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    definition = _record(
        mail=FieldDefinition(type=UniversalType.STRING, format="email"),
        tier=FieldDefinition(type=UniversalType.STRING, categories=["gold", "silver"]),
    )
    dtype = pl.Struct({"mail": pl.String, "tier": pl.String})

    assert _nested_status(definition, [{"mail": "a@b.co", "tier": "gold"}], dtype) == "passed"
    assert _nested_status(definition, [{"mail": "not-mail", "tier": "gold"}], dtype) == "failed"
    assert _nested_status(definition, [{"mail": "a@b.co", "tier": "tin"}], dtype) == "failed"


def test_nested_element_applies_string_format_and_categories() -> None:
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    dtype = pl.List(pl.String)
    emails = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(type=UniversalType.STRING, format="email"),
    )
    tiers = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(type=UniversalType.STRING, categories=["gold"]),
    )

    assert _nested_status(emails, [["a@b.co"]], dtype) == "passed"
    assert _nested_status(emails, [["a@b.co", "nope"]], dtype) == "failed"
    assert _nested_status(tiers, [["gold"]], dtype) == "passed"
    assert _nested_status(tiers, [["gold", "tin"]], dtype) == "failed"


def test_nested_scalar_element_applies_element_constraints() -> None:
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    definition = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(type=UniversalType.INTEGER, minimum=0),
    )
    dtype = pl.List(pl.Int64)

    assert _nested_status(definition, [[1, 2]], dtype) == "passed"
    assert _nested_status(definition, [[1, -1]], dtype) == "failed"


def test_nested_element_requirement_applies_to_null_items() -> None:
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    required = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(type=UniversalType.INTEGER, required=True),
    )
    optional = FieldDefinition(
        type=UniversalType.ARRAY,
        element=FieldDefinition(type=UniversalType.INTEGER),
    )
    dtype = pl.List(pl.Int64)

    assert _nested_status(required, [[1, None]], dtype) == "failed"
    assert _nested_status(optional, [[1, None]], dtype) == "passed"


def test_nested_array_of_records_checks_each_item_member() -> None:
    import polars as pl

    from mountainash.typespec.spec import FieldDefinition
    from mountainash.typespec.universal_types import UniversalType

    definition = FieldDefinition(
        type=UniversalType.ARRAY,
        element=_record(qty=FieldDefinition(type=UniversalType.INTEGER, minimum=1)),
    )
    dtype = pl.List(pl.Struct({"qty": pl.Int64}))

    assert _nested_status(definition, [[{"qty": 1}, {"qty": 2}]], dtype) == "passed"
    assert _nested_status(definition, [[{"qty": 1}, {"qty": 0}]], dtype) == "failed"


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
