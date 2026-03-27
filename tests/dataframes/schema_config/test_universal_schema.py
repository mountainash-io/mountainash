"""
Comprehensive tests for TableSchema (Frictionless Table Schema).

Tests all aspects of the schema system including:
- FieldConstraints creation and serialization
- SchemaField creation and serialization
- TableSchema creation, serialization, and comparison
- Frictionless JSON compliance
- Schema diff utilities
"""
import pytest
import json
from mountainash.dataframes.schema_config.universal_schema import (
    FieldConstraints,
    SchemaField,
    TableSchema,
    SchemaDiff,
    compare_schemas,
)
from mountainash.dataframes.schema_config.types import UniversalType


# ============================================================================
# Test FieldConstraints
# ============================================================================

class TestFieldConstraints:
    """Test FieldConstraints dataclass."""

    def test_field_constraints_defaults(self):
        """Test that all constraints default to False/None."""
        constraints = FieldConstraints()
        assert constraints.required is False
        assert constraints.unique is False
        assert constraints.minimum is None
        assert constraints.maximum is None
        assert constraints.min_length is None
        assert constraints.max_length is None
        assert constraints.pattern is None
        assert constraints.enum is None

    def test_field_constraints_to_dict_empty(self):
        """Test that empty constraints serialize to empty dict."""
        constraints = FieldConstraints()
        assert constraints.to_dict() == {}

    def test_field_constraints_to_dict_with_values(self):
        """Test constraints serialization with values."""
        constraints = FieldConstraints(
            required=True,
            unique=True,
            minimum=0,
            maximum=100,
            min_length=1,
            max_length=50,
            pattern=r"^[A-Z]",
            enum=["A", "B", "C"]
        )
        result = constraints.to_dict()

        assert result["required"] is True
        assert result["unique"] is True
        assert result["minimum"] == 0
        assert result["maximum"] == 100
        assert result["minLength"] == 1  # Frictionless uses camelCase
        assert result["maxLength"] == 50
        assert result["pattern"] == r"^[A-Z]"
        assert result["enum"] == ["A", "B", "C"]

    def test_field_constraints_from_dict(self):
        """Test creating constraints from dict."""
        data = {
            "required": True,
            "unique": True,
            "minimum": 10,
            "maximum": 100,
            "minLength": 5,  # Frictionless camelCase
            "maxLength": 20,
            "pattern": r"\d+",
            "enum": [1, 2, 3]
        }
        constraints = FieldConstraints.from_dict(data)

        assert constraints.required is True
        assert constraints.unique is True
        assert constraints.minimum == 10
        assert constraints.maximum == 100
        assert constraints.min_length == 5
        assert constraints.max_length == 20
        assert constraints.pattern == r"\d+"
        assert constraints.enum == [1, 2, 3]

    def test_field_constraints_from_dict_snake_case(self):
        """Test that snake_case keys also work."""
        data = {
            "min_length": 5,  # Python snake_case
            "max_length": 20,
        }
        constraints = FieldConstraints.from_dict(data)
        assert constraints.min_length == 5
        assert constraints.max_length == 20

    def test_field_constraints_bool(self):
        """Test __bool__ method."""
        empty = FieldConstraints()
        assert not empty  # Empty constraints are falsy

        non_empty = FieldConstraints(required=True)
        assert non_empty  # Non-empty constraints are truthy


# ============================================================================
# Test SchemaField
# ============================================================================

