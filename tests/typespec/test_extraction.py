"""
Tests for mountainash.typespec.extraction

Covers schema extraction from:
- Polars DataFrames
- Pandas DataFrames
- PyArrow Tables
- Narwhals DataFrames
- Ibis memtables
- Python dataclasses
- Pydantic models
"""
import datetime
from dataclasses import dataclass
from typing import Optional

import pytest

from mountainash.core.dtypes import MountainashDtype
from mountainash.typespec.extraction import (
    _DATACLASS_SCHEMA_CACHE,
    extract_schema_from_dataclass,
    extract_schema_from_dataframe,
    extract_schema_from_pydantic,
    extract_from_dataclass,
    extract_from_dataframe,
    extract_from_pydantic,
    from_dataclass,
    from_dataframe,
    from_pydantic,
)
from mountainash.typespec.spec import FieldDefinition, TableSchema
from mountainash.typespec.universal_types import UniversalType
from mountainash.typespec.source_shape import extract_source_shapes


# ============================================================================
# TestExtractFromPolars
# ============================================================================

class TestExtractFromPolars:
    """Tests for schema extraction from Polars DataFrames."""

    @pytest.fixture
    def polars_mixed_df(self):
        pl = pytest.importorskip("polars")
        return pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
            "score": [9.5, 7.0, 4.2],
            "active": [True, False, True],
            "joined": [
                datetime.date(2020, 1, 1),
                datetime.date(2021, 6, 15),
                datetime.date(2022, 3, 10),
            ],
        })

    def test_field_names(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert schema.field_names == ["id", "name", "score", "active", "joined"]

    def test_id_is_integer(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert schema.get_field("id").type == "integer"

    def test_name_is_string(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert schema.get_field("name").type == "string"

    def test_score_is_number(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert schema.get_field("score").type == "number"

    def test_active_is_boolean(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert schema.get_field("active").type == "boolean"

    def test_joined_is_date(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert schema.get_field("joined").type == "date"

    def test_preserve_backend_types_true(self, polars_mixed_df):
        schema = extract_from_dataframe(polars_mixed_df, preserve_backend_types=True)
        id_field = schema.get_field("id")
        assert id_field.backend_type is not None

    def test_preserve_backend_types_false(self, polars_mixed_df):
        schema = extract_from_dataframe(polars_mixed_df, preserve_backend_types=False)
        id_field = schema.get_field("id")
        assert id_field.backend_type is None

    def test_timestamp_extraction_retains_precision_zone_and_nested_shape(self):
        pl = pytest.importorskip("polars")
        from mountainash.core.dtypes import ListDtype, StructDtype, TimestampDtype

        native = pl.List(pl.Struct([
            pl.Field("at", pl.Datetime("ns", "UTC")),
        ]))
        extracted = extract_from_dataframe(pl.DataFrame(schema={"events": native}))
        dtype = extracted.get_field("events").dtype
        assert dtype == ListDtype(StructDtype((
            ("at", TimestampDtype(9, True, "UTC")),
        )))


    def test_source_shapes_use_schema_without_rows(self):
        pl = pytest.importorskip("polars")
        frame = pl.DataFrame(schema={"values": pl.List(pl.Int64)})
        shape = extract_source_shapes(frame)["values"]
        assert shape.canonical_type is MountainashDtype.LIST
        assert shape.item_shape.canonical_type is MountainashDtype.I64

    def test_returns_table_schema(self, polars_mixed_df):
        schema = extract_schema_from_dataframe(polars_mixed_df)
        assert isinstance(schema, TableSchema)

    def test_from_dataframe_alias(self, polars_mixed_df):
        """from_dataframe alias should work identically."""
        schema = from_dataframe(polars_mixed_df, preserve_backend_types=False)
        assert isinstance(schema, TableSchema)


# ============================================================================
# TestExtractFromPandas
# ============================================================================

class TestExtractFromPandas:
    """Tests for schema extraction from Pandas DataFrames."""

    @pytest.fixture
    def pandas_df(self):
        pd = pytest.importorskip("pandas")
        return pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
        })

    def test_id_is_integer(self, pandas_df):
        schema = extract_schema_from_dataframe(pandas_df)
        assert schema.get_field("id").type == "integer"

    def test_returns_table_schema(self, pandas_df):
        schema = extract_schema_from_dataframe(pandas_df)
        assert isinstance(schema, TableSchema)

    def test_field_names(self, pandas_df):
        schema = extract_schema_from_dataframe(pandas_df)
        assert "id" in schema.field_names
        assert "name" in schema.field_names

    def test_preserve_backend_types_keeps_pandas_scalar_dtype(self, pandas_df):
        from mountainash.typespec.converters import to_pandas_dtypes

        schema = extract_from_dataframe(pandas_df, preserve_backend_types=True)
        assert to_pandas_dtypes(schema) == dict(pandas_df.dtypes)

    def test_preserve_string_dtype_metadata(self):
        import pandas as pd
        from mountainash.typespec.converters import to_pandas_dtypes

        native = pd.StringDtype(storage="python", na_value=pd.NA)
        frame = pd.DataFrame({"name": pd.Series(["a", None], dtype=native)})
        schema = extract_from_dataframe(frame, preserve_backend_types=True)
        result = to_pandas_dtypes(schema)["name"]
        assert result.storage == "python"
        assert result.na_value is pd.NA


# ============================================================================
# TestExtractFromPyArrow
# ============================================================================

class TestExtractFromPyArrow:
    """Tests for schema extraction from PyArrow Tables."""

    @pytest.fixture
    def pyarrow_table(self):
        pa = pytest.importorskip("pyarrow")
        return pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "name": pa.array(["Alice", "Bob", "Carol"], type=pa.string()),
        })

    def test_id_is_integer(self, pyarrow_table):
        schema = extract_schema_from_dataframe(pyarrow_table)
        assert schema.get_field("id").type == "integer"

    def test_name_is_string(self, pyarrow_table):
        schema = extract_schema_from_dataframe(pyarrow_table)
        assert schema.get_field("name").type == "string"

    def test_returns_table_schema(self, pyarrow_table):
        schema = extract_schema_from_dataframe(pyarrow_table)
        assert isinstance(schema, TableSchema)


# ============================================================================
# TestExtractFromNarwhals
# ============================================================================

class TestExtractFromNarwhals:
    """Tests for schema extraction from Narwhals DataFrames."""

    @pytest.fixture
    def narwhals_df(self):
        pl = pytest.importorskip("polars")
        nw = pytest.importorskip("narwhals")
        polars_df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
        })
        return nw.from_native(polars_df)

    def test_id_is_integer(self, narwhals_df):
        schema = extract_schema_from_dataframe(narwhals_df)
        assert schema.get_field("id").type == "integer"

    def test_returns_table_schema(self, narwhals_df):
        schema = extract_schema_from_dataframe(narwhals_df)
        assert isinstance(schema, TableSchema)

    def test_field_names(self, narwhals_df):
        schema = extract_schema_from_dataframe(narwhals_df)
        assert "id" in schema.field_names


