"""Public projection naming contracts, independent of native generated names."""

import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_implicit_fill_controls_rules_status(backend_name, backend_factory):
    source = backend_factory.create({"id": [1, 2], "n": [None, 2]}, backend_name)
    rel = ma.relation(source).with_columns(ma.col("n").fill_null(0))
    rel = rel.with_columns(
        ma.when(ma.col("n") == 0).then(ma.lit("no_match")).otherwise(ma.lit("resolved")).alias("status")
    ).sort("id")
    assert rel.columns == ["id", "n", "status"]
    assert rel.to_dicts() == [
        {"id": 1, "n": 0, "status": "no_match"},
        {"id": 2, "n": 2, "status": "resolved"},
    ]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize(
    "case,factory,name,values",
    [
        ("arithmetic", lambda: ma.col("n") + 1, "n", [2, 3]),
        ("two-columns", lambda: ma.col("n") + ma.col("m"), "n", [4, 6]),
        ("literal-first", lambda: ma.lit(1) + ma.col("n"), "literal", [2, 3]),
        ("nested-alias", lambda: ma.col("n").alias("z").fill_null(0), "z", [1, 2]),
        ("suffix", lambda: ma.col("n").fill_null(0).name.suffix("_f"), "n_f", [1, 2]),
        ("outer-alias", lambda: ma.col("n").name.suffix("_f").alias("z"), "z", [1, 2]),
        ("conditional", lambda: ma.when(ma.col("n") > 1).then(ma.col("m")).otherwise(ma.col("n")), "m", [1, 4]),
        ("membership", lambda: ma.col("n").is_in([2]), "n", [False, True]),
        ("cast", lambda: ma.col("n").cast("int64"), "n", [1, 2]),
        ("window", lambda: ma.col("n").sum().over("g"), "n", [3, 3]),
        ("raw-node", lambda: (ma.col("n") + 1)._node, "n", [2, 3]),
    ],
)
def test_projection_contract(backend_name, backend_factory, operation, case, factory, name, values, request):
    if backend_name == "ibis-polars" and case == "window":
        from ibis.common.exceptions import OperationNotDefinedError

        request.node.add_marker(
            pytest.mark.xfail(
                strict=True,
                raises=OperationNotDefinedError,
                reason="IB-WIN-01: Ibis-Polars has no WindowFunction translation",
            )
        )
    data = {"n": [1, 2], "m": [3, 4], "g": ["a", "a"]}
    source = backend_factory.create(data, backend_name)
    rel = getattr(ma.relation(source), operation)(factory())
    expected = dict(data) if operation == "with_columns" else {}
    expected[name] = values
    result = rel.to_polars()
    assert rel.columns == list(expected) == result.columns
    assert result.to_dict(as_series=False) == expected


@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize(
    "factory,name",
    [
        (lambda: (ma.col("n") + 1, ma.col("n").alias("n")), "n"),
        (lambda: (ma.col("n").alias("x"), ma.lit(1).alias("x")), "x"),
        (lambda: (ma.col("n") + 1, ma.col("n") * 2), "n"),
        (lambda: (ma.col("n").alias(""), ma.lit(1).alias("")), ""),
    ],
)
def test_duplicate_names_fail_during_build(operation, factory, name):
    # No data conversion/schema discovery is needed to reject these collisions.
    rel = ma.relation([{"n": 1}])
    with pytest.raises(ValueError, match=f"PROJECT_{operation.upper()}.*expression 1.*duplicate.*{name!r}"):
        getattr(rel, operation)(*factory())


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_literal_and_explicit_replacements_append_in_order(backend_name, backend_factory):
    source = backend_factory.create({"n": [1, 2]}, backend_name)
    rel = ma.relation(source).with_columns(ma.lit(7), (ma.col("n") + 2).alias("n"), ma.col("n").alias("copy"))
    assert rel.columns == ["n", "literal", "copy"]
    assert rel.to_dict() == {"n": [3, 4], "literal": [7, 7], "copy": [1, 2]}


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize("aliased", [False, True])
def test_native_passthrough_has_incomplete_ast_schema(backend_name, backend_factory, operation, aliased):
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    source = backend_factory.create({"n": [None, 2]}, backend_name)
    native = ma.col("n").fill_null(0).compile(source)
    if aliased and backend_name.startswith("ibis-"):
        # compile() returns Deferred; ma.native accepts concrete Ibis values.
        native = native.resolve(source)
    expression = ma.native(native).alias("x") if aliased else native
    rel = getattr(ma.relation(source), operation)(expression)
    with pytest.raises(IncompleteProjectionSchemaError, match="expression 0"):
        _ = rel.columns
    result = rel.to_dict()
    if aliased:
        assert result["x"] == [0, 2]
    else:
        assert [0, 2] in result.values()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_expression_reuse_preserves_standalone_name(backend_name, backend_factory):
    source = backend_factory.create({"n": [1, 2]}, backend_name)
    expression = ma.col("n") + 1
    first = ma.relation(source).select(expression)
    second = ma.relation(source).select(expression.alias("second"))
    assert first.to_dict() == {"n": [2, 3]}
    assert second.to_dict() == {"second": [2, 3]}
    standalone = source.select(expression.compile(source))
    if backend_name.startswith("ibis-"):
        assert list(standalone.columns) == ["Add(n, 1)"]
    else:
        assert standalone.collect_schema().names() == ["n"]


@pytest.mark.parametrize(
    "factory,expected",
    [
        (lambda: ma.native(pl.all()), {"n": [1, 2], "m": [3, 4]}),
        (lambda: ma.native(pl.col("^absent$")).alias("x"), {}),
        (lambda: ma.col("n") + ma.native(pl.col("^absent$")), {}),
        (lambda: ma.when(ma.native(pl.col("^absent$")) > 0).then(ma.col("n")).otherwise(ma.col("m")), {}),
        (lambda: ma.when(ma.col("n") > 0).then(ma.col("m")).otherwise(ma.native(pl.col("^absent$"))), {}),
        (lambda: ma.native(pl.col("^absent$")).cast("int64"), {}),
    ],
)
def test_polars_native_selector_escape(factory, expected):
    """Opaque Polars escape cardinality, not a backend-independent selector API."""
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    rel = ma.relation(pl.DataFrame({"n": [1, 2], "m": [3, 4]})).select(factory())
    with pytest.raises(IncompleteProjectionSchemaError):
        _ = rel.columns
    assert rel.to_dict() == expected


def test_polars_native_multi_output_alias_keeps_native_validation():
    """Opaque Polars escape cardinality, not a backend-independent selector API."""
    from mountainash.relations.core.projection_names import IncompleteProjectionSchemaError

    rel = ma.relation(pl.DataFrame({"n": [1], "m": [2]})).select(ma.native(pl.all()).alias("x"))
    with pytest.raises(IncompleteProjectionSchemaError):
        _ = rel.columns
    with pytest.raises(pl.exceptions.DuplicateError):
        rel.to_polars()
