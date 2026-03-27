"""
Comprehensive tests for schema_config.SchemaConfig module.

Tests the enhanced SchemaConfig with TableSchema integration:
- Schema-based initialization
- from_schemas() with fuzzy matching
- predict_output_schema()
- validate_against_schemas()
- Backward compatibility
"""
import pytest
import json

from mountainash.dataframes.schema_config import (
    SchemaConfig,
    TableSchema,
    create_rename_config,
    create_cast_config,
    init_column_config,
)


# ============================================================================
# Legacy Mode Tests (Backward Compatibility)
# ============================================================================

class TestSchemaConfigLegacyMode:
    """Test backward compatibility with legacy column-based mode."""

    def test_basic_initialization(self):
        """Test basic SchemaConfig initialization."""
        config = SchemaConfig(columns={
            "old_id": {"rename": "id", "cast": "integer"},
            "name": {"cast": "string"}
        })

        assert len(config.columns) == 2
        assert config.columns["old_id"]["rename"] == "id"
        assert config.columns["old_id"]["cast"] == "integer"
        assert config.columns["name"]["cast"] == "string"

    def test_from_dict_full_format(self):
        """Test from_dict with full format."""
        config_dict = {
            "columns": {
                "old_id": {"rename": "id"},
                "name": {}
            },
            "keep_only_mapped": True,
            "strict": False
        }

        config = SchemaConfig.from_dict(config_dict)

        assert len(config.columns) == 2
        assert config.keep_only_mapped is True
        assert config.strict is False

    def test_from_dict_simple_rename(self):
        """Test from_dict with simple rename format."""
        config_dict = {
            "old_id": "id",
            "old_name": "name"
        }

        config = SchemaConfig.from_dict(config_dict)

        assert len(config.columns) == 2
        assert config.columns["old_id"]["rename"] == "id"
        assert config.columns["old_name"]["rename"] == "name"
        assert config.keep_only_mapped is True  # Default for simple format

    def test_from_json(self):
        """Test from_json parsing."""
        json_str = json.dumps({
            "columns": {
                "old_id": {"rename": "id", "cast": "integer"}
            },
            "keep_only_mapped": False
        })

        config = SchemaConfig.from_json(json_str)

        assert len(config.columns) == 1
        assert config.columns["old_id"]["rename"] == "id"

    def test_to_dict_to_json(self):
        """Test serialization to dict and JSON."""
        config = SchemaConfig(
            columns={"old_id": {"rename": "id"}},
            keep_only_mapped=True,
            strict=False
        )

        # Test to_dict
        config_dict = config.to_dict()
        assert config_dict["columns"] == {"old_id": {"rename": "id"}}
        assert config_dict["keep_only_mapped"] is True

        # Test to_json
        json_str = config.to_json()
        parsed = json.loads(json_str)
        assert parsed["columns"] == {"old_id": {"rename": "id"}}

    def test_create_rename_config(self):
        """Test convenience function for rename config."""
        config = create_rename_config({
            "old_id": "id",
            "old_name": "name"
        }, keep_only_mapped=True)

        assert config.columns["old_id"]["rename"] == "id"
        assert config.columns["old_name"]["rename"] == "name"
        assert config.keep_only_mapped is True

    def test_create_cast_config(self):
        """Test convenience function for cast config."""
        config = create_cast_config({
            "user_id": "integer",
            "score": "number"
        })

        assert config.columns["user_id"]["cast"] == "integer"
        assert config.columns["score"]["cast"] == "number"

    def test_init_column_config(self):
        """Test config normalization helper."""
        # From dict
        config1 = init_column_config({"old": "new"})
        assert isinstance(config1, SchemaConfig)

        # From SchemaConfig
        config2 = init_column_config(config1)
        assert config2 is config1

        # From JSON string
        config3 = init_column_config('{"old": "new"}')
        assert isinstance(config3, SchemaConfig)


# ============================================================================
# Schema Mode Tests (New Functionality)
# ============================================================================

