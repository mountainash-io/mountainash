from datetime import date, datetime, time, timezone

import pytest

from mountainash.typespec.temporal import (
    parse_default_datetime,
    parse_temporal_any,
    parse_xsd_duration,
    parse_xsd_partial_date,
)

from mountainash import col
from mountainash.core.errors import InvalidOptionValueError
from mountainash.expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast import CaseFailureBehaviour

@pytest.mark.parametrize(
    "text,expected_year",
    [("01-02-68", 2068), ("01-02-69", 1969)],
)
def test_temporal_any_uses_fixed_two_digit_year_window(text: str, expected_year: int) -> None:
    assert parse_temporal_any(text, kind="date").year == expected_year


def test_temporal_any_passes_native_values_through() -> None:
    d = date(2024, 1, 2)
    t = time(3, 4, 5)
    dt = datetime(2024, 1, 2, 3, 4, 5)
    assert parse_temporal_any(d, kind="date") is d
    assert parse_temporal_any(t, kind="time") is t
    assert parse_temporal_any(dt, kind="datetime") is dt


@pytest.mark.parametrize("text", ["2024-01-02T03:04:05Z", "2024-01-02T03:04:05 UTC", "2024-01-02T03:04:05 GMT"])
def test_temporal_any_normalizes_named_utc_to_naive_utc(text: str) -> None:
    assert parse_temporal_any(text, kind="datetime") == datetime(2024, 1, 2, 3, 4, 5)


def test_temporal_any_normalizes_numeric_offset_to_naive_utc() -> None:
    assert parse_temporal_any("2024-01-02T03:04:05+02:00", kind="datetime") == datetime(2024, 1, 2, 1, 4, 5)


def test_temporal_any_rejects_unknown_timezone() -> None:
    with pytest.raises((ValueError, TypeError, Warning)):
        parse_temporal_any("2024-01-02T03:04:05 EST", kind="datetime")


@pytest.mark.parametrize("value,kind", [(1, "date"), (None, "time"), (object(), "datetime")])
def test_temporal_any_rejects_wrong_runtime_types(value: object, kind: str) -> None:
    with pytest.raises(TypeError):
        parse_temporal_any(value, kind=kind)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "text",
    ["P3Y6M4DT12H30M5S", "PT.5S", "PT1.S", "PT1.0S", "-P1D"],
)
def test_xsd_duration_accepts_lexical_boundaries(text: str) -> None:
    assert parse_xsd_duration(text) == text


@pytest.mark.parametrize("text", ["P", "-P", "PT", "P1DT", "PT.S", "PT1..0S", "P1.5Y"])
def test_xsd_duration_rejects_invalid_lexical_forms(text: str) -> None:
    with pytest.raises(ValueError):
        parse_xsd_duration(text)


@pytest.mark.parametrize(
    "text,kind",
    [
        ("+0000", "year"),
        ("0000", "year"),
        ("2024-01", "yearmonth"),
        ("-2024", "year"),
        ("12345678901234567890-12", "yearmonth"),
        ("2024-01Z", "yearmonth"),
        ("2024-01+14:00", "yearmonth"),
    ],
)
def test_xsd_partial_date_accepts_year_and_yearmonth_forms(text: str, kind: str) -> None:
    assert parse_xsd_partial_date(text, kind=kind) == text


@pytest.mark.parametrize(
    "text,kind",
    [
        ("-0000", "year"),
        ("2024-00", "yearmonth"),
        ("2024-13", "yearmonth"),
        ("2024-01+14:01", "yearmonth"),
        ("2024-01+99:00", "yearmonth"),
        ("202", "year"),
        ("01234", "year"),
    ],
)
def test_xsd_partial_date_rejects_invalid_lexical_forms(text: str, kind: str) -> None:
    with pytest.raises(ValueError):
        parse_xsd_partial_date(text, kind=kind)


def test_default_datetime_accepts_native_values_and_required_forms() -> None:
    d = date(2024, 1, 2)
    t = time(3, 4, 5)
    dt = datetime(2024, 1, 2, 3, 4, 5)
    assert parse_default_datetime(d) == datetime(2024, 1, 2)
    assert parse_default_datetime(t) == datetime(2000, 1, 1, 3, 4, 5)
    assert parse_default_datetime(dt) == dt
    assert parse_default_datetime("2024-01-02T03:04:05") == dt
    assert parse_default_datetime("2024-01-02T03:04:05.1") == datetime(2024, 1, 2, 3, 4, 5, 100000)
    assert parse_default_datetime("2024-01-02T03:04:05Z") == dt
    assert parse_default_datetime("2024-01-02T03:04:05+02:00") == datetime(2024, 1, 2, 1, 4, 5)


def test_default_datetime_rejects_invalid_text() -> None:
    with pytest.raises((TypeError, ValueError)):
        parse_default_datetime("not-a-datetime")


def test_default_datetime_rejects_date_only_and_space_forms() -> None:
    with pytest.raises(ValueError):
        parse_default_datetime("2024-01-02")
    with pytest.raises(ValueError):
        parse_default_datetime("2024-01-02 03:04:05")


@pytest.mark.parametrize("method", ["to_date", "to_datetime", "to_time"])
def test_custom_temporal_methods_accept_failure_behavior_and_optional_field_name(method: str) -> None:
    expression = getattr(col("value").str, method)("%Y-%m-%d", failure_behavior=CaseFailureBehaviour.NULL)
    assert expression is not None


@pytest.mark.parametrize("method", ["to_date", "to_datetime", "to_time"])
def test_custom_temporal_methods_reject_empty_field_name(method: str) -> None:
    with pytest.raises(InvalidOptionValueError):
        getattr(col("value").str, method)("%Y-%m-%d", field_name="")
