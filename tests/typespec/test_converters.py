"""
Tests for mountainash.typespec.converters.

Covers:
- to_polars_schema
- to_pandas_dtypes
- to_arrow_schema
- to_ibis_schema
- convert_to_backend (dispatch + unknown backend)
- backend_type preservation
"""
from __future__ import annotations

import pytest

from mountainash.core.dtypes import MountainashDtype as D
from mountainash.core.dtypes import TypeTarget, registry
from mountainash.typespec.converters import (
    _resolve_field_native,
    convert_to_backend,
    resolve_field_canonical,
    to_arrow_schema,
    to_ibis_schema,
    to_pandas_dtypes,
    to_polars_schema,
)
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.universal_types import UniversalType as U
from mountainash.typespec.spec import FieldSpec, TypeSpec


# ============================================================================
# Shared fixture schema
# ============================================================================

@pytest.fixture()
def basic_schema():
    return TypeSpec.from_simple_dict({
        "id": "integer",
        "name": "string",
        "score": "number",
        "active": "boolean",
    })


# ============================================================================
# TestToPolarsSchema
# ============================================================================

class TestToPolarsSchema:
    """to_polars_schema() tests."""

    def test_basic_types_produce_correct_polars_dtypes(self, basic_schema):
        import polars as pl

        result = to_polars_schema(basic_schema)
        assert result["id"] == pl.Int64
        assert result["name"] in (pl.Utf8, pl.String)
        assert result["score"] == pl.Float64
        assert result["active"] == pl.Boolean

    def test_all_universal_types_produce_a_result(self):
        """Every UniversalType value should map to a Polars dtype without raising."""
        import polars as pl

        fields = [FieldSpec(name=f"col_{ut.value}", type=ut) for ut in UniversalType]
        schema = TypeSpec(fields=fields)
        result = to_polars_schema(schema)
        assert len(result) == len(list(UniversalType))
        for col, dtype in result.items():
            assert dtype is not None

    def test_returns_dict(self, basic_schema):
        result = to_polars_schema(basic_schema)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"id", "name", "score", "active"}


# ============================================================================
# TestToPandasDtypes
# ============================================================================

class TestToPandasDtypes:
    """to_pandas_dtypes() tests."""

    def test_basic_types_produce_correct_strings(self, basic_schema):
        result = to_pandas_dtypes(basic_schema)
        assert result["id"] == "Int64"
        assert result["name"] == "string"
        assert result["score"] == "float64"
        assert result["active"] == "boolean"

    def test_all_universal_types_produce_a_result(self):
        fields = [FieldSpec(name=f"col_{ut.value}", type=ut) for ut in UniversalType]
        schema = TypeSpec(fields=fields)
        result = to_pandas_dtypes(schema)
        assert len(result) == len(list(UniversalType))

    def test_returns_dict_of_strings(self, basic_schema):
        """Non-categorical fields are plain strings; a categorical field is
        the deliberate exception (a real pd.CategoricalDtype instance)."""
        import pandas as pd
        categorical = TypeSpec(fields=[
            FieldSpec(name="cat", type=UniversalType.STRING,
                      categories=["a", "b"], categories_ordered=True),
        ])
        result = to_pandas_dtypes(basic_schema)
        assert isinstance(result, dict)
        for v in result.values():
            assert isinstance(v, str)
        cat_result = to_pandas_dtypes(categorical)
        assert isinstance(cat_result["cat"], pd.CategoricalDtype)
        assert not isinstance(cat_result["cat"], str)

    def test_categorical_field_returns_categorical_dtype(self):
        """§4.3: to_pandas_dtypes returns a real pd.CategoricalDtype instance
        for a categorical field — pandas accepts it directly as astype input."""
        import pandas as pd
        spec = TypeSpec(fields=[
            FieldSpec(name="col", type=UniversalType.STRING,
                      categories=["a", "b"], categories_ordered=True),
        ])
        result = to_pandas_dtypes(spec)
        assert isinstance(result["col"], pd.CategoricalDtype)
        assert list(result["col"].categories) == ["a", "b"]
        assert result["col"].ordered is True

    def test_unordered_categorical_field_ordered_false(self):
        import pandas as pd
        spec = TypeSpec(fields=[
            FieldSpec(name="col", type=UniversalType.STRING,
                      categories=["a", "b"], categories_ordered=False),
        ])
        result = to_pandas_dtypes(spec)
        assert isinstance(result["col"], pd.CategoricalDtype)
        assert result["col"].ordered is False


