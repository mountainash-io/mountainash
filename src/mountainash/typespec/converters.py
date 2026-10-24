"""
Shared field-type resolution and the public native schema converters.

Resolution (``resolve_field_canonical`` / ``resolve_field_type``) interprets an
immutable ``FieldDefinition`` against optional source evidence and a type
target, returning an effective dtype value. It never copies or mutates the
declaration. Native construction belongs to the registered native schema
adapters (``typespec/native_schema.py``); the ``to_*_schema`` functions here
are convenience projections over them.
"""
from __future__ import annotations

import dataclasses
import warnings
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Dict

from mountainash.core.dtypes import (
    ArrayDtype,
    DurationDtype,
    ListDtype,
    NativeDtype,
    InvalidBackendTypeError,
    MountainashDtype,
    SchemaTypeStatus,
    StructDtype,
    TimeDtype,
    TimestampDtype,
    TypeTarget,
    UnknownDtypeError,
    resolve_dtype_parameters,
    dtype_family,
    portable_evidence,
    registry,
)
from mountainash.core.dtypes.errors import DtypeMappingError
from mountainash.typespec.errors import InvalidGeospatialFormatError
from mountainash.typespec.universal_types import UniversalType, parse_universal, to_canonical

if TYPE_CHECKING:
    import pyarrow as pa

    from mountainash.core.dtypes.protocols import ResolvedType
    from mountainash.typespec.protocols import DeclarationPath
    from mountainash.typespec.source_shape import SourceShape
    from mountainash.typespec.spec import FieldDefinition, TableSchema

UNKNOWN = SchemaTypeStatus.UNKNOWN
UNCONSTRAINED = SchemaTypeStatus.UNCONSTRAINED


def format_declaration_path(path: "DeclarationPath") -> str:
    """Presentation of a declaration path; resolution never splits this string.

    A literal member name containing a dot is quoted so it cannot be mistaken
    for nested members; ``[]`` marks a collection-element scope.
    """
    if not path:
        return "<field>"
    parts: list[str] = []
    for segment in path:
        if segment is None:
            if parts:
                parts[-1] += "[]"
            else:
                parts.append("[]")
        else:
            parts.append(repr(segment) if "." in segment else segment)
    return ".".join(parts)


# ============================================================================
# Geospatial field-aware resolution (spec §8.3)
# ============================================================================

_GEOPOINT_FORMAT_CANONICAL: dict[str, MountainashDtype] = {
    "default": MountainashDtype.STRING,
    "array": MountainashDtype.LIST,
    "object": MountainashDtype.STRUCT,
}
_GEOJSON_FORMATS: frozenset[str] = frozenset({"default", "topojson"})


def resolve_field_canonical(
    definition: "FieldDefinition", *, path: "DeclarationPath" = (),
) -> "ResolvedType":
    """Resolve a definition's canonical dtype, target-independent.

    Field context (``format``) is needed for the geospatial types that
    ``to_canonical`` cannot resolve alone: GEOPOINT is a lexical string,
    two-element list or struct by format; GEOJSON is always canonical JSON.
    A declaration with no type constraint is ``UNCONSTRAINED``; an explicitly
    unknown dtype stays ``UNKNOWN``.
    """
    if definition.dtype is not None:
        return definition.dtype
    broad = _resolve_broad_field_canonical(definition, path)
    return UNCONSTRAINED if broad is None else broad


def _resolve_broad_field_canonical(
    definition: "FieldDefinition", path: "DeclarationPath" = (),
) -> Any:
    """Resolve authored broad semantics independently of precise refinements."""
    if definition.type is None:
        return None
    fmt = definition.format
    if definition.type is UniversalType.GEOPOINT:
        if not isinstance(fmt, str) or fmt not in _GEOPOINT_FORMAT_CANONICAL:
            raise InvalidGeospatialFormatError(
                format_declaration_path(path), UniversalType.GEOPOINT, fmt,
                sorted(_GEOPOINT_FORMAT_CANONICAL),
            )
        return _GEOPOINT_FORMAT_CANONICAL[fmt]
    if definition.type is UniversalType.GEOJSON:
        if not isinstance(fmt, str) or fmt not in _GEOJSON_FORMATS:
            raise InvalidGeospatialFormatError(
                format_declaration_path(path), UniversalType.GEOJSON, fmt,
                sorted(_GEOJSON_FORMATS),
            )
        return MountainashDtype.JSON
    if definition.type is UniversalType.STRING and definition.format == "binary":
        return MountainashDtype.BINARY
    return to_canonical(definition.type)


