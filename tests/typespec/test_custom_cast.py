"""Tests for custom_cast field on FieldSpec and Frictionless round-trip."""
from __future__ import annotations

import pytest

from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType, normalize_type
from mountainash.typespec.frictionless import typespec_to_frictionless, typespec_from_frictionless


# ---------------------------------------------------------------------------
# TestFieldSpecCustomCast
# ---------------------------------------------------------------------------

class TestFieldSpecCustomCast:
    def test_custom_cast_default_none(self):
        """custom_cast defaults to None when not provided."""
        spec = FieldSpec(name="col")
        assert spec.custom_cast is None

    def test_custom_cast_set(self):
        """custom_cast stores the provided string value."""
        spec = FieldSpec(name="amount", custom_cast="safe_float")
        assert spec.custom_cast == "safe_float"


# ---------------------------------------------------------------------------
# TestFrictionlessCustomCast
# ---------------------------------------------------------------------------

class TestFrictionlessCustomCast:
    def test_export_custom_cast(self):
        """TypeSpec with custom_cast exports x-mountainash.custom_cast in the field dict."""
        spec = TypeSpec(fields=[
            FieldSpec(name="amount", type=UniversalType.ANY, custom_cast="safe_float"),
        ])
        descriptor = typespec_to_frictionless(spec)
        field_dict = descriptor["fields"][0]
        assert "x-mountainash" in field_dict
        assert field_dict["x-mountainash"]["custom_cast"] == "safe_float"

    def test_import_custom_cast(self):
        """Descriptor with x-mountainash.custom_cast is imported into FieldSpec.custom_cast."""
        descriptor = {
            "fields": [
                {
                    "name": "amount",
                    "type": "any",
                    "x-mountainash": {"custom_cast": "safe_float"},
                }
            ]
        }
        spec = typespec_from_frictionless(descriptor)
        assert spec.fields[0].custom_cast == "safe_float"

    def test_round_trip_custom_cast(self):
        """Export then import preserves custom_cast."""
        original = TypeSpec(fields=[
            FieldSpec(name="amount", type=UniversalType.ANY, custom_cast="safe_float"),
            FieldSpec(name="flag", type=UniversalType.BOOLEAN, custom_cast="rich_boolean"),
        ])
        descriptor = typespec_to_frictionless(original)
        restored = typespec_from_frictionless(descriptor)

        assert restored.fields[0].custom_cast == "safe_float"
        assert restored.fields[1].custom_cast == "rich_boolean"

    def test_no_custom_cast_no_extension(self):
        """FieldSpec without custom_cast (and no other extensions) has no x-mountainash key."""
        spec = TypeSpec(fields=[
            FieldSpec(name="id", type=UniversalType.INTEGER),
        ])
        descriptor = typespec_to_frictionless(spec)
        field_dict = descriptor["fields"][0]
        assert "x-mountainash" not in field_dict