class TestSchemaField:
    """Test SchemaField dataclass."""

    def test_schema_field_minimal(self):
        """Test creating field with minimal required attributes."""
        field = SchemaField(name="id", type="integer")
        assert field.name == "id"
        assert field.type == "integer"
        assert field.format is None
        assert field.constraints is None
        assert field.backend_type is None

    def test_schema_field_full(self):
        """Test creating field with all attributes."""
        constraints = FieldConstraints(required=True, unique=True)
        field = SchemaField(
            name="email",
            type="string",
            format="email",
            constraints=constraints,
            backend_type="Utf8",
            title="Email Address",
            description="User's email",
            example="user@example.com"
        )

        assert field.name == "email"
        assert field.type == "string"
        assert field.format == "email"
        assert field.constraints == constraints
        assert field.backend_type == "Utf8"
        assert field.title == "Email Address"
        assert field.description == "User's email"
        assert field.example == "user@example.com"

    def test_schema_field_invalid_type(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid type"):
            SchemaField(name="id", type="invalid_type")

    def test_schema_field_to_dict_minimal(self):
        """Test serializing minimal field."""
        field = SchemaField(name="id", type="integer")
        result = field.to_dict()

        assert result == {"name": "id", "type": "integer"}

    def test_schema_field_to_dict_full(self):
        """Test serializing field with all attributes."""
        constraints = FieldConstraints(required=True)
        field = SchemaField(
            name="email",
            type="string",
            format="email",
            constraints=constraints,
            backend_type="Utf8",
            title="Email",
            description="User email",
            example="test@example.com"
        )
        result = field.to_dict()

        assert result["name"] == "email"
        assert result["type"] == "string"
        assert result["format"] == "email"
        assert result["constraints"] == {"required": True}
        assert result["backend_type"] == "Utf8"
        assert result["title"] == "Email"
        assert result["description"] == "User email"
        assert result["example"] == "test@example.com"

    def test_schema_field_to_dict_exclude_backend_type(self):
        """Test excluding backend_type from serialization."""
        field = SchemaField(name="id", type="integer", backend_type="Int64")
        result = field.to_dict(include_backend_type=False)

        assert "backend_type" not in result
        assert result == {"name": "id", "type": "integer"}

    def test_schema_field_from_dict_minimal(self):
        """Test creating field from minimal dict."""
        data = {"name": "id", "type": "integer"}
        field = SchemaField.from_dict(data)

        assert field.name == "id"
        assert field.type == "integer"

    def test_schema_field_from_dict_full(self):
        """Test creating field from complete dict."""
        data = {
            "name": "email",
            "type": "string",
            "format": "email",
            "constraints": {"required": True, "unique": True},
            "backend_type": "Utf8",
            "title": "Email",
            "description": "User email",
            "example": "test@example.com"
        }
        field = SchemaField.from_dict(data)

        assert field.name == "email"
        assert field.type == "string"
        assert field.format == "email"
        assert field.constraints.required is True
        assert field.constraints.unique is True
        assert field.backend_type == "Utf8"


# ============================================================================
# Test SchemaField Boolean Values
# ============================================================================

class TestSchemaFieldBooleanValues:
    """Test SchemaField boolean value representations (trueValues/falseValues)."""

    def test_boolean_field_with_custom_values(self):
        """Test creating boolean field with custom true/false values."""
        field = SchemaField(
            name="approved",
            type="boolean",
            true_values=["yes", "Y", "true", "1"],
            false_values=["no", "N", "false", "0"]
        )

        assert field.true_values == ["yes", "Y", "true", "1"]
        assert field.false_values == ["no", "N", "false", "0"]

    def test_boolean_field_to_dict_with_custom_values(self):
        """Test serialization with custom boolean values uses camelCase."""
        field = SchemaField(
            name="approved",
            type="boolean",
            true_values=["yes", "Y"],
            false_values=["no", "N"]
        )

        result = field.to_dict()

        assert result["name"] == "approved"
        assert result["type"] == "boolean"
        assert result["trueValues"] == ["yes", "Y"]  # camelCase!
        assert result["falseValues"] == ["no", "N"]  # camelCase!

    def test_boolean_field_from_dict_camelcase(self):
        """Test deserialization from Frictionless format (camelCase)."""
        data = {
            "name": "active",
            "type": "boolean",
            "trueValues": ["yes", "1"],
            "falseValues": ["no", "0"]
        }

        field = SchemaField.from_dict(data)

        assert field.name == "active"
        assert field.type == "boolean"
        assert field.true_values == ["yes", "1"]
        assert field.false_values == ["no", "0"]

    def test_boolean_field_from_dict_snake_case(self):
        """Test deserialization from Python dict format (snake_case)."""
        data = {
            "name": "enabled",
            "type": "boolean",
            "true_values": ["T", "true"],
            "false_values": ["F", "false"]
        }

        field = SchemaField.from_dict(data)

        assert field.true_values == ["T", "true"]
        assert field.false_values == ["F", "false"]

    def test_boolean_field_without_custom_values(self):
        """Test boolean field without custom values (should be None)."""
        field = SchemaField(name="flag", type="boolean")

        assert field.true_values is None
        assert field.false_values is None

        # Should not appear in serialization
        result = field.to_dict()
        assert "trueValues" not in result
        assert "falseValues" not in result

    def test_non_boolean_field_with_custom_values(self):
        """Test that custom boolean values can be set on non-boolean fields."""
        # Spec doesn't restrict this, though it's only meaningful for boolean fields
        field = SchemaField(
            name="status",
            type="string",
            true_values=["active"],
            false_values=["inactive"]
        )

        assert field.true_values == ["active"]
        assert field.false_values == ["inactive"]

    def test_boolean_field_roundtrip(self):
        """Test that boolean values survive serialization roundtrip."""
        original = SchemaField(
            name="verified",
            type="boolean",
            true_values=["yes", "Y", "1", "true"],
            false_values=["no", "N", "0", "false"]
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = SchemaField.from_dict(data)

        assert restored.true_values == original.true_values
        assert restored.false_values == original.false_values


# ============================================================================
# Test TableSchema
# ============================================================================

class TestTableSchema:
    """Test TableSchema class."""

    def test_universal_schema_minimal(self):
        """Test creating schema with minimal fields."""
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
        ])

        assert len(schema.fields) == 2
        assert schema.field_names == ["id", "name"]
        assert schema.primary_key is None

    def test_universal_schema_with_primary_key_string(self):
        """Test schema with primary key as string (normalized to list)."""
        schema = TableSchema(
            fields=[SchemaField(name="id", type="integer")],
            primary_key="id"
        )

        assert schema.primary_key == ["id"]

    def test_universal_schema_with_primary_key_list(self):
        """Test schema with composite primary key."""
        schema = TableSchema(
            fields=[
                SchemaField(name="user_id", type="integer"),
                SchemaField(name="org_id", type="integer"),
            ],
            primary_key=["user_id", "org_id"]
        )

        assert schema.primary_key == ["user_id", "org_id"]

    def test_universal_schema_with_metadata(self):
        """Test schema with title and description."""
        schema = TableSchema(
            fields=[SchemaField(name="id", type="integer")],
            title="User Schema",
            description="Schema for user data"
        )

        assert schema.title == "User Schema"
        assert schema.description == "Schema for user data"

    def test_universal_schema_empty_fields_raises(self):
        """Test that empty fields list raises ValueError."""
        with pytest.raises(ValueError, match="at least one field"):
            TableSchema(fields=[])

    def test_universal_schema_duplicate_names_raises(self):
        """Test that duplicate field names raise ValueError."""
        with pytest.raises(ValueError, match="Duplicate field names"):
            TableSchema(fields=[
                SchemaField(name="id", type="integer"),
                SchemaField(name="id", type="string"),  # Duplicate!
            ])

    def test_universal_schema_get_field(self):
        """Test getting field by name."""
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
        ])

        field = schema.get_field("id")
        assert field is not None
        assert field.name == "id"
        assert field.type == "integer"

        assert schema.get_field("nonexistent") is None

    def test_universal_schema_has_field(self):
        """Test checking if field exists."""
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
        ])

        assert schema.has_field("id") is True
        assert schema.has_field("nonexistent") is False

    def test_universal_schema_to_dict_minimal(self):
        """Test serializing minimal schema."""
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
        ])
        result = schema.to_dict()

        assert "fields" in result
        assert len(result["fields"]) == 1
        assert result["fields"][0]["name"] == "id"

    def test_universal_schema_to_dict_full(self):
        """Test serializing complete schema."""
        schema = TableSchema(
            fields=[
                SchemaField(name="id", type="integer"),
                SchemaField(name="name", type="string"),
            ],
            primary_key="id",
            title="Test Schema",
            description="A test schema"
        )
        result = schema.to_dict()

        assert result["primaryKey"] == ["id"]  # camelCase
        assert result["title"] == "Test Schema"
        assert result["description"] == "A test schema"

    def test_universal_schema_from_dict(self):
        """Test creating schema from dict."""
        data = {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
            ],
            "primaryKey": ["id"],
            "title": "Test Schema"
        }
        schema = TableSchema.from_dict(data)

        assert len(schema.fields) == 2
        assert schema.primary_key == ["id"]
        assert schema.title == "Test Schema"

    def test_universal_schema_from_dict_snake_case(self):
        """Test that snake_case keys work too."""
        data = {
            "fields": [{"name": "id", "type": "integer"}],
            "primary_key": "id"  # snake_case
        }
        schema = TableSchema.from_dict(data)
        assert schema.primary_key == ["id"]

    def test_universal_schema_json_round_trip(self):
        """Test JSON serialization round-trip."""
        original = TableSchema(
            fields=[
                SchemaField(name="id", type="integer"),
                SchemaField(name="email", type="string", format="email"),
            ],
            primary_key="id",
            title="User Schema"
        )

        json_str = original.to_json()
        restored = TableSchema.from_json(json_str)

        assert len(restored.fields) == 2
        assert restored.fields[0].name == "id"
        assert restored.fields[1].format == "email"
        assert restored.primary_key == ["id"]
        assert restored.title == "User Schema"

    def test_universal_schema_to_simple_dict(self):
        """Test converting to simple dict format."""
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
            SchemaField(name="balance", type="number"),
        ])
        simple = schema.to_simple_dict()

        assert simple == {
            "id": "integer",
            "name": "string",
            "balance": "number"
        }

    def test_universal_schema_from_simple_dict(self):
        """Test creating from simple dict format."""
        simple = {
            "id": "integer",
            "name": "string"
        }
        schema = TableSchema.from_simple_dict(simple, primary_key="id")

        assert len(schema.fields) == 2
        assert schema.get_field("id").type == "integer"
        assert schema.get_field("name").type == "string"
        assert schema.primary_key == ["id"]

    def test_universal_schema_equality(self):
        """Test schema equality comparison."""
        schema1 = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
        ], primary_key="id")

        schema2 = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
        ], primary_key="id")

        schema3 = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="email", type="string"),  # Different field
        ], primary_key="id")

        assert schema1 == schema2
        assert schema1 != schema3
        assert schema1 != "not a schema"

    def test_universal_schema_is_compatible_with(self):
        """Test schema compatibility check."""
        base_schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
            SchemaField(name="extra", type="string"),  # Extra field
        ])

        subset_schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string"),
        ])

        # base_schema is compatible with subset_schema (has all required fields)
        assert base_schema.is_compatible_with(subset_schema) is True

        # subset_schema is NOT compatible with base_schema (missing 'extra')
        assert subset_schema.is_compatible_with(base_schema) is False

    def test_universal_schema_is_compatible_with_type_mismatch(self):
        """Test that type mismatches break compatibility."""
        schema1 = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
        ])

        schema2 = TableSchema(fields=[
            SchemaField(name="id", type="string"),  # Different type!
        ])

        assert schema1.is_compatible_with(schema2) is False


