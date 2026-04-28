"""AST construction tests for comparison API builders."""
import pytest
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode, IfThenNode
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_COMPARISON,
    FKEY_SUBSTRAIT_SCALAR_BOOLEAN,
    FKEY_MOUNTAINASH_SCALAR_TERNARY,
)


class TestBinaryComparisons:
    @pytest.mark.parametrize("method,fkey", [
        ("equal", FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL),
        ("not_equal", FKEY_SUBSTRAIT_SCALAR_COMPARISON.NOT_EQUAL),
        ("lt", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LT),
        ("gt", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT),
        ("lte", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE),
        ("gte", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GTE),
    ])
    def test_binary_comparison(self, method, fkey):
        expr = getattr(ma.col("x"), method)(42)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 42


class TestUnaryStateChecks:
    """Test unary state check methods.

    Note: is_true and is_false resolve to ternary versions because
    MountainAshScalarTernaryAPIBuilder is first in _FLAT_NAMESPACES.
    The Substrait is_true/is_false are available via the SubstraitScalarComparisonAPIBuilder
    but are shadowed at the BooleanExpressionAPI level.
    """

    @pytest.mark.parametrize("method,fkey", [
        ("is_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL),
        ("is_not_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_NULL),
        ("is_nan", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN),
        ("is_finite", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FINITE),
        ("is_infinite", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_INFINITE),
        ("is_not_true", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_TRUE),
        ("is_not_false", FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NOT_FALSE),
    ])
    def test_unary_state_check(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)

    def test_is_true(self):
        """On a boolean expression, is_true() should use Substrait comparison, not ternary."""
        expr = ma.col("x").is_true()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_TRUE

    def test_is_false(self):
        """On a boolean expression, is_false() should use Substrait comparison, not ternary."""
        expr = ma.col("x").is_false()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_FALSE


class TestNullHandling:
    def test_nullif(self):
        expr = ma.col("x").nullif(0)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.NULL_IF
        assert len(node.arguments) == 2
        assert node.arguments[1].value == 0


class TestVariadicComparisons:
    @pytest.mark.parametrize("method,fkey", [
        ("coalesce", FKEY_SUBSTRAIT_SCALAR_COMPARISON.COALESCE),
        ("least", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST),
        ("least_skip_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.LEAST_SKIP_NULL),
        ("greatest", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST),
        ("greatest_skip_null", FKEY_SUBSTRAIT_SCALAR_COMPARISON.GREATEST_SKIP_NULL),
    ])
    def test_variadic_method(self, method, fkey):
        expr = getattr(ma.col("x"), method)(ma.col("y"), ma.col("z"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 3


class TestBetween:
    def test_between(self):
        expr = ma.col("x").between(10, 20)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.BETWEEN
        assert len(node.arguments) == 3
        assert node.arguments[1].value == 10
        assert node.arguments[2].value == 20
        assert node.options["closed"] == "both"

    def test_between_closed_left(self):
        expr = ma.col("x").between(10, 20, closed="left")
        node = expr._node
        assert node.options["closed"] == "left"


class TestComparisonAliases:
    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("eq", "equal"),
        ("ne", "not_equal"),
        ("ge", "gte"),
        ("le", "lte"),
    ])
    def test_short_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x"), canonical_method)(42)._node
        alias = getattr(ma.col("x"), alias_method)(42)._node
        assert canonical.function_key == alias.function_key
        assert canonical.arguments[1].value == alias.arguments[1].value

    def test_is_between_alias(self):
        canonical = ma.col("x").between(10, 20)._node
        alias = ma.col("x").is_between(10, 20)._node
        assert canonical.function_key == alias.function_key
        assert canonical.options == alias.options


class TestComparisonCompositions:
    def test_is_not_nan(self):
        expr = ma.col("x").is_not_nan()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT
        inner = node.arguments[0]
        assert isinstance(inner, ScalarFunctionNode)
        assert inner.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NAN

    def test_clip_both(self):
        expr = ma.col("x").clip(lower=0, upper=100)
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 2

    def test_clip_lower_only(self):
        expr = ma.col("x").clip(lower=0)
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 1

    def test_eq_missing(self):
        expr = ma.col("x").eq_missing(42)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.OR

    def test_ne_missing(self):
        expr = ma.col("x").ne_missing(42)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.NOT

    def test_is_close(self):
        expr = ma.col("x").is_close(3.14)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.LTE
