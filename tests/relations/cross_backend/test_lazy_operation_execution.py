"""Public lazy sampling: source execution, row fidelity and native composition."""

from decimal import Decimal

import narwhals as nw
import polars as pl
import pytest
from polars.io.plugins import register_io_source
from polars.testing import assert_frame_equal

import mountainash as ma


def _source(frame, reads, wrapped):
    def read_source(with_columns, predicate, n_rows, batch_size):
        reads.append(frame.height)
        result = frame
        if predicate is not None:
            result = result.filter(predicate)
        if with_columns is not None:
            result = result[with_columns]
        if n_rows is not None:
            result = result.head(n_rows)
        yield result

    source = register_io_source(
        read_source, schema=frame.schema, validate_schema=True, is_pure=False,
    )
    return nw.from_native(source) if wrapped else source


def _compile_without_reads(query, reads):
    query.schema
    query.collect_schema()
    query.explain()
    compiled = query.compile()
    assert reads == []
    return compiled


@pytest.mark.parametrize("wrapped", [False, True], ids=["polars", "narwhals-polars"])
@pytest.mark.parametrize("empty", [False, True])
@pytest.mark.parametrize("seed", [None, 42])
@pytest.mark.parametrize("options,want", [
    ({"n": 0}, 0), ({"n": 2}, 2), ({"n": 10}, 7),
    ({"n": 2**200}, 7),
    ({"fraction": 0.0}, 0), ({"fraction": 0.5}, 3), ({"fraction": 1.0}, 7),
])
def test_sample_defers_source_and_preserves_rows(wrapped, empty, seed, options, want):
    reads = []
    frame = pl.DataFrame({"id": list(range(7)), "paired": [i * 10 for i in range(7)]})
    if empty:
        frame = frame.clear()
        want = 0
    query = ma.relation(_source(frame, reads, wrapped)).sample(**options, seed=seed)
    compiled = _compile_without_reads(query, reads)
    out = query.to_polars()
    assert out.height == want
    assert out.schema == frame.schema
    assert out["id"].n_unique() == want
    assert all(row["paired"] == 10 * row["id"] for row in out.to_dicts())
    if want:
        assert reads
    reads.clear()
    again = compiled.collect()
    if isinstance(again, nw.DataFrame):
        again = again.to_native()
    assert again.height == want
    if want:
        assert reads  # Compilation must not freeze an eager result, even without a seed.
    if seed is not None:
        assert_frame_equal(again, out)


@pytest.mark.parametrize("wrapped", [False, True], ids=["polars", "narwhals-polars"])
@pytest.mark.parametrize("kind", ["literal_names", "nested", "decimal", "object", "temporal"])
def test_sampling_retains_physical_rows_and_literal_names(wrapped, kind):
    frame = pl.DataFrame({"id": [1, 2, 3, 4]})
    if kind == "literal_names":
        frame = frame.with_columns(
            pl.Series("*", [11, 12, 13, 14]),
            pl.Series("^id$", [21, 22, 23, 24]),
            pl.Series("_ma_sample_index", [31, 32, 33, 34]),
        )
    elif kind == "nested":
        frame = frame.with_columns(pl.Series("value", [[1, None], [], None, [4]]))
    elif kind == "decimal":
        frame = frame.with_columns(pl.Series("value", [Decimal("1.10"), None, Decimal("3.30"), Decimal("4.40")]))
    elif kind == "object":
        frame = frame.with_columns(pl.Series("value", [object(), None, object(), object()], dtype=pl.Object))
    else:
        frame = frame.with_columns(pl.Series("value", [1, None, 3, 4], dtype=pl.Datetime("ns", "Europe/London")))
    reads = []
    query = ma.relation(_source(frame, reads, wrapped)).sample(n=3, seed=0)
    _compile_without_reads(query, reads)
    out = query.to_polars()
    assert out.height == 3
    assert out["id"].n_unique() == 3
    assert out.schema == frame.schema
    expected = frame.filter(pl.col("id").is_in(out["id"].to_list())).sort("id")
    if kind == "object":
        expected_values = dict(expected.iter_rows())
        for identifier, value in out.iter_rows():
            assert value is expected_values[identifier]
    else:
        assert_frame_equal(out.sort("id"), expected)


@pytest.mark.parametrize("wrapped", [False, True], ids=["polars", "narwhals-polars"])
def test_seeded_sampling_composes_without_early_reads(wrapped):
    frame = pl.DataFrame({"id": list(range(7)), "paired": [i * 10 for i in range(7)]})
    reads = []
    sample = ma.relation(_source(frame, reads, wrapped)).sample(n=3, seed=42)
    branch = sample.select("id", "paired").filter(ma.col("id") > 2)
    shared = ma.concat([branch, branch])
    _compile_without_reads(shared, reads)
    out = shared.to_polars()
    assert reads
    selected = sample.to_polars().filter(pl.col("id") > 2)
    assert_frame_equal(out, pl.concat([selected, selected]))
    assert all(row["paired"] == row["id"] * 10 for row in out.to_dicts())


@pytest.mark.parametrize("wrapped", [False, True], ids=["polars", "narwhals-polars"])
def test_sampling_preserves_terminal_data_error(wrapped):
    source = pl.DataFrame({"id": ["bad"]}).lazy().with_columns(pl.col("id").cast(pl.Int64))
    query = ma.relation(nw.from_native(source) if wrapped else source).sample(n=1)
    query.compile()
    with pytest.raises((pl.exceptions.InvalidOperationError, nw.exceptions.InvalidOperationError)):
        query.to_polars()


@pytest.mark.parametrize("wrapped", [False, True], ids=["polars", "narwhals-polars"])
@pytest.mark.parametrize("sample", [False, True])
@pytest.mark.parametrize("seed", [None, 42])
def test_shared_deferred_source_retains_occurrence_transfers(wrapped, sample, seed):
    import ibis

    reads = []
    source = _source(pl.DataFrame({"id": [1], "paired": [10]}), reads, wrapped)
    branch = ma.relation(source)
    if sample:
        branch = branch.sample(n=1, seed=seed)
    branch = branch.select("id", "paired")
    stored = ma.relation(ibis.duckdb.connect().create_table("stored", {"id": [1]}))
    query = ma.concat([stored.join(branch, on="id")] * 4)
    for _ in range(2):
        reads.clear()
        assert query.to_dicts() == [{"id": 1, "paired": 10}] * 4
        assert len(reads) == 4


def test_shared_pivot_retains_input_materializations():
    reads = []
    source = _source(
        pl.DataFrame({"id": [1], "category": ["a"], "value": [10]}), reads, False,
    )
    branch = ma.relation(source).pivot(on="category", index=["id"], values="value")
    query = ma.concat([branch] * 4)
    assert query.to_dicts() == [{"id": 1, "a": 10}] * 4
    assert len(reads) == 4


def test_named_deferred_plan_does_not_freeze_parent_pivot():
    reads = []
    source = _source(
        pl.DataFrame({"id": [1], "category": ["a"], "value": [10]}), reads, False,
    )
    dag = ma.RelationDAG()
    dag.add("source", ma.relation(source))
    branch = dag.ref("source").pivot(on="category", index=["id"], values="value")
    assert ma.concat([branch] * 4).to_dicts() == [{"id": 1, "a": 10}] * 4
    assert len(reads) == 4
