"""
mountainash.typespec — Universal type system foundation.

This package provides the type vocabulary that all schema and conformance
operations depend on.
"""
from __future__ import annotations

from mountainash.typespec.universal_types import (
    UniversalType,
    to_canonical,
    from_canonical,
    parse_universal,
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
from mountainash.typespec.descriptor_context import (
    DescriptorKind,
    DescriptorResolver,
    DescriptorContext,
    build_descriptor_context,
    normalize_base_uri,
    normalize_document_uri,
    descriptor_cache_key,
    LocalDescriptorResolver,
    StorageDescriptorResolver,
)
from mountainash.typespec.frictionless_codec import DescriptorWriteMode
from mountainash.typespec.errors import (
    TypeSpecError,
    AmbiguousGeospatialTypeError,
    InvalidGeospatialFormatError,
    InvalidKeyShapeError,
    IncompatibleFieldPropertiesError,
    InvalidFieldMatchDeclaration,
)

__all__ = [
    # Universal type enum
    "UniversalType",

    # Boundary map (UniversalType <-> MountainashDtype)
    "to_canonical",
    "from_canonical",
    "parse_universal",

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
    "DescriptorWriteMode",
    # Descriptor context and resolution
    "DescriptorKind",
    "DescriptorResolver",
    "DescriptorContext",
    "build_descriptor_context",
    "normalize_base_uri",
    "normalize_document_uri",
    "descriptor_cache_key",
    "LocalDescriptorResolver",
    "StorageDescriptorResolver",

    # Errors
    "TypeSpecError",
    "AmbiguousGeospatialTypeError",
    "InvalidGeospatialFormatError",
    "InvalidKeyShapeError",
    "IncompatibleFieldPropertiesError",
    "InvalidFieldMatchDeclaration",
]
