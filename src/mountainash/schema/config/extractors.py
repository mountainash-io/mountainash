"""
Schema Extractors - Extract TableSchema from Various Sources

Provides functions to extract TableSchema from:
- Python dataclasses
- Pydantic models (v1 and v2)
- DataFrames (Polars, pandas, PyArrow, Ibis, Narwhals)

All extractors use lazy imports to avoid loading unnecessary dependencies.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union
import logging

from .universal_schema import TableSchema, SchemaField, FieldConstraints
from .types import normalize_type, PYTHON_TO_UNIVERSAL

if TYPE_CHECKING:
    import polars as pl
    import pandas as pd
    import pyarrow as pa
    import ibis
    from pydantic import BaseModel
    from .schema_config import SchemaConfig

logger = logging.getLogger(__name__)

# ============================================================================
# Schema Caching (for dataclass and Pydantic models)
# ============================================================================

# Cache for derived schemas: Type -> TableSchema
# Classes don't change at runtime, so simple caching without invalidation
_DATACLASS_SCHEMA_CACHE: Dict[Type, TableSchema] = {}
_PYDANTIC_SCHEMA_CACHE: Dict[Type, TableSchema] = {}


# ============================================================================
# Dataclass Extraction
# ============================================================================

def from_dataclass(
    dataclass_type: Type,
    preserve_optional: bool = True,
    **metadata
) -> TableSchema:
    """
    Extract TableSchema from a Python dataclass.

    Args:
        dataclass_type: Dataclass type (not an instance)
        preserve_optional: Mark Optional fields as not required (default: True)
        **metadata: Additional schema metadata (title, description, primary_key)

    Returns:
        TableSchema extracted from dataclass

    Raises:
        ValueError: If input is not a dataclass

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class User:
        ...     id: int
        ...     name: str
        ...     email: Optional[str] = None
        >>> schema = from_dataclass(User)
        >>> schema.field_names
        ['id', 'name', 'email']
    """
    # Check if it's a dataclass
    if not hasattr(dataclass_type, '__dataclass_fields__'):
        raise ValueError(f"{dataclass_type} is not a dataclass")

    fields = []

    for field_name, field_info in dataclass_type.__dataclass_fields__.items():
        # Get the type annotation
        field_type = field_info.type

        # Handle Optional types (Union[X, None])
        is_optional = False
        if hasattr(field_type, '__origin__'):
            # Handle Union, Optional, List, etc.
            origin = field_type.__origin__
            if origin is Union:
                # Check if it's Optional (Union[X, None])
                args = field_type.__args__
                if type(None) in args:
                    is_optional = True
                    # Get the non-None type
                    field_type = next(arg for arg in args if arg is not type(None))

        # Convert Python type to universal type
        try:
            universal_type = normalize_type(field_type, "python")
        except Exception as e:
            logger.warning(f"Could not normalize type {field_type} for field {field_name}: {e}")
            universal_type = "any"

        # Build constraints
        constraints = None
        if preserve_optional and not is_optional:
            # Field is required if not Optional and has no default
            has_default = field_info.default is not field_info.default_factory
            if not has_default and field_info.default_factory is not field_info.default_factory:
                constraints = FieldConstraints(required=True)

        # Create schema field
        schema_field = SchemaField(
            name=field_name,
            type=universal_type,
            constraints=constraints,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title", dataclass_type.__name__),
        description=metadata.get("description", dataclass_type.__doc__),
        primary_key=metadata.get("primary_key"),
    )


# ============================================================================
# Pydantic Extraction
# ============================================================================

def from_pydantic(
    model_type: Type['BaseModel'],
    **metadata
) -> TableSchema:
    """
    Extract TableSchema from a Pydantic model.

    Supports both Pydantic v1 and v2.

    Args:
        model_type: Pydantic model class (not an instance)
        **metadata: Additional schema metadata (title, description, primary_key)

    Returns:
        TableSchema extracted from Pydantic model

    Raises:
        ImportError: If Pydantic is not installed
        ValueError: If input is not a Pydantic model

    Example:
        >>> from pydantic import BaseModel, Field
        >>> class User(BaseModel):
        ...     id: int = Field(gt=0)
        ...     email: str = Field(pattern=r'^[^@]+@[^@]+$')
        >>> schema = from_pydantic(User)
    """
    try:
        import pydantic
    except ImportError:
        raise ImportError("pydantic is required for from_pydantic()")

    # Detect Pydantic version
    pydantic_version = int(pydantic.__version__.split('.')[0])

    if pydantic_version >= 2:
        return _from_pydantic_v2(model_type, **metadata)
    else:
        return _from_pydantic_v1(model_type, **metadata)


def _from_pydantic_v1(model_type: Type['BaseModel'], **metadata) -> TableSchema:
    """Extract schema from Pydantic v1 model."""
    fields = []

    for field_name, field_info in model_type.__fields__.items():
        # Get field type
        field_type = field_info.outer_type_

        # Handle Optional
        is_optional = not field_info.required

        # Convert to universal type
        try:
            # Try to get the Python type
            if hasattr(field_info, 'type_'):
                python_type = field_info.type_
            else:
                python_type = field_type

            universal_type = normalize_type(python_type, "python")
        except Exception as e:
            logger.warning(f"Could not normalize type {field_type} for field {field_name}: {e}")
            universal_type = "any"

        # Build constraints from Pydantic validators
        constraints = FieldConstraints(required=not is_optional)

        # Extract numeric constraints
        if hasattr(field_info, 'field_info'):
            fi = field_info.field_info
            if hasattr(fi, 'gt') and fi.gt is not None:
                constraints.minimum = fi.gt
            elif hasattr(fi, 'ge') and fi.ge is not None:
                constraints.minimum = fi.ge

            if hasattr(fi, 'lt') and fi.lt is not None:
                constraints.maximum = fi.lt
            elif hasattr(fi, 'le') and fi.le is not None:
                constraints.maximum = fi.le

            # String constraints
            if hasattr(fi, 'min_length') and fi.min_length is not None:
                constraints.min_length = fi.min_length
            if hasattr(fi, 'max_length') and fi.max_length is not None:
                constraints.max_length = fi.max_length
            if hasattr(fi, 'regex') and fi.regex is not None:
                constraints.pattern = str(fi.regex)

        # Detect format from type
        format_hint = _detect_format_from_type(field_type)

        # Get description
        description = None
        if hasattr(field_info, 'field_info') and hasattr(field_info.field_info, 'description'):
            description = field_info.field_info.description

        schema_field = SchemaField(
            name=field_name,
            type=universal_type,
            format=format_hint,
            constraints=constraints if constraints else None,
            description=description,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title", model_type.__name__),
        description=metadata.get("description", model_type.__doc__),
        primary_key=metadata.get("primary_key"),
    )


def _from_pydantic_v2(model_type: Type['BaseModel'], **metadata) -> TableSchema:
    """Extract schema from Pydantic v2 model."""
    fields = []

    # Get model fields from Pydantic v2
    model_fields = model_type.model_fields

    for field_name, field_info in model_fields.items():
        # Get annotation (type)
        field_type = field_info.annotation

        # Check if required
        is_optional = not field_info.is_required()

        # Convert to universal type
        try:
            universal_type = normalize_type(field_type, "python")
        except Exception as e:
            logger.warning(f"Could not normalize type {field_type} for field {field_name}: {e}")
            universal_type = "any"

        # Build constraints
        constraints = FieldConstraints(required=not is_optional)

        # Extract constraints from metadata
        if field_info.metadata:
            for constraint in field_info.metadata:
                # Pydantic v2 uses constraint objects
                if hasattr(constraint, 'gt'):
                    constraints.minimum = constraint.gt
                elif hasattr(constraint, 'ge'):
                    constraints.minimum = constraint.ge

                if hasattr(constraint, 'lt'):
                    constraints.maximum = constraint.lt
                elif hasattr(constraint, 'le'):
                    constraints.maximum = constraint.le

                if hasattr(constraint, 'min_length'):
                    constraints.min_length = constraint.min_length
                if hasattr(constraint, 'max_length'):
                    constraints.max_length = constraint.max_length
                if hasattr(constraint, 'pattern'):
                    constraints.pattern = constraint.pattern

        # Detect format
        format_hint = _detect_format_from_type(field_type)

        # Get description
        description = field_info.description

        schema_field = SchemaField(
            name=field_name,
            type=universal_type,
            format=format_hint,
            constraints=constraints if constraints else None,
            description=description,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title", model_type.__name__),
        description=metadata.get("description", model_type.__doc__),
        primary_key=metadata.get("primary_key"),
    )


def _detect_format_from_type(field_type: Any) -> Optional[str]:
    """Detect format hint from Pydantic special types."""
    type_name = getattr(field_type, '__name__', str(field_type))

    # Common Pydantic types
    if 'email' in type_name.lower():
        return "email"
    elif 'url' in type_name.lower() or 'uri' in type_name.lower():
        return "uri"
    elif 'uuid' in type_name.lower():
        return "uuid"

    return None


# ============================================================================
# DataFrame Extraction
# ============================================================================

def from_dataframe(
    df: Any,
    preserve_backend_types: bool = True,
    **metadata
) -> TableSchema:
    """
    Extract TableSchema from any DataFrame backend.

    Automatically detects backend and extracts schema with type information.

    Supported backends:
    - Polars (DataFrame, LazyFrame)
    - pandas (DataFrame)
    - PyArrow (Table)
    - Ibis (Table)
    - Narwhals (DataFrame, LazyFrame)

    Args:
        df: DataFrame from any supported backend
        preserve_backend_types: Store original backend-specific types (default: True)
        **metadata: Additional schema metadata (title, description, primary_key)

    Returns:
        TableSchema extracted from DataFrame

    Example:
        >>> import polars as pl
        >>> df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> schema = from_dataframe(df)
        >>> schema.field_names
        ['id', 'name']
    """
    # Detect backend
    df_module = type(df).__module__
    df_class = type(df).__name__

    if df_module.startswith('polars'):
        return _from_polars(df, preserve_backend_types, **metadata)
    elif df_module.startswith('pandas'):
        return _from_pandas(df, preserve_backend_types, **metadata)
    elif df_module.startswith('pyarrow'):
        return _from_pyarrow(df, preserve_backend_types, **metadata)
    elif df_module.startswith('ibis'):
        return _from_ibis(df, preserve_backend_types, **metadata)
    elif df_module.startswith('narwhals'):
        return _from_narwhals(df, preserve_backend_types, **metadata)
    else:
        raise ValueError(
            f"Unsupported DataFrame type: {df_module}.{df_class}. "
            f"Supported: Polars, pandas, PyArrow, Ibis, Narwhals"
        )


def _from_polars(df: 'pl.DataFrame', preserve_backend_types: bool, **metadata) -> TableSchema:
    """Extract schema from Polars DataFrame or LazyFrame."""
    from mountainash.core.lazy_imports import import_polars
    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required")

    fields = []

    # Get schema dict {name: DataType}
    schema_dict = df.schema

    for col_name, dtype in schema_dict.items():
        # Get backend type name
        backend_type_str = str(dtype)

        # Convert to universal type
        universal_type = normalize_type(backend_type_str, "polars")

        schema_field = SchemaField(
            name=col_name,
            type=universal_type,
            backend_type=backend_type_str if preserve_backend_types else None,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title"),
        description=metadata.get("description"),
        primary_key=metadata.get("primary_key"),
    )


def _from_pandas(df: 'pd.DataFrame', preserve_backend_types: bool, **metadata) -> TableSchema:
    """Extract schema from pandas DataFrame."""
    from mountainash.core.lazy_imports import import_pandas
    pd = import_pandas()
    if pd is None:
        raise ImportError("pandas is required")

    fields = []

    for col_name in df.columns:
        dtype = df[col_name].dtype

        # Get backend type name
        backend_type_str = str(dtype)

        # Convert to universal type
        universal_type = normalize_type(backend_type_str, "pandas")

        schema_field = SchemaField(
            name=col_name,
            type=universal_type,
            backend_type=backend_type_str if preserve_backend_types else None,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title"),
        description=metadata.get("description"),
        primary_key=metadata.get("primary_key"),
    )


def _from_pyarrow(table: 'pa.Table', preserve_backend_types: bool, **metadata) -> TableSchema:
    """Extract schema from PyArrow Table."""
    from mountainash.core.lazy_imports import import_pyarrow
    pa = import_pyarrow()
    if pa is None:
        raise ImportError("pyarrow is required")

    fields = []

    for field in table.schema:
        # Get backend type
        backend_type = field.type

        # Convert to string for normalization
        backend_type_str = str(backend_type)

        # Convert to universal type
        universal_type = normalize_type(backend_type_str, "arrow")

        schema_field = SchemaField(
            name=field.name,
            type=universal_type,
            backend_type=backend_type_str if preserve_backend_types else None,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title"),
        description=metadata.get("description"),
        primary_key=metadata.get("primary_key"),
    )


def _from_ibis(table: 'ibis.Table', preserve_backend_types: bool, **metadata) -> TableSchema:
    """Extract schema from Ibis Table."""
    fields = []

    # Get Ibis schema
    schema = table.schema()

    for field_name in schema.names:
        # Get field type
        field_type = schema[field_name]

        # Convert to string
        backend_type_str = str(field_type)

        # Convert to universal type
        universal_type = normalize_type(backend_type_str, "ibis")

        schema_field = SchemaField(
            name=field_name,
            type=universal_type,
            backend_type=backend_type_str if preserve_backend_types else None,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title"),
        description=metadata.get("description"),
        primary_key=metadata.get("primary_key"),
    )


def _from_narwhals(df: Any, preserve_backend_types: bool, **metadata) -> TableSchema:
    """Extract schema from Narwhals DataFrame."""
    from mountainash.core.lazy_imports import import_narwhals
    nw = import_narwhals()
    if nw is None:
        raise ImportError("narwhals is required")

    fields = []

    # Narwhals provides a unified schema API
    schema_dict = df.schema

    for col_name, dtype in schema_dict.items():
        # Get backend type
        backend_type_str = str(dtype)

        # Narwhals uses Polars-like types, so use polars normalization
        universal_type = normalize_type(backend_type_str, "polars")

        schema_field = SchemaField(
            name=col_name,
            type=universal_type,
            backend_type=backend_type_str if preserve_backend_types else None,
        )
        fields.append(schema_field)

    return TableSchema(
        fields=fields,
        title=metadata.get("title"),
        description=metadata.get("description"),
        primary_key=metadata.get("primary_key"),
    )


# ============================================================================
# Cast Module Integration - Auto-Derivation Functions with Caching
# ============================================================================

def extract_schema_from_dataframe(
    df: Any,
    include_backend_types: bool = False
) -> TableSchema:
    """
    Auto-derive TableSchema from DataFrame.

    Extracts column names and universal types from any supported DataFrame backend.
    This is the primary function for cast module integration.

    Args:
        df: Any supported DataFrame (pandas, Polars, Ibis, PyArrow, Narwhals)
        include_backend_types: Store native backend types in backend_type field

    Returns:
        TableSchema matching DataFrame structure

    Example:
        >>> import polars as pl
        >>> df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
        >>> schema = extract_schema_from_dataframe(df)
        >>> schema.field_names
        ['id', 'name']
    """
    return from_dataframe(df, preserve_backend_types=include_backend_types)


def extract_schema_from_dataclass(
    dataclass_type: Type,
    use_cache: bool = True
) -> TableSchema:
    """
    Derive TableSchema from dataclass definition with caching.

    Extracts field names and types from dataclass field definitions.
    Results are cached by class type for performance.

    Args:
        dataclass_type: Dataclass type (not an instance)
        use_cache: Use cached schema if available (default: True)

    Returns:
        TableSchema matching dataclass structure

    Raises:
        ValueError: If not a dataclass

    Example:
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class User:
        ...     id: int
        ...     name: str
        >>> schema = extract_schema_from_dataclass(User)
        >>> schema.field_names
        ['id', 'name']
    """
    # Check cache first
    if use_cache and dataclass_type in _DATACLASS_SCHEMA_CACHE:
        logger.debug(f"Using cached schema for dataclass {dataclass_type.__name__}")
        return _DATACLASS_SCHEMA_CACHE[dataclass_type]

    # Extract schema
    schema = from_dataclass(dataclass_type, preserve_optional=True)

    # Cache result
    if use_cache:
        _DATACLASS_SCHEMA_CACHE[dataclass_type] = schema

    return schema


def extract_schema_from_pydantic(
    model_class: Type,
    use_cache: bool = True
) -> TableSchema:
    """
    Derive TableSchema from Pydantic model with caching.

    Supports both Pydantic v1 and v2.
    Results are cached by class type for performance.

    Args:
        model_class: Pydantic model class (not an instance)
        use_cache: Use cached schema if available (default: True)

    Returns:
        TableSchema matching model structure

    Raises:
        ValueError: If not a Pydantic model
        ImportError: If Pydantic is not installed

    Example:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     id: int
        ...     name: str
        >>> schema = extract_schema_from_pydantic(User)
        >>> schema.field_names
        ['id', 'name']
    """
    # Check cache first
    if use_cache and model_class in _PYDANTIC_SCHEMA_CACHE:
        logger.debug(f"Using cached schema for Pydantic model {model_class.__name__}")
        return _PYDANTIC_SCHEMA_CACHE[model_class]

    # Extract schema
    schema = from_pydantic(model_class)

    # Cache result
    if use_cache:
        _PYDANTIC_SCHEMA_CACHE[model_class] = schema

    return schema


def build_schema_config_with_fuzzy_matching(
    source_schema: TableSchema,
    target_schema: TableSchema,
    fuzzy_match_threshold: float = 0.6,
    strict: bool = False
) -> 'SchemaConfig':
    """
    Build SchemaConfig from source and target schemas with fuzzy matching.

    Uses fuzzy string matching to automatically map columns between schemas
    and generates transformation rules based on schema differences.

    Args:
        source_schema: Schema describing input DataFrame
        target_schema: Schema describing desired output
        fuzzy_match_threshold: Minimum similarity ratio for fuzzy matching (0.0-1.0)
        strict: Strict mode - fail fast on validation errors

    Returns:
        SchemaConfig with auto-generated column mappings

    Example:
        >>> source = TableSchema.from_simple_dict({
        ...     "user_id": "integer",
        ...     "user_name": "string"
        ... })
        >>> target = TableSchema.from_simple_dict({
        ...     "id": "integer",
        ...     "name": "string"
        ... })
        >>> config = build_schema_config_with_fuzzy_matching(source, target)
        # Auto-generates: user_id->id, user_name->name
    """
    # Import here to avoid circular dependency
    from .schema_config import SchemaConfig

    # Use existing from_schemas method which already has fuzzy matching
    config = SchemaConfig.from_schemas(
        source_schema=source_schema,
        target_schema=target_schema,
        fuzzy_match_threshold=fuzzy_match_threshold,
        auto_cast=True,
        keep_unmapped_source=False
    )

    # Set strict mode
    config.strict = strict

    return config


# ============================================================================
# Helper Functions - Type Conversion
# ============================================================================

def _backend_type_to_universal(backend_type: Any, backend: str) -> str:
    """
    Convert backend-specific type to universal type name.

    Args:
        backend_type: Type from DataFrame backend (e.g., pl.Int64, np.int64)
        backend: Backend name ('polars', 'pandas', 'arrow', 'ibis')

    Returns:
        Universal type name ('integer', 'string', 'number', 'boolean', 'date', 'datetime')

    Example:
        >>> _backend_type_to_universal('Int64', 'polars')
        'integer'
        >>> _backend_type_to_universal('float64', 'pandas')
        'number'
    """
    backend_type_str = str(backend_type)
    return normalize_type(backend_type_str, backend)


def _python_type_to_universal(python_type: Type) -> str:
    """
    Convert Python type to universal type name.

    Handles Optional types by unwrapping them.

    Args:
        python_type: Python type (int, str, float, bool, datetime.date, etc.)

    Returns:
        Universal type name ('integer', 'string', 'number', 'boolean', 'date', 'datetime')

    Example:
        >>> _python_type_to_universal(int)
        'integer'
        >>> _python_type_to_universal(Optional[str])
        'string'
    """
    # Unwrap Optional if present
    unwrapped_type = _unwrap_optional(python_type)
    return normalize_type(unwrapped_type, "python")


def _unwrap_optional(type_hint: Any) -> Any:
    """
    Unwrap Optional[T] to get the inner type T.

    Args:
        type_hint: Type hint (may be Optional[T] or just T)

    Returns:
        Unwrapped type (T)

    Example:
        >>> _unwrap_optional(Optional[str])
        <class 'str'>
        >>> _unwrap_optional(int)
        <class 'int'>
    """
    # Check if it's a Union type (Optional is Union[T, None])
    if hasattr(type_hint, '__origin__'):
        origin = type_hint.__origin__
        if origin is Union:
            # Get args and filter out NoneType
            args = type_hint.__args__
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                # Return the first non-None type
                return non_none_types[0]

    # Not Optional, return as-is
    return type_hint


__all__ = [
    # Legacy extraction functions
    "from_dataclass",
    "from_pydantic",
    "from_dataframe",
    # Cast module integration functions (with caching)
    "extract_schema_from_dataframe",
    "extract_schema_from_dataclass",
    "extract_schema_from_pydantic",
    "build_schema_config_with_fuzzy_matching",
]
