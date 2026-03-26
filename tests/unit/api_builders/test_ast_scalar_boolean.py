"""AST construction tests for boolean API builders."""
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)


class TestBooleanBinaryMethods:
    def test_and_(self):
        expr = ma.col("a").and_(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], FieldReferenceNode)

    def test_or_(self):
        expr = ma.col("a").or_(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR
        assert len(node.arguments) == 2

    def test_and_not(self):
        expr = ma.col("a").and_not(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND_NOT
        assert len(node.arguments) == 2

    def test_xor(self):
        expr = ma.col("a").xor(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.XOR
        assert len(node.arguments) == 2

    def test_not_(self):
        expr = ma.col("a").not_()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestBooleanExtensionMethods:
    def test_xor_parity(self):
        expr = ma.col("a").xor_parity(ma.col("b"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY
        assert len(node.arguments) == 2

    def test_always_true(self):
        # always_true() returns a LiteralNode(True) — not a ScalarFunctionNode
        expr = ma.col("a").always_true()
        node = expr._node
        assert isinstance(node, LiteralNode)
        assert node.value is True

    def test_always_false(self):
        # always_false() returns a LiteralNode(False) — not a ScalarFunctionNode
        expr = ma.col("a").always_false()
        node = expr._node
        assert isinstance(node, LiteralNode)
        assert node.value is False


class TestBooleanAliases:
    def test_xor_alias(self):
        """xor_() is an alias for xor(), both use FKEY_SUBSTRAIT_SCALAR_BOOLEAN.XOR."""
        canonical = ma.col("a").xor(ma.col("b"))._node
        alias = ma.col("a").xor_(ma.col("b"))._node
        assert isinstance(canonical, ScalarFunctionNode)
        assert isinstance(alias, ScalarFunctionNode)
        assert canonical.function_key == alias.function_key
        assert alias.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.XOR
