"""
mountainash-schema: Schema Management and Column Transformation

This package provides schema management, type conversion, and column transformation
capabilities for DataFrames:

- **Config**: SchemaConfig for defining custom types and validation rules

Example:
    from mountainash.schema import SchemaConfig

    # Define schema with custom types
    schema = SchemaConfig(
        columns={
            "id": {"cast": "integer"},
            "created_at": {"rename": "date"},
        }
    )

    # Apply schema transformation
    result = schema.apply(df)
"""

# Re-export from config module
from mountainash.schema.config import (
    SchemaConfig,
    ValidationIssue,
    ValidationResult,
    apply_column_config,
    create_rename_config,
    create_cast_config,
    init_column_config,
    UniversalType,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    FieldConstraints,
    SchemaField,
    TableSchema,
    TypeConverter,
    TypeConverterSpec,
    CustomTypeRegistry,
)

__all__ = [
    # Config exports
    "SchemaConfig",
    "ValidationIssue",
    "ValidationResult",
    "apply_column_config",
    "create_rename_config",
    "create_cast_config",
    "init_column_config",
    "UniversalType",
    "normalize_type",
    "is_safe_cast",
    "get_polars_type",
    "FieldConstraints",
    "SchemaField",
    "TableSchema",
    "TypeConverter",
    "TypeConverterSpec",
    "CustomTypeRegistry",
]
