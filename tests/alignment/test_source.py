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
