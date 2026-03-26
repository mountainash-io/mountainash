"""AST construction tests for cast API builder."""
import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import CastNode, FieldReferenceNode


class TestCastMethod:
    def test_cast_string(self):
        expr = ma.col("x").cast("f64")
        node = expr._node
        assert isinstance(node, CastNode)
        assert node.target_type == "f64"
        assert isinstance(node.input, FieldReferenceNode)

    def test_cast_python_type(self):
        expr = ma.col("x").cast(int)
        node = expr._node
        assert isinstance(node, CastNode)
        assert node.target_type == "i64"

    def test_cast_bool(self):
        expr = ma.col("x").cast(bool)
        node = expr._node
        assert isinstance(node, CastNode)
        assert node.target_type == "bool"
