"""Cross-backend result verification for struct operations.

Verifies that struct.field() access produces identical results across
backends with native struct column support. Uses reduced backend set since
pandas, narwhals-pandas, and ibis-sqlite lack native struct types.
Ibis backends return floats for nullable integer fields (int → float
promotion on null), so numeric assertions use approximate comparison.
"""

from __future__ import annotations

import pytest

import mountainash as ma


STRUCT_BACKENDS = ["polars", "narwhals-polars", "ibis-polars", "ibis-duckdb"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", STRUCT_BACKENDS)
class TestStructFieldString:
    def test_field_string_basic(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("name"))
        assert actual == ["Alice", "Bob"]

    def test_field_string_with_empty(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"name": "", "v": 1}, {"name": "X", "v": 2}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("name"))
        assert actual == ["", "X"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", STRUCT_BACKENDS)
class TestStructFieldInteger:
    def test_field_integer_basic(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("age"))
        assert [int(v) for v in actual] == [30, 25]

    def test_field_integer_negative(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"x": -5, "y": 10}, {"x": 0, "y": -1}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("x"))
        assert [int(v) for v in actual] == [-5, 0]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", STRUCT_BACKENDS)
class TestStructFieldNull:
    def test_field_with_null_struct(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"x": 1, "y": 2}, None, {"x": 3, "y": 4}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("x"))
        assert int(actual[0]) == 1
        assert actual[1] is None
        assert int(actual[2]) == 3

    def test_field_y_with_null_struct(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"x": 1, "y": 2}, None, {"x": 3, "y": 4}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("y"))
        assert int(actual[0]) == 2
        assert actual[1] is None
        assert int(actual[2]) == 4


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", STRUCT_BACKENDS)
class TestStructFieldNested:
    def test_field_nested_score(self, backend_name, backend_factory, collect_expr):
        data = {
            "s": [
                {"info": {"city": "NYC"}, "score": 90},
                {"info": {"city": "LA"}, "score": 85},
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("score"))
        assert [int(v) for v in actual] == [90, 85]

    def test_field_nested_inner_struct(self, backend_name, backend_factory, collect_expr):
        data = {
            "s": [
                {"info": {"city": "NYC"}, "score": 90},
                {"info": {"city": "LA"}, "score": 85},
            ]
        }
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("info"))
        # Inner struct extraction — result is a struct/dict per row
        assert actual[0]["city"] == "NYC"
        assert actual[1]["city"] == "LA"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", STRUCT_BACKENDS)
class TestStructFieldSingleElement:
    def test_single_field_struct(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"only": 42}, {"only": 99}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("only"))
        assert [int(v) for v in actual] == [42, 99]

    def test_many_fields_select_one(self, backend_name, backend_factory, collect_expr):
        data = {"s": [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]}
        df = backend_factory.create(data, backend_name)
        actual = collect_expr(df, ma.col("s").struct.field("b"))
        assert [int(v) for v in actual] == [2, 5]