# ============================================================================
# TestExtractFromIbis
# ============================================================================

class TestExtractFromIbis:
    """Tests for schema extraction from Ibis tables."""

    @pytest.fixture
    def ibis_table(self):
        ibis = pytest.importorskip("ibis")
        return ibis.memtable({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
        })

    def test_id_is_integer(self, ibis_table):
        schema = extract_schema_from_dataframe(ibis_table)
        assert schema.get_field("id").type == "integer"

    def test_returns_table_schema(self, ibis_table):
        schema = extract_schema_from_dataframe(ibis_table)
        assert isinstance(schema, TableSchema)

    def test_field_names(self, ibis_table):
        schema = extract_schema_from_dataframe(ibis_table)
        assert "id" in schema.field_names


# ============================================================================
# TestExtractFromDataclass
# ============================================================================

# Define test dataclasses at module level (not inside test class) to ensure
# consistent identity for cache testing.

@dataclass
class SimpleTypes:
    name: str
    age: int
    score: float
    active: bool


@dataclass
class OptionalFields:
    name: str
    email: Optional[str] = None


@dataclass
class DatetimeFields:
    created: datetime.date
    updated: datetime.datetime


class TestExtractFromDataclass:
    """Tests for schema extraction from Python dataclasses."""

    def test_simple_types_field_names(self):
        schema = extract_from_dataclass(SimpleTypes)
        assert schema.field_names == ["name", "age", "score", "active"]

    def test_simple_types_str_field(self):
        schema = extract_from_dataclass(SimpleTypes)
        assert schema.get_field("name").type == "string"

    def test_simple_types_int_field(self):
        schema = extract_from_dataclass(SimpleTypes)
        assert schema.get_field("age").type == "integer"

    def test_simple_types_float_field(self):
        schema = extract_from_dataclass(SimpleTypes)
        assert schema.get_field("score").type == "number"

    def test_simple_types_bool_field(self):
        schema = extract_from_dataclass(SimpleTypes)
        assert schema.get_field("active").type == "boolean"

    def test_optional_fields_present(self):
        schema = extract_from_dataclass(OptionalFields)
        assert "email" in schema.field_names

    def test_optional_field_type(self):
        schema = extract_from_dataclass(OptionalFields)
        # Optional[str] should resolve to "string"
        assert schema.get_field("email").type == "string"

    def test_datetime_date_field(self):
        schema = extract_from_dataclass(DatetimeFields)
        assert schema.get_field("created").type == "date"

    def test_datetime_datetime_field(self):
        schema = extract_from_dataclass(DatetimeFields)
        assert schema.get_field("updated").type == "datetime"

    def test_cache_returns_independent_equal_schemas(self):
        # Clear cache entry for SimpleTypes before testing
        _DATACLASS_SCHEMA_CACHE.pop(SimpleTypes, None)
        schema1 = extract_schema_from_dataclass(SimpleTypes)
        schema2 = extract_schema_from_dataclass(SimpleTypes)
        assert schema1 == schema2
        assert schema1 is not schema2
        assert schema1.fields is not schema2.fields

    def test_cached_schema_survives_caller_mutation(self):
        _DATACLASS_SCHEMA_CACHE.pop(SimpleTypes, None)
        first = extract_schema_from_dataclass(SimpleTypes)
        expected_names = list(first.fields)
        first.fields["extra"] = FieldDefinition(type=UniversalType.STRING)
        first.missing_values.append("NA")
        first.title = "mutated"
        second = extract_schema_from_dataclass(SimpleTypes)
        assert list(second.fields) == expected_names
        assert second.missing_values == [""]
        assert second.title == SimpleTypes.__name__

    def test_caching_stores_result(self):
        _DATACLASS_SCHEMA_CACHE.pop(SimpleTypes, None)
        extract_schema_from_dataclass(SimpleTypes)
        assert SimpleTypes in _DATACLASS_SCHEMA_CACHE

    def test_non_dataclass_raises_value_error(self):
        with pytest.raises(ValueError):
            extract_from_dataclass(int)

    def test_non_dataclass_class_raises_value_error(self):
        class NotADataclass:
            pass

        with pytest.raises(ValueError):
            extract_from_dataclass(NotADataclass)

    def test_returns_table_schema(self):
        schema = extract_from_dataclass(SimpleTypes)
        assert isinstance(schema, TableSchema)

    def test_from_dataclass_alias(self):
        """from_dataclass alias should work identically."""
        schema = from_dataclass(SimpleTypes)
        assert isinstance(schema, TableSchema)


