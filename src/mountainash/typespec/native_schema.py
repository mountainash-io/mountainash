"""Native schema adapters: carrier acquisition, schema decoding and construction.

One stateless class per schema carrier, each implementing
``typespec.protocols.NativeSchemaAdapter``. Optional libraries are imported
inside methods only. Native *types* are translated by the dtype registry; these
adapters own what a dtype alone cannot carry (carrier traversal, wrapped-carrier
evidence, field qualifiers, categories and lexical list item types).

Acquisition (``extract_schema``) may enrich decoded evidence with underlying
carrier metadata; ``decode_schema`` reports only what its schema contains.
Neither fabricates evidence. ``encode_schema`` receives the original declarations
plus the operation-local effective types and never claims constraints are
natively enforced.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from dataclasses import replace
from typing import Any

from mountainash.core.dtypes import (
    ArrayDtype,
    ListDtype,
    MountainashDtype,
    NativeDtype,
    SchemaTypeStatus,
    StructDtype,
    TypeTarget,
    portable_evidence,
    registry,
)
from mountainash.core.dtypes.errors import DtypeMappingError, UnknownDtypeError
from mountainash.core.types import (
    detect_schema_carrier,
    is_narwhals_dataframe,
    is_narwhals_lazyframe,
    is_polars_dataframe,
)
from mountainash.typespec.converters import format_declaration_path, lexical_list_element
from mountainash.typespec.protocols import NativeSchemaAdapter
from mountainash.typespec.source_shape import SourceShape, shape_from_dtype
from mountainash.typespec.spec import FieldDefinition, TableSchema

UNKNOWN = SchemaTypeStatus.UNKNOWN
UNCONSTRAINED = SchemaTypeStatus.UNCONSTRAINED


# ----------------------------------------------------------------------------
# Shared evidence assembly (no carrier knowledge)
# ----------------------------------------------------------------------------


def _decode(native: Any, target: TypeTarget) -> Any:
    """Decoded portable evidence; None when the native type is not recognised."""
    try:
        return registry.from_native(native, target=target)
    except UnknownDtypeError:
        return None


def _native_shape(
    native: Any, target: TypeTarget,
    inner_of: Callable[[Any], Any], members_of: Callable[[Any], Iterable[tuple[str, Any]]],
) -> SourceShape:
    """Portable projection of ``native`` with recursive children and owned native evidence."""
    shape = shape_from_dtype(_decode(native, target))
    if shape.item_shape is not None:
        inner = inner_of(native)
        if inner is not None:
            shape = replace(shape, item_shape=_native_shape(inner, target, inner_of, members_of))
    if shape.struct_fields:
        shape = replace(shape, struct_fields=tuple(
            (name, _native_shape(child, target, inner_of, members_of))
            for name, child in members_of(native)
        ))
    return replace(shape, native_dtype=NativeDtype(value=deepcopy(native), target=target))


# ----------------------------------------------------------------------------
# Shared native schema construction pieces
# ----------------------------------------------------------------------------


def _native_override(resolved: NativeDtype, target: TypeTarget, path: tuple[str | None, ...]) -> Any:
    if resolved.target is not target:
        raise DtypeMappingError(
            f"field {format_declaration_path(path)!r}: native type belongs to "
            f"{resolved.target.value}, not {target.value}"
        )
    return deepcopy(resolved.value)


def _lower(
    definition: FieldDefinition, resolved: Any, target: TypeTarget,
    path: tuple[str | None, ...], *, lexical_items: bool = True,
) -> Any:
    """Native type for a declaration's effective type, applying schema projections.

    An unspecified type uses the string projection; a lexical list with
    ``item_type`` is constructed as a list of that item type where the target
    has parameterized lists.
    """
    if isinstance(resolved, NativeDtype):
        return _native_override(resolved, target, path)
    if resolved is UNCONSTRAINED:
        resolved = MountainashDtype.STRING
    elif lexical_items and resolved is MountainashDtype.LIST:
        item = lexical_list_element(definition, path)
        if item is not None:
            resolved = ListDtype(item)
    return registry.to_native_schema(resolved, target)


def _definitions(schema: TableSchema, resolved_types: Mapping[str, Any]) -> Iterable[tuple[str, FieldDefinition, Any]]:
    for name, definition in schema.fields.items():
        yield name, definition, resolved_types[name]


def _categorical_values(definition: FieldDefinition) -> tuple[Any, ...] | None:
    """Category values of a categorical declaration (no authored dtype), else None."""
    if definition.categories is None or definition.dtype is not None:
        return None
    from mountainash.typespec._categorical import categorical_values

    return tuple(categorical_values(definition.categories))


def _has_categories(definition: FieldDefinition) -> bool:
    if _categorical_values(definition) is not None:
        return True
    if isinstance(definition.fields, Mapping):
        return any(_has_categories(child) for child in definition.fields.values())
    return isinstance(definition.element, FieldDefinition) and _has_categories(definition.element)


# ----------------------------------------------------------------------------
# Polars
# ----------------------------------------------------------------------------


def _polars_shape(native: Any) -> SourceShape:
    return _native_shape(
        native, TypeTarget.POLARS,
        lambda n: getattr(n, "inner", None),
        lambda n: ((field.name, field.dtype) for field in n.fields),
    )


class PolarsSchemaAdapter(NativeSchemaAdapter["pl.DataFrame | pl.LazyFrame", "Mapping[str, pl.DataType | type[pl.DataType]]"]):
    """Polars DataFrame/LazyFrame carriers; schema form: ``dict[str, DataType]``."""

    def extract_names(self, carrier: Any) -> tuple[str, ...]:
        if is_polars_dataframe(carrier):
            return tuple(carrier.columns)
        return tuple(carrier.collect_schema().names())

    def extract_schema(self, carrier: Any) -> dict[str, SourceShape]:
        return self.decode_schema(carrier.collect_schema())

    def decode_schema(self, schema: Mapping[str, Any]) -> dict[str, SourceShape]:
        return {name: _polars_shape(dtype) for name, dtype in schema.items()}

    def encode_schema(
        self, schema: TableSchema, *, resolved_types: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            name: self._native(definition, resolved, (name,))
            for name, definition, resolved in _definitions(schema, resolved_types)
        }

    def _native(self, definition: FieldDefinition, resolved: Any, path: tuple[str | None, ...]) -> Any:
        import polars as pl

        if isinstance(resolved, NativeDtype):
            return _native_override(resolved, TypeTarget.POLARS, path)
        values = _categorical_values(definition)
        if values is not None:
            return pl.Enum([str(v) for v in values]) if definition.categories_ordered else pl.Categorical
        if _has_categories(definition):
            if isinstance(resolved, StructDtype) and isinstance(definition.fields, Mapping) \
                    and isinstance(resolved.fields, tuple):
                return pl.Struct({
                    name: self._member(definition.fields.get(name), child, (*path, name))
                    for name, child in resolved.fields
                })
            if isinstance(resolved, ListDtype) and isinstance(definition.element, FieldDefinition):
                return pl.List(self._member(definition.element, resolved.element, (*path, None)))
        return _lower(definition, resolved, TypeTarget.POLARS, path)

    def _member(self, definition: FieldDefinition | None, resolved: Any, path: tuple[str | None, ...]) -> Any:
        import polars as pl

        if resolved is UNKNOWN:
            return pl.Null
        if definition is None:
            return registry.to_native_schema(resolved, TypeTarget.POLARS)
        return self._native(definition, resolved, path)


# ----------------------------------------------------------------------------
# PyArrow
# ----------------------------------------------------------------------------


def _holds_arrow_field(resolved: Any) -> bool:
    """Whether an effective type carries an Arrow ``Field`` override at any depth."""
    import pyarrow as pa

    if isinstance(resolved, NativeDtype):
        return isinstance(resolved.value, pa.Field)
    if isinstance(resolved, (ListDtype, ArrayDtype)):
        return resolved.native is None and _holds_arrow_field(resolved.element)
    if isinstance(resolved, StructDtype) and isinstance(resolved.fields, tuple):
        return resolved.native is None and any(_holds_arrow_field(child) for _, child in resolved.fields)
    return False


def _arrow_shape(native: Any) -> SourceShape:
    """Evidence for an Arrow type or field; field qualifiers stay native evidence."""
    import pyarrow as pa

    qualified = isinstance(native, pa.Field)
    dtype = native.type if qualified else native
    shape = shape_from_dtype(_decode(dtype, TypeTarget.PYARROW))
    if shape.item_shape is not None:
        inner = getattr(dtype, "value_field", None) or getattr(dtype, "value_type", None)
        if inner is not None:
            shape = replace(shape, item_shape=_arrow_shape(inner))
    if shape.struct_fields:
        shape = replace(shape, struct_fields=tuple((field.name, _arrow_shape(field)) for field in dtype))
    evidence = native.with_name("") if qualified and (not native.nullable or native.metadata) else dtype
    return replace(shape, native_dtype=NativeDtype(value=evidence, target=TypeTarget.PYARROW))


class ArrowSchemaAdapter(NativeSchemaAdapter["pa.Table", "pa.Schema"]):
    """PyArrow Table carriers; schema form: ``pyarrow.Schema``."""

    def extract_names(self, carrier: Any) -> tuple[str, ...]:
        return tuple(carrier.column_names)

    def extract_schema(self, carrier: Any) -> dict[str, SourceShape]:
        return self.decode_schema(carrier.schema)

    def decode_schema(self, schema: Any) -> dict[str, SourceShape]:
        return {field.name: _arrow_shape(field) for field in schema}

    def encode_schema(self, schema: TableSchema, *, resolved_types: Mapping[str, Any]) -> Any:
        import pyarrow as pa

        return pa.schema([
            self._field(name, definition, resolved, (name,))
            for name, definition, resolved in _definitions(schema, resolved_types)
        ])

    def _field(
        self, name: str, definition: FieldDefinition | None, resolved: Any,
        path: tuple[str | None, ...],
    ) -> Any:
        """The Arrow field of one declaration.

        A native ``Field`` override supplies its own nullability and metadata,
        at the top level and for nested members and elements alike; every
        other effective type contributes its dtype only.
        """
        import pyarrow as pa

        if isinstance(resolved, NativeDtype) and isinstance(resolved.value, pa.Field):
            return _native_override(resolved, TypeTarget.PYARROW, path).with_name(name)
        return pa.field(name, self._type(definition, resolved, path))

    def _type(
        self, definition: FieldDefinition | None, resolved: Any, path: tuple[str | None, ...],
    ) -> Any:
        """Arrow dtype of an effective type; containers holding Field overrides keep them.

        The dtype-only mapping refuses field qualifiers, so a container with a
        qualified member or element is constructed from fields here, where the
        schema adapter owns field construction.
        """
        import pyarrow as pa

        if not _holds_arrow_field(resolved):
            if definition is None:
                return registry.to_native_schema(resolved, TypeTarget.PYARROW)
            return _lower(definition, resolved, TypeTarget.PYARROW, path)
        if isinstance(resolved, StructDtype):
            members = definition.fields if definition is not None and isinstance(definition.fields, Mapping) else {}
            return pa.struct([
                self._member(name, members.get(name), child, (*path, name))
                for name, child in resolved.fields
            ])
        element = definition.element if definition is not None and isinstance(definition.element, FieldDefinition) else None
        child = self._member("item", element, resolved.element, (*path, None))
        if isinstance(resolved, ListDtype):
            return pa.list_(child)
        if not isinstance(resolved.dimensions, tuple):
            raise DtypeMappingError("PyArrow fixed-size list requires known dimensions")
        for size in reversed(resolved.dimensions):
            list_type = pa.list_(child, size)
            child = pa.field("item", list_type)
        return list_type

    def _member(
        self, name: str, definition: FieldDefinition | None, resolved: Any,
        path: tuple[str | None, ...],
    ) -> Any:
        import pyarrow as pa

        if resolved is UNKNOWN:
            return pa.field(name, pa.null())
        return self._field(name, definition, resolved, path)


# ----------------------------------------------------------------------------
# pandas
# ----------------------------------------------------------------------------


def _in_pandas(shape: SourceShape) -> SourceShape:
    """Evidence of an Arrow-backed column in the pandas domain.

    ``shape`` is the Arrow decoding of the column's storage type. pandas nests
    through ``pd.ArrowDtype``, so every level's native evidence is that level's
    ``pd.ArrowDtype`` and its detailed type is the pandas adapter's decoding of
    it: no member or element carries another target's native override.
    """
    import pandas as pd
    import pyarrow as pa

    arrow = shape.native_dtype.value
    evidence = NativeDtype(
        value=pd.ArrowDtype(arrow.type if isinstance(arrow, pa.Field) else arrow),
        target=TypeTarget.PANDAS,
    )
    return replace(
        shape,
        item_shape=None if shape.item_shape is None else _in_pandas(shape.item_shape),
        struct_fields=tuple((name, _in_pandas(child)) for name, child in shape.struct_fields),
        native_dtype=evidence,
        detailed_dtype=_decode(evidence.value, TypeTarget.PANDAS),
    )


def _pandas_shape(native: Any) -> SourceShape:
    evidence = NativeDtype(value=deepcopy(native), target=TypeTarget.PANDAS)
    arrow = getattr(native, "pyarrow_dtype", None)
    if arrow is not None:
        return replace(_in_pandas(_arrow_shape(arrow)), native_dtype=evidence)
    return replace(shape_from_dtype(_decode(native, TypeTarget.PANDAS)), native_dtype=evidence)


class PandasSchemaAdapter(NativeSchemaAdapter["pd.DataFrame", "Mapping[str, object]"]):
    """pandas DataFrame carriers; schema form: ``dict[str, dtype]``."""

    def extract_names(self, carrier: Any) -> tuple[str, ...]:
        return tuple(carrier.columns)

    def extract_schema(self, carrier: Any) -> dict[str, SourceShape]:
        return self.decode_schema(carrier.dtypes)

    def decode_schema(self, schema: Any) -> dict[str, SourceShape]:
        return {name: _pandas_shape(dtype) for name, dtype in schema.items()}

    def encode_schema(
        self, schema: TableSchema, *, resolved_types: Mapping[str, Any],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, definition, resolved in _definitions(schema, resolved_types):
            if isinstance(resolved, NativeDtype):
                result[name] = _native_override(resolved, TypeTarget.PANDAS, (name,))
            elif (values := _categorical_values(definition)) is not None:
                import pandas as pd

                result[name] = pd.CategoricalDtype(
                    categories=values, ordered=bool(definition.categories_ordered),
                )
            else:
                # pandas has no parameterized list dtype: a lexical list stays object.
                result[name] = _lower(
                    definition, resolved, TypeTarget.PANDAS, (name,), lexical_items=False,
                )
        return result


# ----------------------------------------------------------------------------
# Ibis
# ----------------------------------------------------------------------------


def _ibis_shape(native: Any) -> SourceShape:
    if isinstance(native, str):
        import ibis.expr.datatypes as dt

        native = dt.dtype(native)
    return _native_shape(
        native, TypeTarget.IBIS,
        lambda n: getattr(n, "value_type", None),
        lambda n: n.fields.items(),
    )


class IbisSchemaAdapter(NativeSchemaAdapter["ir.Table", "Mapping[str, str | dt.DataType]"]):
    """Ibis Table carriers; schema form: ``dict[str, type name or Ibis dtype]``."""

    def extract_names(self, carrier: Any) -> tuple[str, ...]:
        return tuple(carrier.columns)

    def extract_schema(self, carrier: Any) -> dict[str, SourceShape]:
        return self.decode_schema(carrier.schema())

    def decode_schema(self, schema: Any) -> dict[str, SourceShape]:
        return {name: _ibis_shape(dtype) for name, dtype in schema.items()}

    def encode_schema(
        self, schema: TableSchema, *, resolved_types: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            name: _lower(definition, resolved, TypeTarget.IBIS, (name,))
            for name, definition, resolved in _definitions(schema, resolved_types)
        }


# ----------------------------------------------------------------------------
# Narwhals
# ----------------------------------------------------------------------------


def _narwhals_shape(native: Any) -> SourceShape:
    return _native_shape(
        native, TypeTarget.NARWHALS,
        lambda n: getattr(n, "inner", None),
        lambda n: ((field.name, field.dtype) for field in n.fields),
    )


def _narwhals_children(native: Any) -> tuple[Any, dict[str, Any]]:
    """Element dtype and named member dtypes of a Narwhals dtype instance."""
    import narwhals as nw

    if isinstance(native, (nw.List, nw.Array)):
        return native.inner, {}
    if isinstance(native, nw.Struct):
        return None, {field.name: field.dtype for field in native.fields}
    return None, {}


def _in_narwhals(shape: SourceShape, native: Any) -> SourceShape:
    """A carrier's evidence presented in the Narwhals domain.

    Portable carrier parameters and opaque carrier detail remain evidence.
    The native slot at every level is Narwhals-owned. Shared resolution, not
    acquisition, projects foreign opaque detail when inheriting an unknown
    declared type into the selected target domain.
    """
    inner, members = _narwhals_children(native)
    detailed = shape.detailed_dtype
    return replace(
        shape,
        item_shape=None if shape.item_shape is None else _in_narwhals(shape.item_shape, inner),
        struct_fields=tuple(
            (name, _in_narwhals(child, members.get(name))) for name, child in shape.struct_fields
        ),
        native_dtype=None if native is None else NativeDtype(
            value=deepcopy(native), target=TypeTarget.NARWHALS,
        ),
        detailed_dtype=None if detailed is None else portable_evidence(detailed),
    )


class NarwhalsSchemaAdapter(NativeSchemaAdapter["nw.DataFrame | nw.LazyFrame | pd.DataFrame | pa.Table | pl.DataFrame | pl.LazyFrame", "Mapping[str, nw.DataType | type[nw.DataType]]"]):
    """Narwhals frames, or any native frame Narwhals wraps; schema: dtype mapping.

    Narwhals loses detail its wrapped carrier still has (for example Arrow
    ``time64[us]`` precision, Polars ``Time`` nanoseconds), so acquisition
    combines the underlying carrier's own schema evidence with the Narwhals
    representation. A standalone schema decodes only what the Narwhals schema
    carries.
    """

    def extract_names(self, carrier: Any) -> tuple[str, ...]:
        from mountainash.core.lazy_imports import import_narwhals
        from mountainash.typespec.adapter_registry import get_native_schema_adapter

        nw = import_narwhals()
        frame = carrier if is_narwhals_dataframe(carrier) or is_narwhals_lazyframe(carrier) \
            else nw.from_native(carrier)
        underlying = frame.to_native()
        owner = detect_schema_carrier(underlying)
        if owner is not None and owner is not TypeTarget.NARWHALS:
            # The wrapped carrier's own metadata; Narwhals would infer pandas
            # object-column types from row values.
            return get_native_schema_adapter(owner).extract_names(underlying)
        if is_narwhals_lazyframe(frame):
            return tuple(frame.collect_schema().names())
        return tuple(frame.columns)

    def extract_schema(self, carrier: Any) -> dict[str, SourceShape]:
        from mountainash.core.lazy_imports import import_narwhals
        from mountainash.typespec.adapter_registry import get_native_schema_adapter

        nw = import_narwhals()
        frame = carrier if is_narwhals_dataframe(carrier) or is_narwhals_lazyframe(carrier) \
            else nw.from_native(carrier)
        underlying = frame.to_native()
        owner = detect_schema_carrier(underlying)
        if owner is None or owner is TypeTarget.NARWHALS:
            return self.decode_schema(frame.collect_schema())
        # Narwhals infers object-column types from values; the pandas dtypes are
        # mapped without row access.
        schema = (
            nw.Schema.from_pandas_like(underlying.dtypes.to_dict())
            if owner is TypeTarget.PANDAS else frame.collect_schema()
        )
        shapes = get_native_schema_adapter(owner).extract_schema(underlying)
        return {name: _in_narwhals(shape, schema[name]) for name, shape in shapes.items()}

    def decode_schema(self, schema: Mapping[str, Any]) -> dict[str, SourceShape]:
        return {name: _narwhals_shape(dtype) for name, dtype in schema.items()}

    def encode_schema(self, schema: TableSchema, *, resolved_types: Mapping[str, Any]) -> Any:
        # A bare container type is valid schema intent. nw.Schema eagerly
        # instantiates type classes, which would invent required shape arguments.
        return {
            name: _lower(definition, resolved, TypeTarget.NARWHALS, (name,))
            for name, definition, resolved in _definitions(schema, resolved_types)
        }


__all__ = [
    "ArrowSchemaAdapter", "IbisSchemaAdapter", "NarwhalsSchemaAdapter",
    "PandasSchemaAdapter", "PolarsSchemaAdapter",
]