# ============================================================================
# Test TableSchema Missing Values
# ============================================================================

class TestTableSchemaMissingValues:
    """Test TableSchema missing_values field."""

    def test_default_missing_values(self):
        """Test that missing_values defaults to ['']."""
        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        assert schema.missing_values == [""]

    def test_custom_missing_values(self):
        """Test creating schema with custom missing values."""
        schema = TableSchema(
            fields=[SchemaField(name="value", type="number")],
            missing_values=["", "NA", "N/A", "null", "-", "NaN"]
        )

        assert schema.missing_values == ["", "NA", "N/A", "null", "-", "NaN"]

    def test_empty_missing_values(self):
        """Test schema with empty missing_values (no null conversion)."""
        schema = TableSchema(
            fields=[SchemaField(name="data", type="string")],
            missing_values=[]
        )

        assert schema.missing_values == []

    def test_missing_values_validation_not_list(self):
        """Test that non-list missing_values raises TypeError."""
        with pytest.raises(TypeError, match="missing_values must be a list"):
            TableSchema(
                fields=[SchemaField(name="x", type="string")],
                missing_values="NA"  # Wrong: should be a list
            )

    def test_missing_values_validation_non_string_elements(self):
        """Test that non-string elements in missing_values raise TypeError."""
        with pytest.raises(TypeError, match="All values in missing_values must be strings"):
            TableSchema(
                fields=[SchemaField(name="x", type="integer")],
                missing_values=["", None, "NA"]  # Wrong: None is not a string
            )

    def test_missing_values_to_dict_default(self):
        """Test that default missing_values [''] is not included in dict."""
        schema = TableSchema(fields=[
            SchemaField(name="col", type="string")
        ])

        result = schema.to_dict()

        # Default should not be included (keeps output clean)
        assert "missingValues" not in result

    def test_missing_values_to_dict_custom(self):
        """Test that custom missing_values is included with camelCase."""
        schema = TableSchema(
            fields=[SchemaField(name="col", type="string")],
            missing_values=["", "NA", "null"]
        )

        result = schema.to_dict()

        assert "missingValues" in result  # camelCase!
        assert result["missingValues"] == ["", "NA", "null"]

    def test_missing_values_to_dict_empty(self):
        """Test that empty missing_values [] is included."""
        schema = TableSchema(
            fields=[SchemaField(name="col", type="string")],
            missing_values=[]
        )

        result = schema.to_dict()

        assert "missingValues" in result
        assert result["missingValues"] == []

    def test_missing_values_from_dict_camelcase(self):
        """Test loading missing_values from Frictionless format (camelCase)."""
        data = {
            "fields": [{"name": "value", "type": "number"}],
            "missingValues": ["", "-", "9999"]
        }

        schema = TableSchema.from_dict(data)

        assert schema.missing_values == ["", "-", "9999"]

    def test_missing_values_from_dict_snake_case(self):
        """Test loading missing_values from Python dict (snake_case)."""
        data = {
            "fields": [{"name": "value", "type": "number"}],
            "missing_values": ["NA", "null"]
        }

        schema = TableSchema.from_dict(data)

        assert schema.missing_values == ["NA", "null"]

    def test_missing_values_from_dict_not_provided(self):
        """Test that missing_values defaults to [''] when not provided."""
        data = {
            "fields": [{"name": "col", "type": "string"}]
        }

        schema = TableSchema.from_dict(data)

        assert schema.missing_values == [""]  # Default

    def test_missing_values_roundtrip(self):
        """Test that missing_values survives serialization roundtrip."""
        original = TableSchema(
            fields=[SchemaField(name="measurement", type="number")],
            missing_values=["", "NA", "-9999", "MISSING"],
            title="Test Schema"
        )

        # Serialize and deserialize
        data = original.to_dict()
        restored = TableSchema.from_dict(data)

        assert restored.missing_values == original.missing_values

    def test_missing_values_from_simple_dict_default(self):
        """Test from_simple_dict uses default missing_values."""
        schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"
        })

        assert schema.missing_values == [""]

    def test_missing_values_from_simple_dict_custom(self):
        """Test from_simple_dict with custom missing_values."""
        schema = TableSchema.from_simple_dict(
            {"value": "number"},
            missing_values=["", "NA", "null"]
        )

        assert schema.missing_values == ["", "NA", "null"]

    def test_missing_values_json_roundtrip(self):
        """Test JSON serialization with missing_values."""
        original = TableSchema(
            fields=[SchemaField(name="score", type="number")],
            missing_values=["", "NA", "N/A", "null"],
            title="Test Schema"
        )

        # Serialize to JSON
        json_str = original.to_json()

        # Deserialize from JSON
        restored = TableSchema.from_json(json_str)

        # Verify missing_values preserved
        assert restored.missing_values == ["", "NA", "N/A", "null"]


