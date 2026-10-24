"""
Tests for mountainash.typespec.converters.

Covers:
- shared field-type resolution (canonical, native override, evidence, recursion)
- native schema construction through the registered adapters
  (Polars, pandas, Arrow, Ibis, Narwhals) and the public converter forms
- adapter/codec registry selection
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import (
    ArrayDtype,
    ListDtype,
    NativeDtype,
    SchemaTypeStatus,
    StructDtype,
    TimeDtype,
    TypeTarget,
    registry,
)
from mountainash.core.dtypes import MountainashDtype as D
from mountainash.typespec.converters import (
    convert_to_backend,
    resolve_field_canonical,
    resolve_field_type,
    resolve_native_type,
    to_arrow_schema,
    to_ibis_schema,
    to_pandas_dtypes,
    to_polars_schema,
)
from mountainash.typespec.source_shape import SourceShape
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.universal_types import UniversalType as U

UNKNOWN = SchemaTypeStatus.UNKNOWN


def _schema(**fields: FieldDefinition) -> TableSchema:
    return TableSchema(fields=fields)


def _resolve(definition, target=TypeTarget.POLARS, *, source=None, path=("x",), **kw):
    return resolve_field_type(definition, source=source, target=target, path=path, **kw)


# ============================================================================
# Shared resolution: authored intent, evidence and native overrides
# ============================================================================


class TestResolveFieldType:
    def test_typeless_declaration_is_unconstrained_not_unknown(self):
        assert resolve_field_canonical(FieldDefinition()) is SchemaTypeStatus.UNCONSTRAINED
        assert _resolve(FieldDefinition()) is SchemaTypeStatus.UNCONSTRAINED

    def test_canonical_resolution_needs_no_target_or_name(self):
        assert resolve_field_canonical(FieldDefinition(type=U.INTEGER)) is D.I64
        assert resolve_field_canonical(FieldDefinition(dtype=D.I8)) is D.I8

    def test_source_evidence_resolves_unspecified_parameters_without_touching_definition(self):
        definition = FieldDefinition(dtype=TimeDtype())
        source = SourceShape(D.TIME, detailed_dtype=TimeDtype(6))
        assert _resolve(definition, source=source) == TimeDtype(6)
        assert definition.dtype == TimeDtype()

    def test_authored_parameter_wins_over_evidence(self):
        definition = FieldDefinition(dtype=TimeDtype(3))
        source = SourceShape(D.TIME, detailed_dtype=TimeDtype(6))
        assert _resolve(definition, source=source) == TimeDtype(3)

    def test_unknown_evidence_is_not_invented(self):
        unspecified = FieldDefinition(dtype=TimeDtype())
        assert _resolve(unspecified, source=SourceShape(None)) == TimeDtype()

    def test_native_override_wins_and_reports_the_field_path(self):
        import polars as pl

        definition = FieldDefinition(dtype=D.I8, backend_type=pl.Int64)
        with pytest.warns(UserWarning, match="x"):
            effective = _resolve(definition)
        assert effective == NativeDtype(value=pl.Int64, target=TypeTarget.POLARS)

    def test_native_override_warning_can_be_suppressed_by_the_caller(self):
        import polars as pl

        definition = FieldDefinition(dtype=D.I8, backend_type=pl.Int64)
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            _resolve(definition, emit_warning=False)

    def test_native_string_override_is_parsed_by_the_target(self):
        import polars as pl

        definition = FieldDefinition(type=U.INTEGER, backend_type="Int32")
        assert _resolve(definition) == NativeDtype(value=pl.Int32, target=TypeTarget.POLARS)

    @pytest.mark.parametrize("backend_type", [None, ""])
    def test_empty_override_means_no_override(self, backend_type):
        definition = FieldDefinition(type=U.INTEGER, backend_type=backend_type)
        assert _resolve(definition) is D.I64

    def test_unparseable_override_names_field_value_and_target(self):
        from mountainash.core.dtypes import InvalidBackendTypeError

        definition = FieldDefinition(type=U.INTEGER, backend_type="garbage")
        for target in (TypeTarget.POLARS, TypeTarget.NARWHALS, TypeTarget.PYARROW):
            with pytest.raises(InvalidBackendTypeError) as caught:
                _resolve(definition, target)
            message = str(caught.value)
            assert "x" in message and "garbage" in message and target.value in message

    def test_native_object_of_another_target_is_rejected(self):
        import polars as pl
        from mountainash.core.dtypes.errors import DtypeMappingError

        definition = FieldDefinition(dtype=D.I8, backend_type=pl.Int8)
        with pytest.raises(DtypeMappingError, match="x"):
            _resolve(definition, TypeTarget.PYARROW)

    def test_nested_override_target_error_carries_member_path_segments(self):
        import polars as pl
        from mountainash.core.dtypes.errors import DtypeMappingError

        record = FieldDefinition(fields={
            "a.b": FieldDefinition(fields={"leaf": FieldDefinition(backend_type=pl.Int8)}),
        })
        with pytest.raises(DtypeMappingError) as caught:
            _resolve(record, TypeTarget.PYARROW, path=("record",))
        message = str(caught.value)
        assert "record" in message and "leaf" in message
        # a literal dotted member name is not presented as two nested members
        assert "'a.b'" in message

    def test_element_scope_is_a_segment_not_a_name(self):
        import polars as pl
        from mountainash.core.dtypes.errors import DtypeMappingError

        listing = FieldDefinition(element=FieldDefinition(backend_type=pl.Int8))
        with pytest.raises(DtypeMappingError) as caught:
            _resolve(listing, TypeTarget.PYARROW, path=("items",))
        assert "items[]" in str(caught.value)

    def test_ibis_override_equivalence_uses_the_native_type_owner(self):
        definition = FieldDefinition(dtype=D.I64, backend_type="int64")
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            _resolve(definition, TypeTarget.IBIS)

    def test_lossy_reverse_mapping_cannot_certify_native_equivalence(self):
        import pyarrow as pa

        definition = FieldDefinition(dtype=D.FP32, backend_type=pa.float16())
        with pytest.warns(UserWarning, match="equivalence unverified|dtype mismatch"):
            effective = _resolve(definition, TypeTarget.PYARROW)
        assert effective.value == pa.float16()


class TestResolveRecursiveStructure:
    def test_struct_members_resolve_in_declaration_order(self):
        record = FieldDefinition(fields={"b": FieldDefinition(dtype=D.I8), "a": FieldDefinition(type=U.STRING)})
        assert _resolve(record) == StructDtype((("b", D.I8), ("a", D.STRING)))

    def test_member_native_override_wins_with_its_own_path_and_leaves_definitions_unchanged(self):
        import polars as pl

        child = FieldDefinition(dtype=D.STRING, backend_type=pl.Float64, description="kept")
        record = FieldDefinition(fields={"value": child})
        with pytest.warns(UserWarning) as caught:
            effective = _resolve(record, path=("record",))
        assert effective == StructDtype((("value", NativeDtype(value=pl.Float64, target=TypeTarget.POLARS)),))
        assert any("record.value" in str(w.message) for w in caught)
        assert record.fields["value"] is child
        assert child.dtype is D.STRING and child.description == "kept"

    def test_nested_members_and_collection_elements_recurse(self):
        definition = FieldDefinition(element=FieldDefinition(fields={
            "id": FieldDefinition(dtype=D.I16),
            "tags": FieldDefinition(element=FieldDefinition(type=U.STRING)),
        }))
        assert _resolve(definition) == ListDtype(StructDtype((
            ("id", D.I16), ("tags", ListDtype(D.STRING)),
        )))

    def test_known_empty_unknown_shapes_stay_distinct(self):
        unknown_record = _resolve(FieldDefinition(fields=UNKNOWN))
        empty_record = _resolve(FieldDefinition(fields={}))
        unknown_element = _resolve(FieldDefinition(element=UNKNOWN))
        assert unknown_record == StructDtype(UNKNOWN)
        assert empty_record == StructDtype(())
        assert unknown_record != empty_record
        assert unknown_element == ListDtype(UNKNOWN)

    def test_fixed_dimensions_are_retained_and_unknown_dimensions_differ(self):
        element = FieldDefinition(fields={"id": FieldDefinition(dtype=D.I16)})
        fixed = _resolve(FieldDefinition(element=element, dimensions=(2, 3)))
        unknown = _resolve(FieldDefinition(element=element, dimensions=UNKNOWN))
        assert fixed == ArrayDtype(StructDtype((("id", D.I16),)), (2, 3))
        assert unknown == ArrayDtype(StructDtype((("id", D.I16),)), UNKNOWN)

    def test_source_evidence_fills_unspecified_member_parameters_by_name(self):
        record = FieldDefinition(fields={"at": FieldDefinition(dtype=TimeDtype())})
        evidence = StructDtype((("at", TimeDtype(6)),))
        source = SourceShape(
            D.STRUCT, struct_fields=(("at", SourceShape(D.TIME)),), detailed_dtype=evidence,
        )
        assert _resolve(record, source=source) == StructDtype((("at", TimeDtype(6)),))
        assert record.fields["at"].dtype == TimeDtype()

    def test_unknown_member_type_stays_unknown(self):
        record = FieldDefinition(dtype=StructDtype((("value", UNKNOWN),)))
        assert _resolve(record) == StructDtype((("value", UNKNOWN),))

    def test_resolution_does_not_mutate_or_share_results_between_calls(self):
        record = FieldDefinition(fields={"a": FieldDefinition(dtype=D.I8)})
        first, second = _resolve(record), _resolve(record)
        assert first == second and first is not second


# ============================================================================
# Native schema construction through the public converters
# ============================================================================


@pytest.fixture()
def basic_schema():
    return TableSchema.from_simple_dict({
        "id": "integer",
        "name": "string",
        "score": "number",
        "active": "boolean",
    })


class TestToPolarsSchema:
    def test_basic_types(self, basic_schema):
        import polars as pl

        result = to_polars_schema(basic_schema)
        assert result == {
            "id": pl.Int64, "name": pl.String, "score": pl.Float64, "active": pl.Boolean,
        }
        assert isinstance(result, dict)
        assert list(result) == ["id", "name", "score", "active"]

    def test_every_universal_type_produces_a_dtype(self):
        schema = _schema(**{f"col_{ut.value}": FieldDefinition(type=ut) for ut in UniversalType})
        result = to_polars_schema(schema)
        assert len(result) == len(list(UniversalType))
        assert all(dtype is not None for dtype in result.values())


class TestToPandasDtypes:
    def test_basic_types(self, basic_schema):
        assert to_pandas_dtypes(basic_schema) == {
            "id": "Int64", "name": "string", "score": "float64", "active": "boolean",
        }

    def test_every_universal_type_produces_a_dtype(self):
        schema = _schema(**{f"col_{ut.value}": FieldDefinition(type=ut) for ut in UniversalType})
        assert len(to_pandas_dtypes(schema)) == len(list(UniversalType))

    @pytest.mark.parametrize("ordered", [True, False])
    def test_categories_become_a_real_categorical_dtype(self, ordered):
        import pandas as pd

        schema = _schema(col=FieldDefinition(
            type=U.STRING, categories=["a", "b"], categories_ordered=ordered,
        ))
        result = to_pandas_dtypes(schema)["col"]
        assert isinstance(result, pd.CategoricalDtype)
        assert list(result.categories) == ["a", "b"]
        assert result.ordered is ordered

    def test_native_string_override_passes_through(self):
        schema = _schema(val=FieldDefinition(type=U.NUMBER, backend_type="Float32"))
        assert to_pandas_dtypes(schema)["val"] == "Float32"


class TestToArrowSchema:
    def test_schema_types_and_order(self, basic_schema):
        pa = pytest.importorskip("pyarrow")
        result = to_arrow_schema(basic_schema)
        assert isinstance(result, pa.Schema)
        assert result.names == ["id", "name", "score", "active"]
        assert [field.type for field in result] == [pa.int64(), pa.string(), pa.float64(), pa.bool_()]

    def test_invalid_override_string_is_typed_not_raw(self):
        from mountainash.core.dtypes import InvalidBackendTypeError

        schema = _schema(x=FieldDefinition(type=U.INTEGER, backend_type="timestamp[badunit]"))
        with pytest.raises(InvalidBackendTypeError, match=r"timestamp\[badunit\]"):
            to_arrow_schema(schema)


class TestToIbisSchema:
    def test_basic_types(self, basic_schema):
        assert to_ibis_schema(basic_schema) == {
            "id": "int64", "name": "string", "score": "float64", "active": "boolean",
        }

    def test_categories_stay_string(self):
        schema = _schema(cat=FieldDefinition(
            type=U.STRING, categories=["a", "b"], categories_ordered=True,
        ))
        assert to_ibis_schema(schema)["cat"] == "string"


class TestConvertToBackend:
    @pytest.mark.parametrize("backend", ["polars", "pandas", "ibis"])
    def test_dict_backends(self, basic_schema, backend):
        assert isinstance(convert_to_backend(basic_schema, backend), dict)

    @pytest.mark.parametrize("backend", ["arrow", "pyarrow"])
    def test_arrow_aliases(self, basic_schema, backend):
        pa = pytest.importorskip("pyarrow")
        assert isinstance(convert_to_backend(basic_schema, backend), pa.Schema)

    def test_unknown_backend_raises_value_error(self, basic_schema):
        with pytest.raises(ValueError, match="Unknown backend"):
            convert_to_backend(basic_schema, "unknown_backend")


@pytest.mark.parametrize("target", ["polars", "pandas", "arrow", "ibis"])
def test_native_override_wins_over_precise_declaration(target):
    import polars as pl
    import pyarrow as pa

    cases = {
        "polars": (to_polars_schema, "Int64", pl.Int64),
        "pandas": (to_pandas_dtypes, "Int64", "Int64"),
        "arrow": (to_arrow_schema, "int64", pa.int64()),
        "ibis": (to_ibis_schema, "int64", "int64"),
    }
    converter, override, expected = cases[target]
    schema = _schema(x=FieldDefinition(dtype=D.I8, backend_type=override))
    with pytest.warns(UserWarning, match="x"):
        result = converter(schema)
    actual = result.field("x").type if target == "arrow" else result["x"]
    assert str(actual) == str(expected)


def test_native_object_cannot_be_lowered_on_another_target():
    import polars as pl
    from mountainash.core.dtypes.errors import DtypeMappingError

    schema = _schema(x=FieldDefinition(dtype=D.I8, backend_type=pl.Int8))
    with pytest.raises(DtypeMappingError):
        to_arrow_schema(schema)


def test_typeless_field_materializes_as_string_without_changing_the_declaration():
    import polars as pl

    definition = FieldDefinition(type=U.ANY)
    assert to_polars_schema(_schema(a=definition))["a"] is pl.String
    assert resolve_field_canonical(definition) is SchemaTypeStatus.UNCONSTRAINED


@pytest.mark.parametrize(
    ("type_", "expected"),
    [(U.YEAR, "string"), (U.YEARMONTH, "string")],
)
def test_semantic_string_types_are_strings_on_pandas(type_, expected):
    assert to_pandas_dtypes(_schema(y=FieldDefinition(type=type_)))["y"] == expected


def test_native_member_parameters_and_nested_canonical_members_survive_allocation():
    import polars as pl

    schema = _schema(record=FieldDefinition(fields={
        "id": FieldDefinition(dtype=D.I8),
        "at": FieldDefinition(dtype=D.TIMESTAMP, backend_type=pl.Datetime("ns", "UTC")),
    }))
    with pytest.warns(UserWarning):
        frame = pl.DataFrame(schema=to_polars_schema(schema))
    assert frame.schema["record"] == pl.Struct({"id": pl.Int8, "at": pl.Datetime("ns", "UTC")})


def test_unknown_member_uses_native_null_without_claiming_a_type():
    import polars as pl

    dtype = StructDtype((("value", UNKNOWN),))
    definition = FieldDefinition(dtype=dtype)
    assert to_polars_schema(_schema(row=definition)) == {"row": pl.Struct({"value": pl.Null})}
    assert definition.dtype == dtype


def test_fixed_struct_array_keeps_dimensions_and_member_authority():
    import polars as pl

    definition = FieldDefinition(
        element=FieldDefinition(fields={"id": FieldDefinition(dtype=D.I16)}), dimensions=(2, 3),
    )
    assert to_polars_schema(_schema(rows=definition)) == {
        "rows": pl.Array(pl.Struct({"id": pl.Int16}), (2, 3)),
    }


# ----------------------------------------------------------------------------
# Lexical list item_type is a distinct operation from composed element
# ----------------------------------------------------------------------------


class TestLexicalListItemType:
    def _schema(self, item_type=None):
        return _schema(lst=FieldDefinition(type=U.LIST, item_type=item_type))

    def test_polars(self):
        import polars as pl

        assert to_polars_schema(self._schema("integer"))["lst"] == pl.List(pl.Int64)

    def test_narwhals(self):
        import narwhals as nw

        native = resolve_native_type(
            self._schema("integer").fields["lst"], TypeTarget.NARWHALS, path=("lst",),
        )
        assert native == nw.List(nw.Int64)
        assert native is not nw.List

    def test_pyarrow_element_is_the_item_type_not_string(self):
        pa = pytest.importorskip("pyarrow")
        assert to_arrow_schema(self._schema("integer")).field("lst").type == pa.list_(pa.int64())

    def test_ibis(self):
        assert str(to_ibis_schema(self._schema("integer"))["lst"]) == "array<int64>"


    @pytest.mark.parametrize("item_type", [None, "any"])
    def test_unparameterized_keeps_bare_container(self, item_type):
        import polars as pl

        assert to_polars_schema(self._schema(item_type))["lst"] is pl.List

    def test_unknown_item_type_names_the_field_and_chains_the_cause(self):
        from mountainash.core.dtypes import UnknownDtypeError

        with pytest.raises(UnknownDtypeError) as caught:
            to_polars_schema(self._schema("garbage"))
        assert "lst" in str(caught.value) and "garbage" in str(caught.value)
        assert isinstance(caught.value.__cause__, UnknownDtypeError)

    def test_geopoint_item_type_is_ambiguous(self):
        from mountainash.typespec.errors import AmbiguousGeospatialTypeError

        with pytest.raises(AmbiguousGeospatialTypeError):
            to_polars_schema(self._schema("geopoint"))

    def test_geojson_item_type_is_a_string_backed_list(self):
        import polars as pl

        assert to_polars_schema(self._schema("geojson"))["lst"] == pl.List(pl.String)


# ----------------------------------------------------------------------------
# Categories on a Polars schema
# ----------------------------------------------------------------------------


class TestCategoricalSchema:
    def _schema(self, categories, ordered=None):
        return _schema(cat=FieldDefinition(
            type=U.STRING, categories=categories, categories_ordered=ordered,
        ))

    def test_unordered_is_categorical(self):
        import polars as pl

        assert to_polars_schema(self._schema(["a", "b"], False))["cat"] is pl.Categorical

    def test_ordered_is_enum(self):
        import polars as pl

        assert to_polars_schema(self._schema(["a", "b"], True))["cat"] == pl.Enum(["a", "b"])

    def test_object_form_categories_use_the_shared_extraction(self):
        import polars as pl
        from mountainash.typespec._categorical import categorical_values

        categories = [{"value": 0, "label": "Low"}, {"value": 1, "label": "High"}]
        assert to_polars_schema(self._schema(categories, True))["cat"] == pl.Enum(
            [str(v) for v in categorical_values(categories)]
        )

    def test_member_categories_are_retained(self):
        import polars as pl

        record = FieldDefinition(fields={"kind": FieldDefinition(
            type=U.STRING, categories=["home", "work"], categories_ordered=True,
        )})
        assert to_polars_schema(_schema(addr=record))["addr"] == pl.Struct(
            {"kind": pl.Enum(["home", "work"])}
        )


# ----------------------------------------------------------------------------
# Composed records and collections on every schema target
# ----------------------------------------------------------------------------


class TestComposedStructure:
    FLAT = {"street": FieldDefinition(type=U.STRING), "zip": FieldDefinition(type=U.STRING)}
    NESTED = {
        "street": FieldDefinition(type=U.STRING),
        "geo": FieldDefinition(fields={
            "lat": FieldDefinition(type=U.NUMBER), "lon": FieldDefinition(type=U.NUMBER),
        }),
    }

    def _addr(self, fields):
        return _schema(addr=FieldDefinition(type=U.OBJECT, fields=fields))

    def test_polars_flat_and_nested(self):
        import polars as pl

        assert to_polars_schema(self._addr(self.FLAT))["addr"] == pl.Struct(
            {"street": pl.String, "zip": pl.String}
        )
        assert to_polars_schema(self._addr(self.NESTED))["addr"] == pl.Struct({
            "street": pl.String, "geo": pl.Struct({"lat": pl.Float64, "lon": pl.Float64}),
        })

    def test_arrow_flat(self):
        pa = pytest.importorskip("pyarrow")
        field = to_arrow_schema(self._addr(self.FLAT)).field("addr")
        assert field.type == pa.struct([pa.field("street", pa.string()), pa.field("zip", pa.string())])

    def test_narwhals_flat(self):
        import narwhals as nw

        native = resolve_native_type(
            self._addr(self.FLAT).fields["addr"], TypeTarget.NARWHALS, path=("addr",),
        )
        assert native == nw.Struct({"street": nw.String, "zip": nw.String})

    def test_ibis_flat_and_nested(self):
        assert str(to_ibis_schema(self._addr(self.FLAT))["addr"]) == "struct<street: string, zip: string>"
        assert str(to_ibis_schema(self._addr(self.NESTED))["addr"]) == (
            "struct<street: string, geo: struct<lat: float64, lon: float64>>"
        )

    def test_pandas_nested_is_arrow_backed_with_declared_members(self):
        import pandas as pd
        import pyarrow as pa

        native = to_pandas_dtypes(self._addr(self.FLAT))["addr"]
        assert isinstance(native, pd.ArrowDtype)
        assert native.pyarrow_dtype == pa.struct([
            pa.field("street", pa.string()), pa.field("zip", pa.string()),
        ])

    def test_bare_record_keeps_bare_container(self):
        import polars as pl

        assert to_polars_schema(_schema(addr=FieldDefinition(type=U.OBJECT)))["addr"] is pl.Struct

    def test_known_empty_record_is_an_empty_struct_not_a_bare_container(self):
        import polars as pl

        assert to_polars_schema(self._addr({}))["addr"] == pl.Struct({})

    def test_empty_member_collection_keeps_its_struct_hierarchy(self):
        import polars as pl

        rows = FieldDefinition(type=U.ARRAY, element=FieldDefinition(fields={}))
        assert to_polars_schema(_schema(rows=rows))["rows"] == pl.List(pl.Struct({}))

    def test_encode_uses_the_supplied_resolved_types_not_a_second_resolution(self):
        import polars as pl
        from mountainash.typespec.adapter_registry import get_native_schema_adapter

        schema = _schema(x=FieldDefinition(dtype=D.I64))
        encoded = get_native_schema_adapter(TypeTarget.POLARS).encode_schema(
            schema, resolved_types={"x": D.I8},
        )
        assert encoded == {"x": pl.Int8}


# ============================================================================
# Field-aware canonical resolution, every target
# ============================================================================


@pytest.mark.parametrize("target", [t for t in TypeTarget if t is not TypeTarget.PYTHON])
@pytest.mark.parametrize(
    "definition,canonical",
    [
        (FieldDefinition(type=U.LIST), D.LIST),
        (FieldDefinition(type=U.ARRAY), D.LIST),
        (FieldDefinition(type=U.GEOPOINT), D.STRING),
        (FieldDefinition(type=U.GEOPOINT, format="array"), D.LIST),
        (FieldDefinition(type=U.GEOPOINT, format="object"), D.STRUCT),
        (FieldDefinition(type=U.GEOJSON), D.JSON),
        (FieldDefinition(type=U.GEOJSON, format="topojson"), D.JSON),
        (FieldDefinition(type=U.DURATION), D.XSD_DURATION),
        (FieldDefinition(type=U.YEAR), D.XSD_YEAR),
        (FieldDefinition(type=U.YEARMONTH), D.XSD_YEARMONTH),
    ],
)
def test_v2_types_resolve_on_every_schema_target(target, definition, canonical):
    assert resolve_native_type(definition, target, path=("x",)) == registry.to_native_schema(
        canonical, target
    )




@pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.NARWHALS, TypeTarget.IBIS])
def test_v2_six_field_schema_resolves_on_polars_narwhals_and_ibis(target):
    definitions = {
        "list": FieldDefinition(type=U.LIST, item_type="integer"),
        "point": FieldDefinition(type=U.GEOPOINT, format="array"),
        "geometry": FieldDefinition(type=U.GEOJSON),
        "duration": FieldDefinition(type=U.DURATION),
        "year": FieldDefinition(type=U.YEAR),
        "yearmonth": FieldDefinition(type=U.YEARMONTH),
    }
    resolved = {
        name: resolve_native_type(definition, target, path=(name,))
        for name, definition in definitions.items()
    }
    if target is TypeTarget.POLARS:
        import polars as pl

        assert resolved["list"] == pl.List(pl.Int64)
        assert resolved["point"] is pl.List
        string_type = pl.String
    elif target is TypeTarget.NARWHALS:
        import narwhals as nw

        assert resolved["list"] == nw.List(nw.Int64)
        assert resolved["point"] is nw.List
        string_type = nw.String
    else:
        assert str(resolved["list"]) == "array<int64>"
        assert resolved["point"] == "array"
        string_type = "string"
    assert resolved["point"] == registry.to_native_schema(D.LIST, target)
    for name in ("geometry", "duration", "year", "yearmonth"):
        assert resolved[name] == string_type
        assert registry.from_native(resolved[name], target) is D.STRING


# ============================================================================
# Schema validation consumers of effective native types
# ============================================================================


@pytest.mark.parametrize("in_array", [False, True])
def test_validate_match_checks_nested_effective_types(in_array):
    import polars as pl
    from mountainash.typespec.validation import validate_match

    def definition(child):
        if in_array:
            return FieldDefinition(element=FieldDefinition(fields={"id": child}))
        return FieldDefinition(fields={"id": child})

    source = pl.DataFrame({"record": [[{"id": 128}]] if in_array else [{"id": 128}]})
    narrow = FieldDefinition(dtype=D.I8)
    assert not validate_match(source, _schema(record=definition(narrow)))[0]
    overridden = narrow.variant(backend_type="Int64")
    with pytest.warns(UserWarning):
        assert validate_match(source, _schema(record=definition(overridden))) == (True, [])
    assert validate_match(source, _schema(record=definition(FieldDefinition()))) == (True, [])


def test_schema_validation_uses_effective_native_target():
    import polars as pl
    from mountainash.typespec.validation import validate_match

    schema = _schema(x=FieldDefinition(dtype=D.I8, backend_type="Int64"))
    with pytest.warns(UserWarning):
        assert validate_match(pl.DataFrame({"x": [127]}, schema={"x": pl.Int64}), schema) == (True, [])
    with pytest.warns(UserWarning):
        valid, errors = validate_match(pl.DataFrame({"x": [127]}, schema={"x": pl.Int8}), schema)
    assert not valid and "x" in errors[0]


def test_extracted_nested_width_is_portable_without_backend_spelling():
    import polars as pl
    import pyarrow as pa
    from mountainash.typespec.extraction import extract_from_dataframe

    frame = pl.DataFrame(schema={"record": pl.Struct({"id": pl.Int8, "payload": pl.Binary})})
    schema = extract_from_dataframe(frame, preserve_backend_types=False)
    restored = TableSchema.from_frictionless(schema.to_frictionless())
    assert to_arrow_schema(restored).field("record").type == pa.struct([
        pa.field("id", pa.int8()), pa.field("payload", pa.binary()),
    ])


# ============================================================================
# Native schema adapters: carrier, standalone decode and encode
# ============================================================================


def _adapter(target):
    from mountainash.typespec.adapter_registry import get_native_schema_adapter

    return get_native_schema_adapter(target)


def _fidelity_schema(target):
    """A native schema per carrier holding parameterized types its target represents exactly.

    Narwhals Time is nanosecond-only and carries no precision, so it is absent there.
    """
    pytest.importorskip(target.value)
    if target is TypeTarget.POLARS:
        import polars as pl

        return {
            "ts": pl.Datetime("ms", "UTC"), "t": pl.Time, "dec": pl.Decimal(12, 4), "dur": pl.Duration("ms"),
            "rows": pl.List(pl.Struct({"a": pl.Int16, "at": pl.Datetime("us")})),
            "fixed": pl.Array(pl.Int16, (2, 3)),
        }
    if target is TypeTarget.PYARROW:
        import pyarrow as pa

        return pa.schema([
            ("ts", pa.timestamp("ms", "UTC")), ("t", pa.time64("us")), ("dec", pa.decimal128(12, 4)),
            ("dur", pa.duration("ms")),
            ("rows", pa.list_(pa.struct([("a", pa.int16()), ("at", pa.timestamp("us"))]))),
            ("fixed", pa.list_(pa.list_(pa.int16(), 3), 2)),
        ])
    if target is TypeTarget.PANDAS:
        import pandas as pd
        import pyarrow as pa

        return {
            "ts": pd.DatetimeTZDtype(unit="ms", tz="UTC"),
            "t": pd.ArrowDtype(pa.time64("us")), "dec": pd.ArrowDtype(pa.decimal128(12, 4)),
            "dur": pd.ArrowDtype(pa.duration("ms")),
            "rows": pd.ArrowDtype(pa.list_(pa.struct([("a", pa.int16()), ("at", pa.timestamp("us"))]))),
            "fixed": pd.ArrowDtype(pa.list_(pa.list_(pa.int16(), 3), 2)),
        }
    if target is TypeTarget.IBIS:
        import ibis.expr.datatypes as dt

        return {
            "ts": dt.Timestamp(timezone="UTC", scale=3), "t": dt.time, "dec": dt.Decimal(12, 4),
            "dur": dt.Interval("ms"),
            "rows": dt.Array(dt.Struct({"a": dt.int16, "at": dt.Timestamp(scale=6)})),
            "fixed": dt.Array(dt.Array(dt.int16, length=3), length=2),
        }
    import narwhals as nw

    return {
        "ts": nw.Datetime("ms", "UTC"), "dec": nw.Decimal(12, 4), "dur": nw.Duration("ms"),
        "rows": nw.List(nw.Struct({"a": nw.Int16, "at": nw.Datetime("us")})),
        "fixed": nw.Array(nw.Int16, (2, 3)),
    }


class TestNativeSchemaAdapterRoundTrip:
    """decode(encode(schema)) retains the representable portable shape."""

    DEFINITIONS = {
        "id": FieldDefinition(dtype=D.I32),
        "name": FieldDefinition(type=U.STRING),
        "record": FieldDefinition(fields={
            "a": FieldDefinition(dtype=D.I16),
            "tags": FieldDefinition(element=FieldDefinition(type=U.STRING)),
        }),
    }

    @pytest.mark.parametrize(
        "target",
        [TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.IBIS, TypeTarget.NARWHALS],
    )
    def test_encode_then_decode_keeps_names_order_and_structure(self, target):
        pytest.importorskip("pyarrow" if target is TypeTarget.PYARROW else target.value)
        schema = TableSchema(fields=dict(self.DEFINITIONS))
        resolved = {
            name: resolve_field_type(definition, source=None, target=target, path=(name,))
            for name, definition in schema.fields.items()
        }
        adapter = _adapter(target)
        shapes = adapter.decode_schema(adapter.encode_schema(schema, resolved_types=resolved))
        assert list(shapes) == ["id", "name", "record"]
        assert shapes["id"].canonical_type is D.I32
        record = shapes["record"]
        assert record.canonical_type is D.STRUCT
        assert [name for name, _ in record.struct_fields] == ["a", "tags"]
        assert record.struct_fields[0][1].canonical_type is D.I16
        assert record.struct_fields[1][1].item_shape == SourceShape(D.STRING)

    def test_pandas_dtype_mapping_decodes(self):
        schema = TableSchema(fields={"id": FieldDefinition(dtype=D.I32)})
        adapter = _adapter(TypeTarget.PANDAS)
        encoded = adapter.encode_schema(schema, resolved_types={"id": D.I32})
        assert adapter.decode_schema(encoded)["id"].canonical_type is D.I32

    @pytest.mark.parametrize("target", [
        TypeTarget.POLARS, TypeTarget.PYARROW, TypeTarget.PANDAS, TypeTarget.IBIS, TypeTarget.NARWHALS,
    ])
    def test_parameterized_native_types_survive_decode_then_encode(self, target):
        """Time/timestamp/duration/decimal parameters and nesting are lossless where the target can hold them."""
        native = _fidelity_schema(target)
        adapter = _adapter(target)
        shapes = adapter.decode_schema(native)
        schema = TableSchema(fields={
            name: FieldDefinition(dtype=shape.detailed_dtype) for name, shape in shapes.items()
        })
        resolved = {
            name: resolve_field_type(definition, source=shapes[name], target=target, path=(name,))
            for name, definition in schema.fields.items()
        }
        assert adapter.encode_schema(schema, resolved_types=resolved) == native

    def test_encode_does_not_mutate_the_declarations(self):
        schema = TableSchema(fields=dict(self.DEFINITIONS))
        before = dict(schema.fields)
        resolved = {name: D.STRING for name in schema.fields}
        _adapter(TypeTarget.POLARS).encode_schema(schema, resolved_types=resolved)
        assert schema.fields == before


class TestArrowFieldQualifiers:
    def _field(self):
        pa = pytest.importorskip("pyarrow")
        return pa.field("x", pa.int64(), nullable=False, metadata={"unit": "m"})

    def test_acquisition_decode_extraction_and_encode_reconstruct_the_field(self):
        pa = pytest.importorskip("pyarrow")
        adapter = _adapter(TypeTarget.PYARROW)
        original = pa.schema([self._field()])
        shapes = adapter.extract_schema(pa.table({"x": pa.array([1], pa.int64())}).cast(original))
        assert shapes == adapter.decode_schema(original)
        native = shapes["x"].native_dtype
        assert native is not None and native.target is TypeTarget.PYARROW
        schema = TableSchema(fields={"x": FieldDefinition(backend_type=native)})
        resolved = {"x": resolve_field_type(
            schema.fields["x"], source=shapes["x"], target=TypeTarget.PYARROW, path=("x",),
        )}
        rebuilt = adapter.encode_schema(schema, resolved_types=resolved)
        assert rebuilt.field("x").equals(self._field(), check_metadata=True)
        assert rebuilt.field("x").nullable is False

    def test_portable_evidence_keeps_the_type_without_inventing_requirements(self):
        pa = pytest.importorskip("pyarrow")
        shapes = _adapter(TypeTarget.PYARROW).decode_schema(pa.schema([self._field()]))
        assert shapes["x"].canonical_type is D.I64
        schema = TableSchema(fields={"x": FieldDefinition(dtype=D.I64)})
        assert schema.fields["x"].constraints.required is False

    def test_dtype_only_conversion_keeps_refusing_field_qualifiers(self):
        from mountainash.core.dtypes.errors import DtypeMappingError

        shapes = _adapter(TypeTarget.PYARROW).decode_schema(
            __import__("pyarrow").schema([self._field()])
        )
        with pytest.raises(DtypeMappingError, match="qualifier"):
            registry.to_native_schema(shapes["x"].native_dtype, TypeTarget.PYARROW)

    def test_plain_arrow_columns_carry_their_type_as_native_evidence(self):
        pa = pytest.importorskip("pyarrow")
        shapes = _adapter(TypeTarget.PYARROW).decode_schema(pa.schema([pa.field("y", pa.int32())]))
        assert shapes["y"].native_dtype == NativeDtype(value=pa.int32(), target=TypeTarget.PYARROW)

    def test_extraction_then_encoding_reconstructs_the_original_schema(self):
        pa = pytest.importorskip("pyarrow")
        from mountainash.typespec.extraction import extract_from_dataframe

        original = pa.schema([self._field()])
        table = pa.table({"x": pa.array([1], pa.int64())}).cast(original)
        extracted = extract_from_dataframe(table, preserve_backend_types=True)
        assert to_arrow_schema(extracted).equals(original, check_metadata=True)
        portable = extract_from_dataframe(table, preserve_backend_types=False)
        assert portable.fields["x"].constraints.required is not True

    def test_nested_member_and_element_qualifiers_are_kept_by_schema_construction(self):
        pa = pytest.importorskip("pyarrow")
        member = pa.field("a", pa.int64(), nullable=False, metadata={"unit": "m"})
        element = pa.field("item", pa.int64(), nullable=False)
        original = pa.schema([
            pa.field("record", pa.struct([member])),
            pa.field("values", pa.list_(element)),
            pa.field("pair", pa.list_(element, 2)),
        ])
        adapter = _adapter(TypeTarget.PYARROW)
        shapes = adapter.decode_schema(original)
        schema = _schema(
            record=FieldDefinition(fields={
                "a": FieldDefinition(backend_type=shapes["record"].struct_fields[0][1].native_dtype),
            }),
            values=FieldDefinition(element=FieldDefinition(backend_type=shapes["values"].item_shape.native_dtype)),
            pair=FieldDefinition(
                element=FieldDefinition(backend_type=shapes["pair"].item_shape.native_dtype), dimensions=(2,),
            ),
        )
        assert to_arrow_schema(schema).equals(original, check_metadata=True)


# ============================================================================
# Registries
# ============================================================================


class TestAdapterRegistry:
    def test_adapter_instances_are_stateless_and_retained(self):
        from mountainash.typespec.adapter_registry import NATIVE_SCHEMA_ADAPTERS, get_native_schema_adapter

        for target in NATIVE_SCHEMA_ADAPTERS.list_keys():
            assert get_native_schema_adapter(target) is get_native_schema_adapter(target)

    def test_python_dtype_target_has_no_table_schema_adapter(self):
        from mountainash.typespec.adapter_registry import get_native_schema_adapter

        with pytest.raises(KeyError):
            get_native_schema_adapter(TypeTarget.PYTHON)

    def test_codec_registry_resolves_the_frictionless_codec_by_name(self):
        from mountainash.typespec.adapter_registry import get_schema_codec

        codec = get_schema_codec("frictionless")
        schema = _schema(id=FieldDefinition(type=U.INTEGER))
        assert codec.decode(codec.encode(schema)).fields["id"].type is U.INTEGER

    def test_unknown_codec_names_the_available_formats(self):
        from mountainash.typespec.adapter_registry import get_schema_codec

        with pytest.raises(KeyError, match="frictionless"):
            get_schema_codec("no-such-format")

    def test_selecting_one_adapter_does_not_import_other_optional_libraries(self):
        import subprocess
        import sys

        code = (
            "import sys\n"
            "from mountainash.core.dtypes import TypeTarget\n"
            "from mountainash.typespec.adapter_registry import get_native_schema_adapter\n"
            "from mountainash.typespec.spec import FieldDefinition, TableSchema\n"
            "from mountainash.typespec.universal_types import UniversalType\n"
            "adapter = get_native_schema_adapter(TypeTarget.POLARS)\n"
            "adapter.encode_schema(TableSchema(fields={'x': FieldDefinition(type=UniversalType.INTEGER)}),"
            " resolved_types={'x': __import__('mountainash.core.dtypes', fromlist=['x']).MountainashDtype.I64})\n"
            "assert 'polars' in sys.modules\n"
            "for name in ('pandas', 'ibis', 'pyarrow'):\n"
            "    assert name not in sys.modules, name\n"
        )
        completed = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr


def test_central_recognition_identifies_each_supported_schema_carrier():
    from mountainash.core.types import detect_schema_carrier

    pl = pytest.importorskip("polars")
    pd = pytest.importorskip("pandas")
    pa = pytest.importorskip("pyarrow")
    nw = pytest.importorskip("narwhals")
    ibis = pytest.importorskip("ibis")
    frame = pl.DataFrame({"x": [1]})
    assert detect_schema_carrier(frame) is TypeTarget.POLARS
    assert detect_schema_carrier(frame.lazy()) is TypeTarget.POLARS
    assert detect_schema_carrier(pd.DataFrame({"x": [1]})) is TypeTarget.PANDAS
    assert detect_schema_carrier(pa.table({"x": [1]})) is TypeTarget.PYARROW
    assert detect_schema_carrier(nw.from_native(frame)) is TypeTarget.NARWHALS
    assert detect_schema_carrier(ibis.table({"x": "int64"}, name="t")) is TypeTarget.IBIS
    assert detect_schema_carrier(ibis.literal(1)) is None
    assert detect_schema_carrier(object()) is None


@pytest.mark.parametrize("backend", ["polars", "pandas", "pyarrow", "ibis", "narwhals"])
def test_nested_lexical_list_keeps_its_declared_item_type(backend):
    import ibis.expr.datatypes as dt
    import narwhals as nw
    import pandas as pd
    import polars as pl
    import pyarrow as pa

    schema = TableSchema(fields={"record": FieldDefinition(fields={
        "codes": FieldDefinition(type=UniversalType.LIST, item_type="integer"),
    })})
    record = pa.struct([pa.field("codes", pa.list_(pa.int64()))])
    expected = {
        "polars": {"record": pl.Struct({"codes": pl.List(pl.Int64)})},
        "pandas": {"record": pd.ArrowDtype(record)},
        "pyarrow": pa.schema([pa.field("record", record)]),
        "ibis": {"record": dt.Struct({"codes": dt.Array(dt.int64)})},
        "narwhals": {"record": nw.Struct({"codes": nw.List(nw.Int64)})},
    }
    encoded = convert_to_backend(schema, backend)
    assert encoded == expected[backend]
    from mountainash.typespec.adapter_registry import get_native_schema_adapter
    from mountainash.core.dtypes import MountainashDtype, TypeTarget

    shape = get_native_schema_adapter(TypeTarget(backend)).decode_schema(encoded)["record"]
    assert dict(shape.struct_fields)["codes"].item_shape.canonical_type is MountainashDtype.I64
