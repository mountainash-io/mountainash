"""DAGRelation schema-family + assess_drift resolve refs via the DAG. PR-2 §2.2."""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from fixtures.backend_registry import ALL_BACKENDS
from mountainash.relations.dag.dag import RelationDAG


def _dag():
    dag = RelationDAG()
    dag.add("raw", ma.relation(pl.DataFrame({"x": [1, 2], "y": ["a", "b"]})))
    return dag


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_implicit_projection_keeps_dag_terminal_routing(backend_name, backend_factory):
    dag = RelationDAG()
    dag.add("raw", ma.relation(backend_factory.create({"n": [None, 2]}, backend_name)))
    rel = dag.ref("raw").with_columns(ma.col("n").fill_null(0))
    assert rel.columns == ["n"]
    assert rel.to_dict() == {"n": [0, 2]}


@pytest.mark.cross_backend
def test_projection_schema_distinguishes_computation_through_ref(backend_name, backend_factory):
    from mountainash.core.dtypes import MountainashDtype as D

    dag = RelationDAG()
    dag.add("raw", ma.relation(backend_factory.create({"n": [1, 2]}, backend_name)))
    derived = dag.ref("raw").select((ma.col("n") > 1).alias("n"), ma.col("n").alias("copy"))
    dag.add("derived", derived)
    boolean_type = D.I64 if backend_name == "ibis-sqlite" else D.BOOL
    assert dag.schema("derived") == {"n": boolean_type, "copy": D.I64}
    assert derived.to_dict() == {"n": [False, True], "copy": [1, 2]}


def test_schema_resolves_over_ref_tree():
    dag = _dag()
    rel = dag.ref("raw").filter(ma.col("x").gt(0))
    # The owning DAG resolver binds the RefRelNode to its registered relation.
    schema = rel.schema
    assert set(schema.keys()) == {"x", "y"}
    assert set(rel.columns) == {"x", "y"}
    assert rel.width == 2
    assert list(rel.dtypes)  # non-empty, resolved
    assert rel.output_schema is not None


def test_plain_relation_still_degenerate_over_ref():
    # Contrast guard: a plain Relation wrapping the same RefRelNode still infers
    # empty (no resolver) — proves DAG ownership is part of the base resolver.
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        RefRelNode,
    )
    plain = Relation(RefRelNode(name="raw"))
    assert plain.schema == {}


def test_assess_drift_resolves_refs_without_compiling(monkeypatch):
    # assess_drift remains structural even though the regular schema property
    # compiles through the owning DAG.
    dag = _dag()
    spec = ma.TableSchema.from_simple_dict({"x": "integer", "y": "string"})
    rel = dag.ref("raw").conform(spec)

    def fail_compile(*args, **kwargs):
        raise AssertionError("assess_drift must not compile")

    monkeypatch.setattr(rel, "_compile_and_execute_with_visitor", fail_compile)
    assert isinstance(rel.assess_drift(), list)


def test_assess_drift_plain_relation_over_ref_is_degenerate():
    # Contrast: a plain Relation conform over a bare ref has no resolver, so its
    # assess_drift remains structural; the DAG-bound resolver is the
    # differentiator, while a plain Relation has no resolver.
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import (
        RefRelNode,
    )
    spec = ma.TableSchema.from_simple_dict({"x": "integer", "y": "string"})
    # fields_match must be "open" explicitly (the model default is now the
    # strict "exact", which would raise on the ref's empty inferred schema
    # instead of under-assessing). This test pins the resolver-less degenerate
    # path, not exact-mode column enforcement.
    spec.fields_match = "open"
    plain = Relation(RefRelNode(name="raw")).conform(spec)
    # Should not raise; returns a list (possibly under-assessed). This is the
    # baseline the DAGRelation override improves on.
    assert isinstance(plain.assess_drift(), list)


