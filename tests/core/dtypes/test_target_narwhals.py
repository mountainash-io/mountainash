"""Narwhals parse_type_string — parameterized backend_type fidelity (item 54, gap 1).

Mirrors the Polars cases against nw.*, plus the Important-finding-2 regression
guard: the post-upgrade guard must be `isinstance(t, type)`, NOT an
`issubclass(t, nw.DataType)` check — there is no `nw.DataType` class, so a
naive literal port of the Polars code would AttributeError at import time.
"""
from __future__ import annotations

import narwhals as nw
import pytest

from mountainash.core.dtypes import target_narwhals


class TestGuardAdaptedNotCopied:
    def test_no_nw_datatype_class_exists(self):
        """Premise of the Important-finding-2 guard: a literal port of the
        Polars guard would reference a class that does not exist."""
        assert hasattr(nw, "DataType") is False

    def test_bare_name_guard_is_isinstance_type(self):
        """DTypeClass instances (nw.Int64 etc.) ARE types; a passing
        bare-name parse proves the guard was adapted, not copy-pasted."""
        assert target_narwhals.parse_type_string("Int64") is nw.Int64


class TestParameterizedRoundTrip:
    @pytest.mark.parametrize("s,expected", [
        ("Datetime(time_unit='us', time_zone='UTC')",
         nw.Datetime(time_unit="us", time_zone="UTC")),
        ("Duration(time_unit='ms')", nw.Duration(time_unit="ms")),
        # NOTE: MountainashDtype has no canonical DECIMAL member
        # (canonical.py) — backend_type is Decimal's ONLY path to a schema
        # entry on every target; there is no canonical fallback to fall back
        # to. That is why this test has no non-backend_type counterpart.
        ("Decimal(precision=38, scale=10)", nw.Decimal(precision=38, scale=10)),
        ("List(Int64)", nw.List(nw.Int64)),
    ])
    def test_parameterized_repr_round_trips(self, s, expected):
        assert target_narwhals.parse_type_string(s) == expected

    def test_array_with_bare_name_arg_and_shape_tuple(self):
        """Critical-finding case (bare-Name arg + tuple-of-Constant kwarg)."""
        result = target_narwhals.parse_type_string("Array(Int64, shape=(5,))")
        assert result == nw.Array(nw.Int64, shape=(5,))

    def test_enum_categories(self):
        result = target_narwhals.parse_type_string("Enum(categories=['a', 'b'])")
        assert result == nw.Enum(categories=["a", "b"])


class TestBareNamesUnchanged:
    def test_bare_names_still_resolve(self):
        assert target_narwhals.parse_type_string("Int32") is nw.Int32
        assert target_narwhals.parse_type_string("String") is nw.String


class TestGarbageRejected:
    @pytest.mark.parametrize("s", [
        "garbage",
        "Datetime(nonsense=1)",
        "NotARealDtype",
    ])
    def test_unparseable_returns_none(self, s):
        assert target_narwhals.parse_type_string(s) is None