# ============================================================================
# Shared target resolution
# ============================================================================
def _execution_type_target(family: Any) -> TypeTarget | None:
    """Translate an execution family, not a dataframe carrier, to its dtype domain."""
    if family is None:
        return None
    if family.value in ("pandas", "pyarrow", "narwhals"):
        return TypeTarget.NARWHALS
    return TypeTarget(family.value)


def _check_native_target(native: NativeDtype, target: TypeTarget, path: "DeclarationPath") -> None:
    if native.target is not target:
        raise DtypeMappingError(
            f"field {format_declaration_path(path)!r}: native override belongs to "
            f"{native.target}, not {target}"
        )


def resolve_field_type(
    definition: "FieldDefinition",
    *,
    source: "SourceShape | None",
    target: TypeTarget,
    path: "DeclarationPath",
    emit_warning: bool = True,
) -> "ResolvedType":
    """Resolve one declaration to its effective type for ``target``.

    Precedence: a native override (whole-dtype refinement or ``backend_type``)
    wins; otherwise the composed canonical type, with unspecified parameters
    filled from ``source`` evidence. Members and elements resolve recursively
    under extended ``path`` segments. The definition is never changed and
    nothing is cached; source UNKNOWN stays a legitimate result.
    """
    declared = resolve_field_canonical(definition, path=path)
    if declared is UNKNOWN:
        broad = _resolve_broad_field_canonical(definition, path)
        declared = UNCONSTRAINED if broad is None else broad
    dtype_native = getattr(definition.dtype, "native", None)
    override = definition.backend_type
    no_override = override is None or (isinstance(override, str) and not override)
    if isinstance(dtype_native, NativeDtype) and no_override:
        _check_native_target(dtype_native, target, path)
        return dtype_native
    if no_override:
        composed = _compose(definition, declared, target, path, emit_warning)
        return resolve_dtype_parameters(composed, _source_detail_for_target(source, target))
    if isinstance(override, NativeDtype):
        _check_native_target(override, target, path)
        effective = override
    else:
        native = registry.parse_type_string(override, target)
        if native is None:
            raise InvalidBackendTypeError(format_declaration_path(path), override, target)
        effective = NativeDtype(value=native, target=target)
    if definition.dtype is not None and emit_warning:
        _warn_on_unverified_override(declared, effective, target, path)
    return effective


def _inherit_source_detail(observed: Any, counterpart: Any, target: TypeTarget) -> Any:
    """Inherited detail may retain native evidence only in its selected domain."""
    if isinstance(observed, NativeDtype):
        return observed if observed.target is target else portable_evidence(counterpart)
    if isinstance(observed, (ListDtype, ArrayDtype)):
        return dataclasses.replace(
            observed, native=None,
            element=_inherit_source_detail(observed.element, getattr(counterpart, "element", UNKNOWN), target),
        )
    if isinstance(observed, StructDtype) and observed.fields is not UNKNOWN:
        fields = getattr(counterpart, "fields", UNKNOWN)
        members = {} if fields is UNKNOWN else dict(fields)
        return dataclasses.replace(observed, native=None, fields=tuple(
            (name, _inherit_source_detail(child, members.get(name, UNKNOWN), target))
            for name, child in observed.fields
        ))
    return portable_evidence(observed)


def _source_detail_for_target(source: "SourceShape | None", target: TypeTarget) -> Any:
    if source is None:
        return UNKNOWN
    native = source.native_dtype
    counterpart = (
        registry.from_native(native.value, target)
        if native is not None and native.target is target else UNKNOWN
    )
    return _inherit_source_detail(source.detailed_dtype, counterpart, target)


def _combine_type_matches(results):
    result = True
    for match in results:
        if match is False:
            return False
        if match is UNKNOWN:
            result = UNKNOWN
    return result


