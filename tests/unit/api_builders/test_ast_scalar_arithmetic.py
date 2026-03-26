"""AST construction tests for arithmetic API builders."""
import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import ScalarFunctionNode, FieldReferenceNode, LiteralNode
from mountainash_expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_ARITHMETIC,
    FKEY_MOUNTAINASH_SCALAR_ARITHMETIC,
)


class TestBinaryArithmetic:
    @pytest.mark.parametrize("method,fkey", [
        ("add", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD),
        ("subtract", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT),
        ("multiply", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY),
        ("divide", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE),
        ("modulus", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO),
        ("power", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER),
    ])
    def test_binary_arithmetic(self, method, fkey):
        expr = getattr(ma.col("x"), method)(5)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 2
        assert isinstance(node.arguments[0], FieldReferenceNode)
        assert isinstance(node.arguments[1], LiteralNode)
        assert node.arguments[1].value == 5


class TestReverseArithmetic:
    @pytest.mark.parametrize("method,fkey", [
        ("rsubtract", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SUBTRACT),
        ("rdivide", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DIVIDE),
        ("rmodulus", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MODULO),
        ("rpower", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.POWER),
    ])
    def test_reverse_arithmetic(self, method, fkey):
        expr = getattr(ma.col("x"), method)(10)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        # Reverse: literal is first argument, column is second
        assert isinstance(node.arguments[0], LiteralNode)
        assert node.arguments[0].value == 10
        assert isinstance(node.arguments[1], FieldReferenceNode)


class TestUnaryArithmetic:
    @pytest.mark.parametrize("method,fkey", [
        ("negate", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.NEGATE),
        ("sqrt", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SQRT),
        ("exp", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.EXP),
        ("abs", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ABS),
        ("sign", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIGN),
    ])
    def test_unary_arithmetic(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1
        assert isinstance(node.arguments[0], FieldReferenceNode)


class TestTrigonometric:
    @pytest.mark.parametrize("method,fkey", [
        ("sin", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SIN),
        ("cos", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COS),
        ("tan", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TAN),
        ("asin", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASIN),
        ("acos", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOS),
        ("atan", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN),
    ])
    def test_trig_unary(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1

    def test_atan2(self):
        expr = ma.col("y").atan2(ma.col("x"))
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATAN2
        assert len(node.arguments) == 2


class TestHyperbolic:
    @pytest.mark.parametrize("method,fkey", [
        ("sinh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.SINH),
        ("cosh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.COSH),
        ("tanh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.TANH),
        ("asinh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ASINH),
        ("acosh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ACOSH),
        ("atanh", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ATANH),
    ])
    def test_hyperbolic_unary(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1


class TestAngularConversion:
    @pytest.mark.parametrize("method,fkey", [
        ("radians", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.RADIANS),
        ("degrees", FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.DEGREES),
    ])
    def test_angular_conversion(self, method, fkey):
        expr = getattr(ma.col("x"), method)()
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == fkey
        assert len(node.arguments) == 1


class TestExtensionArithmetic:
    def test_floor_divide(self):
        expr = ma.col("x").floor_divide(3)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE
        assert len(node.arguments) == 2

    def test_rfloor_divide(self):
        expr = ma.col("x").rfloor_divide(10)
        node = expr._node
        assert isinstance(node, ScalarFunctionNode)
        assert node.function_key == FKEY_MOUNTAINASH_SCALAR_ARITHMETIC.FLOOR_DIVIDE
        # Reverse: literal is first argument, column is second
        assert isinstance(node.arguments[0], LiteralNode)
        assert node.arguments[0].value == 10


class TestArithmeticAliases:
    @pytest.mark.parametrize("alias_method,canonical_method", [
        ("sub", "subtract"),
        ("mul", "multiply"),
        ("truediv", "divide"),
        ("mod", "modulus"),
        ("pow", "power"),
    ])
    def test_polars_alias(self, alias_method, canonical_method):
        canonical = getattr(ma.col("x"), canonical_method)(5)._node
        alias = getattr(ma.col("x"), alias_method)(5)._node
        assert canonical.function_key == alias.function_key
        assert canonical.arguments[1].value == alias.arguments[1].value

    def test_neg_alias(self):
        canonical = ma.col("x").negate()._node
        alias = ma.col("x").neg()._node
        assert canonical.function_key == alias.function_key

    def test_floordiv_alias(self):
        canonical = ma.col("x").floor_divide(3)._node
        alias = ma.col("x").floordiv(3)._node
        assert canonical.function_key == alias.function_key

    def test_modulo_alias(self):
        canonical = ma.col("x").modulus(3)._node
        alias = ma.col("x").modulo(3)._node
        assert canonical.function_key == alias.function_key

    def test_rmodulo_alias(self):
        canonical = ma.col("x").rmodulus(3)._node
        alias = ma.col("x").rmodulo(3)._node
        assert canonical.function_key == alias.function_key


class TestBitwiseStubs:
    """Bitwise methods are protocol stubs (body is `...`), not yet implemented."""

    @pytest.mark.xfail(reason="bitwise_not is a protocol stub, not yet implemented")
    def test_bitwise_not(self):
        expr = ma.col("x").bitwise_not()
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="bitwise_and is a protocol stub, not yet implemented")
    def test_bitwise_and(self):
        expr = ma.col("x").bitwise_and(ma.col("y"))
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="bitwise_or is a protocol stub, not yet implemented")
    def test_bitwise_or(self):
        expr = ma.col("x").bitwise_or(ma.col("y"))
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="bitwise_xor is a protocol stub, not yet implemented")
    def test_bitwise_xor(self):
        expr = ma.col("x").bitwise_xor(ma.col("y"))
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="shift_left is a protocol stub, not yet implemented")
    def test_shift_left(self):
        expr = ma.col("x").shift_left(2)
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="shift_right is a protocol stub, not yet implemented")
    def test_shift_right(self):
        expr = ma.col("x").shift_right(2)
        assert isinstance(expr._node, ScalarFunctionNode)

    @pytest.mark.xfail(reason="shift_right_unsigned is a protocol stub, not yet implemented")
    def test_shift_right_unsigned(self):
        expr = ma.col("x").shift_right_unsigned(2)
        assert isinstance(expr._node, ScalarFunctionNode)
