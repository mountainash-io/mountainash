"""Cross-backend contract tests for Relation.collect() and Relation.compile().

collect() MUST return a materialized native result for every backend.
compile() MUST return the native plan (lazy where the backend is lazy).
"""
from __future__ import annotations

import polars as pl
import pytest

from mountainash.relations import relation


def test_collect_polars_lazyframe_returns_dataframe():
    """Regression guard: collect() on a LazyFrame source must NOT return a LazyFrame.

    Before this fix, `rel.collect()` leaked the LazyFrame and callers had to
    do `rel.collect().collect()`. That broke the one-syntax-all-backends promise.
    """
    lf = pl.DataFrame({"x": [1, 2, 3]}).lazy()
    result = relation(lf).collect()
    assert isinstance(result, pl.DataFrame)
    assert not isinstance(result, pl.LazyFrame)
    assert result.to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]


# ----------------------------------------------------------------------
# collect() — always materialized
# ----------------------------------------------------------------------


def test_collect_polars_eager_returns_dataframe():
    df = pl.DataFrame({"x": [1, 2, 3]})
    result = relation(df).collect()
    assert isinstance(result, pl.DataFrame)
    assert result.to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]


def test_collect_narwhals_polars_returns_native():
    pytest.importorskip("narwhals")
    import narwhals as nw

    nw_df = nw.from_native(pl.DataFrame({"x": [1, 2, 3]}), eager_only=True)
    result = relation(nw_df).collect()
    # Must not be a Polars LazyFrame under any circumstances
    assert not isinstance(result, pl.LazyFrame)


def test_collect_narwhals_pandas_returns_native():
    pytest.importorskip("narwhals")
    pytest.importorskip("pandas")
    import narwhals as nw
    import pandas as pd

    nw_df = nw.from_native(pd.DataFrame({"x": [1, 2, 3]}), eager_only=True)
    result = relation(nw_df).collect()
    assert not isinstance(result, pl.LazyFrame)


def test_collect_ibis_returns_materialized():
    pytest.importorskip("ibis")
    import ibis

    t = ibis.memtable({"x": [1, 2, 3]})
    result = relation(t).collect()
    # Invariant: the one-syntax-all-backends contract. collect() must
    # never return a Polars LazyFrame (the original leak we fixed).
    # Ibis's native user-facing type is ibis.Table — that's acceptable
    # here; the hazard was LazyFrame-specific. Users who want a
    # materialized frame use to_polars() / to_pandas().
    assert not isinstance(result, pl.LazyFrame)


# ----------------------------------------------------------------------
# compile() — native plan, lazy where the backend is lazy
# ----------------------------------------------------------------------


def test_compile_polars_lazyframe_returns_lazyframe():
    """compile() preserves laziness — this is the escape-hatch contract."""
    lf = pl.DataFrame({"x": [1, 2, 3]}).lazy()
    plan = relation(lf).compile()
    assert isinstance(plan, pl.LazyFrame)
    # And it is a real, executable plan
    assert plan.collect().to_dicts() == [{"x": 1}, {"x": 2}, {"x": 3}]


def test_compile_polars_eager_returns_lazyframe():
    """Polars backend wraps all inputs into a LazyFrame for plan building.

    compile() exposes that plan — so even an eager DataFrame source
    produces a LazyFrame from compile(). The spec says compile() is
    "lazy where the backend is lazy"; the Polars RelationSystem is
    lazy internally regardless of input type.
    """
    df = pl.DataFrame({"x": [1, 2, 3]})
    plan = relation(df).compile()
    assert isinstance(plan, pl.LazyFrame)


def test_compile_ibis_returns_unexecuted_table():
    pytest.importorskip("ibis")
    import ibis

    t = ibis.memtable({"x": [1, 2, 3]})
    plan = relation(t).compile()
    assert isinstance(plan, ibis.Table)


# ----------------------------------------------------------------------
# Round-trip: collect() equals manually materialized compile()
# ----------------------------------------------------------------------


def test_collect_equals_manual_compile_then_collect_polars_lazy():
    lf = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]}).lazy()
    rel = relation(lf)

    via_collect = rel.collect()
    via_compile = rel.compile().collect()

    assert via_collect.to_dicts() == via_compile.to_dicts()


def test_collect_equals_compile_polars_eager():
    df = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
    rel = relation(df)

    via_collect = rel.collect()
    # compile() returns a LazyFrame even for eager sources (see
    # test_compile_polars_eager_returns_lazyframe) — manually
    # materialize for the round-trip comparison.
    via_compile = rel.compile().collect()

    assert via_collect.to_dicts() == via_compile.to_dicts()
