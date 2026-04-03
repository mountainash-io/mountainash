"""
Tests for type_bridge.py — mapping UniversalType → MountainashDtype.
"""
from __future__ import annotations

import pytest

from mountainash.typespec.type_bridge import UNIVERSAL_TO_MOUNTAINASH, bridge_type
from mountainash.typespec.universal_types import UniversalType
from mountainash.core.dtypes import MountainashDtype


# ============================================================================
# TestBridgeType
# ============================================================================

class TestBridgeType:
    """bridge_type() maps the 7 supported universal types to MountainashDtype."""

    def test_string(self):
        assert bridge_type(UniversalType.STRING) == MountainashDtype.STRING

    def test_integer(self):
        assert bridge_type(UniversalType.INTEGER) == MountainashDtype.I64

    def test_number(self):
        assert bridge_type(UniversalType.NUMBER) == MountainashDtype.FP64

    def test_boolean(self):
        assert bridge_type(UniversalType.BOOLEAN) == MountainashDtype.BOOL

    def test_date(self):
        assert bridge_type(UniversalType.DATE) == MountainashDtype.DATE

    def test_time(self):
        assert bridge_type(UniversalType.TIME) == MountainashDtype.TIME

    def test_datetime(self):
        assert bridge_type(UniversalType.DATETIME) == MountainashDtype.TIMESTAMP

    def test_unsupported_raises(self):
        """DURATION is not in the 7-type mapping and should raise ValueError."""
        with pytest.raises(ValueError, match="duration"):
            bridge_type(UniversalType.DURATION)

    def test_any_raises(self):
        """ANY is not in the 7-type mapping and should raise ValueError."""
        with pytest.raises(ValueError, match="any"):
            bridge_type(UniversalType.ANY)


# ============================================================================
# TestMappingCompleteness
# ============================================================================

class TestMappingCompleteness:
    """Structural tests for the UNIVERSAL_TO_MOUNTAINASH mapping dict."""

    def test_seven_types_mapped(self):
        assert len(UNIVERSAL_TO_MOUNTAINASH) == 7

    def test_all_mapped_types_are_valid(self):
        """Every value in the mapping is a valid MountainashDtype member."""
        for universal_type, mountainash_dtype in UNIVERSAL_TO_MOUNTAINASH.items():
            assert isinstance(mountainash_dtype, MountainashDtype), (
                f"{universal_type} maps to {mountainash_dtype!r}, "
                f"which is not a MountainashDtype"
            )
