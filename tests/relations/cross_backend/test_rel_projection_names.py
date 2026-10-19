"""Public projection naming contracts, independent of native generated names."""

import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS


@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize("selector,selected", [("*", ["n", "m"]), ("^n$", ["n"]), ("^absent$", [])])
def test_string_selector_schema_matches_supported_execution(operation, selector, selected):
    """Polars string-selector lowering, not a new portable selector API."""
    relation = getattr(ma.relation(pl.DataFrame({"n": [2, 3], "m": [4, 5]})), operation)(selector)
    expected = ["n", "m"] if operation == "with_columns" else selected
    assert relation.columns == expected
    assert relation.to_polars().columns == expected


@pytest.mark.parametrize("operation", ["select", "with_columns"])
@pytest.mark.parametrize("selector", ["^n$", "^absent$"])
@pytest.mark.parametrize("compose,values", [
    (lambda e: e, [True, False]),
    (lambda e: e.fill_null(False), [True, False]),
    (lambda e: ~e, [False, True]),
])
def test_computed_selector_membership_does_not_promise_unenforced_names(operation, selector, compose, values):
    """Polars expansion keeps native lowering; no generated scalar alias is safe."""
    relation = getattr(ma.relation(pl.DataFrame({"n": [2, 3]})), operation)(
        compose(ma.col(selector).is_in([2]))
    )
    if selector == "^absent$":
        expected = {"n": [2, 3]} if operation == "with_columns" else {}
        assert relation.columns == list(expected)
        assert relation.to_dict() == expected
        return
    result = relation.to_dict()
    assert result["literal"] == values
    if operation == "with_columns":
        assert result["n"] == [2, 3]


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
def test_projection_contract(backend_name, backend_factory, operation, case, factory, name, values):
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
def test_native_passthrough_preserves_execution_values(backend_name, backend_factory, operation, aliased):
    source = backend_factory.create({"n": [None, 2]}, backend_name)
    native = ma.col("n").fill_null(0).compile(source)
    if aliased and backend_name.startswith("ibis-"):
        # compile() returns Deferred; ma.native accepts concrete Ibis values.
        native = native.resolve(source)
    expression = ma.native(native).alias("x") if aliased else native
    rel = getattr(ma.relation(source), operation)(expression)
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
    rel = ma.relation(pl.DataFrame({"n": [1, 2], "m": [3, 4]})).select(factory())
    assert rel.to_dict() == expected


def test_polars_native_multi_output_alias_keeps_native_validation():
    """Opaque Polars escape cardinality, not a backend-independent selector API."""
    rel = ma.relation(pl.DataFrame({"n": [1], "m": [2]})).select(ma.native(pl.all()).alias("x"))
    with pytest.raises(pl.exceptions.DuplicateError):
        rel.to_polars()


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
@pytest.mark.parametrize("rows", [0, 3])
def test_scalar_only_projection_preserves_source_cardinality(backend_name, backend_factory, rows):
    from mountainash.core.dtypes import TimestampDtype

    source = backend_factory.create({"n": [1, 2, 3]}, backend_name)
    result = ma.relation(source).head(rows).select(
        ma.lit(7).alias("n"),
        (ma.lit(2) + ma.lit(3)).alias("computed"),
        ma.lit("4").cast("int16").alias("cast"),
        ma.lit(None, dtype=TimestampDtype(6, True, "UTC")).alias("at"),
    ).to_polars()
    assert result.to_dict(as_series=False) == {
        "n": [7] * rows, "computed": [5] * rows,
        "cast": [4] * rows, "at": [None] * rows,
    }
    assert result.schema["at"] == pl.Datetime("us", "UTC")


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_scalar_alignment_does_not_change_aggregate_projection(backend_name, backend_factory):
    source = backend_factory.create({"n": [1, 2, 3]}, backend_name)
    result = ma.relation(source).select(
        ma.lit(7).alias("constant"), ma.col("n").sum().alias("total"),
    ).to_polars()
    # Ibis projects a windowed aggregate; Polars/Narwhals select a reduction.
    rows = 3 if backend_name.startswith("ibis-") else 1
    assert result.to_dict(as_series=False) == {"constant": [7] * rows, "total": [6] * rows}


@pytest.mark.parametrize("rows", [0, 3])
def test_native_scalar_expansion_preserves_cardinality_and_names(rows):
    """Polars-native multi-output escape retains every expanded scalar field."""
    source = pl.DataFrame({"n": range(rows)})
    result = ma.relation(source).select(
        ma.native(pl.lit({"a": 3, "b": 4}).struct.unnest()),
    ).to_polars()
    assert result.to_dict(as_series=False) == {"a": [3] * rows, "b": [4] * rows}


def test_scalar_projection_of_zero_column_native_frame_has_zero_rows():
    """Polars cannot retain height when a native frame has no columns."""
    source = pl.DataFrame().clear(3).lazy()
    result = ma.relation(source).select(ma.lit(7).alias("value")).to_polars()
    assert result["value"].to_list() == []

def test_zero_argument_native_aggregate_is_not_broadcast():
    source = pl.DataFrame({"n": [1, 2, 3]})
    result = ma.relation(source).select(ma.native(pl.len()).alias("count")).to_polars()
    assert result.to_dict(as_series=False) == {"count": [3]}

def test_native_aggregate_arithmetic_and_expansion_are_not_broadcast():
    source = pl.DataFrame({"n": [1, 2, 3]})
    result = ma.relation(source).select(
        ma.native((pl.len() + 1).alias("count")),
        ma.native(
            pl.struct(
                pl.lit(7).alias("constant"),
                (pl.len() + 1).alias("expanded_count"),
            ).struct.unnest()
        ),
    ).to_polars()
    assert result.to_dict(as_series=False) == {
        "count": [4], "constant": [7], "expanded_count": [4],
    }