# ============================================================================
# TestToArrowSchema
# ============================================================================

class TestToArrowSchema:
    """to_arrow_schema() tests."""

    def test_returns_pyarrow_schema(self, basic_schema):
        pa = pytest.importorskip("pyarrow")
        result = to_arrow_schema(basic_schema)
        assert isinstance(result, pa.Schema)

    def test_correct_field_types(self, basic_schema):
        pa = pytest.importorskip("pyarrow")
        result = to_arrow_schema(basic_schema)
        assert result.field("id").type == pa.int64()
        assert result.field("name").type in (pa.string(), pa.large_string(), pa.utf8())
        assert result.field("score").type == pa.float64()
        assert result.field("active").type == pa.bool_()

    def test_field_names_preserved(self, basic_schema):
        pytest.importorskip("pyarrow")
        result = to_arrow_schema(basic_schema)
        assert set(result.names) == {"id", "name", "score", "active"}


# ============================================================================
# TestToIbisSchema
# ============================================================================

class TestToIbisSchema:
    """to_ibis_schema() tests."""

    def test_basic_types_produce_correct_ibis_strings(self, basic_schema):
        result = to_ibis_schema(basic_schema)
        assert result["id"] == "int64"
        assert result["name"] == "string"
        assert result["score"] == "float64"
        # spec 2026-06-10-type-system-unification: BOOL->IBIS canon is "boolean" (was "bool")
        assert result["active"] == "boolean"

    def test_all_universal_types_produce_a_result(self):
        fields = [FieldSpec(name=f"col_{ut.value}", type=ut) for ut in UniversalType]
        schema = TypeSpec(fields=fields)
        result = to_ibis_schema(schema)
        assert len(result) == len(list(UniversalType))

    def test_returns_dict_of_strings(self, basic_schema):
        result = to_ibis_schema(basic_schema)
        assert isinstance(result, dict)
        for v in result.values():
            assert isinstance(v, str)


# ============================================================================
# TestConvertToBackend
# ============================================================================

class TestConvertToBackend:
    """convert_to_backend() tests — dispatch and edge cases."""

    @pytest.mark.parametrize("backend", ["polars", "pandas", "ibis"])
    def test_known_backends_dispatch(self, basic_schema, backend):
        result = convert_to_backend(basic_schema, backend)
        assert result is not None
        assert isinstance(result, dict)

    def test_arrow_backend_dispatches(self, basic_schema):
        pytest.importorskip("pyarrow")
        pa = pytest.importorskip("pyarrow")
        result = convert_to_backend(basic_schema, "arrow")
        assert isinstance(result, pa.Schema)

    def test_pyarrow_alias_dispatches(self, basic_schema):
        pytest.importorskip("pyarrow")
        pa = pytest.importorskip("pyarrow")
        result = convert_to_backend(basic_schema, "pyarrow")
        assert isinstance(result, pa.Schema)

    def test_unknown_backend_raises_value_error(self, basic_schema):
        with pytest.raises(ValueError, match="Unknown backend"):
            convert_to_backend(basic_schema, "unknown_backend")

    def test_backend_type_preserved_in_polars(self):
        """FieldSpec with backend_type should use that type in polars output."""
        import polars as pl

        field = FieldSpec(name="val", type=UniversalType.NUMBER, backend_type="Float32")
        schema = TypeSpec(fields=[field])
        result = to_polars_schema(schema)
        assert result["val"] == pl.Float32

    def test_backend_type_preserved_in_pandas(self):
        """FieldSpec with backend_type should pass through as-is for pandas."""
        field = FieldSpec(name="val", type=UniversalType.NUMBER, backend_type="Float32")
        schema = TypeSpec(fields=[field])
        result = to_pandas_dtypes(schema)
        assert result["val"] == "Float32"

    def test_backend_type_preserved_in_ibis(self):
        """FieldSpec with backend_type should pass through as-is for ibis."""
        field = FieldSpec(name="val", type=UniversalType.NUMBER, backend_type="float32")
        schema = TypeSpec(fields=[field])
        result = to_ibis_schema(schema)
        assert result["val"] == "float32"


