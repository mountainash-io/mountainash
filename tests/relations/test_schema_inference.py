"""Tests for schema inference from relation node trees."""
import pytest
import mountainash as ma
import polars as pl

from mountainash.core.dtypes import MountainashDtype as D, SchemaTypeStatus
from mountainash.relations.schema_inference import (
    infer_expression_name,
    _schema_from_dataframe,
    _schema_from_table_schema,
    infer_schema,
)


def _native_source_schema(frame, backend_name):
    from mountainash.core.dtypes import NativeDtype, TypeTarget

    text = D.STRING
    if backend_name in {"pandas", "narwhals-pandas"}:
        import narwhals as nw
        text = NativeDtype(value=nw.to_native(frame).dtypes["text"], target=TypeTarget.PANDAS)
    return {"n": D.I64, "text": text}

@pytest.mark.cross_backend
@pytest.mark.parametrize("expression,origins", [
    (ma.col("n").alias("copy"), {"copy": "n"}),
    (ma.col("*").name.prefix("p_"), {"p_n": "n", "p_text": "text"}),
    (ma.col("*").name.suffix("_s"), {"n_s": "n", "text_s": "text"}),
    (ma.col("*").name.to_uppercase(), {"N": "n", "TEXT": "text"}),
    (ma.col("*").name.to_uppercase().name.to_lowercase(), {"n": "n", "text": "text"}),
    (ma.col("^n$").alias("copy"), {"copy": "n"}),
])
def test_projection_preserves_source_identity(backend_name, backend_factory, expression, origins):
    frame = backend_factory.create({"n": [1], "text": ["a"]}, backend_name)
    source_schema = _native_source_schema(frame, backend_name)
    expected = {name: source_schema[source] for name, source in origins.items()}
    rel = ma.relation(frame)
    assert list(infer_schema(rel.select(expression)._node).items()) == list(expected.items())


@pytest.mark.cross_backend
@pytest.mark.parametrize("expression,expected_type", [
    (ma.col("n") + 1, D.I64),
    (ma.col("n") > 0, D.BOOL),
    (ma.col("n").cast(D.STRING), D.STRING),
    ((ma.col("n") + 1).name.prefix("computed_"), D.I64),
])
def test_projection_computation_has_native_result_type(backend_name, backend_factory, expression, expected_type):
    frame = backend_factory.create({"n": [1], "text": ["a"]}, backend_name)
    source_schema = _native_source_schema(frame, backend_name)
    rel = ma.relation(frame)
    changed = rel.with_columns(expression.alias("n"))
    from mountainash.core.dtypes import dtype_family
    if backend_name == "ibis-sqlite" and expected_type is D.BOOL:
        expected_type = D.I64  # SQLite's physical Boolean result is an integer.
    assert changed.schema["text"] == source_schema["text"]
    assert list(changed.schema) == ["n", "text"]
    assert dtype_family(changed.schema["n"]) is expected_type
    selected = rel.select(expression.alias("new"))
    assert list(selected.schema) == ["new"]
    assert dtype_family(selected.schema["new"]) is expected_type


@pytest.mark.cross_backend
def test_projection_computed_type_survives_rename_and_select(backend_name, backend_factory):
    rel = ma.relation(backend_factory.create({"n": [1]}, backend_name))
    changed = rel.with_columns((ma.col("n") + 1).alias("n"))
    assert changed.rename({"n": "renamed"}).select(ma.col("renamed").alias("copy")).schema == {
        "copy": D.I64,
    }


@pytest.mark.cross_backend
def test_projection_replacements_use_original_input(backend_name, backend_factory):
    frame = backend_factory.create({"n": [1], "text": ["a"]}, backend_name)
    source_schema = _native_source_schema(frame, backend_name)
    rel = ma.relation(frame)
    changed = rel.with_columns(ma.col("text").alias("n"), ma.col("n").alias("copy"))
    expected = {
        "n": source_schema["text"],
        "text": source_schema["text"],
        "copy": source_schema["n"],
    }
    assert changed.schema == expected
    empty = rel.head(0).with_columns(ma.col("text").alias("n"), ma.col("n").alias("copy"))
    assert empty.schema == expected


def test_projection_preserves_unconstrained_source_status():
    # The structural helper preserves a declaration without opening its source.
    pkg = ma.DataPackage(resources=[ma.DataResource(
        name="source", path="not-read.csv", type="table", format="csv",
        table_schema={"fields": [{"name": "free", "type": "any"}]},
    )])
    dag = pkg.to_relation_dag()
    from mountainash.relations.dag.introspection import structural_schema
    projected = dag.ref("source").select(ma.col("free").alias("copy"))
    assert infer_schema(projected._node, lambda name: structural_schema(dag, name)) == {
        "copy": SchemaTypeStatus.UNCONSTRAINED,
    }


