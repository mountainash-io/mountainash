"""Tests for custom_cast field on FieldDefinition and Frictionless round-trip."""
from __future__ import annotations


from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.frictionless import table_schema_to_frictionless, table_schema_from_frictionless


# ---------------------------------------------------------------------------
# TestFieldDefinitionCustomCast
# ---------------------------------------------------------------------------

class TestFieldDefinitionCustomCast:
    def test_custom_cast_default_none(self):
        """custom_cast defaults to None when not provided."""
        spec = FieldDefinition(type=UniversalType.ANY)
        assert spec.custom_cast is None

    def test_custom_cast_set(self):
        """custom_cast stores the provided string value."""
        spec = FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float")
        assert spec.custom_cast == "safe_float"


# ---------------------------------------------------------------------------
# TestFrictionlessCustomCast
# ---------------------------------------------------------------------------

class TestFrictionlessCustomCast:
    def test_export_custom_cast(self):
        """TableSchema with custom_cast exports x-mountainash.custom_cast in the field dict."""
        spec = TableSchema(fields={
            "amount": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),
        })
        descriptor = table_schema_to_frictionless(spec)
        field_dict = descriptor["fields"][0]
        assert "x-mountainash" in field_dict
        assert field_dict["x-mountainash"]["custom_cast"] == "safe_float"

    def test_import_custom_cast(self):
        """Descriptor with x-mountainash.custom_cast is imported into FieldDefinition.custom_cast."""
        descriptor = {
            "fields": [
                {
                    "name": "amount",
                    "type": "any",
                    "x-mountainash": {"custom_cast": "safe_float"},
                }
            ]
        }
        spec = table_schema_from_frictionless(descriptor)
        assert spec.fields["amount"].custom_cast == "safe_float"

    def test_round_trip_custom_cast(self):
        """Export then import preserves custom_cast."""
        original = TableSchema(fields={
            "amount": FieldDefinition(type=UniversalType.ANY, custom_cast="safe_float"),
            "flag": FieldDefinition(type=UniversalType.BOOLEAN, custom_cast="rich_boolean"),
        })
        descriptor = table_schema_to_frictionless(original)
        restored = table_schema_from_frictionless(descriptor)

        assert restored.fields["amount"].custom_cast == "safe_float"
        assert restored.fields["flag"].custom_cast == "rich_boolean"

    def test_no_custom_cast_no_extension(self):
        """FieldDefinition without custom_cast (and no other extensions) has no x-mountainash key."""
        spec = TableSchema(fields={
            "id": FieldDefinition(type=UniversalType.INTEGER),
        })
        descriptor = table_schema_to_frictionless(spec)
        field_dict = descriptor["fields"][0]
        assert "x-mountainash" not in field_dict
