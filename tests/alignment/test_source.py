"""Tests for SourceRelNode — Python data source for relations."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.core.relation_nodes import SourceRelNode
from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT


class TestSourceRelNodeConstruction:
    """SourceRelNode holds Python data and detected format."""

    def test_create_with_list_of_dicts(self):
        data = [{"a": 1, "b": 2}]
        node = SourceRelNode(data=data, detected_format=CONST_PYTHON_DATAFORMAT.PYLIST)
        assert node.data is data
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_create_with_dict_of_lists(self):
        data = {"a": [1, 2], "b": [3, 4]}
        node = SourceRelNode(data=data, detected_format=CONST_PYTHON_DATAFORMAT.PYDICT)
        assert node.data is data
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYDICT

    def test_accept_calls_visit_source_rel(self):
        data = [{"a": 1}]
        node = SourceRelNode(data=data, detected_format=CONST_PYTHON_DATAFORMAT.PYLIST)

        class MockVisitor:
            def visit_source_rel(self, node):
                return "visited"

        result = node.accept(MockVisitor())
        assert result == "visited"


class TestSourceRelVisitorExecution:
    """SourceRelNode visitor materializes Python data into a DataFrame."""

    def test_source_list_of_dicts_collects_to_polars(self):
        data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        result = ma.relation(data).collect()
        assert isinstance(result, (pl.DataFrame, pl.LazyFrame))
        if isinstance(result, pl.LazyFrame):
            result = result.collect()
        assert result.shape == (2, 2)
        assert result["a"].to_list() == [1, 2]
        assert result["b"].to_list() == ["x", "y"]

    def test_source_dict_of_lists_collects_to_polars(self):
        data = {"x": [10, 20, 30], "y": ["a", "b", "c"]}
        result = ma.relation(data).to_polars()
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)
        assert result["x"].to_list() == [10, 20, 30]


class TestSourceWithTransforms:
    """Python data sourced through relation transforms."""

    def test_source_filter(self):
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 20}]
        result = ma.relation(data).filter(ma.col("age").gt(25)).to_polars()
        assert result.shape == (1, 2)
        assert result["name"].to_list() == ["Alice"]

    def test_source_sort(self):
        data = [{"x": 3}, {"x": 1}, {"x": 2}]
        result = ma.relation(data).sort("x").to_polars()
        assert result["x"].to_list() == [1, 2, 3]

    def test_source_head(self):
        data = {"val": [10, 20, 30, 40, 50]}
        result = ma.relation(data).head(3).to_polars()
        assert result.shape == (3, 1)

    def test_source_select(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        result = ma.relation(data).select("a", "c").to_polars()
        assert result.columns == ["a", "c"]

    def test_source_with_columns(self):
        data = [{"x": 10}, {"x": 20}]
        result = ma.relation(data).with_columns(
            ma.col("x").mul(2).name.alias("x2")
        ).to_polars()
        assert "x2" in result.columns
        assert result["x2"].to_list() == [20, 40]


class TestSourceDetectedFormat:
    """SourceRelNode exposes detected format for introspection."""

    def test_list_of_dicts_detected_as_pylist(self):
        data = [{"a": 1}]
        r = ma.relation(data)
        node = r._node
        assert isinstance(node, SourceRelNode)
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYLIST

    def test_dict_of_lists_detected_as_pydict(self):
        data = {"a": [1, 2]}
        r = ma.relation(data)
        node = r._node
        assert isinstance(node, SourceRelNode)
        assert node.detected_format == CONST_PYTHON_DATAFORMAT.PYDICT
