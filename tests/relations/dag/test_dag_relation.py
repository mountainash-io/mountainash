"""DAGRelation: type-preserving fluent terminals over a DAG. PR-2 §2.2/§2.4."""
from __future__ import annotations

import inspect

import polars as pl
import pytest

import mountainash as ma
from mountainash.relations.dag.dag import RelationDAG
from mountainash.relations.dag import DAGRelation


def _dag_with_source():
    dag = RelationDAG()
    df = pl.DataFrame({"x": [1, 2, 3, -1], "y": [4, 5, 6, 7]})
    raw = dag.source("raw", df)
    return dag, raw


def test_ref_and_source_return_dagrelation():
    dag, raw = _dag_with_source()
    assert isinstance(raw, DAGRelation)
    assert isinstance(dag.ref("raw"), DAGRelation)


def test_chaining_preserves_type():
    _, raw = _dag_with_source()
    chained = raw.filter(ma.col("x").gt(0)).sort("y").head(2)
    assert isinstance(chained, DAGRelation)
    grouped = raw.group_by("x").agg(ma.col("y").sum())
    assert isinstance(grouped, DAGRelation)


def test_namespace_builder_methods_preserve_type():
    # select/with_columns/drop/rename dispatch via __getattr__ ->
    # RelationProjectionBuilder._build (Task 1 fixed _build -> _make). Before
    # that fix these crashed (DAGRelation(node) missing dag) or dropped type.
    _, raw = _dag_with_source()
    assert isinstance(raw.select("x"), DAGRelation)
    assert isinstance(raw.with_columns(ma.col("x").alias("z")), DAGRelation)
    assert isinstance(raw.drop("y"), DAGRelation)
    assert isinstance(raw.rename({"x": "x2"}), DAGRelation)
    assert raw.select("x").filter(ma.col("x").gt(0)).count_rows() == 3


def test_fluent_terminal_end_to_end():
    _, raw = _dag_with_source()
    out = raw.filter(ma.col("x").gt(0)).sort("y").to_polars()
    assert out["x"].to_list() == [1, 2, 3]


def test_terminal_parity_with_registered_collect():
    dag, raw = _dag_with_source()
    fluent = raw.filter(ma.col("x").gt(0)).to_polars()
    dag.add("derived", dag.ref("raw").filter(ma.col("x").gt(0)))
    # RelationDAG.collect() returns the backend-native compiled value, not
    # forced eager — for Polars that is a LazyFrame (unlike
    # Relation.collect()/.to_polars(), which always materialize).
    registered = dag.collect("derived")
    if isinstance(registered, pl.LazyFrame):
        registered = registered.collect()
    assert fluent.sort("x").to_dicts() == registered.sort("x").to_dicts()


def test_scalar_terminal_over_ref_tree():
    _, raw = _dag_with_source()
    assert raw.filter(ma.col("x").gt(0)).count_rows() == 3
    assert raw.filter(ma.col("x").gt(0)).sum("x") == 6


def test_terminal_does_not_mutate_dag():
    dag, raw = _dag_with_source()
    before_relations = set(dag.relations)
    before_edges = set(dag.dependency_edges)
    raw.filter(ma.col("x").gt(0)).to_polars()
    assert set(dag.relations) == before_relations
    assert set(dag.dependency_edges) == before_edges


# --- Closed-by-default terminal sweep ---
TERMINAL_EXCEPTIONS = {
    "describe": "Polars-only, delegates to collect().describe()",
    "pipe": "takes an arbitrary user function, not a terminal",
    "explain": "returns backend plan string; covered separately",
    "compile": "returns unexecuted native plan; covered separately",
    "collect_with_drift": "shares _compile_and_execute_with_visitor with collect(), already exercised",
}
TERMINAL_SMOKE_ARGS = {
    "item": (("x",), {}),
    "sum": (("x",), {}),
    "avg": (("x",), {}),
    "mean": (("x",), {}),
    "min": (("x",), {}),
    "max": (("x",), {}),
    "product": (("x",), {}),
    "std_dev": (("x",), {}),
    "variance": (("x",), {}),
    "any_value": (("x",), {}),
    "to_dataclasses": None,
    "to_pydantic": None,
    "to_index_of_dicts": (("x",), {}),
    "to_index_of_tuples": (("x",), {}),
    "to_index_of_named_tuples": (("x",), {}),
    "to_index_of_typed_named_tuples": (("x",), {}),
}
_ARG_EXEMPT = {
    "to_dataclasses": "requires a user dataclass target",
    "to_pydantic": "requires a user Pydantic model target",
}


def _terminal_names() -> list[str]:
    from mountainash.relations.core.relation_api.relation import Relation

    names = []
    for name, member in inspect.getmembers(Relation, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        ann = inspect.signature(member).return_annotation
        if ann in ("Relation", "GroupedRelation", Relation):
            continue
        names.append(name)
    return names


# --- Schema-family property sweep (Task 4) ---

# Properties that resolve over a ref tree via the DAG. Each must be
# non-degenerate on a DAGRelation over dag.ref("raw"). Anything ref-independent
# goes in the exception set WITH A REASON.
_SCHEMA_FAMILY = {
    "schema": lambda v: set(v.keys()) == {"x", "y"},
    "columns": lambda v: set(v) == {"x", "y"},
    "dtypes": lambda v: len(list(v)) == 2,
    "width": lambda v: v == 2,
    "output_schema": lambda v: v is not None,
}


@pytest.mark.parametrize("prop", sorted(_SCHEMA_FAMILY))
def test_schema_family_resolves_over_ref(prop):
    _, raw = _dag_with_source()
    # source has columns x,y (see _dag_with_source); a filter keeps the schema.
    rel = raw.filter(ma.col("x").gt(0))
    value = getattr(rel, prop)
    assert _SCHEMA_FAMILY[prop](value), (
        f"schema-family property {prop!r} did not resolve over the ref tree: {value!r}"
    )


@pytest.mark.parametrize("term", _terminal_names())
def test_terminal_sweep_dag_aware(term):
    """Every discovered terminal is DAG-aware on a DAGRelation over a ref tree:
    it does not raise RelationDAGRequired."""
    from mountainash.relations.dag.errors import RelationDAGRequired

    if term in TERMINAL_EXCEPTIONS or term in _ARG_EXEMPT:
        pytest.skip(f"{term}: {TERMINAL_EXCEPTIONS.get(term) or _ARG_EXEMPT[term]}")

    _, raw = _dag_with_source()
    rel = raw.filter(ma.col("x").gt(0))
    fn = getattr(rel, term)

    if term in TERMINAL_SMOKE_ARGS and TERMINAL_SMOKE_ARGS[term] is not None:
        args, kwargs = TERMINAL_SMOKE_ARGS[term]
    else:
        args, kwargs = (), {}
    sig = inspect.signature(fn)
    required = [
        p for p in sig.parameters.values()
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    if required and term not in TERMINAL_SMOKE_ARGS:
        pytest.fail(
            f"terminal {term!r} needs args but has no smoke-arg entry or "
            f"exemption — add one so the sweep stays closed"
        )
    try:
        fn(*args, **kwargs)
    except RelationDAGRequired as e:
        pytest.fail(f"terminal {term!r} raised RelationDAGRequired on a DAGRelation: {e}")
