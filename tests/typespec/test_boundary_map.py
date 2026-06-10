"""UniversalType <-> canonical boundary map: complete in both directions."""
import pytest

from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.typespec.universal_types import (
    UNIVERSAL_TO_CANONICAL,
    UniversalType as U,
    from_canonical,
    parse_universal,
    to_canonical,
)


class TestForward:
    def test_all_universal_members_present(self):
        assert set(UNIVERSAL_TO_CANONICAL) == set(U)

    @pytest.mark.parametrize("u,expected", [
        (U.STRING, D.STRING), (U.INTEGER, D.I64), (U.NUMBER, D.FP64),
        (U.BOOLEAN, D.BOOL), (U.DATE, D.DATE), (U.TIME, D.TIME),
        (U.DATETIME, D.TIMESTAMP), (U.DURATION, D.DURATION),
        (U.YEAR, D.I32), (U.YEARMONTH, D.STRING),
        (U.ARRAY, D.LIST), (U.OBJECT, D.STRUCT),
    ])
    def test_mappings(self, u, expected):
        assert to_canonical(u) is expected

    def test_any_is_unconstrained(self):
        assert to_canonical(U.ANY) is None


class TestReverse:
    def test_all_canon_members_present(self):
        from mountainash.typespec.universal_types import CANONICAL_TO_UNIVERSAL
        assert set(CANONICAL_TO_UNIVERSAL) == set(D)

    @pytest.mark.parametrize("d,expected", [
        (D.I8, (U.INTEGER, None)), (D.U64, (U.INTEGER, None)),
        (D.FP32, (U.NUMBER, None)),
        (D.BINARY, (U.STRING, "binary")),
        (D.LIST, (U.ARRAY, None)), (D.STRUCT, (U.OBJECT, None)),
        (D.TIMESTAMP, (U.DATETIME, None)),
    ])
    def test_collapse(self, d, expected):
        assert from_canonical(d) == expected

    def test_untyped_renders_any(self):
        assert from_canonical(None) == (U.ANY, None)

    def test_direct_types_round_trip(self):
        for u in (U.STRING, U.INTEGER, U.NUMBER, U.BOOLEAN,
                  U.DATE, U.TIME, U.DATETIME, U.DURATION):
            back, _fmt = from_canonical(to_canonical(u))
            assert back is u


class TestParseUniversal:
    def test_valid(self):
        assert parse_universal("integer") is U.INTEGER

    def test_invalid_raises(self):
        with pytest.raises(UnknownDtypeError, match="frictionless"):
            parse_universal("Int64")
