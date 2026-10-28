# tests/pipelines/units/sinks/test_parquet_dir_sink.py
import pytest, polars as pl
from mountainash.pipelines.core.values import *
from mountainash.pipelines.units.sinks.base import WriteMode
from mountainash.pipelines.units.sinks.parquet_dir import ParquetDirectorySink
from mountainash.pipelines.errors import UnsupportedValueKind

def _ctx(): return RunContext({}, None, {}, "p", "k", "r")

@pytest.mark.cell("unit:ParquetDirectorySink")
@pytest.mark.cell("unit:SinkUnit")
@pytest.mark.cell("mode:ParquetDirectorySink:REPLACE_PARTITION")
def test_replace_partition_clears_empty_partition(tmp_path):            # Review Focus #4
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",))
    k.run({"s": Value.of(pl.DataFrame({"p": ["a", "b"], "v": [1, 2]}), Identity.of("i"), Coverage.source({"a", "b"}, {"a", "b"}, set()))}, _ctx())
    assert (tmp_path / "p=a").exists() and (tmp_path / "p=b").exists()
    k.run({"s": Value.of(pl.DataFrame({"p": ["a"], "v": [9]}), Identity.of("i"), Coverage.source({"a", "b"}, {"a", "b"}, set()))}, _ctx())
    assert not (tmp_path / "p=b").exists() and pl.read_parquet(tmp_path / "p=a" / "*.parquet")["v"].to_list() == [9]

@pytest.mark.cell("unit:ParquetDirectorySink")
@pytest.mark.cell("unit:SinkUnit")
@pytest.mark.cell("mode:ParquetDirectorySink:APPEND")
@pytest.mark.cell("mode:ParquetDirectorySink:REPLACE")
@pytest.mark.cell("mode:ParquetDirectorySink:UPSERT")
def test_append_replace_and_upsert_unsupported(tmp_path, backend_name, backend_df):
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.APPEND)
    k.run({"s": Value.of(backend_df, Identity.of("i"))}, _ctx()); k.run({"s": Value.of(backend_df, Identity.of("i"))}, _ctx())
    assert len(list(tmp_path.glob("*.parquet"))) == 2
    r = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE)
    r.run({"s": Value.of(backend_df, Identity.of("i"))}, _ctx())
    assert len(list(tmp_path.glob("*.parquet"))) == 1
    with pytest.raises(UnsupportedValueKind):                                     # before key validation (F23)
        ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.UPSERT)

@pytest.mark.cell("unit:ParquetDirectorySink")
@pytest.mark.cell("unit:SinkUnit")
@pytest.mark.cell("mode:ParquetDirectorySink:REPLACE_PARTITION")
def test_composite_partition_directories(tmp_path):                                # F18
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p", "q"))
    df = pl.DataFrame({"p": ["a", "a"], "q": ["x", "y"], "v": [1, 2]})
    k.run({"s": Value.of(df, Identity.of("i"), Coverage.source({("a", "x"), ("a", "y")}, {("a", "x"), ("a", "y")}, set()))}, _ctx())
    k.run({"s": Value.of(pl.DataFrame({"p": ["a"], "q": ["x"], "v": [9]}), Identity.of("i"), Coverage.source({("a", "x")}, {("a", "x")}, set()))}, _ctx())
    assert pl.read_parquet(tmp_path / "p=a" / "q=y" / "*.parquet")["v"].to_list() == [2] and pl.read_parquet(tmp_path / "p=a" / "q=x" / "*.parquet")["v"].to_list() == [9]

@pytest.mark.cell("unit:ParquetDirectorySink")
@pytest.mark.cell("unit:SinkUnit")
@pytest.mark.cell("mode:ParquetDirectorySink:REPLACE_PARTITION")
def test_partition_values_are_path_safe_and_distinct(tmp_path):
    root = tmp_path / "root"
    k = ParquetDirectorySink(root, name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",))
    vals = ["a", "a/b", "..", "../x", "__HIVE_DEFAULT_PARTITION__", None]
    df = pl.DataFrame({"p": vals, "v": list(range(len(vals)))})
    k.run({"s": Value.of(df, Identity.of("i"), Coverage.source(set(vals), set(vals), set()))}, _ctx())
    assert len({d.name for d in root.iterdir()}) == len(vals) and not (tmp_path / "x").exists()
    assert all(d.is_dir() and d.parent == root for d in root.iterdir())
    k.run({"s": Value.of(pl.DataFrame({"p": ["a"], "v": [99]}), Identity.of("i"), Coverage.source({"a", "a/b"}, {"a"}, {"a/b"}))}, _ctx())
    got = pl.read_parquet(root / "**" / "*.parquet", hive_partitioning=False).sort("v")["v"].to_list()
    assert got == [1, 2, 3, 4, 5, 99]      # 'a' replaced, failed 'a/b' (v=1) untouched

@pytest.mark.parametrize("composite", [False, True])
@pytest.mark.cell("unit:ParquetDirectorySink")
@pytest.mark.cell("unit:SinkUnit")
@pytest.mark.cell("mode:ParquetDirectorySink:REPLACE_PARTITION")
def test_replace_partition_matches_null_partition(tmp_path, composite):
    parts = ("p", "q") if composite else ("p",)
    part = (lambda p: (p, "x")) if composite else (lambda p: p)
    def df(*rows): return pl.DataFrame({"p": [r[0] for r in rows], "q": ["x"] * len(rows), "v": [r[1] for r in rows]}, schema={"p": pl.String, "q": pl.String, "v": pl.Int64})
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=parts)
    cov = Coverage.source({part(None)}, {part(None)}, set())
    k.run({"s": Value.of(df((None, 1)), Identity.of("i"), cov)}, _ctx())
    k.run({"s": Value.of(df((None, 2)), Identity.of("i"), cov)}, _ctx())
    assert sorted(pl.read_parquet(tmp_path / "**" / "*.parquet", hive_partitioning=False)["v"].to_list()) == [2]
    k.run({"s": Value.of(df(("a", 3)), Identity.of("i"), cov)}, _ctx())              # empty success clears the NULL partition
    assert not list(tmp_path.glob("**/*.parquet"))