# ============================================================================
# TestExtractFromPydantic
# ============================================================================

class TestExtractFromPydantic:
    """Tests for schema extraction from Pydantic models."""

    @pytest.fixture(autouse=True)
    def require_pydantic(self):
        pytest.importorskip("pydantic")

    @pytest.fixture
    def basic_model(self):
        from pydantic import BaseModel

        class ProductModel(BaseModel):
            sku: str
            price: float

        return ProductModel

    @pytest.fixture
    def optional_model(self):
        from pydantic import BaseModel

        class UserModel(BaseModel):
            username: str
            email: Optional[str] = None

        return UserModel

    def test_basic_model_field_names(self, basic_model):
        schema = extract_from_pydantic(basic_model)
        assert "sku" in schema.field_names
        assert "price" in schema.field_names

    def test_basic_model_str_field(self, basic_model):
        schema = extract_from_pydantic(basic_model)
        assert schema.get_field("sku").type == "string"

    def test_basic_model_float_field(self, basic_model):
        schema = extract_from_pydantic(basic_model)
        assert schema.get_field("price").type == "number"

    def test_optional_field_present(self, optional_model):
        schema = extract_from_pydantic(optional_model)
        assert "email" in schema.field_names

    @pytest.mark.parametrize(
        ("annotation", "expected"),
        [(Optional[str], "string"), (str | None, "string"), (int | None, "integer")],
    )
    def test_nullable_type_preserves_requiredness(self, annotation, expected):
        from pydantic import create_model

        model = create_model(
            "NullableModel",
            required_value=(annotation, ...),
            defaulted_value=(annotation, None),
        )
        schema = extract_from_pydantic(model)
        required = schema.get_field("required_value")
        defaulted = schema.get_field("defaulted_value")
        assert required.type == expected
        assert defaulted.type == expected
        assert required.constraints.required is True
        assert defaulted.constraints.required is False

    def test_multi_type_union_is_not_reduced_to_one_member(self):
        from pydantic import BaseModel

        class MixedModel(BaseModel):
            value: str | int | None = None

        assert extract_from_pydantic(MixedModel).get_field("value").type == "any"

    def test_cache_returns_independent_equal_schemas(self, basic_model):
        from mountainash.typespec.extraction import _PYDANTIC_SCHEMA_CACHE
        _PYDANTIC_SCHEMA_CACHE.pop(basic_model, None)
        schema1 = extract_schema_from_pydantic(basic_model)
        schema2 = extract_schema_from_pydantic(basic_model)
        assert schema1 == schema2
        assert schema1 is not schema2
        assert schema1.fields is not schema2.fields

    def test_cached_schema_survives_caller_mutation(self, basic_model):
        from mountainash.typespec.extraction import _PYDANTIC_SCHEMA_CACHE
        _PYDANTIC_SCHEMA_CACHE.pop(basic_model, None)
        first = extract_schema_from_pydantic(basic_model)
        names = list(first.fields)
        first.fields["extra"] = FieldDefinition(type=UniversalType.STRING)
        second = extract_schema_from_pydantic(basic_model)
        assert list(second.fields) == names

    def test_field_constraints_extracted(self):
        from pydantic import BaseModel, Field

        class Constrained(BaseModel):
            id: int = Field(gt=0)
            score: float = Field(ge=1, le=10)
            code: str = Field(min_length=2, max_length=5, pattern=r"^[a-z]+$")
            free: str = "x"

        schema = extract_from_pydantic(Constrained)
        assert schema.get_field("id").constraints.minimum == 0
        assert (schema.get_field("score").constraints.minimum,
                schema.get_field("score").constraints.maximum) == (1, 10)
        code = schema.get_field("code").constraints
        assert (code.min_length, code.max_length, code.pattern) == (2, 5, r"^[a-z]+$")
        assert schema.get_field("id").constraints.required is True
        assert schema.get_field("free").constraints.required is False

    def test_returns_table_schema(self, basic_model):
        schema = extract_from_pydantic(basic_model)
        assert isinstance(schema, TableSchema)

    def test_from_pydantic_alias(self, basic_model):
        """from_pydantic alias should work identically."""
        schema = from_pydantic(basic_model)
        assert isinstance(schema, TableSchema)