# ============================================================================
# Test SchemaDiff and compare_schemas
# ============================================================================

class TestSchemaDiff:
    """Test SchemaDiff dataclass."""

    def test_schema_diff_defaults(self):
        """Test SchemaDiff defaults."""
        diff = SchemaDiff()
        assert diff.missing_columns == []
        assert diff.extra_columns == []
        assert diff.type_mismatches == []
        assert diff.is_compatible is True

    def test_schema_diff_has_differences(self):
        """Test has_differences method."""
        empty_diff = SchemaDiff()
        assert empty_diff.has_differences() is False

        diff_with_changes = SchemaDiff(missing_columns=["col1"])
        assert diff_with_changes.has_differences() is True

    def test_schema_diff_str(self):
        """Test string representation."""
        diff = SchemaDiff(
            missing_columns=["col1", "col2"],
            extra_columns=["col3"],
            type_mismatches=[("col4", "integer", "string")]
        )
        diff_str = str(diff)

        assert "Missing columns" in diff_str
        assert "Extra columns" in diff_str
        assert "Type mismatches" in diff_str


class TestCompareSchemas:
    """Test compare_schemas function."""

    def test_compare_identical_schemas(self):
        """Test comparing identical schemas."""
        schema1 = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"
        })
        schema2 = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"
        })

        diff = compare_schemas(schema1, schema2)

        assert not diff.has_differences()
        assert diff.is_compatible is True

    def test_compare_schemas_missing_columns(self):
        """Test detecting missing columns."""
        actual = TableSchema.from_simple_dict({
            "id": "integer"
        })
        expected = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"  # Missing in actual
        })

        diff = compare_schemas(actual, expected)

        assert diff.missing_columns == ["name"]
        assert diff.is_compatible is False

    def test_compare_schemas_extra_columns(self):
        """Test detecting extra columns."""
        actual = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "extra": "string"  # Extra column
        })
        expected = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"
        })

        diff = compare_schemas(actual, expected)

        assert diff.extra_columns == ["extra"]
        # Extra columns don't break compatibility
        assert diff.is_compatible is True

    def test_compare_schemas_type_mismatches(self):
        """Test detecting type mismatches."""
        actual = TableSchema.from_simple_dict({
            "id": "string",  # Wrong type
            "name": "string"
        })
        expected = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"
        })

        diff = compare_schemas(actual, expected)

        assert len(diff.type_mismatches) == 1
        assert diff.type_mismatches[0] == ("id", "string", "integer")
        assert diff.is_compatible is False

    def test_compare_schemas_multiple_differences(self):
        """Test detecting multiple types of differences."""
        actual = TableSchema.from_simple_dict({
            "id": "string",  # Type mismatch
            "extra": "number"  # Extra column
        })
        expected = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"  # Missing column
        })

        diff = compare_schemas(actual, expected)

        assert "name" in diff.missing_columns
        assert "extra" in diff.extra_columns
        assert len(diff.type_mismatches) == 1
        assert diff.is_compatible is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestTableSchemaIntegration:
    """Integration tests for the complete schema system."""

    def test_frictionless_json_compliance(self):
        """Test that generated JSON is Frictionless-compliant."""
        schema = TableSchema(
            fields=[
                SchemaField(
                    name="id",
                    type="integer",
                    constraints=FieldConstraints(required=True, unique=True)
                ),
                SchemaField(
                    name="email",
                    type="string",
                    format="email",
                    constraints=FieldConstraints(required=True)
                ),
            ],
            primary_key="id",
            title="User Schema",
            description="Schema for user data"
        )

        json_str = schema.to_json()
        data = json.loads(json_str)

        # Check Frictionless structure
        assert "fields" in data
        assert "primaryKey" in data  # camelCase
        assert data["fields"][0]["name"] == "id"
        assert data["fields"][0]["constraints"]["required"] is True

    def test_backend_type_preservation(self):
        """Test that backend types are preserved through serialization."""
        schema = TableSchema(fields=[
            SchemaField(
                name="id",
                type="integer",
                backend_type="Int64"  # Polars-specific type
            ),
            SchemaField(
                name="name",
                type="string",
                backend_type="Utf8"
            ),
        ])

        # Serialize and deserialize
        json_str = schema.to_json()
        restored = TableSchema.from_json(json_str)

        assert restored.get_field("id").backend_type == "Int64"
        assert restored.get_field("name").backend_type == "Utf8"

    def test_schema_diff_workflow(self):
        """Test complete workflow of schema comparison."""
        # Current schema
        current = TableSchema.from_simple_dict({
            "id": "integer",
            "old_name": "string",
            "status": "string"
        })

        # Target schema
        target = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",  # Renamed from old_name
            "email": "string",  # New field
        })

        # Compare
        diff = compare_schemas(current, target)

        # Should detect missing and extra columns
        assert "email" in diff.missing_columns
        assert "name" in diff.missing_columns
        assert "old_name" in diff.extra_columns
        assert "status" in diff.extra_columns

    def test_comprehensive_frictionless_features(self):
        """Test all new Frictionless features together (missing_values, trueValues, falseValues)."""
        # Create schema with all new features
        original = TableSchema(
            fields=[
                SchemaField(
                    name="approved",
                    type="boolean",
                    true_values=["yes", "Y", "true", "1"],
                    false_values=["no", "N", "false", "0"],
                    title="Approval Status"
                ),
                SchemaField(
                    name="score",
                    type="number",
                    constraints=FieldConstraints(minimum=0, maximum=100)
                ),
                SchemaField(name="notes", type="string")
            ],
            missing_values=["", "NA", "N/A", "null", "-"],
            primary_key="approved",
            title="Survey Results Schema",
            description="Schema for survey data with custom missing value handling"
        )

        # Test to_dict includes all new fields with correct casing
        result_dict = original.to_dict()

        assert "missingValues" in result_dict
        assert result_dict["missingValues"] == ["", "NA", "N/A", "null", "-"]

        approved_field = result_dict["fields"][0]
        assert approved_field["name"] == "approved"
        assert "trueValues" in approved_field
        assert approved_field["trueValues"] == ["yes", "Y", "true", "1"]
        assert "falseValues" in approved_field
        assert approved_field["falseValues"] == ["no", "N", "false", "0"]

        # Test JSON serialization roundtrip
        json_str = original.to_json()
        assert "missingValues" in json_str
        assert "trueValues" in json_str
        assert "falseValues" in json_str

        # Deserialize and verify all fields preserved
        restored = TableSchema.from_json(json_str)

        assert restored.missing_values == ["", "NA", "N/A", "null", "-"]

        approved_field = restored.get_field("approved")
        assert approved_field is not None
        assert approved_field.true_values == ["yes", "Y", "true", "1"]
        assert approved_field.false_values == ["no", "N", "false", "0"]

        assert restored.title == "Survey Results Schema"
        assert restored.description == "Schema for survey data with custom missing value handling"
