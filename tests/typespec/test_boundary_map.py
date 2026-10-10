"""UniversalType <-> canonical boundary map: complete in both directions."""
import pytest

from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.typespec.errors import AmbiguousGeospatialTypeError
from mountainash.typespec.universal_types import (
    _FORMAT_DEPENDENT_MEMBERS,
    UNIVERSAL_TO_CANONICAL,
    UniversalType as U,
    from_canonical,
    parse_universal,
    to_canonical,
)


class TestForward:
    def test_all_universal_members_are_mapped_or_context_dependent(self):
        # GEOPOINT is deliberately absent from UNIVERSAL_TO_CANONICAL — its
        # canonical shape depends on FieldSpec.format, which to_canonical()
        # has no access to (see resolve_field_canonical in converters.py).
        assert set(UNIVERSAL_TO_CANONICAL) | set(_FORMAT_DEPENDENT_MEMBERS) == set(U)

    @pytest.mark.parametrize("u,expected", [
        (U.STRING, D.STRING), (U.INTEGER, D.I64), (U.NUMBER, D.FP64),
        (U.BOOLEAN, D.BOOL), (U.DATE, D.DATE), (U.TIME, D.TIME),
        (U.DATETIME, D.TIMESTAMP),
        (U.DURATION, D.XSD_DURATION), (U.YEAR, D.XSD_YEAR),
        (U.YEARMONTH, D.XSD_YEARMONTH),
        (U.LIST, D.LIST), (U.ARRAY, D.LIST), (U.OBJECT, D.STRUCT),
        (U.GEOJSON, D.JSON),
    ])
    def test_mappings(self, u, expected):
        assert to_canonical(u) is expected

    def test_any_is_unconstrained(self):
        assert to_canonical(U.ANY) is None

    def test_geopoint_requires_field_context(self):
        with pytest.raises(AmbiguousGeospatialTypeError):
            to_canonical(U.GEOPOINT)


# ============================================================================
# Step 1 fixtures (verbatim from the task brief) — kept as a standalone
# closed-vocabulary/forward-mapping check alongside TestForward above.
# ============================================================================

@pytest.mark.parametrize(
    "universal,canonical",
    [
        (U.DURATION, D.XSD_DURATION),
        (U.YEAR, D.XSD_YEAR),
        (U.YEARMONTH, D.XSD_YEARMONTH),
        (U.LIST, D.LIST),
        (U.ARRAY, D.LIST),
        (U.OBJECT, D.STRUCT),
        (U.GEOJSON, D.JSON),
    ],
)
def test_v2_forward_mappings(universal: U, canonical: D) -> None:
    assert to_canonical(universal) is canonical


def test_geopoint_requires_field_context() -> None:
    with pytest.raises(AmbiguousGeospatialTypeError):
        to_canonical(U.GEOPOINT)


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
        (D.JSON, (U.GEOJSON, None)),
        (D.XSD_DURATION, (U.DURATION, None)),
        (D.XSD_YEAR, (U.YEAR, None)),
        (D.XSD_YEARMONTH, (U.YEARMONTH, None)),
    ])
    def test_collapse(self, d, expected):
        assert from_canonical(d) == expected

    def test_untyped_renders_any(self):
        assert from_canonical(None) == (U.ANY, None)

    def test_direct_types_round_trip(self):
        # DURATION/YEAR/YEARMONTH still round-trip despite the underlying
        # canonical dtype changing (physical DURATION/I32/STRING -> semantic
        # XSD_DURATION/XSD_YEAR/XSD_YEARMONTH) — CANONICAL_TO_UNIVERSAL maps
        # each new semantic dtype straight back to its originating
        # UniversalType (see test_collapse above).
        for u in (U.STRING, U.INTEGER, U.NUMBER, U.BOOLEAN,
                  U.DATE, U.TIME, U.DATETIME, U.DURATION,
                  U.YEAR, U.YEARMONTH):
            back, _fmt = from_canonical(to_canonical(u))
            assert back is u

    def test_list_reverse_stays_array_not_list(self):
        # Preserves: canonical LIST reverse inference remains ARRAY (LIST
        # and ARRAY share physical MountainashDtype.LIST during this
        # interim; only the forward direction distinguishes lexical intent).
        assert from_canonical(D.LIST) == (U.ARRAY, None)


class TestParseUniversal:
    def test_valid(self):
        assert parse_universal("integer") is U.INTEGER

    def test_invalid_raises(self):
        with pytest.raises(UnknownDtypeError, match="frictionless"):
            parse_universal("Int64")