@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize("selector,names", [("*", ["n", "m"]), ("^n$", ["n"]), ("^absent$", [])])
def test_complete_projection_expansion_schema(operation, selector, names):
    rel = getattr(ma.relation([{"n": 1, "m": 2}]), operation)(ma.col(selector))
    assert rel.columns == (names if operation == "select" else ["n", "m"])


@pytest.mark.parametrize("operation", ["select", "with_columns"])
def test_projection_expansion_collisions_rejected_when_schema_known(operation):
    from mountainash.relations.core.projection_names import ProjectionNameError

    rel = getattr(ma.relation([{"n": 1, "m": 2}]), operation)(ma.col("*"), ma.col("n"))
    with pytest.raises(ProjectionNameError, match="expression 1.*duplicate.*n"):
        _ = rel.columns


@pytest.mark.parametrize("transform", [lambda r: r.select("n"), lambda r: r.unique()])
def test_incomplete_projection_schema_survives_downstream_operation(transform):
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode
    source = Relation(RefRelNode(name="unbound"))
    rel = transform(source.with_columns(ma.native(pl.all()).alias("x")))
    with pytest.raises(IncompleteProjectionSchemaError, match="PROJECT_WITH_COLUMNS.*expression 0"):
        _ = rel.schema


@pytest.mark.parametrize("operation", ["select", "with_columns"])
def test_empty_alias_is_a_known_projection_name(operation):
    rel = getattr(ma.relation([{"n": 1}]), operation)(ma.col("n").alias(""))
    assert rel.columns == ([""] if operation == "select" else ["n", ""])


def test_projection_build_does_not_require_dag_source_schema():
    dag = ma.RelationDAG()
    rel = dag.ref("not_registered_yet").select(ma.col("n") + 1)
    dag.add("not_registered_yet", ma.relation([{"n": 1}]))
    assert rel.columns == ["n"]


@pytest.mark.parametrize("operation", ["select", "with_columns"])
def test_unnamed_projection_requires_alias_with_operation_diagnostic(operation):
    from mountainash.expressions.core.expression_nodes import WindowFunctionNode
    from mountainash.expressions.core.expression_system.function_keys.enums import SUBSTRAIT_ARITHMETIC_WINDOW
    from mountainash.relations.core.projection_names import ProjectionNameError

    expr = ma.col("n").create(WindowFunctionNode(function_key=SUBSTRAIT_ARITHMETIC_WINDOW.PERCENT_RANK))
    rel = ma.relation([{"n": 1}])
    with pytest.raises(ProjectionNameError, match=f"PROJECT_{operation.upper()}.*expression 0.*PERCENT_RANK.*alias"):
        getattr(rel, operation)(expr)
    named = getattr(rel, operation)(expr.alias("percentile"))
    assert list(infer_schema(named._node)) == (["percentile"] if operation == "select" else ["n", "percentile"])
    with pytest.raises(ValueError, match="requires .over"):
        named.collect_schema(allow_execution=True)


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

    def test_native_ibis_deferred_does_not_recurse(self):
        """A raw Ibis deferred's __getattr__ returns a new Deferred for any
        attribute, including `_node` -- the hasattr(expr_node, "_node") probe
        this function used to use recursed on it forever. Regression for the
        same bug class as item 115 (structured_lineage._named_values)."""
        import ibis

        assert infer_expression_name(ibis._.score) is None


