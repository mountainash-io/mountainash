"""Disposable public-API proof for the non-Polars Narwhals source bridge."""
import duckdb
import narwhals as nw
import mountainash as ma

connection = duckdb.connect()
reads = []

def witness(value):
    reads.append(value)
    return value

connection.create_function("witness", witness, ["BIGINT"], "BIGINT", side_effects=True)
source = nw.from_native(connection.sql(
    "SELECT witness(i) AS id, i * 10 AS paired FROM range(7) t(i)"
))
cases = 0
for empty in (False, True):
    for seed in (None, 0, 42):
        for options in ({"n": 0}, {"n": 2}, {"n": 10},
                        {"fraction": 0.0}, {"fraction": 0.5}, {"fraction": 1.0}):
            reads.clear()
            relation = ma.relation(source)
            if empty:
                relation = relation.filter(ma.col("paired") < 0)
            sampled = relation.sample(**options, seed=seed)
            wrapped = sampled.select("id", "paired").filter(ma.col("id") >= 0)
            wrapped.schema
            wrapped.explain()
            compiled = wrapped.compile()
            assert not reads, (empty, seed, options, reads)
            rows = wrapped.to_dicts()
            size = 0 if empty else 7
            expected_count = min(options["n"], size) if "n" in options else int(options["fraction"] * size)
            assert len(rows) == expected_count
            assert len({row["id"] for row in rows}) == expected_count
            assert all(row["paired"] == row["id"] * 10 for row in rows)
            if expected_count:
                assert reads
            if seed is not None:
                assert compiled.collect().to_native().to_dicts() == rows
            cases += 1

shared = ma.relation(source).sample(n=2, seed=42)
reads.clear()
query = ma.concat([shared, shared.select("id", "paired")])
query.compile()
assert not reads
rows = query.to_dicts()
assert rows[:2] == rows[2:]
assert len(rows) == 4
assert all(row["paired"] == row["id"] * 10 for row in rows)
print({"provider": "narwhals-duckdb", "cases": cases,
       "shared_composition": "passed", "phase_boundaries": "passed"})
connection.close()
