# ==================== BACKEND-AGNOSTIC COLUMN TRANSFORMATION ====================
# DataFrame-independent column mapping, casting, and null handling
# Works with pandas, polars, ibis, pyarrow, and narwhals DataFrames

from .schema_config import (
    SchemaConfig,
    ValidationIssue,
    ValidationResult,
    apply_column_config,
    create_rename_config,
    create_cast_config,
    init_column_config
)

# Type system (centralized type mappings)
from .types import (
    UniversalType,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    get_arrow_type,
    UNIVERSAL_TO_PANDAS,
    UNIVERSAL_TO_IBIS,
    POLARS_TO_UNIVERSAL,
    PANDAS_TO_UNIVERSAL,
    ARROW_TO_UNIVERSAL,
    IBIS_TO_UNIVERSAL,
    PYTHON_TO_UNIVERSAL,
    SAFE_CASTS,
    UNSAFE_CASTS,
)

# Universal Schema (Frictionless Table Schema)
from .universal_schema import (
    FieldConstraints,
    SchemaField,
    TableSchema,
    SchemaDiff,
    compare_schemas,
)

# Schema Extractors (dataclass, Pydantic, DataFrames)
from .extractors import (
    from_dataclass,
    from_pydantic,
    from_dataframe,
    # Cast module integration (with caching)
    extract_schema_from_dataframe,
    extract_schema_from_dataclass,
    extract_schema_from_pydantic,
    build_schema_config_with_fuzzy_matching,
)

# Schema Converters (Universal → Backend)
from .converters import (
    to_polars_schema,
    to_pandas_dtypes,
    to_arrow_schema,
    to_ibis_schema,
    convert_to_backend,
)

# Schema Validators (Round-trip validation, schema matching)
from .validators import (
    SchemaValidationError,
    validate_round_trip,
    assert_round_trip,
    validate_schema_match,
    assert_schema_match,
    validate_transformation_config,
    assert_transformation_config,
)

# Custom Type Converters (Layer 2 - Semantic Converters)
from .custom_types import (
    TypeConverter,
    TypeConverterSpec,
    CustomTypeRegistry,
)


__all__ = [
    # Main configuration class
    'SchemaConfig',
    'ValidationIssue',
    'ValidationResult',

    # Public API functions
    'apply_column_config',
    'create_rename_config',
    'create_cast_config',
    'init_column_config',

    # Type system
    'UniversalType',
    'normalize_type',
    'is_safe_cast',
    'get_polars_type',
    'get_arrow_type',
    'UNIVERSAL_TO_PANDAS',
    'UNIVERSAL_TO_IBIS',
    'POLARS_TO_UNIVERSAL',
    'PANDAS_TO_UNIVERSAL',
    'ARROW_TO_UNIVERSAL',
    'IBIS_TO_UNIVERSAL',
    'PYTHON_TO_UNIVERSAL',
    'SAFE_CASTS',
    'UNSAFE_CASTS',

    # Universal Schema
    'FieldConstraints',
    'SchemaField',
    'TableSchema',
    'SchemaDiff',
    'compare_schemas',

    # Schema Extractors
    'from_dataclass',
    'from_pydantic',
    'from_dataframe',
    # Cast module integration extractors
    'extract_schema_from_dataframe',
    'extract_schema_from_dataclass',
    'extract_schema_from_pydantic',
    'build_schema_config_with_fuzzy_matching',

    # Schema Converters
    'to_polars_schema',
    'to_pandas_dtypes',
    'to_arrow_schema',
    'to_ibis_schema',
    'convert_to_backend',

    # Schema Validators
    'SchemaValidationError',
    'validate_round_trip',
    'assert_round_trip',
    'validate_schema_match',
    'assert_schema_match',
    'validate_transformation_config',
    'assert_transformation_config',

    # Custom Type Converters
    'TypeConverter',
    'TypeConverterSpec',
    'CustomTypeRegistry',
]
