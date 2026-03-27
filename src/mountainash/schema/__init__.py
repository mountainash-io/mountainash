"""
mountainash-schema: Schema Management and Column Transformation

This package provides schema management, type conversion, and column transformation
capabilities for DataFrames:

- **Config**: SchemaConfig for defining custom types and validation rules
- **Transform**: Apply schema transformations across DataFrame backends
- **Column Mapper**: Column renaming, reordering, and expression-based transformations

Example:
    from mountainash.schema import SchemaConfig, SchemaTransformFactory

    # Define schema with custom types
    schema = SchemaConfig(
        columns={
            "id": {"dtype": "int64"},
            "created_at": {"dtype": "datetime", "format": "%Y-%m-%d"},
        }
    )

    # Apply schema transformation
    factory = SchemaTransformFactory()
    strategy = factory.get_strategy(df)
    df = strategy.transform(df, schema)
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

# Re-export from transform module (requires mountainash.dataframes infrastructure)
try:
    from mountainash.schema.transform import (
        SchemaTransformFactory,
        BaseSchemaTransformStrategy,
        SchemaTransformError,
    )
    _TRANSFORM_AVAILABLE = True
except ImportError:
    _TRANSFORM_AVAILABLE = False

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

if _TRANSFORM_AVAILABLE:
    __all__ += [
        "SchemaTransformFactory",
        "BaseSchemaTransformStrategy",
        "SchemaTransformError",
    ]