class TestExtractionOverRegistry:
    def test_polars_native_list_has_no_lexical_properties(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame({"tags": [[1, 2], [3]]})
        spec = extract_from_dataframe(df)
        field = spec.get_field("tags")
        assert field.type == UniversalType.ARRAY
        assert field.item_type is None
        assert field.delimiter is None

    def test_polars_array_of_structs_recurses_nested_array_of_structs(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame(
            {
                "rows": [
                    [{"name": "outer", "children": [{"id": 1, "tags": ["a"]}]}],
                ],
            }
        )
        spec = extract_from_dataframe(df)
        field = spec.get_field("rows")
        assert field.type is UniversalType.ARRAY
        assert field.item_type is None
        assert field.delimiter is None
        assert [(name, f.type) for name, f in field.element.fields.items()] == [
            ("name", UniversalType.STRING),
            ("children", UniversalType.ARRAY),
        ]
        children = field.element.fields["children"]
        assert children.item_type is None
        assert children.delimiter is None
        assert [(name, f.type) for name, f in children.element.fields.items()] == [
            ("id", UniversalType.INTEGER),
            ("tags", UniversalType.ARRAY),
        ]
        tags = children.element.fields["tags"]
        assert tags.item_type is None
        from mountainash.typespec.converters import to_polars_schema
        assert to_polars_schema(spec)["rows"] == pl.List(
            pl.Struct(
                {
                    "name": pl.String,
                    "children": pl.List(
                        pl.Struct({"id": pl.Int64, "tags": pl.List(pl.String)})
                    ),
                }
            )
        )

    def test_polars_struct_populates_fields(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = extract_from_dataframe(df)
        field = spec.get_field("addr")
        assert field.type == UniversalType.OBJECT
        names = {name: f.type for name, f in field.fields.items()}
        assert names == {"street": UniversalType.STRING, "zip": UniversalType.STRING}

    def test_polars_struct_two_levels_deep_populates_fields_recursively(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame([{"addr": {"street": "Main St", "geo": {"lat": 1.0, "lon": 2.0}}}])
        spec = extract_from_dataframe(df)
        geo = spec.get_field("addr").fields["geo"]
        assert geo.type == UniversalType.OBJECT
        assert set(geo.fields) == {"lat", "lon"}

    def test_extracted_nested_definitions_are_immutable_and_unnamed(self):
        import dataclasses
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame([{"addr": {"street": "Main St"}}])
        field = extract_from_dataframe(df).get_field("addr")
        child = field.fields["street"]
        assert "name" not in {item.name for item in dataclasses.fields(child)}
        with pytest.raises(dataclasses.FrozenInstanceError):
            child.type = UniversalType.INTEGER
        with pytest.raises(TypeError):
            field.fields["other"] = child

    def test_extractions_do_not_share_definition_state(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame([{"addr": {"street": "Main St"}}])
        first = extract_from_dataframe(df)
        second = extract_from_dataframe(df)
        first.fields["extra"] = FieldDefinition(type=UniversalType.STRING)
        assert list(second.fields) == ["addr"]


    def test_pyarrow_struct_populates_fields(self):
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        from mountainash.typespec.extraction import extract_from_dataframe
        table = pa.table({"addr": pa.array(
            [{"street": "Main St", "zip": "12345"}],
            type=pa.struct([pa.field("street", pa.string()), pa.field("zip", pa.string())]),
        )})
        spec = extract_from_dataframe(table)
        field = spec.get_field("addr")
        assert field.type == UniversalType.OBJECT
        names = {name: f.type for name, f in field.fields.items()}
        assert names == {"street": UniversalType.STRING, "zip": UniversalType.STRING}


    def test_pyarrow_array_of_structs_recurses_nested_array_of_structs(self):
        pytest.importorskip("pyarrow")
        import pyarrow as pa
        from mountainash.typespec.extraction import extract_from_dataframe

        child_type = pa.struct([pa.field("code", pa.string())])
        row_type = pa.struct(
            [
                pa.field("id", pa.int64()),
                pa.field("children", pa.list_(child_type)),
            ]
        )
        table = pa.table(
            {
                "rows": pa.array(
                    [[{"id": 1, "children": [{"code": "x"}]}]],
                    type=pa.list_(row_type),
                )
            }
        )
        spec = extract_from_dataframe(table)
        field = spec.get_field("rows")
        assert field.type is UniversalType.ARRAY
        assert field.item_type is None
        children = field.element.fields["children"]
        assert children.type is UniversalType.ARRAY
        code = children.element.fields["code"]
        assert code.type is UniversalType.STRING

    def test_pandas_arrow_list_and_struct_use_source_shapes(self):
        pytest.importorskip("pyarrow")
        import pandas as pd
        import pyarrow as pa
        from mountainash.typespec.extraction import extract_from_dataframe

        row_type = pa.struct([pa.field("id", pa.int64())])
        df = pd.DataFrame(
            {
                "rows": pd.Series(
                    [[{"id": 1}]],
                    dtype=pd.ArrowDtype(pa.list_(row_type)),
                ),
                "addr": pd.Series(
                    [{"id": 1}],
                    dtype=pd.ArrowDtype(row_type),
                ),
            }
        )
        spec = extract_from_dataframe(df)
        rows = spec.get_field("rows")
        addr = spec.get_field("addr")
        assert rows.type is UniversalType.ARRAY
        assert rows.element.fields["id"].type is UniversalType.INTEGER
        assert addr.type is UniversalType.OBJECT
        assert addr.fields["id"].type is UniversalType.INTEGER

    def test_polars_list_null_child_has_bare_array_shape(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe

        spec = extract_from_dataframe(
            pl.DataFrame({"values": pl.Series([None], dtype=pl.List(pl.Null))})
        )
        field = spec.get_field("values")
        assert field.type is UniversalType.ARRAY
        assert field.item_type is None

    def test_extraction_resolver_round_trip_pins_full_struct_not_just_no_raise(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        from mountainash.typespec.converters import to_polars_schema
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = extract_from_dataframe(df, preserve_backend_types=True)
        result = to_polars_schema(spec)
        assert result["addr"] == pl.Struct({"street": pl.String, "zip": pl.String})

    def test_extraction_resolver_round_trip_empty_frame(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        from mountainash.relations.backends.relation_systems.polars.extensions_mountainash.relsys_pl_ext_ma_util import (
            MountainashPolarsExtensionRelationSystem,
        )
        df = pl.DataFrame([{"addr": {"street": "Main St", "zip": "12345"}}])
        spec = extract_from_dataframe(df, preserve_backend_types=True)
        empty = MountainashPolarsExtensionRelationSystem().empty_frame(spec)
        collected = empty.collect()
        assert collected.schema["addr"] == pl.Struct({"street": pl.String, "zip": pl.String})
        assert collected.shape == (0, 1)

    def test_polars_object_is_a_known_dynamic_type(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe

        df = pl.DataFrame({"dynamic": [object()]})
        field = extract_from_dataframe(df).get_field("dynamic")
        assert field.type is UniversalType.ANY

    def test_native_decimal_extracts_as_number(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame({"d": [1]}).cast({"d": pl.Decimal(10, 2)})
        (field,) = extract_from_dataframe(df).fields.values()
        assert field.type == UniversalType.NUMBER

    def test_null_column_extracts_as_any(self):
        import polars as pl
        from mountainash.typespec.extraction import extract_from_dataframe
        df = pl.DataFrame({"n": [None, None]})
        spec = extract_from_dataframe(df)
        assert spec.get_field("n").type == UniversalType.ANY




@pytest.mark.parametrize("values", [[], [1]])
def test_arrow_extraction_round_trips_field_qualifiers_without_inventing_constraints(values):
    import pyarrow as pa
    from mountainash.typespec.converters import to_arrow_schema

    native = pa.schema([
        pa.field("count", pa.int16(), nullable=False, metadata={b"unit": b"items"}),
    ])
    table = pa.Table.from_arrays([pa.array(values, type=pa.int16())], schema=native)
    preserved = extract_from_dataframe(table, preserve_backend_types=True)
    assert to_arrow_schema(preserved).equals(native, check_metadata=True)

    portable = extract_from_dataframe(table, preserve_backend_types=False)
    for schema in (preserved, portable):
        field = schema.fields["count"]
        assert field.constraints is None or field.constraints.required is not True
        assert field.dtype is MountainashDtype.I16
    assert portable.fields["count"].backend_type is None


@pytest.mark.parametrize("family", ["polars", "pyarrow", "pandas", "ibis", "narwhals"])
def test_extraction_composes_each_nested_scalar_list_element(family):
    import ibis
    import narwhals as nw
    import pandas as pd
    import polars as pl
    import pyarrow as pa

    carriers = {
        "polars": pl.DataFrame(schema={"values": pl.List(pl.List(pl.Int16))}),
        "pyarrow": pa.Table.from_arrays(
            [pa.array([], type=pa.list_(pa.list_(pa.int16())))],
            names=["values"],
        ),
        "pandas": pd.DataFrame({
            "values": pd.Series([], dtype=pd.ArrowDtype(pa.list_(pa.list_(pa.int16())))),
        }),
        "ibis": ibis.table({"values": "array<array<int16>>"}),
        "narwhals": nw.from_native(pl.DataFrame(schema={"values": pl.List(pl.List(pl.Int16))})),
    }
    field = extract_from_dataframe(
        carriers[family], preserve_backend_types=False,
    ).fields["values"]
    assert field.element.element.dtype is MountainashDtype.I16
    assert field.element.backend_type is None
    assert field.element.element.backend_type is None


@pytest.mark.parametrize("preserve", [False, True])
def test_fixed_array_extraction_can_conform_without_flattening_axes(preserve):
    """Polars exposes the fixed-size representation used by this witness."""
    import mountainash as ma
    import polars as pl
    from mountainash.typespec.converters import to_polars_schema

    native = pl.Array(pl.Int16, (2, 3))
    frame = pl.DataFrame({"grid": [[[1, 2, 3], [4, 5, 6]]]}, schema={"grid": native})
    schema = extract_from_dataframe(frame, preserve_backend_types=preserve)
    assert to_polars_schema(schema)["grid"] == native
    result = ma.relation(frame).conform(schema).to_polars()
    assert result.to_dicts() == frame.to_dicts()
    assert result.schema["grid"] == native
