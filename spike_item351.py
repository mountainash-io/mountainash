"""Disposable item-351 evidence runner; not a permanent test suite."""
import json
from collections import Counter
from decimal import Decimal

import ibis
import narwhals as nw
import polars as pl
import mountainash as ma
from mountainash.core.types import BackendCapabilityError

reports = []

def receipt(kind, **values):
    reports.append(dict(kind=kind, **values))


def local_sampling():
    frames = {
        "ordinary": pl.DataFrame({"id": [1, 2, 3, 4], "paired": [10, 20, 30, 40]}),
        "nested": pl.DataFrame({"id": [1, 2, 3, 4], "paired": [[10], [], None, [40, None]]}),
        "decimal": pl.DataFrame({"id": [1, 2, 3, 4], "paired": [Decimal("1.10"), None, Decimal("3.30"), Decimal("4.40")]}),
        "object": pl.DataFrame({"id": [1, 2, 3, 4]}).with_columns(pl.Series("paired", [object(), None, object(), object()], dtype=pl.Object)),
    }
    options = [{"n": n} for n in (0, 2, 10)] + [{"fraction": f} for f in (0.0, 0.5, 1.0)]
    for provider in ("polars", "narwhals-lazy"):
        for dtype, original in frames.items():
            for empty in (False, True):
                frame = original.clear() if empty else original
                for opts in options:
                    for seed in (None, 42):
                        batches = []
                        def observe(batch):
                            batches.append(batch.height)
                            return batch
                        source = frame.lazy().map_batches(observe, schema=frame.schema,
                            predicate_pushdown=False, projection_pushdown=False, slice_pushdown=False)
                        native = nw.from_native(source) if provider == "narwhals-lazy" else source
                        sample = ma.relation(native).sample(**opts, seed=seed)
                        query = sample.select("id", "paired").filter(ma.col("id") > 1)
                        assert not batches
                        query.schema
                        query.explain()
                        compiled = query.compile()
                        assert not batches, (provider, dtype, opts, batches)
                        out = query.collect()
                        assert isinstance(out, pl.DataFrame)
                        assert out.schema == frame.schema
                        if frame.height and (opts.get("n", 0) > 0 or opts.get("fraction", 0) > 0):
                            assert batches, (provider, dtype, opts, "source did not run")
                        assert all(i > 1 for i in out["id"])
                        assert len(set(out["id"])) == out.height
                        values = dict(frame.iter_rows())
                        for i, value in out.iter_rows():
                            assert value is values[i] if dtype == "object" else value == values[i]
                        unfiltered = sample.to_polars()
                        expected_count = min(opts["n"], frame.height) if "n" in opts else int(opts["fraction"] * frame.height)
                        assert unfiltered.height == expected_count
                        if seed is not None:
                            expected = unfiltered.filter(pl.col("id") > 1)
                            assert out.to_dicts() == expected.to_dicts()
                            again = compiled.collect()
                            if isinstance(again, nw.DataFrame):
                                again = nw.to_native(again)
                            assert again["id"].to_list() == expected["id"].to_list()
                        receipt("local", provider=provider, dtype=dtype, empty=empty, options=opts, seed=seed)
        batches = []
        def observe_shared(batch):
            batches.append(batch.height)
            return batch
        source = frames["ordinary"].lazy().map_batches(observe_shared, schema=frames["ordinary"].schema,
            predicate_pushdown=False, projection_pushdown=False, slice_pushdown=False)
        native = nw.from_native(source) if provider == "narwhals-lazy" else source
        shared = ma.relation(native).sample(n=2, seed=42)
        query = ma.concat([shared, shared.select("id", "paired")])
        plan = query.compile()
        assert not batches
        out = query.to_polars()
        expected = shared.to_polars()
        assert out.to_dicts() == pl.concat([expected, expected]).to_dicts()
        receipt("shared", provider=provider, batches=batches, rows=out.to_dicts())


def sql_sampling_and_tail():
    for dialect in ("duckdb", "sqlite"):
        backend = getattr(ibis, dialect).connect()
        table = backend.create_table("spike_source", {"id": [1, 2, 3, 4], "paired": [10, 20, 30, 40]}, temp=True)
        reads = []
        def witness(value):
            reads.append(value)
            return value
        if dialect == "duckdb":
            backend.con.create_function("spike_witness", witness, ["BIGINT"], "BIGINT", side_effects=True)
            backend.raw_sql("CREATE TEMP VIEW spike_observed AS SELECT spike_witness(id) AS id, paired FROM spike_source")
            table = backend.table("spike_observed")
        else:
            def trace(sql):
                if sql.lstrip().upper().startswith("SELECT") and "spike_source" in sql:
                    reads.append(sql)
            backend.con.set_trace_callback(trace)
        for empty in (False, True):
            source = ma.relation(table)
            if empty:
                source = source.filter(ma.col("paired") < 0)
            for n in (0, 2, 10):
                for operation in ("sample", "tail"):
                    reads.clear()
                    query = source.sample(n=n) if operation == "sample" else source.sort("id").tail(n)
                    query.schema
                    query.explain()
                    query.compile()
                    assert not reads, (dialect, operation, "early execution", reads)
                    rows = query.to_dicts()
                    assert len(rows) == (0 if empty else min(n, 4)), (dialect, operation, n, rows)
                    assert len({r["id"] for r in rows}) == len(rows)
                    assert all(r["paired"] == r["id"] * 10 for r in rows)
                    if operation == "tail":
                        expected = [] if empty or not n else [{"id": i, "paired": i * 10} for i in range(1, 5)][-n:]
                        assert rows == expected, (dialect, n, rows)
                    if rows:
                        assert reads
                    receipt("sql", dialect=dialect, operation=operation, empty=empty, n=n, reads=len(reads), rows=rows)
        for seed in (0, 42):
            for n in (0, 2, 10):
                for terminal in ("compile", "to_dicts"):
                    reads.clear()
                    try:
                        getattr(ma.relation(table).sample(n=n, seed=seed), terminal)()
                    except BackendCapabilityError as error:
                        assert "exact-count sampling with a seed is unsupported" in str(error)
                        assert error.limitation is not None
                    else:
                        raise AssertionError((dialect, seed, n, "seeded count accepted"))
                    assert not reads
                    receipt("refusal", dialect=dialect, seed=seed, n=n, terminal=terminal)
        for fraction in (0.0, 0.5, 1.0):
            reads.clear()
            seed = 42 if dialect == "duckdb" else None
            query = ma.relation(table).sample(fraction=fraction, seed=seed)
            query.compile()
            assert not reads
            rows = query.to_dicts()
            assert all(r["paired"] == r["id"] * 10 for r in rows)
            if fraction in (0.0, 1.0):
                assert len(rows) == int(4 * fraction)
            receipt("fraction", dialect=dialect, fraction=fraction, seed=seed, rows=rows)
        shared = ma.relation(table).sample(n=2)
        reads.clear()
        query = ma.concat([shared, shared.select("id", "paired")])
        query.compile()
        assert not reads
        rows = query.to_dicts()
        assert len(rows) == 4 and all(r["paired"] == r["id"] * 10 for r in rows)
        receipt("sql_shared", dialect=dialect, rows=rows)
        backend.disconnect()


if __name__ == "__main__":
    local_sampling()
    sql_sampling_and_tail()
    print(json.dumps({"source": ma.__file__, "versions": {"polars": pl.__version__, "narwhals": nw.__version__, "ibis": ibis.__version__}, "counts": dict(Counter(r["kind"] for r in reports)), "receipts": reports}, indent=2))