# ============================================================================
# TestCategoricalSchema (item 54, gap 3)
# ============================================================================

class TestCategoricalSchema:
    """Gap 3: categories/categoriesOrdered -> real Polars categorical.

    categories takes priority over backend_type/type entirely — mirrors
    conform stage 5's mutually-exclusive branch ordering exactly."""

    def _spec(self, categories, ordered=None, backend_type=None):
        return TypeSpec(fields=[
            FieldSpec(
                name="cat",
                type=UniversalType.STRING,
                categories=categories,
                categories_ordered=ordered,
                backend_type=backend_type,
            ),
        ])

    def test_unordered_categories_is_pl_categorical(self):
        import polars as pl
        result = to_polars_schema(self._spec(["a", "b"], ordered=False))
        assert result["cat"] is pl.Categorical

    def test_ordered_categories_is_pl_enum(self):
        import polars as pl
        result = to_polars_schema(self._spec(["a", "b"], ordered=True))
        assert result["cat"] == pl.Enum(["a", "b"])

    def test_object_form_categories_use_shared_extraction(self):
        """Object-form categories must extract identically to conform's
        stage-5b (shared categorical_values helper — no drift)."""
        import polars as pl
        from mountainash.typespec._categorical import categorical_values
        cats = [{"value": 0, "label": "Low"}, {"value": 1, "label": "High"}]
        result = to_polars_schema(self._spec(cats, ordered=True))
        assert result["cat"] == pl.Enum([str(v) for v in categorical_values(cats)])

    def test_categories_win_over_invalid_backend_type(self):
        """Precedence (spec §5): a field with BOTH categories set AND an
        invalid backend_type takes the categorical branch and never raises —
        the backend_type is never even parsed for such a field."""
        import polars as pl
        result = to_polars_schema(self._spec(["a"], ordered=False, backend_type="garbage"))
        assert result["cat"] is pl.Categorical

    def test_ibis_categories_stay_string(self):
        """Ibis has no categorical primitive — categories present still
        resolves to string (explicit, not silently untested)."""
        result = to_ibis_schema(self._spec(["a", "b"], ordered=True))
        assert result["cat"] == "string"


# ============================================================================
# TestNestedListItemType (item 54, gap 2)
# ============================================================================

