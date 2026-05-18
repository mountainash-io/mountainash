"""AST construction tests for str.to_date() and str.to_datetime()."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_STRING,
)


class TestStrToDate:
    def test_to_date_creates_node(self):
        expr = ma.col("date_str").str.to_date("%Y-%m-%d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.TO_DATE
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert node.options.get("format") == "%Y-%m-%d"


class TestStrToDatetime:
    def test_to_datetime_creates_node(self):
        expr = ma.col("dt_str").str.to_datetime("%Y-%m-%d %H:%M:%S")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_STRING.TO_DATETIME
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert node.options.get("format") == "%Y-%m-%d %H:%M:%S"
