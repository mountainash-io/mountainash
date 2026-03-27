"""
Tests for DataFrameUtils schema convenience methods.

Tests the new schema extraction, validation, and transformation methods
added to DataFrameUtils in Stage 7.
"""
import pytest
import polars as pl
from dataclasses import dataclass

from mountainash.dataframes import DataFrameUtils
from mountainash.dataframes.schema_config import (
    TableSchema,
    SchemaConfig,
    SchemaValidationError,
)


# Test fixtures
@dataclass
class SampleDataclass:
    """Sample dataclass for testing."""
    id: int
    name: str
    active: bool


class TestExtractSchema:
    """Tests for extract_schema() convenience method."""

    def test_extract_from_dataframe(self):
        """Test extracting schema from DataFrame."""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol'],
            'active': [True, False, True]
        })

        schema = DataFrameUtils.extract_schema(df)

        assert isinstance(schema, TableSchema)
        assert set(schema.field_names) == {'id', 'name', 'active'}
        assert schema.get_field('id').type == 'integer'
        assert schema.get_field('name').type == 'string'
        assert schema.get_field('active').type == 'boolean'

    def test_extract_from_dataclass(self):
        """Test extracting schema from dataclass."""
        schema = DataFrameUtils.extract_schema(SampleDataclass)

        assert isinstance(schema, TableSchema)
        assert set(schema.field_names) == {'id', 'name', 'active'}
        assert schema.get_field('id').type == 'integer'
        assert schema.get_field('name').type == 'string'
        assert schema.get_field('active').type == 'boolean'

    def test_extract_from_polars_lazy(self):
        """Test extracting schema from Polars LazyFrame."""
        lf = pl.LazyFrame({
            'id': [1, 2, 3],
            'value': [10.5, 20.5, 30.5]
        })

        schema = DataFrameUtils.extract_schema(lf)

        assert isinstance(schema, TableSchema)
        assert 'id' in schema.field_names
        assert 'value' in schema.field_names


class TestValidateSchema:
    """Tests for validate_schema() and assert_schema() methods."""

    def test_validate_schema_pass(self):
        """Test validate_schema passes for matching schema."""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol']
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        is_valid = DataFrameUtils.validate_schema(df, expected)
        assert is_valid is True

    def test_validate_schema_fail_type_mismatch(self):
        """Test validate_schema fails on type mismatch."""
        df = pl.DataFrame({
            'id': ['1', '2', '3'],  # String instead of integer
            'name': ['Alice', 'Bob', 'Carol']
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        is_valid = DataFrameUtils.validate_schema(df, expected)
        assert is_valid is False

    def test_validate_schema_fail_missing_column(self):
        """Test validate_schema fails on missing column."""
        df = pl.DataFrame({
            'id': [1, 2, 3]
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        is_valid = DataFrameUtils.validate_schema(df, expected)
        assert is_valid is False

    def test_validate_schema_extra_column_strict(self):
        """Test validate_schema fails on extra column in strict mode."""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'extra': ['a', 'b', 'c']
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer'
        })

        is_valid = DataFrameUtils.validate_schema(df, expected, strict=True)
        assert is_valid is False

    def test_validate_schema_extra_column_not_strict(self):
        """Test validate_schema passes on extra column in non-strict mode."""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'extra': ['a', 'b', 'c']
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer'
        })

        is_valid = DataFrameUtils.validate_schema(df, expected, strict=False)
        assert is_valid is True

    def test_assert_schema_pass(self):
        """Test assert_schema does not raise on valid schema."""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol']
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer',
            'name': 'string'
        })

        # Should not raise
        DataFrameUtils.assert_schema(df, expected)

    def test_assert_schema_raises(self):
        """Test assert_schema raises on invalid schema."""
        df = pl.DataFrame({
            'id': ['1', '2', '3']  # Wrong type
        })

        expected = TableSchema.from_simple_dict({
            'id': 'integer'
        })

        with pytest.raises(SchemaValidationError):
            DataFrameUtils.assert_schema(df, expected)


class TestTransformWithSchema:
    """Tests for transform_with_schema() method."""

    def test_transform_with_config(self):
        """Test basic transformation with SchemaConfig."""
        df = pl.DataFrame({
            'old_id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Carol']
        })

        config = SchemaConfig(columns={
            'old_id': {'rename': 'id', 'cast': 'integer'},
            'name': {}
        })

        result = DataFrameUtils.transform_with_schema(df, config)

        assert result.columns == ['id', 'name']
        assert result.schema['id'] == pl.Int64

    def test_transform_preserves_backend(self):
        """Test that transformation preserves DataFrame backend."""
        df = pl.DataFrame({'id': [1, 2, 3]})

        config = SchemaConfig(columns={'id': {}})

        result = DataFrameUtils.transform_with_schema(df, config)

        # Result should still be Polars DataFrame
        assert isinstance(result, pl.DataFrame)


