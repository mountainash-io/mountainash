"""AST construction tests for Polars-compatible window aliases."""
import mountainash.expressions as ma
from mountainash.expressions.core.expression_nodes import WindowFunctionNode


class TestWindowAliases:
    def test_shift_positive_is_lag(self):
        canonical = ma.col("x").lag(3)._node
        alias = ma.col("x").shift(3)._node
        assert isinstance(alias, WindowFunctionNode)
        assert alias.function_key == canonical.function_key
        assert alias.arguments[1].value == 3

    def test_shift_negative_is_lead(self):
        canonical = ma.col("x").lead(3)._node
        alias = ma.col("x").shift(-3)._node
        assert isinstance(alias, WindowFunctionNode)
        assert alias.function_key == canonical.function_key
        assert alias.arguments[1].value == 3

    def test_shift_default(self):
        alias = ma.col("x").shift()._node
        assert isinstance(alias, WindowFunctionNode)
        assert alias.arguments[1].value == 1

    def test_shift_with_fill_value(self):
        alias = ma.col("x").shift(2, fill_value=0)._node
        assert isinstance(alias, WindowFunctionNode)
        assert len(alias.arguments) == 3

    def test_first_is_first_value(self):
        canonical = ma.col("x").first_value()._node
        alias = ma.col("x").first()._node
        assert isinstance(alias, WindowFunctionNode)
        assert alias.function_key == canonical.function_key

    def test_last_is_last_value(self):
        canonical = ma.col("x").last_value()._node
        alias = ma.col("x").last()._node
        assert isinstance(alias, WindowFunctionNode)
        assert alias.function_key == canonical.function_key
