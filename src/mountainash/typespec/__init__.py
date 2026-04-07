"""
mountainash.typespec — Universal type system foundation.

This package provides the type vocabulary that all schema and conformance
operations depend on.
"""
from __future__ import annotations

from mountainash.typespec.universal_types import (
    UniversalType,
    UNIVERSAL_TO_PANDAS,
    UNIVERSAL_TO_IBIS,
    POLARS_TO_UNIVERSAL,
    PANDAS_TO_UNIVERSAL,
    ARROW_TO_UNIVERSAL,
    IBIS_TO_UNIVERSAL,
    PYTHON_TO_UNIVERSAL,
    SAFE_CASTS,
    UNSAFE_CASTS,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    get_arrow_type,
    get_universal_to_backend_mapping,
    get_backend_to_universal_mapping,
)
from mountainash.typespec.type_bridge import (
    UNIVERSAL_TO_MOUNTAINASH,
    bridge_type,
)
from mountainash.typespec.spec import (
    FieldConstraints,
    ForeignKeyReference,
    ForeignKey,
    FieldSpec,
    TypeSpec,
    SpecDiff,
    compare_specs,
)
from mountainash.typespec.extraction import (
    extract_from_dataframe,
    extract_from_dataclass,
    extract_from_pydantic,
    extract_schema_from_dataframe,
    extract_schema_from_dataclass,
    extract_schema_from_pydantic,
    from_dataframe,
    from_dataclass,
    from_pydantic,
)
from mountainash.typespec.validation import (
    SchemaValidationError,
    validate_match,
    assert_match,
    validate_schema_match,
    assert_schema_match,
)
from mountainash.typespec.converters import (
    to_polars_schema,
    to_pandas_dtypes,
    to_arrow_schema,
    to_ibis_schema,
    convert_to_backend,
)
from mountainash.typespec.custom_types import (
    TypeConverter,
    NarwhalsConverter,
    TypeConverterSpec,
    CustomTypeRegistry,
)
from mountainash.typespec.datapackage import (
    TableDialect,
    DataResource,
    DataPackage,
)

__all__ = [
    # Universal type enum
    "UniversalType",

    # Forward mappings
    "UNIVERSAL_TO_PANDAS",
    "UNIVERSAL_TO_IBIS",

    # Reverse mappings
    "POLARS_TO_UNIVERSAL",
    "PANDAS_TO_UNIVERSAL",
    "ARROW_TO_UNIVERSAL",
    "IBIS_TO_UNIVERSAL",
    "PYTHON_TO_UNIVERSAL",

    # Safe casts
    "SAFE_CASTS",
    "UNSAFE_CASTS",

    # Utility functions
    "normalize_type",
    "is_safe_cast",
    "get_polars_type",
    "get_arrow_type",
    "get_universal_to_backend_mapping",
    "get_backend_to_universal_mapping",

    # Type bridge
    "UNIVERSAL_TO_MOUNTAINASH",
    "bridge_type",

    # Spec classes
    "FieldConstraints",
    "ForeignKeyReference",
    "ForeignKey",
    "FieldSpec",
    "TypeSpec",
    "SpecDiff",
    "compare_specs",

    # Extraction functions
    "extract_from_dataframe",
    "extract_from_dataclass",
    "extract_from_pydantic",
    "extract_schema_from_dataframe",
    "extract_schema_from_dataclass",
    "extract_schema_from_pydantic",
    "from_dataframe",
    "from_dataclass",
    "from_pydantic",

    # Validation
    "SchemaValidationError",
    "validate_match",
    "assert_match",
    "validate_schema_match",
    "assert_schema_match",

    # Converters
    "to_polars_schema",
    "to_pandas_dtypes",
    "to_arrow_schema",
    "to_ibis_schema",
    "convert_to_backend",

    # Custom types
    "TypeConverter",
    "NarwhalsConverter",
    "TypeConverterSpec",
    "CustomTypeRegistry",

    # Data Package
    "TableDialect",
    "DataResource",
    "DataPackage",
]