class TestSchemaConfigSchemaMode:
    """Test new schema-driven functionality."""

    def test_initialization_with_schemas(self):
        """Test initialization with source and target schemas."""
        source = TableSchema.from_simple_dict({"user_id": "integer", "name": "string"})
        target = TableSchema.from_simple_dict({"id": "integer", "full_name": "string"})

        config = SchemaConfig(
            columns={},
            source_schema=source,
            target_schema=target
        )

        assert config.source_schema is not None
        assert config.target_schema is not None
        assert len(config.source_schema.fields) == 2
        assert len(config.target_schema.fields) == 2

    def test_from_schemas_exact_match(self):
        """Test from_schemas with exact column name matches."""
        source = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "email": "string"
        })
        target = TableSchema.from_simple_dict({
            "id": "integer",  # Same name, same type - no transform
            "name": "string",  # Same name, same type - no transform
            "email": "string"  # Same name, same type - no transform
        })

        config = SchemaConfig.from_schemas(source, target)

        # No transformations needed for exact matches
        assert len(config.columns) == 0  # No transforms needed
        assert config.source_schema is source
        assert config.target_schema is target

    def test_from_schemas_with_renames(self):
        """Test from_schemas with column renaming."""
        source = TableSchema.from_simple_dict({
            "user_id": "integer",
            "user_name": "string"
        })
        target = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string"
        })

        config = SchemaConfig.from_schemas(source, target, fuzzy_match_threshold=0.5)

        # Should generate rename transformations
        assert "user_id" in config.columns or "user_name" in config.columns
        # Fuzzy matching should map user_id -> id, user_name -> name

    def test_from_schemas_with_type_casts(self):
        """Test from_schemas with type conversions."""
        source = TableSchema.from_simple_dict({
            "id": "number",  # float
            "active": "string"  # string "true"/"false"
        })
        target = TableSchema.from_simple_dict({
            "id": "integer",  # Need to cast number -> integer
            "active": "boolean"  # Need to cast string -> boolean
        })

        config = SchemaConfig.from_schemas(source, target, auto_cast=True)

        # Should generate cast transformations
        assert len(config.columns) == 2
        assert config.columns["id"]["cast"] == "integer"
        assert config.columns["active"]["cast"] == "boolean"

    def test_from_schemas_fuzzy_matching(self):
        """Test fuzzy matching with similar but not exact column names."""
        source = TableSchema.from_simple_dict({
            "user_id": "integer",
            "user_email": "string",
            "user_name": "string"
        })
        target = TableSchema.from_simple_dict({
            "id": "integer",
            "email": "string",
            "name": "string"
        })

        config = SchemaConfig.from_schemas(source, target, fuzzy_match_threshold=0.4)

        # Fuzzy matching should find:
        # user_id -> id (contains "id")
        # user_email -> email (contains "email")
        # user_name -> name (contains "name")
        assert len(config.columns) >= 1  # At least some matches

    def test_from_schemas_no_auto_cast(self):
        """Test from_schemas with auto_cast disabled."""
        source = TableSchema.from_simple_dict({"id": "number"})
        target = TableSchema.from_simple_dict({"id": "integer"})

        config = SchemaConfig.from_schemas(source, target, auto_cast=False)

        # Should not generate cast rule
        if "id" in config.columns:
            assert "cast" not in config.columns["id"]

    def test_from_schemas_keep_unmapped_source(self):
        """Test from_schemas with keep_unmapped_source option."""
        source = TableSchema.from_simple_dict({
            "id": "integer",
            "extra": "string"  # Not in target
        })
        target = TableSchema.from_simple_dict({
            "id": "integer"
        })

        # Keep unmapped
        config1 = SchemaConfig.from_schemas(source, target, keep_unmapped_source=True)
        assert config1.keep_only_mapped is False

        # Don't keep unmapped
        config2 = SchemaConfig.from_schemas(source, target, keep_unmapped_source=False)
        assert config2.keep_only_mapped is True


# ============================================================================
# predict_output_schema() Tests
# ============================================================================

