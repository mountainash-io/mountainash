import pytest
from mountainash.core.capabilities.schema import ValueClass
from mountainash.core.capabilities.value_classes import (
    REPRESENTATIVE_SLICES,
    MULTIPLIER_UNITS,
    matches,
    predicate_for,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2d", True),
        ("3h", True),
        ("12mo", True),
        ("1d", False),
        ("0d", False),
        ("02d", False),
        ("2x", False),
        ("2ns", False),
        ("2d ", False),
        ("2", False),
        ("INVALID", False),
    ],
)
def test_duration_multiplier(value, expected):
    assert matches(ValueClass.DURATION_MULTIPLIER, value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("UTC", True),
        ("Australia/Sydney", True),
        ("America/New_York", True),
        ("Not/AZone", False),
        ("", False),
        ("2d", False),
    ],
)
def test_iana_timezone(value, expected):
    assert matches(ValueClass.IANA_TIMEZONE, value) is expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1d", True),
        ("-3mo", True),
        ("2h30m", True),
        ("1y6mo", True),
        ("", False),
        ("3 days", False),
        ("abc", False),
    ],
)
def test_polars_offset(value, expected):
    assert matches(ValueClass.POLARS_OFFSET, value) is expected


def test_every_class_has_a_predicate_and_a_slice():
    for vc in ValueClass:
        assert callable(predicate_for(vc))
        assert len(REPRESENTATIVE_SLICES[vc]) >= 2
        assert all(matches(vc, v) for v in REPRESENTATIVE_SLICES[vc])


def test_multiplier_units_match_api_builder_duration_tokens():
    from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash._ma_option_domains import (
        _UNIT_DURATION,
    )

    # _UNIT_DURATION holds canonical "1x" forms; strip the leading "1".
    duration_tokens = {v[1:] for v in _UNIT_DURATION}
    assert duration_tokens == set(MULTIPLIER_UNITS)
