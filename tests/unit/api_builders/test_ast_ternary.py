"""AST construction tests for ternary logic API builders."""
import pytest
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_TERNARY

class TestTernaryComparisons:
    @pytest.mark.parametrize("method,fkey", [
        ("t_eq", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_EQ),
        ("t_ne", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NE),
        ("t_gt", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GT),
        ("t_lt", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LT),
        ("t_ge", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_GE),
        ("t_le", FKEY_MOUNTAINASH_SCALAR_TERNARY.T_LE),
    ])
    def test_ternary_comparison(self, method, fkey):
        expr = getattr(ma.col("x"), method)(42)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2

class TestTernarySetMembership:
    def test_t_is_in(self):
        expr = ma.col("x").t_is_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_IN

    def test_t_is_not_in(self):
        expr = ma.col("x").t_is_not_in([1, 2, 3])
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_IS_NOT_IN

class TestTernaryLogic:
    def test_t_and(self):
        expr = ma.col("x").t_gt(10).t_and(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_AND

    def test_t_or(self):
        expr = ma.col("x").t_gt(10).t_or(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_OR

    def test_t_not(self):
        expr = ma.col("x").t_gt(10).t_not()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_NOT
        assert len(node.arguments) == 1

    def test_t_xor(self):
        expr = ma.col("x").t_gt(10).t_xor(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR

    def test_t_xor_parity(self):
        expr = ma.col("x").t_gt(10).t_xor_parity(ma.col("y").t_lt(20))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.T_XOR_PARITY

class TestTernaryBooleanizers:
    @pytest.mark.parametrize("method,fkey", [
        ("is_true", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_TRUE),
        ("is_false", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_FALSE),
        ("is_unknown", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_UNKNOWN),
        ("is_known", FKEY_MOUNTAINASH_SCALAR_TERNARY.IS_KNOWN),
        ("maybe_true", FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_TRUE),
        ("maybe_false", FKEY_MOUNTAINASH_SCALAR_TERNARY.MAYBE_FALSE),
    ])
    def test_booleanizer(self, method, fkey):
        ternary_expr = ma.col("x").t_gt(10)
        expr = getattr(ternary_expr, method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1

class TestTernaryConversion:
    def test_to_ternary(self):
        expr = ma.col("x").gt(10).to_ternary()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_TERNARY.TO_TERNARY
        assert len(node.arguments) == 1
