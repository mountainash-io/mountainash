"""
TableSchema Extractors - Extract TableSchema from Various Sources

Provides functions to extract TableSchema from:
- Python dataclasses
- Pydantic models (v1 and v2)
- DataFrames (Polars, pandas, PyArrow, Ibis, Narwhals)

All extractors use lazy imports to avoid loading unnecessary dependencies.
"""
from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union, get_args, get_origin, get_type_hints
import enum
import logging
import types

from mountainash.core.dtypes import (
    ArrayDtype, MountainashDtype, NativeDtype, SchemaTypeStatus, StructDtype,
    TypeTarget, portable_evidence, registry,
)
from mountainash.core.types import detect_schema_carrier

from .spec import TableSchema, FieldDefinition, FieldConstraints
from .source_shape import extract_source_shapes
from .universal_types import UniversalType, from_canonical

if TYPE_CHECKING:
    from pydantic import BaseModel
    from .source_shape import SourceShape

logger = logging.getLogger(__name__)




def _universal_from_native(native: Any, target: TypeTarget) -> UniversalType:
    """native dtype -> canon -> UniversalType (explicit target, no detection)."""
    canon = registry.from_native(native, target=target)
    universal, _fmt = from_canonical(canon)
    return universal


def _definition_from_source_shape(
    shape: "SourceShape", *, preserve_backend_types: bool,
) -> FieldDefinition:
    """Translate observed evidence, without inventing conformance constraints."""
    canonical = shape.canonical_type
    universal = from_canonical(canonical)[0] if canonical is not None else UniversalType.ANY
    native = shape.native_dtype if preserve_backend_types else None
    detail = shape.decimal or shape.detailed_dtype
    dtype = portable_evidence(canonical if isinstance(detail, NativeDtype) else detail or canonical)
    unknown = SchemaTypeStatus.UNKNOWN

    if canonical is MountainashDtype.STRUCT:
        members = (
            unknown if not isinstance(dtype, StructDtype) or dtype.fields is unknown
            else {
                name: _definition_from_source_shape(
                    child, preserve_backend_types=preserve_backend_types,
                )
                for name, child in shape.struct_fields
            }
        )
        return FieldDefinition(type=UniversalType.OBJECT, fields=members, backend_type=native)
    if canonical is MountainashDtype.LIST:
        item = shape.item_shape
        dimensions = dtype.dimensions if isinstance(dtype, ArrayDtype) else None
        # ArrayDtype stores all fixed axes together; SourceShape exposes each axis.
        if isinstance(dimensions, tuple):
            for _ in dimensions[1:]:
                item = item.item_shape if item is not None else None
        element = (
            unknown if item is None
            else _definition_from_source_shape(
                item, preserve_backend_types=preserve_backend_types,
            )
        )
        return FieldDefinition(
            type=UniversalType.ARRAY, element=element,
            dimensions=dimensions, backend_type=native,
        )
    if canonical in (MountainashDtype.JSON, MountainashDtype.DURATION):
        universal = UniversalType.ANY
    return FieldDefinition(type=universal, dtype=dtype, backend_type=native)


def _table_schema_of(
    definitions: Dict[str, FieldDefinition], metadata: Dict[str, Any]
) -> TableSchema:
    return TableSchema(
        fields=definitions,
        title=metadata.get("title"),
        description=metadata.get("description"),
        primary_key=metadata.get("primary_key"),
    )

# ============================================================================
# Schema Caching (for dataclass and Pydantic models)
# ============================================================================

# Cache for derived schemas: Type -> TableSchema. Entries are private; callers
# always receive an independent copy so a mutated schema never leaks back.
# Classes don't change at runtime, so simple caching without invalidation
_DATACLASS_SCHEMA_CACHE: Dict[Type, TableSchema] = {}
_PYDANTIC_SCHEMA_CACHE: Dict[Type, TableSchema] = {}


# ============================================================================
# Dataclass Extraction
# ============================================================================

