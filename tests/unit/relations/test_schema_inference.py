"""Tests for schema inference from relation node trees."""
import pytest

from mountainash.relations.schema_inference import (
    infer_expression_name,
    _schema_from_dataframe,
    _schema_from_table_schema,
    infer_schema,
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


class TestInferSchemaLeafNodes:
    def test_read_rel_node_polars(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode
        df = pl.LazyFrame({"a": [1], "b": ["x"]})
        node = ReadRelNode(dataframe=df)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]
        assert schema["a"] == pl.Int64
        assert schema["b"] == pl.String

    def test_ref_rel_node_with_resolver(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
        node = RefRelNode(name="users")
        def resolver(name):
            return {"id": "Int64", "username": "String"}
        schema = infer_schema(node, ref_resolver=resolver)
        assert schema == {"id": "Int64", "username": "String"}

    def test_ref_rel_node_without_resolver(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
        node = RefRelNode(name="users")
        schema = infer_schema(node)
        assert schema == {}

    def test_resource_read_rel_node(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
        from mountainash.typespec.datapackage import DataResource
        resource = DataResource(
            name="test", path="test.csv", type="table", format="csv",
            table_schema={
                "fields": [
                    {"name": "id", "type": "integer"},
                    {"name": "value", "type": "number"},
                ]
            },
        )
        node = ResourceReadRelNode(resource=resource)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["id", "value"]
        assert schema["id"] == "integer"

    def test_source_rel_node(self):
        from mountainash.relations.core.relation_nodes.extensions_mountainash import SourceRelNode
        from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
        node = SourceRelNode(
            data=[{"x": 1, "y": "a"}, {"x": 2, "y": "b"}],
            detected_format=CONST_PYTHON_DATAFORMAT.PYLIST,
        )
        schema = infer_schema(node)
        assert "x" in schema
        assert "y" in schema


class TestInferSchemaPassThroughNodes:
    def test_filter_preserves_schema(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, FilterRelNode
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode, LiteralNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": ["x"]}))
        condition = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT,
            arguments=[FieldReferenceNode(field="a"), LiteralNode(value=0)],
        )
        node = FilterRelNode(input=read, predicate=condition)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]

    def test_sort_preserves_schema(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, SortRelNode
        from mountainash.core.constants import SortField
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": ["x"]}))
        node = SortRelNode(input=read, sort_fields=[SortField(column="a", descending=False)])
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]

    def test_fetch_preserves_schema(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, FetchRelNode
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": ["x"]}))
        node = FetchRelNode(input=read, count=10)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]


class TestInferSchemaProject:
    def test_select(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.core.constants import ProjectOperation
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2], "c": [3]}))
        node = ProjectRelNode(
            input=read,
            expressions=[FieldReferenceNode(field="a"), FieldReferenceNode(field="c")],
            operation=ProjectOperation.SELECT,
        )
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "c"]

    def test_with_columns_adds_new(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.core.constants import ProjectOperation
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME, FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2]}))
        add_expr = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD,
            arguments=[FieldReferenceNode(field="a"), FieldReferenceNode(field="b")],
        )
        aliased = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[add_expr],
            options={"name": "c"},
        )
        node = ProjectRelNode(input=read, expressions=[aliased], operation=ProjectOperation.WITH_COLUMNS)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b", "c"]

    def test_with_columns_replaces_existing(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.core.constants import ProjectOperation
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME, FKEY_SUBSTRAIT_SCALAR_ARITHMETIC
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2]}))
        doubled = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.MULTIPLY,
            arguments=[FieldReferenceNode(field="a"), FieldReferenceNode(field="a")],
        )
        aliased = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[doubled],
            options={"name": "a"},
        )
        node = ProjectRelNode(input=read, expressions=[aliased], operation=ProjectOperation.WITH_COLUMNS)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]

    def test_rename(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.core.constants import ProjectOperation
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2]}))
        node = ProjectRelNode(
            input=read, expressions=[], operation=ProjectOperation.RENAME,
            rename_mapping={"a": "x"},
        )
        schema = infer_schema(node)
        assert list(schema.keys()) == ["x", "b"]

    def test_drop(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.core.constants import ProjectOperation
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2], "c": [3]}))
        node = ProjectRelNode(
            input=read,
            expressions=[FieldReferenceNode(field="b")],
            operation=ProjectOperation.DROP,
        )
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "c"]


class TestInferSchemaAggregate:
    def test_group_by_with_measures(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, AggregateRelNode
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode, ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_AGGREGATE, FKEY_MOUNTAINASH_NAME
        read = ReadRelNode(dataframe=pl.LazyFrame({"group": ["a", "b"], "val": [1, 2]}))
        count_node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_AGGREGATE.COUNT,
            arguments=[FieldReferenceNode(field="val")],
        )
        aliased_count = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_NAME.ALIAS,
            arguments=[count_node],
            options={"name": "n"},
        )
        node = AggregateRelNode(
            input=read,
            keys=[FieldReferenceNode(field="group")],
            measures=[aliased_count],
        )
        schema = infer_schema(node)
        assert list(schema.keys()) == ["group", "n"]


class TestInferSchemaJoin:
    def test_inner_join_on(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, JoinRelNode
        from mountainash.core.constants import JoinType
        left = ReadRelNode(dataframe=pl.LazyFrame({"id": [1], "a": [10]}))
        right = ReadRelNode(dataframe=pl.LazyFrame({"id": [1], "b": [20]}))
        node = JoinRelNode(left=left, right=right, join_type=JoinType.INNER, on=["id"])
        schema = infer_schema(node)
        assert "id" in schema
        assert "a" in schema
        assert "b" in schema
        assert "id_right" not in schema

    def test_left_join_left_on_right_on(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, JoinRelNode
        from mountainash.core.constants import JoinType
        left = ReadRelNode(dataframe=pl.LazyFrame({"lid": [1], "a": [10]}))
        right = ReadRelNode(dataframe=pl.LazyFrame({"rid": [1], "b": [20]}))
        node = JoinRelNode(left=left, right=right, join_type=JoinType.LEFT, left_on=["lid"], right_on=["rid"])
        schema = infer_schema(node)
        assert list(schema.keys()) == ["lid", "a", "rid", "b"]

    def test_join_suffix_on_overlap(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, JoinRelNode
        from mountainash.core.constants import JoinType
        left = ReadRelNode(dataframe=pl.LazyFrame({"id": [1], "val": [10]}))
        right = ReadRelNode(dataframe=pl.LazyFrame({"id": [1], "val": [20]}))
        node = JoinRelNode(left=left, right=right, join_type=JoinType.INNER, on=["id"], suffix="_r")
        schema = infer_schema(node)
        assert "val" in schema
        assert "val_r" in schema

    def test_semi_join_only_left_columns(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, JoinRelNode
        from mountainash.core.constants import JoinType
        left = ReadRelNode(dataframe=pl.LazyFrame({"id": [1], "a": [10]}))
        right = ReadRelNode(dataframe=pl.LazyFrame({"id": [1], "b": [20]}))
        node = JoinRelNode(left=left, right=right, join_type=JoinType.SEMI, on=["id"])
        schema = infer_schema(node)
        assert list(schema.keys()) == ["id", "a"]


class TestInferSchemaSet:
    def test_set_uses_first_input_schema(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, SetRelNode
        from mountainash.core.constants import SetType
        first = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2]}))
        second = ReadRelNode(dataframe=pl.LazyFrame({"a": [3], "b": [4]}))
        node = SetRelNode(inputs=[first, second], set_type=SetType.UNION_ALL)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]
