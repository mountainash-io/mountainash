"""
Tests for schema validation utilities.

Tests round-trip validation, schema matching, and transformation config validation.
"""
import pytest
import polars as pl

from mountainash.dataframes.schema_config import (
    SchemaConfig,
    TableSchema,
    SchemaValidationError,
    validate_round_trip,
    assert_round_trip,
    validate_schema_match,
    assert_schema_match,
    validate_transformation_config,
    assert_transformation_config,
)
from mountainash.dataframes.schema_transform import SchemaTransformFactory


class TestValidateRoundTrip:
    """Tests for validate_round_trip() function."""

    def test_valid_transformation(self):
        """Test validation passes for correct transformation."""
        # Setup
        config = SchemaConfig(
            columns={
                'old_id': {'rename': 'id', 'cast': 'integer'},
                'name': {}
            }
        )

        source = pl.DataFrame({'old_id': ['1', '2', '3'], 'name': ['Alice', 'Bob', 'Carol']})

        # Transform
        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(source)
        target = strategy.apply(source, config)

        # Validate
        is_valid, errors = validate_round_trip(target, source, config)

        assert is_valid
        assert len(errors) == 0

    def test_missing_column(self):
        """Test validation fails when expected column is missing."""
        # Setup - config expects 'new_col' but transformation doesn't create it
        config = SchemaConfig(
            columns={
                'old_id': {'rename': 'id'},
            }
        )

        source = pl.DataFrame({'old_id': [1, 2, 3]})

        # Manually create target missing the 'id' column
        target = pl.DataFrame({'wrong_name': [1, 2, 3]})

        # Validate
        is_valid, errors = validate_round_trip(target, source, config)

        assert not is_valid
        assert any('missing' in err.lower() for err in errors)

    def test_type_mismatch(self):
        """Test validation fails when column type is wrong."""
        config = SchemaConfig(
            columns={
                'value': {'cast': 'integer'}
            }
        )

        source = pl.DataFrame({'value': ['1', '2', '3']})

        # Create target with wrong type (string instead of integer)
        target = pl.DataFrame({'value': ['1', '2', '3']})  # Still string

        is_valid, errors = validate_round_trip(target, source, config)

        assert not is_valid
        assert any('type mismatch' in err.lower() for err in errors)

    def test_extra_columns_allowed(self):
        """Test that extra columns are allowed when keep_only_mapped=False."""
        config = SchemaConfig(
            columns={'id': {}},
            keep_only_mapped=False  # Allow extra columns
        )

        source = pl.DataFrame({'id': [1, 2], 'extra': ['a', 'b']})

        # Transform (will keep both columns)
        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(source)
        target = strategy.apply(source, config)

        # Validate
        is_valid, errors = validate_round_trip(target, source, config)

        assert is_valid
        assert len(errors) == 0

    def test_extra_columns_not_allowed(self):
        """Test that extra columns cause error when keep_only_mapped=True."""
        config = SchemaConfig(
            columns={'id': {}},
            keep_only_mapped=True  # Filter out unmapped columns
        )

        source = pl.DataFrame({'id': [1, 2], 'extra': ['a', 'b']})

        # Manually create target with extra column
        target = pl.DataFrame({'id': [1, 2], 'unexpected': ['x', 'y']})

        is_valid, errors = validate_round_trip(target, source, config)

        assert not is_valid
        assert any('extra' in err.lower() or 'unexpected' in err.lower() for err in errors)


class TestAssertRoundTrip:
    """Tests for assert_round_trip() function."""

    def test_assert_passes(self):
        """Test assert_round_trip passes for valid transformation."""
        config = SchemaConfig(columns={'id': {}})
        source = pl.DataFrame({'id': [1, 2, 3]})

        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(source)
        target = strategy.apply(source, config)

        # Should not raise
        assert_round_trip(target, source, config)

    def test_assert_raises(self):
        """Test assert_round_trip raises SchemaValidationError on failure."""
        config = SchemaConfig(columns={'id': {}})
        source = pl.DataFrame({'id': [1, 2, 3]})

        # Wrong target
        target = pl.DataFrame({'wrong': [1, 2, 3]})

        with pytest.raises(SchemaValidationError) as exc_info:
            assert_round_trip(target, source, config)

        assert 'round-trip validation failed' in str(exc_info.value).lower()


class TestValidateSchemaMatch:
    """Tests for validate_schema_match() function."""

    def test_exact_match(self):
        """Test validation passes for exact schema match."""
        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol']
        })

        is_valid, errors = validate_schema_match(df, expected)

        assert is_valid
        assert len(errors) == 0

    def test_missing_column_fails(self):
        """Test validation fails when required column is missing."""
        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        df = pl.DataFrame({'id': [1, 2, 3]})  # Missing 'name'

        is_valid, errors = validate_schema_match(df, expected)

        assert not is_valid
        assert any('missing' in err.lower() for err in errors)
        assert any('name' in err for err in errors)

    def test_type_mismatch_fails(self):
        """Test validation fails when column type is wrong."""
        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        df = pl.DataFrame({
            'id': ['1', '2', '3'],  # Wrong type (string instead of integer)
            'name': ['Alice', 'Bob', 'Carol']
        })

        is_valid, errors = validate_schema_match(df, expected)

        assert not is_valid
        assert any('type mismatch' in err.lower() for err in errors)
        assert any('id' in err for err in errors)

    def test_extra_columns_strict(self):
        """Test that extra columns cause error in strict mode."""
        expected = TableSchema.from_simple_dict({'id': 'integer'})

        df = pl.DataFrame({
            'id': [1, 2, 3],
            'extra': ['a', 'b', 'c']  # Extra column
        })

        is_valid, errors = validate_schema_match(df, expected, strict=True)

        assert not is_valid
        assert any('unexpected' in err.lower() or 'extra' in err.lower() for err in errors)

    def test_extra_columns_not_strict(self):
        """Test that extra columns are allowed in non-strict mode."""
        expected = TableSchema.from_simple_dict({'id': 'integer'})

        df = pl.DataFrame({
            'id': [1, 2, 3],
            'extra': ['a', 'b', 'c']
        })

        is_valid, errors = validate_schema_match(df, expected, strict=False)

        assert is_valid
        assert len(errors) == 0