def _compare_type_parameters(expected: Any, actual: Any):
    if expected is UNKNOWN or expected is UNCONSTRAINED:
        return True
    if actual is UNKNOWN:
        return UNKNOWN
    if isinstance(expected, TimestampDtype) and expected.timezone_aware is True and expected.timezone is None:
        expected = dataclasses.replace(expected, timezone="UTC")
    if isinstance(actual, TimestampDtype) and actual.timezone_aware is True and actual.timezone is None:
        actual = dataclasses.replace(actual, timezone="UTC")
    if type(expected) is type(actual) and dataclasses.is_dataclass(expected):
        return _combine_type_matches(
            _compare_type_parameters(getattr(expected, field.name), getattr(actual, field.name))
            for field in dataclasses.fields(expected) if field.name != "native"
        )
    if isinstance(expected, tuple) and isinstance(actual, tuple):
        if len(expected) != len(actual):
            return False
        return _combine_type_matches(
            _compare_type_parameters(left, right) for left, right in zip(expected, actual)
        )
    return expected == actual


def compare_resolved_type(expected: "ResolvedType", source: "SourceShape | None"):
    """Compare intent with observed metadata: True, False, or UNKNOWN.

    Unknown requirements constrain nothing; unknown evidence proves nothing.
    Native overrides use matching-domain evidence at their own nesting level.
    Neither side is reconstructed as a native cast merely to compare types.
    """
    if expected is UNKNOWN or expected is UNCONSTRAINED:
        return True
    if source is None:
        return UNKNOWN
    native = expected if isinstance(expected, NativeDtype) else getattr(expected, "native", None)
    if native is not None:
        observed = source.native_dtype
        if observed is None or observed.target is not native.target:
            return UNKNOWN
        return registry.types_equal(native.value, observed.value, native.target)
    actual = source.decimal or source.detailed_dtype or source.canonical_type
    if isinstance(actual, NativeDtype):
        actual = source.canonical_type
    actual = portable_evidence(actual)
    if actual is UNKNOWN:
        return UNKNOWN
    expected = resolve_dtype_parameters(expected, actual)
    if isinstance(expected, MountainashDtype):
        return expected is dtype_family(actual)
    if isinstance(actual, MountainashDtype):
        return UNKNOWN if dtype_family(expected) is actual else False
    if isinstance(expected, (ListDtype, ArrayDtype, StructDtype)):
        if type(expected) is not type(actual):
            return False
        if isinstance(expected, StructDtype):
            if expected.fields is UNKNOWN:
                return True
            if actual.fields is UNKNOWN:
                return UNKNOWN
            if tuple(name for name, _ in expected.fields) != tuple(name for name, _ in actual.fields):
                return False
            members = dict(source.struct_fields)
            return _combine_type_matches(
                compare_resolved_type(child, members.get(name)) for name, child in expected.fields
            )
        item = source.item_shape
        dimensions_match = True
        if isinstance(expected, ArrayDtype):
            dimensions_match = _compare_type_parameters(expected.dimensions, actual.dimensions)
            if isinstance(actual.dimensions, tuple):
                for _ in actual.dimensions[1:]:
                    item = item.item_shape if item is not None else None
        return _combine_type_matches((
            dimensions_match, compare_resolved_type(expected.element, item),
        ))
    return _compare_type_parameters(expected, actual)


def _compose(
    definition: "FieldDefinition", declared: Any, target: TypeTarget,
    path: "DeclarationPath", emit_warning: bool,
) -> Any:
    """The canonical type with members/elements replaced by their effective types."""
    if definition.type is UniversalType.GEOPOINT:
        if declared is MountainashDtype.LIST:
            return ListDtype(MountainashDtype.FP64)
        if declared is MountainashDtype.STRUCT:
            return StructDtype((("lon", MountainashDtype.FP64), ("lat", MountainashDtype.FP64)))
    if declared is MountainashDtype.LIST and definition.item_type:
        item = lexical_list_element(definition, path)
        return declared if item is None else ListDtype(item)

    def child(member: Any, segment: str | None) -> Any:
        effective = resolve_field_type(
            member, source=None, target=target, path=(*path, segment),
            emit_warning=emit_warning,
        )
        return UNKNOWN if effective is UNCONSTRAINED else effective

    members = definition.fields
    if members is not None:
        if members is UNKNOWN:
            return StructDtype(UNKNOWN)
        return StructDtype(tuple((name, child(member, name)) for name, member in members.items()))
    element, dimensions = definition.element, definition.dimensions
    if element is None and dimensions is None:
        return declared
    if element is None:
        element = declared.element if isinstance(declared, (ListDtype, ArrayDtype)) else UNKNOWN
    elif element is not UNKNOWN:
        element = child(element, None)
    return ListDtype(element) if dimensions is None else ArrayDtype(element, dimensions)


