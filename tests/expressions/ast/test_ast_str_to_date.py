"""AST construction tests for str.to_date() and str.to_datetime()."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_DATETIME,
)


class TestStrToDate:
    def test_to_date_creates_node(self):
        expr = ma.col("date_str").str.to_date("%Y-%m-%d")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_DATE
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert node.options.get("format") == "%Y-%m-%d"


class TestStrToDatetime:
    def test_to_datetime_creates_node(self):
        expr = ma.col("dt_str").str.to_datetime("%Y-%m-%d %H:%M:%S")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert node.options == {"format": "%Y-%m-%d %H:%M:%S"}

    def test_to_datetime_with_timezone_includes_option(self):
        """item 62: timezone reaches the node end-to-end (options dict), not
        just the builder signature."""
        expr = ma.col("dt_str").str.to_datetime("%Y-%m-%d %H:%M:%S", timezone="UTC")
        node = expr._node
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_DATETIME.STRPTIME_TIMESTAMP
        assert node.options == {"format": "%Y-%m-%d %H:%M:%S", "timezone": "UTC"}

    def test_to_datetime_without_timezone_omits_option(self):
        """Omission is distinct from an explicit value at the AST level."""
        expr = ma.col("dt_str").str.to_datetime("%Y-%m-%d %H:%M:%S")
        node = expr._node
        assert "timezone" not in node.options
