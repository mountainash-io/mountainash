"""Tests for schema inference from relation node trees."""
import pytest

from mountainash.relations.schema_inference import (
    infer_expression_name,
    _schema_from_dataframe,
    _schema_from_table_schema,
)


class TestInferExpressionName:
    def test_field_reference(self):
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode
        node = FieldReferenceNode(field="age")
        assert infer_expression_name(node) == "age"

    def test_alias_wrapping_field(self):
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
        inner = FieldReferenceNode(field="age")
        alias_node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[inner],
            options={"name": "user_age"},
        )
        assert infer_expression_name(alias_node) == "user_age"

    def test_alias_wrapping_computation(self):
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC, FKEY_MOUNTAINASH_NAME
        a = FieldReferenceNode(field="a")
        b = FieldReferenceNode(field="b")
        add_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            arguments=[a, b],
        )
        alias_node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[add_node],
            options={"name": "sum_ab"},
        )
        assert infer_expression_name(alias_node) == "sum_ab"

    def test_computed_no_alias_returns_none(self):
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        a = FieldReferenceNode(field="a")
        b = FieldReferenceNode(field="b")
        add_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            arguments=[a, b],
        )
        assert infer_expression_name(add_node) is None

    def test_prefix_name_operation(self):
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
        inner = FieldReferenceNode(field="score")
        prefix_node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.PREFIX,
            arguments=[inner],
            options={"prefix": "raw_"},
        )
        assert infer_expression_name(prefix_node) == "raw_score"

    def test_suffix_name_operation(self):
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME
        inner = FieldReferenceNode(field="score")
        suffix_node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.SUFFIX,
            arguments=[inner],
            options={"suffix": "_norm"},
        )
        assert infer_expression_name(suffix_node) == "score_norm"

    def test_literal_node_returns_none(self):
        from mountainash.expressions.core.expression_nodes import LiteralNode
        node = LiteralNode(value=42)
        assert infer_expression_name(node) is None


class TestSchemaFromDataframe:
    def test_polars_lazyframe(self):
        import polars as pl
        lf = pl.LazyFrame({"a": [1, 2], "b": ["x", "y"], "c": [1.0, 2.0]})
        schema = _schema_from_dataframe(lf)
        assert list(schema.keys()) == ["a", "b", "c"]
        assert schema["a"] == pl.Int64
        assert schema["b"] == pl.String
        assert schema["c"] == pl.Float64

    def test_polars_dataframe(self):
        import polars as pl
        df = pl.DataFrame({"x": [True, False], "y": [1, 2]})
        schema = _schema_from_dataframe(df)
        assert list(schema.keys()) == ["x", "y"]
        assert schema["x"] == pl.Boolean
        assert schema["y"] == pl.Int64

    def test_unknown_type_returns_empty(self):
        schema = _schema_from_dataframe("not a dataframe")
        assert schema == {}


class TestSchemaFromTableSchema:
    def test_frictionless_schema(self):
        table_schema = {
            "fields": [
                {"name": "id", "type": "integer"},
                {"name": "name", "type": "string"},
                {"name": "active", "type": "boolean"},
            ]
        }
        schema = _schema_from_table_schema(table_schema)
        assert list(schema.keys()) == ["id", "name", "active"]
        assert schema["id"] == "integer"
        assert schema["name"] == "string"
        assert schema["active"] == "boolean"

    def test_empty_schema(self):
        schema = _schema_from_table_schema({})
        assert schema == {}

    def test_missing_fields(self):
        schema = _schema_from_table_schema({"primaryKey": "id"})
        assert schema == {}