_UNVERIFIED_FAMILIES = (
    MountainashDtype.JSON, MountainashDtype.XSD_DURATION, MountainashDtype.XSD_YEAR,
    MountainashDtype.XSD_YEARMONTH, MountainashDtype.TIMESTAMP, MountainashDtype.DURATION,
    MountainashDtype.LIST, MountainashDtype.STRUCT,
)


def _warn_on_unverified_override(
    declared: Any, effective: NativeDtype, target: TypeTarget, path: "DeclarationPath",
) -> None:
    unverified = declared in _UNVERIFIED_FAMILIES or isinstance(
        declared, (TimestampDtype, TimeDtype, DurationDtype, ListDtype, ArrayDtype, StructDtype),
    )
    equivalent = False
    try:
        if not unverified:
            expected = registry.to_native_schema(declared, target)
            equivalent = registry.types_equal(expected, effective.value, target)
    except DtypeMappingError:
        unverified = True
    if not equivalent:
        reason = "equivalence unverified" if unverified else "dtype mismatch"
        warnings.warn(
            f"field {format_declaration_path(path)!r} on {target.value}: {reason} between "
            f"canonical {declared!r} and native override {effective.value!r}; native override wins",
            UserWarning, stacklevel=3,
        )


def lexical_list_element(definition: "FieldDefinition", path: "DeclarationPath") -> Any:
    """Canonical element of a lexical list's ``item_type``; None when unparameterized.

    ``item_type`` is a Frictionless-standard lexical carriage, distinct from a
    composed ``element`` declaration. ``any`` parameterizes nothing.
    """
    if not definition.item_type:
        return None
    try:
        item_universal = parse_universal(definition.item_type)
    except UnknownDtypeError as error:
        raise UnknownDtypeError(
            f"field {format_declaration_path(path)!r}: item_type {definition.item_type!r} "
            f"is not a recognized UniversalType"
        ) from error
    return to_canonical(item_universal)


def resolve_native_type(
    definition: "FieldDefinition", target: TypeTarget, *,
    source: "SourceShape | None" = None, path: "DeclarationPath" = (),
) -> Any:
    """Native dtype for one declaration: shared resolution plus adapter projection.

    Includes the schema projections a dtype alone cannot carry (categories,
    lexical ``item_type``). Used where a nested operation needs the native type
    of a single member declaration.
    """
    from mountainash.typespec.adapter_registry import get_native_schema_adapter
    from mountainash.typespec.spec import TableSchema

    name = path[-1] if path and isinstance(path[-1], str) else "value"
    resolved = resolve_field_type(definition, source=source, target=target, path=path)
    encoded = get_native_schema_adapter(target).encode_schema(
        TableSchema(fields={name: definition}), resolved_types={name: resolved},
    )
    return encoded[name] if isinstance(encoded, Mapping) else encoded.field(name).type


def _encode_schema(schema: "TableSchema", target: TypeTarget) -> Any:
    from mountainash.typespec.adapter_registry import get_native_schema_adapter

    resolved = {
        name: resolve_field_type(definition, source=None, target=target, path=(name,))
        for name, definition in schema.fields.items()
    }
    return get_native_schema_adapter(target).encode_schema(schema, resolved_types=resolved)


# ============================================================================
# Polars Converters
# ============================================================================