class TestTransformFromSchemas:
    """Tests for transform_from_schemas() method."""

    def test_transform_with_exact_match(self):
        """Test transformation with exact name matching."""
        df = pl.DataFrame({
            'user_id': ['1', '2', '3'],
            'user_name': ['Alice', 'Bob', 'Carol']
        })

        source = TableSchema.from_simple_dict({
            'user_id': 'string',
            'user_name': 'string'
        })

        target = TableSchema.from_simple_dict({
            'user_id': 'integer',
            'user_name': 'string'
        })

        result = DataFrameUtils.transform_from_schemas(
            df,
            source,
            target,
            auto_cast=True,
            keep_unmapped_source=True
        )

        assert 'user_id' in result.columns
        assert 'user_name' in result.columns
        assert result.schema['user_id'] == pl.Int64

    def test_transform_with_keep_unmapped(self):
        """Test keep_unmapped_source parameter."""
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'extra': ['a', 'b', 'c']
        })

        source = TableSchema.from_simple_dict({
            'id': 'integer',
            'extra': 'string'
        })

        target = TableSchema.from_simple_dict({
            'id': 'integer'
        })

        # With keep_unmapped_source=True
        result = DataFrameUtils.transform_from_schemas(
            df,
            source,
            target,
            keep_unmapped_source=True
        )

        assert 'extra' in result.columns

        # With keep_unmapped_source=False
        result = DataFrameUtils.transform_from_schemas(
            df,
            source,
            target,
            keep_unmapped_source=False
        )

        assert 'extra' not in result.columns


class TestValidateTransformation:
    """Tests for validate_transformation() and assert_transformation() methods."""

    def test_validate_transformation_pass(self):
        """Test validate_transformation passes for valid transformation."""
        source = pl.DataFrame({
            'old_id': ['1', '2', '3'],
            'name': ['Alice', 'Bob', 'Carol']
        })

        config = SchemaConfig(columns={
            'old_id': {'rename': 'id', 'cast': 'integer'},
            'name': {}
        })

        target = DataFrameUtils.transform_with_schema(source, config)

        is_valid = DataFrameUtils.validate_transformation(target, source, config)
        assert is_valid is True

    def test_validate_transformation_fail(self):
        """Test validate_transformation fails for invalid transformation."""
        source = pl.DataFrame({
            'old_id': ['1', '2', '3']
        })

        config = SchemaConfig(columns={
            'old_id': {'rename': 'id', 'cast': 'integer'}
        })

        # Intentionally create wrong target
        wrong_target = pl.DataFrame({
            'wrong_name': [1, 2, 3]
        })

        is_valid = DataFrameUtils.validate_transformation(wrong_target, source, config)
        assert is_valid is False

    def test_assert_transformation_pass(self):
        """Test assert_transformation does not raise on valid transformation."""
        source = pl.DataFrame({
            'id': ['1', '2', '3']
        })

        config = SchemaConfig(columns={
            'id': {'cast': 'integer'}
        })

        target = DataFrameUtils.transform_with_schema(source, config)

        # Should not raise
        DataFrameUtils.assert_transformation(target, source, config)

    def test_assert_transformation_raises(self):
        """Test assert_transformation raises on invalid transformation."""
        source = pl.DataFrame({
            'id': ['1', '2', '3']
        })

        config = SchemaConfig(columns={
            'id': {'cast': 'integer'}
        })

        # Wrong target
        wrong_target = pl.DataFrame({
            'wrong': [1, 2, 3]
        })

        with pytest.raises(SchemaValidationError):
            DataFrameUtils.assert_transformation(wrong_target, source, config)


class TestIntegration:
    """Integration tests combining multiple schema methods."""

    def test_full_workflow(self):
        """Test complete workflow: extract → transform → validate."""
        # Step 1: Create source data
        source_df = pl.DataFrame({
            'user_id': ['1', '2', '3'],
            'user_name': ['Alice', 'Bob', 'Carol']
        })

        # Step 2: Extract source schema
        source_schema = DataFrameUtils.extract_schema(source_df)
        assert 'user_id' in source_schema.field_names

        # Step 3: Create manual config (simpler than fuzzy matching)
        config = SchemaConfig(columns={
            'user_id': {'cast': 'integer'},
            'user_name': {}
        })

        # Step 4: Apply transformation
        result = DataFrameUtils.transform_with_schema(source_df, config)

        # Step 5: Define expected target schema
        target_schema = TableSchema.from_simple_dict({
            'user_id': 'integer',
            'user_name': 'string'
        })

        # Step 6: Validate result schema
        assert DataFrameUtils.validate_schema(result, target_schema) is True

        # Step 7: Verify transformation
        assert DataFrameUtils.validate_transformation(result, source_df, config) is True

    def test_dataclass_to_dataframe_workflow(self):
        """Test workflow: dataclass → extract schema → create DataFrame → validate."""
        # Step 1: Extract schema from dataclass
        schema = DataFrameUtils.extract_schema(SampleDataclass)

        # Step 2: Create DataFrame
        df = pl.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Carol'],
            'active': [True, False, True]
        })

        # Step 3: Validate DataFrame matches dataclass schema
        is_valid = DataFrameUtils.validate_schema(df, schema)
        assert is_valid is True