class TestNestedListItemType:
    """Gap 2: nested LIST inner type via the existing FieldSpec.item_type.

    item_type is a Frictionless-standard carriage (spec §list) already carried
    on FieldSpec — the resolver previously never read it, so ARRAY resolved to
    a bare container (and PyArrow silently defaulted every untyped list to a
    string element)."""

    def _spec(self, item_type=None):
        return TypeSpec(fields=[
            FieldSpec(name="lst", type=UniversalType.ARRAY, item_type=item_type),
        ])

    def test_polars_item_type_resolves_inner(self):
        import polars as pl
        result = to_polars_schema(self._spec("integer"))
        assert result["lst"] == pl.List(pl.Int64)

    def test_narwhals_item_type_resolves_inner(self):
        import narwhals as nw
        result = to_polars_schema(self._spec("integer"))
        # narwhals wraps the already-cast polars-native frame on the live
        # consumers (empty_frame / inline-read); assert the narwhals-native
        # form of the same inner type is reachable via the registry.
        from mountainash.core.dtypes import TypeTarget, registry
        from mountainash.typespec.converters import _resolve_field_native
        native = _resolve_field_native(self._spec("integer").fields[0], TypeTarget.NARWHALS)
        assert native == nw.List(nw.Int64)
        assert native is not nw.List  # real parameterized instance, not bare class

    def test_pyarrow_item_type_resolves_inner_not_string(self):
        """Second latent bug regression: the bare fallback silently defaulted
        every untyped list to a string element. With item_type the inner must
        be the real element type."""
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        result = to_arrow_schema(self._spec("integer"))
        field = result.field("lst")
        assert field.type == pa.list_(pa.int64())
        assert field.type.value_type == pa.int64()  # NOT pa.string()

    def test_ibis_item_type_resolves_inner(self):
        result = to_ibis_schema(self._spec("integer"))
        assert result["lst"] == "array<int64>"

    def test_pandas_stays_object(self):
        """Pandas has no native parameterized list dtype — 'object' is the
        correct, only representation (regression lock, not a gap)."""
        result = to_pandas_dtypes(self._spec("integer"))
        assert result["lst"] == "object"

    @pytest.mark.parametrize("item_type", [None, "any"])
    def test_no_parameterization_keeps_bare_container(self, item_type):
        """No item_type (or item_type='any' — same code path) -> bare
        container, unchanged (regression)."""
        import polars as pl
        result = to_polars_schema(self._spec(item_type))
        assert result["lst"] is pl.List

    def test_unknown_item_type_raises_with_field_context_and_chain(self):
        """item_type='garbage' is a second raise surface beyond
        InvalidBackendTypeError: UnknownDtypeError naming the field, chained
        to the original parse_universal error (chain must not be dropped)."""
        from mountainash.core.dtypes import UnknownDtypeError
        with pytest.raises(UnknownDtypeError) as exc_info:
            to_polars_schema(self._spec("garbage"))
        assert "lst" in str(exc_info.value)
        assert "garbage" in str(exc_info.value)
        # chain: __cause__ is the original UnknownDtypeError parse_universal
        # raised, not swallowed by a message-only copy
        assert isinstance(exc_info.value.__cause__, UnknownDtypeError)


# ============================================================================
# TestGeospatialItemType (item 113 Unit B, Task 2)
#
# item_type is a raw UniversalType-string carriage (parsed via
# parse_universal then to_canonical) — it has no FieldSpec.format context of
# its own, so item_type="geopoint" hits to_canonical(GEOPOINT) directly and
# must raise the same AmbiguousGeospatialTypeError a bare to_canonical()
# call would. item_type="geojson" resolves statically to canonical JSON
# (a string on every target) with no field-context ambiguity — the LIST
# wraps a JSON-string element.
# ============================================================================

class TestGeospatialItemType:
    def _spec(self, item_type):
        return TypeSpec(fields=[
            FieldSpec(name="lst", type=UniversalType.ARRAY, item_type=item_type),
        ])

    def test_item_type_geopoint_raises_ambiguous(self):
        from mountainash.typespec.errors import AmbiguousGeospatialTypeError
        with pytest.raises(AmbiguousGeospatialTypeError):
            to_polars_schema(self._spec("geopoint"))

    def test_item_type_geojson_produces_string_backed_list(self):
        import polars as pl
        result = to_polars_schema(self._spec("geojson"))
        assert result["lst"] == pl.List(pl.String)


# ============================================================================
# TestNestedStructObjectFields (item 102)
# ============================================================================