class TestSchemaFromDataframe:
    def test_polars_lazyframe(self):
        import polars as pl
        lf = pl.LazyFrame({"a": [1, 2], "b": ["x", "y"], "c": [1.0, 2.0]})
        schema = _schema_from_dataframe(lf)
        assert list(schema.keys()) == ["a", "b", "c"]
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["a"] == D.I64
        assert schema["b"] == D.STRING
        assert schema["c"] == D.FP64

    def test_polars_dataframe(self):
        import polars as pl
        df = pl.DataFrame({"x": [True, False], "y": [1, 2]})
        schema = _schema_from_dataframe(df)
        assert list(schema.keys()) == ["x", "y"]
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["x"] == D.BOOL
        assert schema["y"] == D.I64

    def test_unknown_type_returns_empty(self):
        schema = _schema_from_dataframe("not a dataframe")
        assert schema == {}

    def test_pandas_dataframe(self):
        """item 48 Task 7: pandas branch resolves recognized dtypes via
        the registry's PANDAS target (not degraded to UNKNOWN)."""
        import pandas as pd
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"], "c": [1.0, 2.0], "d": [True, False]})
        schema = _schema_from_dataframe(df)
        assert list(schema.keys()) == ["a", "b", "c", "d"]
        assert schema["a"] == D.I64
        from mountainash.core.dtypes import NativeDtype, TypeTarget
        assert schema["b"] == NativeDtype(value=df.dtypes["b"], target=TypeTarget.PANDAS)
        assert schema["c"] == D.FP64
        assert schema["d"] == D.BOOL

    def test_pandas_object_dtype_is_preserved_as_native_not_raise(self):
        """Object storage is known native metadata, not inferred value type."""
        import pandas as pd
        from mountainash.core.dtypes import NativeDtype, TypeTarget

        df = pd.DataFrame({"a": [1, 2], "obj": [object(), object()]})
        schema = _schema_from_dataframe(df)
        assert schema["a"] == D.I64
        assert isinstance(schema["obj"], NativeDtype)
        assert schema["obj"].target is TypeTarget.PANDAS

    def test_ibis_table(self):
        """An Ibis table's logical schema decodes through the Ibis type target,
        not the Polars default (which once degraded every Ibis column to UNKNOWN)."""
        import ibis
        t = ibis.memtable({"a": [1, 2], "b": ["x", "y"]})
        schema = _schema_from_dataframe(t)
        assert schema["a"] == D.I64
        assert schema["b"] == D.STRING

    @pytest.mark.parametrize("lazy", [False, True])
    def test_wrapped_polars_keeps_polars_time_precision(self, lazy):
        """Narwhals' own Time carries no precision; the wrapped Polars schema does."""
        import datetime

        import narwhals as nw
        from mountainash.core.dtypes import TimeDtype

        frame = pl.DataFrame({"t": [datetime.time(1)]})
        wrapped = nw.from_native(frame.lazy() if lazy else frame)
        assert _schema_from_dataframe(wrapped)["t"] == TimeDtype(precision=9)
        relation = ma.relation(wrapped)
        assert relation.schema["t"] == TimeDtype(precision=9)
        assert relation.collect_schema()["t"] == TimeDtype(precision=9)

    @pytest.mark.parametrize("wrapped", [False, True])
    def test_empty_arrow_backed_pandas_time_precision_comes_from_schema(self, wrapped):
        """Schema evidence, not value sampling: a zero-row column still has precision."""
        import narwhals as nw
        import pandas as pd
        import pyarrow as pa
        from mountainash.core.dtypes import TimeDtype

        frame = pd.DataFrame({"t": pd.Series([], dtype=pd.ArrowDtype(pa.time64("us")))})
        relation = ma.relation(nw.from_native(frame) if wrapped else frame)
        assert relation.schema["t"] == TimeDtype(precision=6)
        assert relation.collect_schema()["t"] == TimeDtype(precision=6)

    def test_logical_acquisition_never_describes_sql_output(self, monkeypatch):
        """Logical Ibis types come from the expression; physical SQL description is
        the relation system's separate operation."""
        import ibis

        connection = ibis.duckdb.connect()
        try:
            table = connection.create_table("logical_only", {"n": [1]})

            def unexpected_compile(*args, **kwargs):
                raise AssertionError("logical acquisition must not describe SQL output")

            monkeypatch.setattr(connection, "compile", unexpected_compile)
            assert _schema_from_dataframe(table) == {"n": D.I64}
            assert infer_schema(ma.relation(table)._node) == {"n": D.I64}
        finally:
            connection.disconnect()


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
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["id"] == D.I64
        assert schema["name"] == D.STRING
        assert schema["active"] == D.BOOL

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
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["a"] == D.I64
        assert schema["b"] == D.STRING

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
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["id"] == D.I64

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
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2], "c": [3]}))
        node = ProjectRelNode(
            input=read,
            expressions=[FieldReferenceNode(field="a"), FieldReferenceNode(field="c")],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_SELECT,
        )
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "c"]

    def test_with_columns_adds_new(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
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
        node = ProjectRelNode(input=read, expressions=[aliased], operation=RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b", "c"]

    def test_with_columns_replaces_existing(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
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
        node = ProjectRelNode(input=read, expressions=[aliased], operation=RKEY_SUBSTRAIT_REL.PROJECT_WITH_COLUMNS)
        schema = infer_schema(node)
        assert list(schema.keys()) == ["a", "b"]

    def test_rename(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2]}))
        node = ProjectRelNode(
            input=read, expressions=[], operation=RKEY_SUBSTRAIT_REL.PROJECT_RENAME,
            rename_mapping={"a": "x"},
        )
        schema = infer_schema(node)
        assert list(schema.keys()) == ["x", "b"]

    def test_drop(self):
        import polars as pl
        from mountainash.relations.core.relation_nodes.substrait import ReadRelNode, ProjectRelNode
        from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL
        from mountainash.expressions.core.expression_nodes import FieldReferenceNode
        read = ReadRelNode(dataframe=pl.LazyFrame({"a": [1], "b": [2], "c": [3]}))
        node = ProjectRelNode(
            input=read,
            expressions=[FieldReferenceNode(field="b")],
            operation=RKEY_SUBSTRAIT_REL.PROJECT_DROP,
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

    def test_unaliased_measure_named_after_source_column(self):
        # Item 46 (a): col("v").sum() infers as {"v": UNKNOWN}, not absent.
        df = pl.DataFrame({"k": ["a"], "v": [1]})
        rel = ma.relation(df).group_by("k").agg(ma.col("v").sum())
        schema = infer_schema(rel._node, None)
        assert schema["v"] is SchemaTypeStatus.UNKNOWN
        assert "k" in schema
        assert schema["k"] is not SchemaTypeStatus.UNKNOWN  # key stays typed

    def test_unaliased_compound_measure_uses_leftmost_root(self):
        # (col("a") + col("b")).sum() -> named "a" (Polars leftmost-root rule)
        df = pl.DataFrame({"k": ["x"], "a": [1], "b": [2]})
        rel = ma.relation(df).group_by("k").agg((ma.col("a") + ma.col("b")).sum())
        schema = infer_schema(rel._node, None)
        assert schema["a"] is SchemaTypeStatus.UNKNOWN

    def test_aliased_measure_unchanged(self):
        # Regression: alias still wins over the source-column fallback.
        df = pl.DataFrame({"k": ["a"], "v": [1]})
        rel = ma.relation(df).group_by("k").agg(ma.col("v").sum().alias("total"))
        schema = infer_schema(rel._node, None)
        assert "total" in schema
        assert "v" not in schema


@pytest.mark.parametrize("key,name", [
    (ma.col("g").alias("x"), "x"),
    (ma.col("g").alias(""), ""),
    (ma.col("g").name.prefix("pre_"), "pre_g"),
    (ma.col("g").name.suffix("_post"), "g_post"),
    (ma.col("g").name.to_uppercase(), "G"),
    (ma.col("g").alias("G").name.to_lowercase(), "g"),
])
def test_aggregate_key_type_follows_source(key, name):
    base = ma.relation([{"g": "a", "x": 3}])
    q = base.group_by(key).agg(ma.col("x").sum().alias("total"))
    assert q.columns == [name, "total"]
    assert q.schema[name] is D.STRING
    assert q.schema["total"] is D.I64


@pytest.mark.parametrize("key,expected", [
    ((ma.col("g") > 0).alias("g"), D.BOOL),
    (ma.col("g").cast(str), D.STRING),
    (ma.t_col("g", unknown={-1}), D.I64),
])
def test_aggregate_computed_key_uses_native_result_type(key, expected):
    q = ma.relation([{"g": 1, "x": 3}]).group_by(key).agg(ma.col("x").sum())
    assert q.schema["g"] is expected


def test_aggregate_key_preserves_unconstrained_type():
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    q = Relation(RefRelNode(name="source")).group_by(ma.col("g").alias("key")).agg(ma.col("x").sum())
    schema = infer_schema(q._node, lambda _: {"g": SchemaTypeStatus.UNCONSTRAINED})
    assert schema == {"key": SchemaTypeStatus.UNCONSTRAINED, "x": SchemaTypeStatus.UNKNOWN}


@pytest.mark.parametrize("transform", [
    lambda r: r,
    lambda r: r.filter(ma.col("x") > 0).sort("x").head(1),
    lambda r: r.with_columns(ma.lit(2).alias("two")),
    lambda r: r.rename({"x": "y"}),
    lambda r: r.drop("x"),
])
def test_aggregate_unknown_source_is_not_empty(transform):
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    q = transform(Relation(RefRelNode(name="unresolved"))).group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    # Even a nonempty legacy dtype mapping cannot certify all source names.
    with pytest.raises(IncompleteProjectionSchemaError):
        infer_schema(q._node, lambda _: {"x": D.I64})


@pytest.mark.parametrize("closed", [False, True])
def test_aggregate_scalar_names_over_unresolved_ref(closed):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    base = Relation(RefRelNode(name="unresolved"))
    if closed:
        base = base.select("g", "x").drop("x")
    q = base.group_by(ma.col("*") if closed else "g").agg(ma.col("x").sum())
    assert q.columns == ["g", "x"]


@pytest.mark.parametrize("source,selector,want", [
    (pl.DataFrame(), "*", ["one"]),
    ([{"x": 1}], "^absent$", ["one"]),
    ([{"x": 1}, {"x": 2, "y": 3}], "*", ["x", "y", "one"]),
])
def test_aggregate_complete_source_expansions(source, selector, want):
    q = ma.relation(source).filter(ma.lit(True)).head(1).group_by(ma.col(selector)).agg(ma.lit(1).alias("one"))
    assert q.columns == want


def test_aggregate_literal_measure_has_name_without_field_root():
    q = ma.relation([{"g": "a"}]).group_by("g").agg(ma.lit(1).sum())
    assert q.columns == ["g", "literal"]


def test_aggregate_resource_declaration_does_not_certify_all_columns(tmp_path):
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode

    path = tmp_path / "open.csv"
    pl.DataFrame({"x": [1], "y": [2]}).write_csv(path)
    resource = ma.DataResource(
        name="open", path=str(path), format="csv",
        schema={
            "fields": [{"name": "x", "type": "integer"}],
            "x-mountainash": {"fields_match": "open"},
        },
    )
    q = Relation(ResourceReadRelNode(resource=resource)).group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    with pytest.raises(IncompleteProjectionSchemaError):
        infer_schema(q._node)
    assert q.columns == ["x", "y", "one"]
    assert q.to_dicts() == [{"x": 1, "y": 2, "one": 1}]


class TestInferSchemaJoin:
    @pytest.mark.parametrize("how,coalesce,expected", [
        ("left", None, ["k", "v", "w", "kk", "w_right"]),
        ("left", True, ["k", "v", "w", "w_right"]),
        ("outer", None, ["k", "v", "w", "kk", "w_right"]),
    ])
    def test_left_on_right_on_columns(self, how, coalesce, expected):
        left = pl.DataFrame({"k": [1], "v": ["a"], "w": [0]})
        right = pl.DataFrame({"kk": [1], "w": [1]})
        rel = ma.relation(left).join(right, left_on="k", right_on="kk", how=how, coalesce=coalesce)
        assert rel.columns == expected

    def test_on_coalesce_false_keeps_suffixed_key(self):
        rel = ma.relation(pl.DataFrame({"id": [1], "a": [1]})).join(
            pl.DataFrame({"id": [1], "b": [1]}), on="id", coalesce=False)
        assert rel.columns == ["id", "a", "id_right", "b"]

    @pytest.mark.parametrize("raw", [
        {"kk": [1], "w": [1]},
        [{"kk": 1, "w": 1}, {"kk": 2, "w": 2}],
        ({"kk": 1}, {"kk": 2, "w": 2}),
    ])
    def test_raw_python_join_operand_names(self, raw):
        rel = ma.relation(pl.DataFrame({"k": [1], "w": [0]})).join(raw, left_on="k", right_on="kk")
        assert rel.columns == ["k", "w", "kk", "w_right"]
        assert rel.schema["kk"] is D.I64

    def test_merged_key_dtype_uses_native_join_result(self):
        left = pl.DataFrame({"k": pl.Series([1, 2], dtype=pl.Int32)})
        right = pl.DataFrame({"kk": pl.Series([2, 3], dtype=pl.Int64)})
        rel = ma.relation(left).join(right, left_on="k", right_on="kk", how="outer", coalesce=True)
        assert rel.schema["k"] is D.I64

    def test_merged_key_dtype_kept_when_key_dtypes_match(self):
        left = pl.DataFrame({"k": pl.Series([1, 2], dtype=pl.Int32)})
        right = pl.DataFrame({"kk": pl.Series([2, 3], dtype=pl.Int32)})
        rel = ma.relation(left).join(right, left_on="k", right_on="kk", how="outer", coalesce=True)
        assert rel.schema["k"] is D.I32
        assert rel.to_polars().schema["k"] == pl.Int32

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


class TestInferSchemaChain:
    def test_read_filter_project_chain(self):
        """Schema propagates through Read -> Filter -> Project correctly."""
        import polars as pl
        import mountainash as ma

        df = pl.LazyFrame({"a": [1, 2], "b": [3.0, 4.0], "c": ["x", "y"]})
        r = ma.relation(df).filter(ma.col("a").gt(1)).select("a", "c")
        schema = r.schema
        assert list(schema.keys()) == ["a", "c"]
        # spec 2026-06-10-type-system-unification: schema values are canonical now
        assert schema["a"] == D.I64
        assert schema["c"] == D.STRING

    def test_read_with_columns_rename_chain(self):
        """Schema propagates through Read -> WithColumns -> Rename."""
        import polars as pl
        import mountainash as ma

        df = pl.LazyFrame({"a": [1, 2], "b": [3, 4]})
        r = (
            ma.relation(df)
            .with_columns(ma.col("a").add(ma.col("b")).name.alias("c"))
            .rename({"a": "x"})
        )
        schema = r.schema
        assert "x" in schema
        assert "b" in schema
        assert "c" in schema
        assert "a" not in schema



class TestSourceDataInference:
    """Tests for _schema_from_source_data inline-data type inference (Task 2).

    Oracle for each case: pl.DataFrame(data, strict=False) schema mapped through
    the dtype registry (_schema_from_dataframe).
    """

    def test_list_of_dicts_int_and_str(self):
        """list[dict] with int and str columns infers canonical types.

        Oracle: pl.DataFrame([{"x": 1, "s": "a"}], strict=False)
            -> {"x": Int64, "s": String}
            -> {"x": D.I64, "s": D.STRING}
        """
        import mountainash as ma
        from mountainash.core.dtypes import MountainashDtype as D

        data = [{"x": 1, "s": "a"}]
        schema = ma.relation(data).schema
        assert schema["x"] == D.I64
        assert schema["s"] == D.STRING
        # Must also agree with the oracle (runtime to_polars path)
        import polars as pl
        from mountainash.relations.schema_inference import _schema_from_dataframe
        oracle = _schema_from_dataframe(pl.DataFrame(data, strict=False))
        assert schema == oracle

    def test_dict_mixed_int_float_coerces_to_fp64(self):
        """dict with mixed int/float values coerces to Float64 under strict=False.

        Oracle: pl.DataFrame({"a": [1, 2.5]}, strict=False)
            -> {"a": Float64}
            -> {"a": D.FP64}
        """
        import mountainash as ma
        from mountainash.core.dtypes import MountainashDtype as D

        data = {"a": [1, 2.5]}
        schema = ma.relation(data).schema
        assert schema["a"] == D.FP64

    def test_empty_list_returns_empty_schema(self):
        """Empty list → empty schema (no columns to infer)."""
        import mountainash as ma

        schema = ma.relation([]).schema
        assert schema == {}

    def test_unconstructable_inline_data_falls_back_to_unknown(self):
        """If pl.DataFrame construction fails, falls back to names-only UNKNOWN.

        A list with heterogeneous types that polars cannot reconcile
        (list vs str) triggers a ComputeError; the fallback preserves column
        names from data[0] and maps each to SchemaTypeStatus.UNKNOWN.
        """
        from mountainash.relations.core.relation_nodes.extensions_mountainash import SourceRelNode
        from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT
        from mountainash.relations.schema_inference import infer_schema
        from mountainash.core.dtypes import SchemaTypeStatus

        # [1, 2] vs "not_a_list" — polars strict=False cannot reconcile
        data = [{"x": [1, 2]}, {"x": "not_a_list"}]
        node = SourceRelNode(
            data=data,
            detected_format=CONST_PYTHON_DATAFORMAT.PYLIST,
        )
        schema = infer_schema(node)
        assert "x" in schema
        assert schema["x"] is SchemaTypeStatus.UNKNOWN


@pytest.mark.parametrize("data,expected", [
    ({"A": [{"x": 1}]}, [(1, "A", 1)]),
    ({"A": [(1, 2)]}, [(1, 2, "A", 1)]),
])
def test_aggregate_indexed_python_data_does_not_certify_index_keys(data, expected):
    """Python ingress owns indexed conversion; outer dict keys are not columns."""
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    q = ma.relation(data).group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    with pytest.raises(IncompleteProjectionSchemaError):
        infer_schema(q._node)
    assert "A" not in q.columns
    assert list(q.collect_schema()) == list(q.to_dict())
    assert q.to_tuples() == expected


@pytest.mark.parametrize("fields_match,contract,complete", [
    ("exact", None, True),
    ("equal", None, True),
    ("subset", None, True),
    ("partial", None, False),
    ("open", None, False),
    ("equal", {"extra_columns": "evolve"}, False),
    ("subset", {"missing_columns": "skip"}, False),
    ("partial", {"missing_columns": "null_fill"}, True),
])
@pytest.mark.parametrize("apply_conform", [True, False])
def test_aggregate_resource_names_require_closed_effective_contract(fields_match, contract, complete, apply_conform):
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    from mountainash.typespec.frictionless import table_schema_to_frictionless
    from mountainash.typespec.spec import FieldDefinition, TableSchema
    from mountainash.typespec.universal_types import UniversalType

    spec = TableSchema(fields={"x": FieldDefinition(type=UniversalType.INTEGER)}, fields_match=fields_match, contract=contract)
    resource = ma.DataResource(name="source", data=[{"x": 1}], schema=table_schema_to_frictionless(spec))
    base = Relation(ResourceReadRelNode(resource=resource, apply_schema_conform=apply_conform))
    q = base.group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    if complete and apply_conform:
        assert list(infer_schema(q._node)) == ["x", "one"]
    else:
        with pytest.raises(IncompleteProjectionSchemaError):
            infer_schema(q._node)


def test_aggregate_exact_resource_selector_schema_matches_execution(tmp_path):
    """Polars selector escape over an exact-conformed resource stays introspectable."""
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode

    path = tmp_path / "exact.csv"
    pl.DataFrame({"x": [1], "y": [2]}).write_csv(path)
    resource = ma.DataResource(name="exact", path=str(path), format="csv", schema={
        "fields": [{"name": "x", "type": "integer"}, {"name": "y", "type": "integer"}],
    })
    q = Relation(ResourceReadRelNode(resource=resource)).group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    assert q.columns == ["x", "y", "one"]
    assert q.select(*q.columns).to_dicts() == [{"x": 1, "y": 2, "one": 1}]


@pytest.mark.parametrize("transform,names", [
    (lambda r: r.with_columns(ma.lit(4).alias("z")), ["x", "y", "z", "one"]),
    (lambda r: r.rename({"x": "z"}).drop("y"), ["z", "one"]),
    (lambda r: r.group_by("x").agg(ma.col("y").sum()), ["x", "y", "one"]),
    (lambda r: r.unique(), ["x", "y", "one"]),
])
def test_aggregate_complete_names_through_reshaping(transform, names):
    """Name evidence follows closed outputs, without changing DISTINCT schema policy."""
    q = transform(ma.relation({"x": [1], "y": [2]})).group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    assert q.columns == names


def test_aggregate_subset_distinct_does_not_promise_portable_expansion():
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    base = ma.relation({"x": [1], "y": [2]}).unique(subset=["x"])
    q = base.group_by(ma.col("*")).agg(ma.lit(1).alias("one"))
    with pytest.raises(IncompleteProjectionSchemaError):
        infer_schema(q._node)
    assert q.columns == ["x", "y", "one"]
    assert q.to_dicts() == [{"x": 1, "y": 2, "one": 1}]
    # Scalar names need no claim about the subset DISTINCT's complete shape.
    assert base.group_by("x").agg(ma.lit(1).alias("one")).columns == ["x", "one"]


@pytest.mark.parametrize("backend_name", [
    "polars", "narwhals-polars", "narwhals-pandas", "narwhals-pyarrow",
    "ibis-duckdb", "ibis-sqlite",
])
@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("name", ["index", "ordinal"])
def test_row_index_native_schema(backend_factory, backend_name, empty, name):
    """Ordinal metadata must describe native type/placement, including empty sources."""
    import numpy as np

    data = {"value": np.array([] if empty else [8, 3], dtype=np.int64)}
    if backend_name == "narwhals-pyarrow":
        import narwhals as nw
        import pyarrow as pa

        source = nw.from_native(pa.table(data))
    else:
        source = backend_factory.create(data, backend_name)
    rel = ma.relation(source).with_row_index(**({} if name == "index" else {"name": name}))
    dtype = D.U64 if pl.get_index_type() == pl.UInt64 else D.U32
    if backend_name not in {"polars", "narwhals-polars"}:
        dtype = D.I64
    expected = [("value", D.I64), (name, dtype)] if backend_name.startswith("ibis") else [
        (name, dtype), ("value", D.I64),
    ]
    assert list(rel.schema.items()) == expected
    result = rel.to_polars()
    assert result.columns == [field for field, _ in expected]
    assert sorted(result[name].to_list()) == list(range(0 if empty else 2))
    assert rel.select(name).schema == {name: dtype}


@pytest.mark.parametrize("input_schema", [{}, {"value": D.I64}, {"ordinal": D.STRING}])
def test_row_index_unknown_route_preserves_partial_evidence(input_schema):
    """Unbound refs expose the ordinal without inventing native metadata or mutating input."""
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    rel = Relation(RefRelNode(name="source")).with_row_index(name="ordinal")
    assert rel.schema == {"ordinal": SchemaTypeStatus.UNKNOWN}
    original = dict(input_schema)
    assert infer_schema(rel._node, lambda _: input_schema) == {
        **input_schema, "ordinal": SchemaTypeStatus.UNKNOWN,
    }
    assert input_schema == original


def test_row_index_unbound_ibis_has_known_metadata():
    """A connection is unnecessary to describe Ibis's native ordinal."""
    import ibis

    rel = ma.relation(ibis.table({"value": "int64"}, name="source")).with_row_index(name="ordinal")
    assert list(rel.schema.items()) == [("value", D.I64), ("ordinal", D.I64)]


@pytest.mark.parametrize("execute_on", ["left", "right"])
def test_row_index_follows_selected_join_location(backend_factory, execute_on):
    """Indexing after a mixed join follows its target, not the first source."""
    left = ma.relation(pl.DataFrame({"value": [8, 3]}))
    right = ma.relation(backend_factory.create({"value": [8, 3]}, "ibis-duckdb"))
    rel = left.join(right, on="value", execute_on=execute_on).with_row_index(name="ordinal")
    dtype = D.U64 if pl.get_index_type() == pl.UInt64 else D.U32
    expected = [("ordinal", dtype), ("value", D.I64)] if execute_on == "left" else [
        ("value", D.I64), ("ordinal", D.I64),
    ]
    assert list(rel.schema) == [name for name, _ in expected]
    assert rel.schema["ordinal"] is dict(expected)["ordinal"]
    assert rel.to_polars().columns == [name for name, _ in expected]
@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("reshape", [False, True])
def test_whole_row_distinct_schema_matches_execution(backend_factory, backend_name, empty, reshape):
    """Keyless DISTINCT must not discard known fields, even on empty inputs."""
    data = pl.DataFrame(
        {"request_id": [1, 1, 2], "amount": [5, 5, None]},
        schema={"request_id": pl.Int64, "amount": pl.Int64},
    )
    if empty:
        data = data.clear()
    rel = ma.relation(backend_factory.create(data, backend_name))
    names = ["request_id", "amount"]
    rows = [(1, 5), (2, None)]
    if reshape:
        rel = rel.rename({"amount": "value"}).select("value", "request_id")
        names = ["value", "request_id"]
        rows = [(5, 1), (None, 2)]
    distinct = rel.unique()
    assert list(distinct.schema.items()) == [(name, D.I64) for name in names]
    assert distinct.columns == names
    assert distinct.dtypes == [D.I64, D.I64]
    assert distinct.width == 2
    result = distinct.to_polars()
    assert result.columns == names
    from collections import Counter
    assert Counter(result.rows()) == Counter([] if empty else rows)


@pytest.mark.parametrize("backend_name", ["polars", "narwhals-polars", "ibis-duckdb"])
def test_whole_row_distinct_join_preserves_identity(backend_factory, backend_name):
    """Schema and execution preserve request identity and payload multiplicity."""
    left, right = backend_factory.create_pair(
        pl.DataFrame(
            {"request_id": [1, 1, 2], "amount": [5, 5, None]},
            schema={"request_id": pl.Int64, "amount": pl.Int64},
        ),
        {"request_id": [1, 1, 2], "slot": [7, 7, 8]},
        backend_name,
    )
    joined = ma.relation(left).unique().join(ma.relation(right), on="request_id")
    assert list(joined.schema.items()) == [
        ("request_id", D.I64), ("amount", D.I64), ("slot", D.I64),
    ]
    result = joined.to_polars()
    assert result.columns == ["request_id", "amount", "slot"]
    from collections import Counter
    assert Counter(result.rows()) == Counter([(1, 5, 7), (1, 5, 7), (2, None, 8)])


def test_whole_row_distinct_preserves_partial_type_evidence():
    """DISTINCT cannot erase known names just because their types are unknown."""
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import RefRelNode

    rel = Relation(RefRelNode(name="source")).unique()
    assert infer_schema(rel._node, lambda _: {
        "known": D.I64, "unknown": SchemaTypeStatus.UNKNOWN,
        "unconstrained": SchemaTypeStatus.UNCONSTRAINED,
    }) == {
        "known": D.I64, "unknown": SchemaTypeStatus.UNKNOWN,
        "unconstrained": SchemaTypeStatus.UNCONSTRAINED,
    }


@pytest.mark.cross_backend
def test_registered_relation_system_describes_each_native_source(backend_name, backend_factory):
    """The selected system, not a generic ladder, reports a native source's output."""
    from mountainash.relations.core.execution.location import IdentityTokens, LocationResolver
    from mountainash.relations.core.relation_nodes import ReadRelNode
    from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system

    frame = backend_factory.create({"n": [1], "text": ["a"]}, backend_name)
    location = LocationResolver(IdentityTokens()).resolve(ReadRelNode(dataframe=frame))
    system = get_relation_system(location.family)(dialect=location.dialect)

    described = system.describe_output_schema(frame, location=location)

    assert list(described.items()) == list(_native_source_schema(frame, backend_name).items())
    assert ma.relation(frame).schema == described
