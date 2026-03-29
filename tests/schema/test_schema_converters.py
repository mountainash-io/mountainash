"""
Tests for mountainash.schema.config.converters.

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

from mountainash.schema.config.converters import (
    convert_to_backend,
    to_arrow_schema,
    to_ibis_schema,
    to_pandas_dtypes,
    to_polars_schema,
)
from mountainash.schema.config.types import UniversalType
from mountainash.schema.config.universal_schema import SchemaField, TableSchema


# ============================================================================
# Shared fixture schema
# ============================================================================

@pytest.fixture()
def basic_schema():
    return TableSchema.from_simple_dict({
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

        fields = [SchemaField(name=f"col_{ut.value}", type=ut) for ut in UniversalType]
        schema = TableSchema(fields=fields)
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
        fields = [SchemaField(name=f"col_{ut.value}", type=ut) for ut in UniversalType]
        schema = TableSchema(fields=fields)
        result = to_pandas_dtypes(schema)
        assert len(result) == len(list(UniversalType))

    def test_returns_dict_of_strings(self, basic_schema):
        result = to_pandas_dtypes(basic_schema)
        assert isinstance(result, dict)
        for v in result.values():
            assert isinstance(v, str)


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
        assert result["active"] == "bool"

    def test_all_universal_types_produce_a_result(self):
        fields = [SchemaField(name=f"col_{ut.value}", type=ut) for ut in UniversalType]
        schema = TableSchema(fields=fields)
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
        """SchemaField with backend_type should use that type in polars output."""
        import polars as pl

        field = SchemaField(name="val", type=UniversalType.NUMBER, backend_type="Float32")
        schema = TableSchema(fields=[field])
        result = to_polars_schema(schema)
        assert result["val"] == pl.Float32

    def test_backend_type_preserved_in_pandas(self):
        """SchemaField with backend_type should pass through as-is for pandas."""
        field = SchemaField(name="val", type=UniversalType.NUMBER, backend_type="Float32")
        schema = TableSchema(fields=[field])
        result = to_pandas_dtypes(schema)
        assert result["val"] == "Float32"

    def test_backend_type_preserved_in_ibis(self):
        """SchemaField with backend_type should pass through as-is for ibis."""
        field = SchemaField(name="val", type=UniversalType.NUMBER, backend_type="float32")
        schema = TableSchema(fields=[field])
        result = to_ibis_schema(schema)
        assert result["val"] == "float32"