class TestNestedStructObjectFields:
    """object_fields: nested STRUCT inner-field schema via FieldSpec."""

    def _spec(self, object_fields=None):
        return TypeSpec(fields=[
            FieldSpec(name="addr", type=UniversalType.OBJECT, object_fields=object_fields),
        ])

    def _flat_fields(self):
        return [
            FieldSpec(name="street", type=UniversalType.STRING),
            FieldSpec(name="zip", type=UniversalType.STRING),
        ]

    def _nested_fields(self):
        return [
            FieldSpec(name="street", type=UniversalType.STRING),
            FieldSpec(name="geo", type=UniversalType.OBJECT, object_fields=[
                FieldSpec(name="lat", type=UniversalType.NUMBER),
                FieldSpec(name="lon", type=UniversalType.NUMBER),
            ]),
        ]

    def test_polars_flat_struct_resolves_inner_fields(self):
        import polars as pl
        result = to_polars_schema(self._spec(self._flat_fields()))
        assert result["addr"] == pl.Struct({"street": pl.String, "zip": pl.String})

    def test_polars_two_level_nested_struct_resolves_recursively(self):
        import polars as pl
        result = to_polars_schema(self._spec(self._nested_fields()))
        expected = pl.Struct({
            "street": pl.String,
            "geo": pl.Struct({"lat": pl.Float64, "lon": pl.Float64}),
        })
        assert result["addr"] == expected

    def test_pyarrow_flat_struct_resolves_inner_fields(self):
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        result = to_arrow_schema(self._spec(self._flat_fields()))
        field = result.field("addr")
        assert pa.types.is_struct(field.type)
        assert field.type.field("street").type == pa.string()
        assert field.type.field("zip").type == pa.string()

    def test_narwhals_flat_struct_resolves_inner_fields(self):
        import narwhals as nw
        from mountainash.core.dtypes import TypeTarget
        from mountainash.typespec.converters import _resolve_field_native
        native = _resolve_field_native(self._spec(self._flat_fields()).fields[0], TypeTarget.NARWHALS)
        assert native == nw.Struct({"street": nw.String, "zip": nw.String})

    def test_ibis_flat_struct_resolves_inner_fields_as_schema_string(self):
        result = to_ibis_schema(self._spec(self._flat_fields()))
        assert result["addr"] == "struct<street: string, zip: string>"

    def test_ibis_two_level_nested_struct_schema_string(self):
        result = to_ibis_schema(self._spec(self._nested_fields()))
        assert result["addr"] == "struct<street: string, geo: struct<lat: float64, lon: float64>>"

    def test_pandas_stays_object_regardless_of_object_fields(self):
        result = to_pandas_dtypes(self._spec(self._flat_fields()))
        assert result["addr"] == "object"

    def test_no_object_fields_keeps_bare_container(self):
        import polars as pl
        result = to_polars_schema(self._spec(None))
        assert result["addr"] is pl.Struct

    def test_empty_object_fields_list_keeps_bare_container(self):
        import polars as pl
        result = to_polars_schema(self._spec([]))
        assert result["addr"] is pl.Struct

    def test_inner_field_categories_resolve_correctly(self):
        import polars as pl
        fields = [FieldSpec(name="kind", type=UniversalType.STRING,
                            categories=["home", "work"], categories_ordered=True)]
        result = to_polars_schema(self._spec(fields))
        assert result["addr"] == pl.Struct({"kind": pl.Enum(["home", "work"])})

    def test_recursion_error_on_pathologically_deep_chain(self):
        from mountainash.core.dtypes import TypeTarget
        from mountainash.typespec.converters import _resolve_struct_inner
        deep = FieldSpec(name="leaf", type=UniversalType.INTEGER)
        for i in range(10000):
            deep = FieldSpec(name=f"level_{i}", type=UniversalType.OBJECT, object_fields=[deep])
        with pytest.raises(RecursionError):
            _resolve_struct_inner("addr", [deep], TypeTarget.POLARS, None)


# ============================================================================
# TestCategoricalRefactorRegression (item 102, spec §4.1)
# ============================================================================

class TestCategoricalRefactorRegression:
    def test_resolve_field_native_polars_categorical(self):
        import polars as pl
        from mountainash.core.dtypes import TypeTarget
        from mountainash.typespec.converters import _resolve_field_native
        field = FieldSpec(name="cat", type=UniversalType.STRING,
                          categories=["a", "b"], categories_ordered=False)
        assert _resolve_field_native(field, TypeTarget.POLARS) is pl.Categorical

    def test_resolve_field_native_pandas_categorical(self):
        import pandas as pd
        from mountainash.core.dtypes import TypeTarget
        from mountainash.typespec.converters import _resolve_field_native
        field = FieldSpec(name="cat", type=UniversalType.STRING,
                          categories=["a", "b"], categories_ordered=True)
        result = _resolve_field_native(field, TypeTarget.PANDAS)
        assert isinstance(result, pd.CategoricalDtype)
        assert list(result.categories) == ["a", "b"]
        assert result.ordered is True