@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
def test_row_index_schema_resolves_dag_identity(backend_factory, backend_name, monkeypatch):
    """Refs retain native order without compiling or substituting dtype-map keys."""
    from mountainash.core.dtypes import MountainashDtype as D
    from mountainash.relations.core.execution.compilation import CompilationSession
    from mountainash.typespec import source_shape

    dag = RelationDAG()
    dag.add("raw", ma.relation(backend_factory.create({"value": [8, 3]}, backend_name)))
    indexed = dag.ref("raw").with_row_index(name="ordinal")
    dag.add("indexed", indexed)
    if backend_name == "narwhals-lazy":
        # Existing lazy row-index execution requires an order_by argument.
        with pytest.raises(TypeError):
            _ = indexed.columns
        with pytest.raises(TypeError):
            indexed.to_polars()
        return
    dtype = (
        D.U64 if pl.get_index_type() == pl.UInt64 else D.U32
    ) if backend_name in {"polars", "polars-lazy", "narwhals-polars"} else D.I64
    expected = [("value", D.I64), ("ordinal", dtype)] if backend_name.startswith("ibis-") else [
        ("ordinal", dtype), ("value", D.I64),
    ]
    combined = indexed.cross_join(dag.ref("raw").select(ma.col("value").alias("other")))
    names = ["value", "ordinal", "other"] if backend_name.startswith("ibis-") else [
        "ordinal", "value", "other",
    ]

    def forbidden(*args, **kwargs):
        raise AssertionError("proven DAG names must not compile or decode types")

    with monkeypatch.context() as guard:
        guard.setattr(CompilationSession, "compile_root", forbidden)
        guard.setattr(source_shape, "extract_source_shapes", forbidden)
        assert combined.columns == names
        assert combined.width == 3
    assert combined.to_polars().columns == names
    assert list(indexed.schema.items()) == expected
    assert list(dag.schema("indexed").items()) == expected
    projected = indexed.select("ordinal")
    assert projected.schema == {"ordinal": dtype}
    assert sorted(projected.to_polars()["ordinal"].to_list()) == [0, 1]


def test_constraint_cycle_does_not_recurse_or_collect_during_schema_inference(monkeypatch):
    from mountainash.core.dtypes import MountainashDtype as D

    dag = RelationDAG()
    dag.add("raw", ma.relation(pl.LazyFrame({"n": [1, 2]})))
    computed = dag.ref("raw").select(ma.col("n").add(1).alias("next"))
    dag.add("computed", computed)
    dag.constraint_edges.update({("raw", "computed"), ("computed", "raw")})

    collections = []
    transfers = []
    native_collect = pl.LazyFrame.collect
    native_to_arrow = pl.DataFrame.to_arrow

    def observe_collect(frame, *args, **kwargs):
        collections.append(True)
        return native_collect(frame, *args, **kwargs)

    def observe_transfer(frame, *args, **kwargs):
        transfers.append(True)
        return native_to_arrow(frame, *args, **kwargs)

    monkeypatch.setattr(pl.LazyFrame, "collect", observe_collect)
    monkeypatch.setattr(pl.DataFrame, "to_arrow", observe_transfer)

    assert computed.collect_schema() == {"next": D.I64}
    assert dag.schema("computed") == {"next": D.I64}
    assert not collections
    assert not transfers
    assert computed.columns == ["next"]


def test_dependency_cycle_retains_explicit_cycle_error_during_schema_inference():
    dag = RelationDAG()
    dag.add("a", dag.ref("b"))
    dag.add("b", dag.ref("a"))

    with pytest.raises(ValueError, match="[Cc]ycle detected"):
        dag.schema("a")
    for relation in (dag.ref("a"), dag.ref("a").select(ma.lit(1).alias("one"))):
        with pytest.raises(ValueError, match="[Cc]ycle detected"):
            _ = relation.columns


def test_missing_dag_binding_retains_explicit_error_during_schema_inference():
    dag = RelationDAG()
    missing = dag.ref("missing")

    with pytest.raises(KeyError, match="missing"):
        missing.collect_schema()
    for relation in (missing, missing.select(ma.lit(1).alias("one"))):
        with pytest.raises(KeyError, match="missing"):
            _ = relation.columns
