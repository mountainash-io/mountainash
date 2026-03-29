"""Smoke tests for mountainash.schema port."""
import pytest
import polars as pl


class TestSchemaImports:
    """Verify key schema classes are importable."""

    def test_schema_config_importable(self):
        from mountainash.schema import SchemaConfig
        assert SchemaConfig is not None

    def test_universal_type_importable(self):
        from mountainash.schema import UniversalType
        assert hasattr(UniversalType, "STRING")
        assert hasattr(UniversalType, "INTEGER")
        assert hasattr(UniversalType, "DATE")

    def test_field_constraints_importable(self):
        from mountainash.schema import FieldConstraints
        assert FieldConstraints is not None

    def test_schema_field_importable(self):
        from mountainash.schema import SchemaField
        assert SchemaField is not None

    def test_table_schema_importable(self):
        from mountainash.schema import TableSchema
        assert TableSchema is not None


class TestSchemaBasicOperations:
    """Verify basic schema operations work."""

    def test_schema_config_creation(self):
        from mountainash.schema import SchemaConfig
        config = SchemaConfig(columns={
            "old_name": {"rename": "new_name"},
        })
        assert config is not None

    def test_normalize_type(self):
        from mountainash.schema.config.types import UniversalType, normalize_type
        assert normalize_type("string") == "string"
        assert normalize_type("integer") == "integer"
        assert normalize_type(int, "python") == "integer"

    def test_universal_type_enum_members(self):
        from mountainash.schema.config.types import UniversalType
        # Verify key enum members exist
        expected = {"STRING", "INTEGER", "NUMBER", "BOOLEAN", "DATE", "DATETIME", "TIME"}
        actual = {m.name for m in UniversalType}
        assert expected.issubset(actual)

    def test_table_schema_from_simple_dict(self):
        from mountainash.schema import TableSchema
        schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        assert len(schema.fields) == 2
        assert schema.field_names == ["id", "name"]

    def test_schema_field_creation(self):
        from mountainash.schema import SchemaField, FieldConstraints
        from mountainash.schema.config.types import UniversalType
        field = SchemaField(
            name="age",
            type=UniversalType.INTEGER,
            constraints=FieldConstraints(required=True),
        )
        assert field.name == "age"
        assert field.constraints.required is True