# ============================================================================
# TestConvertersOverRegistry
# ============================================================================

class TestConvertersOverRegistry:
    def test_year_now_string(self):
        """item 113 Unit B, Task 2: YEAR's canonical mapping changed from
        the physical int32 refinement to the semantic-string XSD_YEAR type
        (an XSD year is a lexical form, not a bounded physical integer) —
        it now materializes as string on every target, same as YEARMONTH."""
        import polars as pl
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_polars_schema, to_pandas_dtypes
        spec = TypeSpec(fields=[FieldSpec(name="y", type=UniversalType.YEAR)])
        assert to_polars_schema(spec)["y"] is pl.String
        assert to_pandas_dtypes(spec)["y"] == "string"

    def test_yearmonth_now_string_on_pandas(self):
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_pandas_dtypes
        spec = TypeSpec(fields=[FieldSpec(name="ym", type=UniversalType.YEARMONTH)])
        assert to_pandas_dtypes(spec)["ym"] == "string"  # spec: known change (was period[M])

    def test_any_materializes_as_string(self):
        import polars as pl
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_polars_schema
        spec = TypeSpec(fields=[FieldSpec(name="a", type=UniversalType.ANY)])
        assert to_polars_schema(spec)["a"] is pl.String

    def test_invalid_backend_type_raises_on_every_fixed_target(self):
        """Spec §7 test 6: the raise fires per-target on the three targets
        whose parsers were upgraded (Polars/Narwhals/PyArrow). Ibis/Pandas
        are skipped — their parsers are already correct and regression-locked
        (Task 5), so an unparseable string there is not the primary surface."""
        from mountainash.core.dtypes import InvalidBackendTypeError, TypeTarget
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import _resolve_field_native
        field = FieldSpec(name="x", type=UniversalType.INTEGER, backend_type="garbage")
        for target in (TypeTarget.POLARS, TypeTarget.NARWHALS, TypeTarget.PYARROW):
            with pytest.raises(InvalidBackendTypeError) as exc_info:
                _resolve_field_native(field, target)
            msg = str(exc_info.value)
            assert "x" in msg          # names the field
            assert "garbage" in msg    # names the string
            assert target.value in msg  # names its own target

    @pytest.mark.parametrize("backend_type", [None, ""])
    def test_empty_or_none_backend_type_falls_through(self, backend_type):
        """Spec §5: backend_type=None/"" is 'no override given', not invalid
        input — falls through to canonical (item 53's ANY->STRING case relies
        on this)."""
        import polars as pl
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_polars_schema
        spec = TypeSpec(fields=[
            FieldSpec(name="x", type=UniversalType.INTEGER, backend_type=backend_type),
        ])
        assert to_polars_schema(spec)["x"] is pl.Int64

    def test_semantically_invalid_backend_type_raises_typed_error_not_raw(self):
        """Regression (GLM-5.2 whole-branch review, Important finding 1): a
        syntactically-valid-but-semantically-invalid PyArrow string
        (timestamp[badunit]) must surface as the typed InvalidBackendTypeError
        through the converter, never a raw Arrow constructor ValueError."""
        from mountainash.core.dtypes import InvalidBackendTypeError
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_arrow_schema
        spec = TypeSpec(fields=[
            FieldSpec(name="x", type=UniversalType.INTEGER,
                      backend_type="timestamp[badunit]"),
        ])
        with pytest.raises(InvalidBackendTypeError, match="timestamp\[badunit\]"):
            to_arrow_schema(spec)

    def test_backend_type_preferred_when_parseable(self):
        import polars as pl
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_polars_schema
        spec = TypeSpec(fields=[
            FieldSpec(name="x", type=UniversalType.INTEGER, backend_type="Int32"),
        ])
        assert to_polars_schema(spec)["x"] is pl.Int32

    def test_unparseable_backend_type_raises(self):
        """Validation strictness (item 54, §5): a non-empty, non-None
        backend_type that the target cannot parse raises — the resolver no
        longer silently falls back to canonical."""
        import polars as pl
        from mountainash.core.dtypes import InvalidBackendTypeError
        from mountainash.typespec import TypeSpec, FieldSpec
        from mountainash.typespec.universal_types import UniversalType
        from mountainash.typespec.converters import to_polars_schema
        spec = TypeSpec(fields=[
            FieldSpec(name="x", type=UniversalType.INTEGER, backend_type="garbage"),
        ])
        with pytest.raises(InvalidBackendTypeError, match="garbage"):
            to_polars_schema(spec)