def extract_from_dataclass(
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
        >>> schema = extract_from_dataclass(User)
        >>> schema.field_names
        ['id', 'name', 'email']
    """
    # Check if it's a dataclass
    if not hasattr(dataclass_type, '__dataclass_fields__'):
        raise ValueError(f"{dataclass_type} is not a dataclass")

    fields: Dict[str, FieldDefinition] = {}

    # Resolve postponed (string) annotations once per class. Under
    # `from __future__ import annotations`, dataclasses.fields()[i].type is
    # an unresolved string; get_type_hints() evaluates it in the class's
    # module namespace, returning real type/typing objects for every field
    # (also a no-op for classes that never used postponed annotations).
    resolved_hints = get_type_hints(dataclass_type, include_extras=True)

    for field_name, field_info in dataclass_type.__dataclass_fields__.items():
        # Get the resolved type annotation, falling back to the raw
        # Field.type if get_type_hints somehow omitted this field.
        field_type = resolved_hints.get(field_name, field_info.type)

        # Handle Optional types: typing.Union[X, None] (Optional[X]) and,
        # under PEP 604, X | None (types.UnionType — a distinct object with
        # no __origin__ pointing at typing.Union).
        is_optional = False
        origin = getattr(field_type, '__origin__', None)
        if origin is Union or isinstance(field_type, types.UnionType):
            args = getattr(field_type, '__args__', ())
            if type(None) in args:
                is_optional = True
                # Only a singleton nullable union is concrete source evidence.
                non_null = tuple(arg for arg in args if arg is not type(None))
                if len(non_null) == 1:
                    field_type = non_null[0]

        # Enum fields resolve via their native value mixin — StrEnum -> str,
        # IntEnum -> int, etc. — rather than falling through to ANY.
        if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
            for native_base in (str, int, float, bool, bytes):
                if issubclass(field_type, native_base):
                    field_type = native_base
                    break

        # Convert Python type to universal type
        try:
            universal_type = _universal_from_native(field_type, TypeTarget.PYTHON)
        except Exception as e:
            logger.warning(f"Could not normalize type {field_type} for field {field_name}: {e}")
            universal_type = UniversalType.ANY

        # Build constraints
        constraints = None
        if preserve_optional and not is_optional:
            # Field is required if not Optional and has no default
            has_default = field_info.default is not field_info.default_factory
            if not has_default and field_info.default_factory is not field_info.default_factory:
                constraints = FieldConstraints(required=True)

        # Create the unnamed definition; the mapping key names it
        fields[field_name] = FieldDefinition(type=universal_type, constraints=constraints)

    return TableSchema(
        fields=fields,
        title=metadata.get("title", dataclass_type.__name__),
        description=metadata.get("description", dataclass_type.__doc__),
        primary_key=metadata.get("primary_key"),
    )


# Alias for backward compatibility
from_dataclass = extract_from_dataclass


# ============================================================================
# Pydantic Extraction
# ============================================================================

def extract_from_pydantic(
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
        >>> schema = extract_from_pydantic(User)
    """
    try:
        import pydantic
    except ImportError:
        raise ImportError("pydantic is required for extract_from_pydantic()")

    # Detect Pydantic version
    pydantic_version = int(pydantic.__version__.split('.')[0])

    if pydantic_version >= 2:
        return _from_pydantic_v2(model_type, **metadata)
    else:
        return _from_pydantic_v1(model_type, **metadata)


# Alias for backward compatibility
from_pydantic = extract_from_pydantic


def _from_pydantic_v1(model_type: Type['BaseModel'], **metadata) -> TableSchema:
    """Extract schema from Pydantic v1 model."""
    fields: Dict[str, FieldDefinition] = {}

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

            universal_type = _universal_from_native(python_type, TypeTarget.PYTHON)
        except Exception as e:
            logger.warning(f"Could not normalize type {field_type} for field {field_name}: {e}")
            universal_type = UniversalType.ANY

        # Build constraints from Pydantic validators
        constraints: Dict[str, Any] = {"required": not is_optional}

        # Extract numeric constraints
        if hasattr(field_info, 'field_info'):
            fi = field_info.field_info
            if hasattr(fi, 'gt') and fi.gt is not None:
                constraints["minimum"] = fi.gt
            elif hasattr(fi, 'ge') and fi.ge is not None:
                constraints["minimum"] = fi.ge

            if hasattr(fi, 'lt') and fi.lt is not None:
                constraints["maximum"] = fi.lt
            elif hasattr(fi, 'le') and fi.le is not None:
                constraints["maximum"] = fi.le

            # String constraints
            if hasattr(fi, 'min_length') and fi.min_length is not None:
                constraints["min_length"] = fi.min_length
            if hasattr(fi, 'max_length') and fi.max_length is not None:
                constraints["max_length"] = fi.max_length
            if hasattr(fi, 'regex') and fi.regex is not None:
                constraints["pattern"] = str(fi.regex)

        # Detect format from type
        format_hint = _detect_format_from_type(field_type)

        # Get description
        description = None
        if hasattr(field_info, 'field_info') and hasattr(field_info.field_info, 'description'):
            description = field_info.field_info.description

        fields[field_name] = FieldDefinition(
            type=universal_type,
            format=format_hint or "default",
            constraints=FieldConstraints(**constraints),
            description=description,
        )

    return TableSchema(
        fields=fields,
        title=metadata.get("title", model_type.__name__),
        description=metadata.get("description", model_type.__doc__),
        primary_key=metadata.get("primary_key"),
    )


def _from_pydantic_v2(model_type: Type['BaseModel'], **metadata) -> TableSchema:
    """Extract schema from Pydantic v2 model."""
    fields: Dict[str, FieldDefinition] = {}

    # Get model fields from Pydantic v2
    model_fields = model_type.model_fields

    for field_name, field_info in model_fields.items():
        # Get annotation (type)
        field_type = field_info.annotation
        # Nullability supplies the value type, not whether the field is required.
        if get_origin(field_type) in (Union, types.UnionType):
            members = get_args(field_type)
            non_null = tuple(member for member in members if member is not type(None))
            if type(None) in members and len(non_null) == 1:
                field_type = non_null[0]

        # Check if required
        is_optional = not field_info.is_required()

        # Convert to universal type
        try:
            universal_type = _universal_from_native(field_type, TypeTarget.PYTHON)
        except Exception as e:
            logger.warning(f"Could not normalize type {field_type} for field {field_name}: {e}")
            universal_type = UniversalType.ANY

        # Build constraints
        constraints: Dict[str, Any] = {"required": not is_optional}

        # Extract constraints from metadata
        if field_info.metadata:
            for constraint in field_info.metadata:
                # Pydantic v2 uses constraint objects
                if hasattr(constraint, 'gt'):
                    constraints["minimum"] = constraint.gt
                elif hasattr(constraint, 'ge'):
                    constraints["minimum"] = constraint.ge

                if hasattr(constraint, 'lt'):
                    constraints["maximum"] = constraint.lt
                elif hasattr(constraint, 'le'):
                    constraints["maximum"] = constraint.le

                if hasattr(constraint, 'min_length'):
                    constraints["min_length"] = constraint.min_length
                if hasattr(constraint, 'max_length'):
                    constraints["max_length"] = constraint.max_length
                if hasattr(constraint, 'pattern'):
                    constraints["pattern"] = constraint.pattern

        # Detect format
        format_hint = _detect_format_from_type(field_type)

        # Get description
        description = field_info.description

        fields[field_name] = FieldDefinition(
            type=universal_type,
            format=format_hint or "default",
            constraints=FieldConstraints(**constraints),
            description=description,
        )

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

def extract_from_dataframe(
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
        >>> schema = extract_from_dataframe(df)
        >>> schema.field_names
        ['id', 'name']
    """
    if detect_schema_carrier(df) is None:
        raise ValueError(f"Unsupported DataFrame type: {type(df).__module__}.{type(df).__name__}")
    fields = {
        name: _definition_from_source_shape(
            shape, preserve_backend_types=preserve_backend_types,
        )
        for name, shape in extract_source_shapes(df).items()
    }
    return _table_schema_of(fields, metadata)


# Alias for backward compatibility
from_dataframe = extract_from_dataframe






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
    return extract_from_dataframe(df, preserve_backend_types=include_backend_types)


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
    # Check cache first (cache entries are private; callers get independent copies)
    if use_cache and dataclass_type in _DATACLASS_SCHEMA_CACHE:
        logger.debug(f"Using cached schema for dataclass {dataclass_type.__name__}")
        return deepcopy(_DATACLASS_SCHEMA_CACHE[dataclass_type])

    # Extract schema
    schema = extract_from_dataclass(dataclass_type, preserve_optional=True)

    # Cache result
    if use_cache:
        _DATACLASS_SCHEMA_CACHE[dataclass_type] = deepcopy(schema)

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
    # Check cache first (cache entries are private; callers get independent copies)
    if use_cache and model_class in _PYDANTIC_SCHEMA_CACHE:
        logger.debug(f"Using cached schema for Pydantic model {model_class.__name__}")
        return deepcopy(_PYDANTIC_SCHEMA_CACHE[model_class])

    # Extract schema
    schema = extract_from_pydantic(model_class)

    # Cache result
    if use_cache:
        _PYDANTIC_SCHEMA_CACHE[model_class] = deepcopy(schema)

    return schema


# ============================================================================
# Helper Functions - Type Conversion
# ============================================================================



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
    return _universal_from_native(unwrapped_type, TypeTarget.PYTHON)


def python_type_to_universal(python_type: Type) -> str:
    """Universal type name for a Python annotation (public alias)."""
    return _python_type_to_universal(python_type)


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
    # Primary extraction functions
    "extract_from_dataclass",
    "extract_from_pydantic",
    "extract_from_dataframe",
    # Legacy aliases
    "from_dataclass",
    "from_pydantic",
    "from_dataframe",
    # Cast module integration functions (with caching)
    "extract_schema_from_dataframe",
    "extract_schema_from_dataclass",
    "extract_schema_from_pydantic",
]
