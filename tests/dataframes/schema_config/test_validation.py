"""
Tests for SchemaConfig validation functionality.

Tests ValidationIssue, ValidationResult, and validate_against_dataframe method.
"""
import pytest
import polars as pl
from mountainash.dataframes.schema_config import (
    SchemaConfig,
    ValidationIssue,
    ValidationResult,
    TableSchema,
    SchemaField,
)


class TestValidationDataclasses:
    """Test ValidationIssue and ValidationResult dataclasses."""

    def test_validation_issue_creation(self):
        """Test creating a ValidationIssue."""
        issue = ValidationIssue(
            type='missing_columns',
            severity='error',
            message='Column not found',
            columns=['id', 'name']
        )
        assert issue.type == 'missing_columns'
        assert issue.severity == 'error'
        assert issue.message == 'Column not found'
        assert issue.columns == ['id', 'name']
        assert issue.details is None

    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        issues = [
            ValidationIssue(
                type='missing_columns',
                severity='error',
                message='Missing column: id'
            )
        ]
        result = ValidationResult(valid=False, issues=issues)
        assert result.valid is False
        assert len(result.issues) == 1
        assert result.issues[0].message == 'Missing column: id'

    def test_validation_result_log_issues(self, caplog):
        """Test logging issues from ValidationResult."""
        import logging
        caplog.set_level(logging.INFO)  # Ensure INFO level is captured

        issues = [
            ValidationIssue(
                type='missing_columns',
                severity='error',
                message='Error message',
            ),
            ValidationIssue(
                type='extra_columns',
                severity='warning',
                message='Warning message',
            ),
            ValidationIssue(
                type='info',
                severity='info',
                message='Info message',
            ),
        ]
        result = ValidationResult(valid=False, issues=issues)

        result.log_issues()

        # Check that error and warning messages were logged
        assert 'Error message' in caplog.text
        assert 'Warning message' in caplog.text
        # Info messages may not be captured depending on log level config
        # so we won't assert on them


class TestValidateAgainstDataFrame:
    """Test SchemaConfig.validate_against_dataframe method."""

    def test_validate_against_dataframe_success(self):
        """Test validation passes when DataFrame matches schema."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        config = SchemaConfig(source_schema=schema, strict=False)
        result = config.validate_against_dataframe(df, mode='source')

        assert result.valid is True
        assert len(result.issues) == 0

    def test_validate_against_dataframe_missing_columns_lenient(self):
        """Test lenient mode with missing columns."""
        df = pl.DataFrame({
            "id": [1, 2, 3]
        })

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        config = SchemaConfig(source_schema=schema, strict=False)
        result = config.validate_against_dataframe(df, mode='source')

        # Lenient mode: warnings don't fail validation (only errors do)
        assert result.valid is True  # Warnings don't make validation fail
        assert len(result.issues) == 1
        assert result.issues[0].type == 'missing_columns'
        assert result.issues[0].severity == 'warning'
        assert 'name' in result.issues[0].columns

    def test_validate_against_dataframe_missing_columns_strict(self):
        """Test strict mode raises on missing columns."""
        df = pl.DataFrame({
            "id": [1, 2, 3]
        })

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        config = SchemaConfig(source_schema=schema, strict=True)

        with pytest.raises(ValueError, match="Schema validation failed"):
            config.validate_against_dataframe(df, mode='source')

    def test_validate_against_dataframe_extra_columns_strict(self):
        """Test strict mode flags extra columns."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "extra": [True, False, True]
        })

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        config = SchemaConfig(source_schema=schema, strict=True)
        result = config.validate_against_dataframe(df, mode='source')

        # Strict mode shows extra columns as warning (not error)
        assert result.valid is True  # Only errors block validation
        assert len(result.issues) == 1
        assert result.issues[0].type == 'extra_columns'
        assert 'extra' in result.issues[0].columns

    def test_validate_against_dataframe_no_schema_raises(self):
        """Test validation raises when schema not set."""
        df = pl.DataFrame({"id": [1, 2, 3]})

        config = SchemaConfig(strict=False)  # No source_schema

        with pytest.raises(ValueError, match="source_schema is not set"):
            config.validate_against_dataframe(df, mode='source')

    def test_validate_against_dataframe_target_mode(self):
        """Test validation against target_schema."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        config = SchemaConfig(target_schema=schema, strict=False)
        result = config.validate_against_dataframe(df, mode='target')

        assert result.valid is True
        assert len(result.issues) == 0

    def test_validate_type_mismatch_warning(self):
        """Test type mismatches generate warnings."""
        df = pl.DataFrame({
            "id": ["1", "2", "3"],  # String instead of integer
            "name": ["Alice", "Bob", "Charlie"]
        })

        schema = TableSchema(fields=[
            SchemaField(name="id", type="integer"),
            SchemaField(name="name", type="string")
        ])

        config = SchemaConfig(source_schema=schema, strict=False)
        result = config.validate_against_dataframe(df, mode='source')

        # Type mismatches are warnings, not errors
        assert result.valid is True
        # Should have type mismatch warning
        type_issues = [i for i in result.issues if i.type == 'type_mismatch']
        assert len(type_issues) >= 1