class TestAssertSchemaMatch:
    """Tests for assert_schema_match() function."""

    def test_assert_passes(self):
        """Test assert_schema_match passes for matching schema."""
        expected = TableSchema.from_simple_dict({'id': 'integer'})
        df = pl.DataFrame({'id': [1, 2, 3]})

        # Should not raise
        assert_schema_match(df, expected)

    def test_assert_raises(self):
        """Test assert_schema_match raises on mismatch."""
        expected = TableSchema.from_simple_dict({'id': 'integer'})
        df = pl.DataFrame({'wrong': [1, 2, 3]})

        with pytest.raises(SchemaValidationError) as exc_info:
            assert_schema_match(df, expected)

        assert 'schema validation failed' in str(exc_info.value).lower()


class TestValidateTransformationConfig:
    """Tests for validate_transformation_config() function."""

    def test_valid_config_with_schemas(self):
        """Test validation passes for valid configuration."""
        source = TableSchema.from_simple_dict({'old_id': 'string', 'name': 'string'})
        target = TableSchema.from_simple_dict({'id': 'integer', 'name': 'string'})

        config = SchemaConfig(
            columns={'old_id': {'rename': 'id', 'cast': 'integer'}},
            source_schema=source,
            target_schema=target
        )

        is_valid, errors = validate_transformation_config(config)

        assert is_valid
        assert len(errors) == 0

    def test_missing_source_column(self):
        """Test validation fails when source column doesn't exist."""
        source = TableSchema.from_simple_dict({'id': 'string'})

        config = SchemaConfig(
            columns={'missing_col': {'rename': 'new_col'}},
            source_schema=source
        )

        is_valid, errors = validate_transformation_config(config)

        assert not is_valid
        assert any('missing_col' in err for err in errors)

    def test_type_mismatch_with_target(self):
        """Test validation fails when predicted output doesn't match target."""
        source = TableSchema.from_simple_dict({'id': 'string'})
        target = TableSchema.from_simple_dict({'id': 'integer'})

        # Config doesn't cast, so output will be string (mismatch)
        config = SchemaConfig(
            columns={},  # No cast
            source_schema=source,
            target_schema=target
        )

        is_valid, errors = validate_transformation_config(config)

        assert not is_valid
        assert any('type mismatch' in err.lower() or 'missing' in err.lower() for err in errors)

    def test_with_parameter_schemas(self):
        """Test validation with schemas passed as parameters."""
        source = TableSchema.from_simple_dict({'old_id': 'string'})
        target = TableSchema.from_simple_dict({'id': 'integer'})

        config = SchemaConfig(
            columns={'old_id': {'rename': 'id', 'cast': 'integer'}}
            # No source_schema or target_schema in config
        )

        # Pass schemas as parameters
        is_valid, errors = validate_transformation_config(config, source, target)

        assert is_valid
        assert len(errors) == 0


class TestAssertTransformationConfig:
    """Tests for assert_transformation_config() function."""

    def test_assert_passes(self):
        """Test assert_transformation_config passes for valid config."""
        source = TableSchema.from_simple_dict({'id': 'string'})
        target = TableSchema.from_simple_dict({'id': 'string'})

        config = SchemaConfig(
            columns={},
            source_schema=source,
            target_schema=target
        )

        # Should not raise
        assert_transformation_config(config)

    def test_assert_raises(self):
        """Test assert_transformation_config raises on invalid config."""
        source = TableSchema.from_simple_dict({'id': 'string'})

        config = SchemaConfig(
            columns={'missing': {}},
            source_schema=source
        )

        with pytest.raises(SchemaValidationError) as exc_info:
            assert_transformation_config(config)

        assert 'configuration validation failed' in str(exc_info.value).lower()


class TestIntegration:
    """Integration tests combining validators with transformations."""

    def test_full_pipeline_validation(self):
        """Test complete pipeline: config → transform → validate."""
        # Create simple manual config to avoid fuzzy matching complexity
        config = SchemaConfig(
            columns={
                'user_id': {'cast': 'integer'},
                'user_name': {}
            },
            keep_only_mapped=False
        )

        # Create source data
        source_df = pl.DataFrame({
            'user_id': ['1', '2', '3'],
            'user_name': ['Alice', 'Bob', 'Carol']
        })

        # Apply transformation
        factory = SchemaTransformFactory()
        strategy = factory.get_strategy(source_df)
        target_df = strategy.apply(source_df, config)

        # Validate round-trip
        assert_round_trip(target_df, source_df, config)

        # Verify transformation succeeded
        assert target_df.shape[0] == 3  # Same number of rows
        assert target_df.schema['user_id'] == pl.Int64  # Type cast applied

    def test_error_propagation(self):
        """Test that validation errors are properly propagated."""
        source_schema = TableSchema.from_simple_dict({'id': 'string'})
        target_schema = TableSchema.from_simple_dict({'id': 'integer'})

        # Config without cast (will cause type mismatch)
        config = SchemaConfig(
            columns={},
            source_schema=source_schema,
            target_schema=target_schema
        )

        # Validation should fail
        with pytest.raises(SchemaValidationError) as exc_info:
            assert_transformation_config(config)

        error_msg = str(exc_info.value).lower()
        assert 'type mismatch' in error_msg or 'missing' in error_msg
