"""Opt-in, fresh-process qualification of the public fingerprint terminal.

Run with the candidate package installed, or PYTHONPATH=src during development.
Fixture generation is excluded from elapsed time; RSS includes process/setup cost.
"""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
from pathlib import Path
import resource
import tempfile
import time

import polars as pl

import mountainash as ma


def rss_mib():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument("--source", choices=["polars", "duckdb", "postgres"], default="polars")
    parser.add_argument("--columns", choices=["narrow", "wide"], default="narrow")
    parser.add_argument("--slice", choices=["full", "group", "small"], default="full")
    parser.add_argument("--index", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile-vectors", action="store_true")
    args = parser.parse_args()
    if args.source == "postgres" or args.index:
        parser.error("PostgreSQL qualification is deferred: reader lifecycle defects (backlog 265)")
    if args.rows <= 0 or args.batch_size <= 0:
        parser.error("rows and batch-size must be positive")
    if args.profile_vectors:
        if pl.__version__ != "1.44.2":
            parser.error(f"literal vectors require Polars 1.44.2; runtime is {pl.__version__}")
        vector = ma.relation(pl.DataFrame({
            "a": [1, 1, 2, 2], "b": [3, 4, 3, 4],
            "value": [float("nan"), -0.0, None, 1.125], "__keys__": ["x", "y", "z", "w"],
        })).fingerprint(keys=["a", "b"], columns=["value", "__keys__", "a"])
        assert vector["fingerprint"].to_list() == [
            "8dc86337a737c1051cfc8906f447c84c", "00cbe0baedec050e4920ac1876cd41db",
            "7ef7be7ad251acaeb076c698878801a7", "c0904800b1d12061027d79877a1a7484",
        ]
    columns = ["value"] if args.columns == "narrow" else ["value", "score", "text", "flag", "nullable", "payload"]
    keys = ["axis_a", "axis_b"]
    packages = {name: version(name) for name in ["mountainash", "polars", "pyarrow"]}
    con = None
    with tempfile.TemporaryDirectory(prefix="fingerprint-") as directory:
        try:
            if args.source == "polars":
                # Incremental fixture creation keeps setup independent of total rows.
                import pyarrow.parquet as pq
                path = Path(directory) / "source.parquet"
                writer = None
                try:
                    for start in range(0, args.rows, 100_000):
                        frame = pl.DataFrame({"i": pl.int_range(start, min(start + 100_000, args.rows), eager=True)}).select(
                            (pl.col("i") // 1000).alias("axis_a"), (pl.col("i") % 1000).alias("axis_b"),
                            (pl.col("i") % 100003).alias("value"), (pl.col("i") * 0.125).alias("score"),
                            (pl.col("i") % 97).cast(pl.String).alias("text"), (pl.col("i") % 2 == 0).alias("flag"),
                            pl.when(pl.col("i") % 29 != 0).then(pl.col("i") % 127).alias("nullable"),
                            pl.lit("x" * 128).alias("payload"),
                        )
                        table = frame.to_arrow()
                        if writer is None:
                            writer = pq.ParquetWriter(path, table.schema)
                        writer.write_table(table)
                    del frame, table
                finally:
                    if writer is not None:
                        writer.close()
                source = pl.scan_parquet(path)
            else:
                import ibis
                con = ibis.duckdb.connect()
                packages.update({name: version(name) for name in ["ibis-framework", "duckdb"]})
                source = con.sql(
                    "SELECT i // 1000 AS axis_a, i % 1000 AS axis_b, i % 100003 AS value, "
                    "i * 0.125::DOUBLE AS score, (i % 97)::VARCHAR AS text, i % 2 = 0 AS flag, "
                    "CASE WHEN i % 29 != 0 THEN i % 127 END AS nullable, repeat('x',128) AS payload "
                    f"FROM range({args.rows}) AS s(i)"
                )
            rel = ma.relation(source)
            expected = args.rows
            if args.slice != "full":
                rel = rel.filter(ma.col("axis_a") == 42)
                expected = max(0, min(1000, args.rows - 42000))
            if args.slice == "small":
                rel = rel.filter((ma.col("axis_b") >= 101) & (ma.col("axis_b") <= 110))
                expected = max(0, min(10, args.rows - 42101))
            plan = rel.select(*keys, *columns).compile()
            if con is None:
                explanation = plan.explain()
            else:
                sql = con.compile(plan)
                explanation = con.con.execute("EXPLAIN " + sql).fetchall()
            starting_peak = rss_mib()
            start = time.perf_counter()
            result = rel.fingerprint(keys=keys, columns=columns, batch_size=args.batch_size)
            elapsed = time.perf_counter() - start
            assert result["row_count"].to_list() == [expected] * (len(columns) + 1)
            assert result["key_schema"][0] == '[["axis_a",{"type":"Int64"}],["axis_b",{"type":"Int64"}]]'
            receipt = {
                "source": args.source, "rows": args.rows, "selected_rows": expected, "columns": columns,
                "batch_size": args.batch_size, "slice": args.slice, "elapsed_seconds": elapsed,
                "starting_peak_rss_mib": starting_peak, "peak_rss_mib": rss_mib(),
                "versions": packages, "plan": explanation, "result": result.to_dicts(),
            }
            text = json.dumps(receipt, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text + "\n")
            print(text)
        finally:
            if con is not None:
                con.disconnect()


if __name__ == "__main__":
    main()