# ============================================================================
# TestV2FieldsAcrossTargets (item 113 Unit B, Task 2)
#
# Introspected cross product over every TypeTarget — the exhaustive
# converter-fixture migration this task requires: these fixtures call
# _resolve_field_native(field, target) (the field-aware path), not the old
# context-free to_canonical(field.type) — GEOPOINT with no field.format
# override would raise AmbiguousGeospatialTypeError through that path.
# ============================================================================

@pytest.mark.parametrize("target", list(TypeTarget))
@pytest.mark.parametrize(
    "field,canonical",
    [
        (FieldSpec("list", U.LIST), D.LIST),
        (FieldSpec("array", U.ARRAY), D.LIST),
        (FieldSpec("point_text", U.GEOPOINT), D.STRING),
        (FieldSpec("point_array", U.GEOPOINT, format="array"), D.LIST),
        (FieldSpec("point_object", U.GEOPOINT, format="object"), D.STRUCT),
        (FieldSpec("geojson", U.GEOJSON), D.JSON),
        (FieldSpec("topojson", U.GEOJSON, format="topojson"), D.JSON),
        (FieldSpec("duration", U.DURATION), D.XSD_DURATION),
        (FieldSpec("year", U.YEAR), D.XSD_YEAR),
        (FieldSpec("yearmonth", U.YEARMONTH), D.XSD_YEARMONTH),
    ],
)
def test_v2_fields_resolve_on_every_target(target, field, canonical) -> None:
    assert _resolve_field_native(field, target) == registry.to_native_schema(
        canonical, target
    )


class TestResolveFieldCanonicalPublicSurface:
    """resolve_field_canonical is re-exported from the typespec package
    surface (mountainash.typespec.__init__), not just converters.py."""

    def test_importable_from_typespec_package(self) -> None:
        from mountainash.typespec import resolve_field_canonical as pkg_resolve
        assert pkg_resolve is resolve_field_canonical


# ============================================================================
# TestV2SixFieldCrossTargetIntegration (item 113 Unit B, Task 6)
# ============================================================================

V2_INTEGRATION_SPEC = TypeSpec(
    fields=[
        FieldSpec("list", U.LIST, item_type="integer"),
        FieldSpec("point", U.GEOPOINT, format="array"),
        FieldSpec("geometry", U.GEOJSON),
        FieldSpec("duration", U.DURATION),
        FieldSpec("year", U.YEAR),
        FieldSpec("yearmonth", U.YEARMONTH),
    ]
)


@pytest.mark.parametrize("target", [TypeTarget.POLARS, TypeTarget.NARWHALS, TypeTarget.IBIS])
def test_v2_six_field_spec_resolves_on_polars_narwhals_and_ibis(target) -> None:
    resolved = {
        field.name: _resolve_field_native(field, target)
        for field in V2_INTEGRATION_SPEC.fields
    }
    assert set(resolved) == {
        "list", "point", "geometry", "duration", "year", "yearmonth",
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
        assert resolved["list"] == "array<int64>"
        assert resolved["point"] == "array"
        string_type = "string"
    assert resolved["point"] == registry.to_native_schema(D.LIST, target)
    for name in ("geometry", "duration", "year", "yearmonth"):
        assert resolved[name] == string_type
        assert registry.from_native(resolved[name], target) is D.STRING
