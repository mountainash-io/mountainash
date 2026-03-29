"""AST construction tests for name operations API builders."""
import pytest
import mountainash_expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME

class TestNameMethods:
    def test_alias(self):
        expr = ma.col("x").name.alias("new_name")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.ALIAS
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == "new_name"

    def test_prefix(self):
        expr = ma.col("x").name.prefix("raw_")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.PREFIX
        assert node.arguments[1].value == "raw_"

    def test_suffix(self):
        expr = ma.col("x").name.suffix("_v2")
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.SUFFIX
        assert node.arguments[1].value == "_v2"

    def test_name_to_upper(self):
        expr = ma.col("x").name.name_to_upper()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.NAME_TO_UPPER
        assert len(node.arguments) == 1

    def test_name_to_lower(self):
        expr = ma.col("x").name.name_to_lower()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_NAME.NAME_TO_LOWER
        assert len(node.arguments) == 1

class TestNameAliases:
    def test_to_uppercase_alias(self):
        canonical = ma.col("x").name.name_to_upper()._node
        alias = ma.col("x").name.to_uppercase()._node
        assert canonical.function_key == alias.function_key

    def test_to_lowercase_alias(self):
        canonical = ma.col("x").name.name_to_lower()._node
        alias = ma.col("x").name.to_lowercase()._node
        assert canonical.function_key == alias.function_key
