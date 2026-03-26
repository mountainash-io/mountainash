"""AST construction tests for conditional API builders."""
import pytest
import mountainash_expressions as ma
from mountainash_expressions.core.expression_nodes import IfThenNode, FieldReferenceNode, LiteralNode, ScalarFunctionNode


class TestConditionalChain:
    def test_simple_when_then_otherwise(self):
        expr = ma.when(ma.col("x").gt(10)).then(ma.lit("big")).otherwise(ma.lit("small"))
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 1
        cond, value = node.conditions[0]
        assert isinstance(cond, ScalarFunctionNode)
        assert isinstance(value, LiteralNode)
        assert value.value == "big"
        assert isinstance(node.else_clause, LiteralNode)
        assert node.else_clause.value == "small"

    def test_chained_when_then(self):
        expr = (
            ma.when(ma.col("x").gt(90)).then(ma.lit("A"))
            .when(ma.col("x").gt(80)).then(ma.lit("B"))
            .otherwise(ma.lit("C"))
        )
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 2
        assert node.conditions[0][1].value == "A"
        assert node.conditions[1][1].value == "B"
        assert node.else_clause.value == "C"

    def test_condition_is_field_reference(self):
        expr = ma.when(ma.col("flag")).then(ma.lit(1)).otherwise(ma.lit(0))
        node = expr._node
        assert isinstance(node, IfThenNode)
        cond, _ = node.conditions[0]
        assert isinstance(cond, FieldReferenceNode)
        assert cond.field == "flag"

    def test_raw_literal_values_wrapped(self):
        # Raw values (not ma.lit()) should be automatically wrapped in LiteralNode
        expr = ma.when(ma.col("x").gt(10)).then("big").otherwise("small")
        node = expr._node
        assert isinstance(node, IfThenNode)
        _, value = node.conditions[0]
        assert isinstance(value, LiteralNode)
        assert value.value == "big"
        assert isinstance(node.else_clause, LiteralNode)
        assert node.else_clause.value == "small"

    def test_triple_chained_when_then(self):
        expr = (
            ma.when(ma.col("x").gt(90)).then(ma.lit("A"))
            .when(ma.col("x").gt(80)).then(ma.lit("B"))
            .when(ma.col("x").gt(70)).then(ma.lit("C"))
            .otherwise(ma.lit("F"))
        )
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert len(node.conditions) == 3
        assert node.conditions[0][1].value == "A"
        assert node.conditions[1][1].value == "B"
        assert node.conditions[2][1].value == "C"
        assert node.else_clause.value == "F"

    def test_nested_expression_in_then(self):
        # The then() value can itself be an expression
        expr = ma.when(ma.col("x").gt(10)).then(ma.col("y").add(1)).otherwise(ma.lit(0))
        node = expr._node
        assert isinstance(node, IfThenNode)
        _, value = node.conditions[0]
        assert isinstance(value, ScalarFunctionNode)

    def test_otherwise_with_expression(self):
        expr = ma.when(ma.col("x").gt(10)).then(ma.lit(1)).otherwise(ma.col("default"))
        node = expr._node
        assert isinstance(node, IfThenNode)
        assert isinstance(node.else_clause, FieldReferenceNode)
        assert node.else_clause.field == "default"
