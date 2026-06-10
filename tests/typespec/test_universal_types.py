"""
Tests for the UniversalType enum and the surviving boundary surface.

Coverage:
- UniversalType StrEnum membership and values
- A couple of boundary spot-checks (to_canonical / from_canonical / parse_universal)

The legacy string-based type parsing / safe-cast / forward+reverse backend
mapping behaviours were deleted in the type-system unification: their coverage now
lives in tests/core/dtypes/ (test_casts.py, test_target_modules.py) and the
boundary map itself is exhaustively covered in tests/typespec/test_boundary_map.py.
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import MountainashDtype
from mountainash.core.dtypes.errors import UnknownDtypeError
from mountainash.typespec.universal_types import (
    UniversalType,
    from_canonical,
    parse_universal,
    to_canonical,
)


# ============================================================================
# TestUniversalTypeEnum
# ============================================================================

_ALL_MEMBERS = [
    ("STRING", "string"),
    ("INTEGER", "integer"),
    ("NUMBER", "number"),
    ("BOOLEAN", "boolean"),
    ("DATE", "date"),
    ("TIME", "time"),
    ("DATETIME", "datetime"),
    ("DURATION", "duration"),
    ("YEAR", "year"),
    ("YEARMONTH", "yearmonth"),
    ("ARRAY", "array"),
    ("OBJECT", "object"),
    ("ANY", "any"),
]


class TestUniversalTypeEnum:
    """UniversalType is a StrEnum; each value == lowercase name."""

    @pytest.mark.parametrize("name,value", _ALL_MEMBERS)
    def test_member_exists(self, name, value):
        assert hasattr(UniversalType, name)

    @pytest.mark.parametrize("name,value", _ALL_MEMBERS)
    def test_member_value(self, name, value):
        assert getattr(UniversalType, name).value == value

    @pytest.mark.parametrize("name,value", _ALL_MEMBERS)
    def test_strenum_equality(self, name, value):
        """StrEnum members should compare equal to their string value."""
        member = getattr(UniversalType, name)
        assert member == value

    def test_is_strenum(self):
        from enum import StrEnum
        assert issubclass(UniversalType, StrEnum)

    def test_membership_matches_declared(self):
        declared = {value for _, value in _ALL_MEMBERS}
        assert {t.value for t in UniversalType} == declared


# ============================================================================
# TestBoundarySpotChecks
# ============================================================================

class TestBoundarySpotChecks:
    """A couple of boundary smoke checks; exhaustive coverage in
    test_boundary_map.py."""

    def test_to_canonical_string(self):
        assert to_canonical(UniversalType.STRING) == MountainashDtype.STRING

    def test_to_canonical_any_is_none(self):
        assert to_canonical(UniversalType.ANY) is None

    def test_from_canonical_integer(self):
        assert from_canonical(MountainashDtype.I64) == (UniversalType.INTEGER, None)

    def test_from_canonical_none_is_any(self):
        assert from_canonical(None) == (UniversalType.ANY, None)

    def test_parse_universal_valid(self):
        assert parse_universal("integer") == UniversalType.INTEGER

    def test_parse_universal_invalid_raises(self):
        with pytest.raises(UnknownDtypeError):
            parse_universal("not-a-frictionless-type")