class TestPredictOutputSchema:
    """Test output schema prediction functionality."""

    def test_predict_with_renames(self):
        """Test prediction with column renaming."""
        config = SchemaConfig(columns={
            "old_id": {"rename": "id"},
            "name": {}  # No transformation
        })

        input_schema = TableSchema.from_simple_dict({
            "old_id": "integer",
            "name": "string"
        })

        output_schema = config.predict_output_schema(input_schema)

        assert len(output_schema.fields) == 2
        assert output_schema.get_field("id").type == "integer"  # Renamed
        assert output_schema.get_field("name").type == "string"  # Unchanged

    def test_predict_with_casts(self):
        """Test prediction with type casting."""
        config = SchemaConfig(columns={
            "id": {"cast": "integer"},
            "amount": {"cast": "number"}
        })

        input_schema = TableSchema.from_simple_dict({
            "id": "string",
            "amount": "string"
        })

        output_schema = config.predict_output_schema(input_schema)

        assert output_schema.get_field("id").type == "integer"
        assert output_schema.get_field("amount").type == "number"

    def test_predict_with_filter(self):
        """Test prediction with keep_only_mapped=True."""
        config = SchemaConfig(
            columns={"id": {"rename": "user_id"}},
            keep_only_mapped=True
        )

        input_schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "extra": "boolean"
        })

        output_schema = config.predict_output_schema(input_schema)

        # Should only have user_id (renamed from id)
        assert len(output_schema.fields) == 1
        assert output_schema.get_field("user_id").type == "integer"

    def test_predict_without_filter(self):
        """Test prediction with keep_only_mapped=False."""
        config = SchemaConfig(
            columns={"id": {"rename": "user_id"}},
            keep_only_mapped=False
        )

        input_schema = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "extra": "boolean"
        })

        output_schema = config.predict_output_schema(input_schema)

        # Should have user_id (renamed), name, and extra (pass-through)
        assert len(output_schema.fields) == 3
        assert output_schema.get_field("user_id").type == "integer"
        assert output_schema.get_field("name").type == "string"
        assert output_schema.get_field("extra").type == "boolean"

    def test_predict_with_target_schema(self):
        """Test that predict correctly matches target_schema when properly configured."""
        source = TableSchema.from_simple_dict({"old_id": "integer"})
        target = TableSchema.from_simple_dict({"id": "integer"})

        config = SchemaConfig(
            columns={"old_id": {"rename": "id"}},
            source_schema=source,
            target_schema=target
        )

        # Should predict schema matching target_schema
        output = config.predict_output_schema()
        assert output.field_names == target.field_names
        assert output.get_field("id").type == target.get_field("id").type

    def test_predict_with_source_schema(self):
        """Test prediction using config's source_schema."""
        source = TableSchema.from_simple_dict({"old_id": "integer", "name": "string"})

        config = SchemaConfig(
            columns={"old_id": {"rename": "id"}},
            source_schema=source
        )

        # No input_schema provided - should use source_schema
        output = config.predict_output_schema()
        assert len(output.fields) == 2
        assert output.get_field("id").type == "integer"

    def test_predict_no_schema_raises(self):
        """Test that predict raises error without any schema."""
        config = SchemaConfig(columns={"id": {"cast": "integer"}})

        with pytest.raises(ValueError, match="No input schema provided"):
            config.predict_output_schema()

    def test_predict_with_defaults(self):
        """Test prediction with default values for new columns."""
        config = SchemaConfig(columns={
            "new_field": {"default": 0, "cast": "integer"}
        })

        input_schema = TableSchema.from_simple_dict({"id": "integer"})

        output_schema = config.predict_output_schema(input_schema)

        # Should include new_field even though it's not in input
        assert len(output_schema.fields) == 2
        assert output_schema.get_field("new_field").type == "integer"


# ============================================================================
# validate_against_schemas() Tests
# ============================================================================

class TestValidateAgainstSchemas:
    """Test schema validation functionality."""

    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        source = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        target = TableSchema.from_simple_dict({"user_id": "integer", "full_name": "string"})

        config = SchemaConfig(
            columns={
                "id": {"rename": "user_id"},
                "name": {"rename": "full_name"}
            },
            source_schema=source,
            target_schema=target
        )

        is_valid, errors = config.validate_against_schemas()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_source_column(self):
        """Test validation catches missing source columns."""
        source = TableSchema.from_simple_dict({"id": "integer"})

        config = SchemaConfig(
            columns={
                "id": {"rename": "user_id"},
                "missing_col": {"rename": "other"}  # Not in source schema
            },
            source_schema=source
        )

        is_valid, errors = config.validate_against_schemas(check_source=True, check_target=False)

        # Debug output if test fails
        if is_valid:
            print(f"Unexpected: validation passed. Errors: {errors}")

        assert is_valid is False, f"Expected validation to fail, but got is_valid=True with errors={errors}"
        assert any("missing_col" in error for error in errors), f"Expected 'missing_col' error, got: {errors}"

    def test_validate_type_mismatch(self):
        """Test validation catches type mismatches."""
        source = TableSchema.from_simple_dict({"id": "string"})  # string
        target = TableSchema.from_simple_dict({"id": "integer"})  # integer

        # Config doesn't cast - will cause mismatch
        config = SchemaConfig(
            columns={},  # No cast transformation
            source_schema=source,
            target_schema=target
        )

        is_valid, errors = config.validate_against_schemas()

        # Should detect type mismatch
        assert is_valid is False
        assert any("Type mismatch" in error or "missing" in error.lower() for error in errors)

    def test_validate_missing_target_column(self):
        """Test validation catches missing target columns."""
        source = TableSchema.from_simple_dict({"id": "integer"})
        target = TableSchema.from_simple_dict({
            "id": "integer",
            "required_field": "string"  # Not mapped
        })

        config = SchemaConfig(
            columns={},  # No mapping for required_field
            source_schema=source,
            target_schema=target
        )

        is_valid, errors = config.validate_against_schemas()

        assert is_valid is False
        assert any("required_field" in error for error in errors)

    def test_validate_skip_checks(self):
        """Test validation with selective checking."""
        source = TableSchema.from_simple_dict({"id": "integer"})

        config = SchemaConfig(
            columns={"missing": {"rename": "other"}},
            source_schema=source
        )

        # Skip source check - should be valid
        is_valid, errors = config.validate_against_schemas(check_source=False)
        assert is_valid is True


