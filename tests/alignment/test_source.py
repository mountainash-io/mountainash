"""Tests for SourceRelNode — Python data source for relations."""
from __future__ import annotations

import pytest

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


import polars as pl

import mountainash as ma


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
