"""Polars parse_type_string — parameterized backend_type fidelity (item 54, gap 1).

Round-trips: str(pl.<dtype>) output is valid constructor-call syntax against
the polars namespace; parse_type_string must reconstruct the real
parameterized dtype instead of returning None (canonical fallback).
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.core.dtypes import target_polars


class TestParameterizedRoundTrip:
    @pytest.mark.parametrize("s,expected", [
        ("Datetime(time_unit='us', time_zone='UTC')",
         pl.Datetime(time_unit="us", time_zone="UTC")),
        ("Duration(time_unit='ms')", pl.Duration(time_unit="ms")),
        # NOTE: MountainashDtype has no canonical DECIMAL member
        # (canonical.py) — backend_type is Decimal's ONLY path to a schema
        # entry on every target; there is no canonical fallback to fall back
        # to. That is why this test has no non-backend_type counterpart.
        ("Decimal(precision=38, scale=10)", pl.Decimal(precision=38, scale=10)),
        ("List(Int64)", pl.List(pl.Int64)),
    ])
    def test_parameterized_repr_round_trips(self, s, expected):
        assert target_polars.parse_type_string(s) == expected

    def test_array_with_bare_name_arg_and_shape_tuple(self):
        """Critical-finding case: bare-Name arg (Int64) + tuple-of-Constant
        kwarg (shape=(5,)) — the naive Name-rejecting implementation fails
        this one explicitly."""
        result = target_polars.parse_type_string("Array(Int64, shape=(5,))")
        assert result == pl.Array(pl.Int64, shape=(5,))

    def test_parameterized_result_is_instance_not_class(self):
        result = target_polars.parse_type_string(
            "Datetime(time_unit='us', time_zone='UTC')"
        )
        assert isinstance(result, pl.Datetime)


class TestBareNamesUnchanged:
    def test_bare_name_still_resolves(self):
        assert target_polars.parse_type_string("Int64") is pl.Int64
        assert target_polars.parse_type_string("String") is pl.String

    def test_bare_enum_categorical_still_resolve(self):
        """Gap 4 resolution: the bare (no-param) Enum/Categorical forms
        legitimately parse to the bare classes — unchanged, not newly invalid.
        The empty-categories footgun of *using* them is pre-existing and
        addressed via `categories`/parameterized strings, not by rejecting
        the bare form here."""
        assert target_polars.parse_type_string("Enum") is pl.Enum
        assert target_polars.parse_type_string("Categorical") is pl.Categorical


class TestGarbageRejected:
    @pytest.mark.parametrize("s", [
        "garbage",
        "Datetime(nonsense=1)",
        "NotARealDtype",
        "os.system('x')",
    ])
    def test_unparseable_returns_none(self, s):
        assert target_polars.parse_type_string(s) is None