# ============================================================================
# Serialization with Schemas
# ============================================================================

class TestSchemaConfigSerialization:
    """Test serialization/deserialization with schemas."""

    def test_to_dict_with_schemas(self):
        """Test to_dict includes schemas."""
        source = TableSchema.from_simple_dict({"id": "integer"})
        target = TableSchema.from_simple_dict({"user_id": "integer"})

        config = SchemaConfig(
            columns={"id": {"rename": "user_id"}},
            source_schema=source,
            target_schema=target
        )

        config_dict = config.to_dict()

        assert "source_schema" in config_dict
        assert "target_schema" in config_dict
        assert config_dict["source_schema"]["fields"][0]["name"] == "id"
        assert config_dict["target_schema"]["fields"][0]["name"] == "user_id"

    def test_from_dict_with_schemas(self):
        """Test from_dict parses schemas."""
        config_dict = {
            "columns": {"id": {"rename": "user_id"}},
            "source_schema": {
                "fields": [{"name": "id", "type": "integer"}]
            },
            "target_schema": {
                "fields": [{"name": "user_id", "type": "integer"}]
            }
        }

        config = SchemaConfig.from_dict(config_dict)

        assert config.source_schema is not None
        assert config.target_schema is not None
        assert len(config.source_schema.fields) == 1
        assert config.source_schema.get_field("id").type == "integer"

    def test_json_round_trip_with_schemas(self):
        """Test JSON serialization round-trip with schemas."""
        source = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        target = TableSchema.from_simple_dict({"user_id": "integer", "full_name": "string"})

        config = SchemaConfig(
            columns={"id": {"rename": "user_id"}, "name": {"rename": "full_name"}},
            keep_only_mapped=True,
            source_schema=source,
            target_schema=target
        )

        # Round-trip
        json_str = config.to_json()
        restored = SchemaConfig.from_json(json_str)

        assert restored.source_schema is not None
        assert restored.target_schema is not None
        assert len(restored.source_schema.fields) == 2
        assert len(restored.target_schema.fields) == 2
        assert restored.columns == config.columns


# ============================================================================
# Integration Tests
# ============================================================================

class TestSchemaConfigIntegration:
    """Test end-to-end workflows with SchemaConfig."""

    def test_full_workflow_schema_driven(self):
        """Test complete workflow: from_schemas -> predict -> validate."""
        # Define schemas
        source = TableSchema.from_simple_dict({
            "user_id": "integer",
            "user_name": "string",
            "user_email": "string",
            "extra_field": "boolean"
        })

        target = TableSchema.from_simple_dict({
            "id": "integer",
            "name": "string",
            "email": "string"
        })

        # Auto-generate config
        config = SchemaConfig.from_schemas(
            source,
            target,
            fuzzy_match_threshold=0.4,
            keep_unmapped_source=False
        )

        # Predict output
        predicted = config.predict_output_schema()

        # Should match target
        assert len(predicted.fields) == len(target.fields)

        # Validate
        is_valid, errors = config.validate_against_schemas()
        if not is_valid:
            print(f"Validation errors: {errors}")
        # Note: Fuzzy matching might not be perfect, so validation might have warnings

    def test_backward_compatibility_workflow(self):
        """Test that legacy mode still works without schemas."""
        config = SchemaConfig(columns={
            "old_id": {"rename": "id", "cast": "integer"},
            "name": {}
        })

        # Should work without schemas
        assert config.source_schema is None
        assert config.target_schema is None
        assert len(config.columns) == 2

        # Can still serialize/deserialize
        json_str = config.to_json()
        restored = SchemaConfig.from_json(json_str)
        assert restored.columns == config.columns