def to_polars_schema(schema: "TableSchema") -> Dict[str, Any]:
    """
    Convert TableSchema to Polars schema dict.

    Args:
        schema: TableSchema to convert

    Returns:
        Dict mapping column names to Polars DataType objects

    Raises:
        ImportError: If polars is not installed

    Example:
        >>> schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        >>> polars_schema = to_polars_schema(schema)
        >>> polars_schema
        {'id': Int64, 'name': Utf8}
    """
    from mountainash.core.lazy_imports import import_polars
    pl = import_polars()
    if pl is None:
        raise ImportError("polars is required for to_polars_schema()")
    return _encode_schema(schema, TypeTarget.POLARS)


# ============================================================================
# Pandas Converters
# ============================================================================

def to_pandas_dtypes(schema: "TableSchema") -> Dict[str, Any]:
    """
    Convert TableSchema to pandas dtypes dict.

    Non-categorical fields map to pandas dtype strings; a field with
    ``categories`` set maps to a real ``pd.CategoricalDtype`` instance
    (item 54, gap 3) — accepted directly by ``df.astype(...)``.

    Args:
        schema: TableSchema to convert

    Returns:
        Dict mapping column names to pandas dtype strings (or
        pd.CategoricalDtype instances for categorical fields)

    Example:
        >>> schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        >>> pandas_dtypes = to_pandas_dtypes(schema)
        >>> pandas_dtypes
        {'id': 'Int64', 'name': 'string'}
    """
    return _encode_schema(schema, TypeTarget.PANDAS)


# ============================================================================
# PyArrow Converters
# ============================================================================

def to_arrow_schema(schema: "TableSchema") -> 'pa.Schema':
    """
    Convert TableSchema to PyArrow Schema.

    Args:
        schema: TableSchema to convert

    Returns:
        PyArrow Schema object

    Raises:
        ImportError: If pyarrow is not installed

    Example:
        >>> schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        >>> arrow_schema = to_arrow_schema(schema)
        >>> arrow_schema
        id: int64
        name: string
    """
    from mountainash.core.lazy_imports import import_pyarrow
    pa = import_pyarrow()
    if pa is None:
        raise ImportError("pyarrow is required for to_arrow_schema()")
    return _encode_schema(schema, TypeTarget.PYARROW)


# ============================================================================
# Ibis Converters
# ============================================================================

def to_ibis_schema(schema: "TableSchema") -> Dict[str, Any]:
    """
    Convert TableSchema to an Ibis schema dict.

    Plain types map to Ibis type names; parameterized types are Ibis dtypes.

    Args:
        schema: TableSchema to convert

    Returns:
        Dict mapping column names to Ibis type names or dtypes

    Example:
        >>> schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
        >>> ibis_schema = to_ibis_schema(schema)
        >>> ibis_schema
        {'id': 'int64', 'name': 'string'}
    """
    return _encode_schema(schema, TypeTarget.IBIS)


# ============================================================================
# Utility Functions
# ============================================================================

def convert_to_backend(schema: "TableSchema", backend: str) -> Any:
    """
    Convert TableSchema to the specified backend format.

    Args:
        schema: TableSchema to convert
        backend: Registered schema target name; "arrow" aliases "pyarrow".

    Returns:
        Backend-specific schema format

    Raises:
        ValueError: If backend is unknown
        ImportError: If backend library is not installed

    Example:
        >>> schema = TableSchema.from_simple_dict({"id": "integer"})
        >>> convert_to_backend(schema, "pandas")
        {'id': 'Int64'}
    """
    from mountainash.typespec.adapter_registry import NATIVE_SCHEMA_ADAPTERS

    try:
        target = TypeTarget("pyarrow" if backend == "arrow" else backend)
    except ValueError:
        raise ValueError(f"Unknown backend: {backend}") from None
    if NATIVE_SCHEMA_ADAPTERS.get_optional(target) is None:
        raise ValueError(f"Unknown backend: {backend}")
    return _encode_schema(schema, target)


__all__ = [
    # Individual converters
    "to_polars_schema",
    "to_pandas_dtypes",
    "to_arrow_schema",
    "to_ibis_schema",

    # Generic converter
    "convert_to_backend",

    # Field-aware resolution
    "resolve_field_canonical",
    "resolve_field_type",
    "resolve_native_type",
    "lexical_list_element",
    "format_declaration_path",
]
