# tests/pipelines/units/sinks/test_parquet_dir_sink.py
import pytest, polars as pl
from mountainash.pipelines.core.values import *
from mountainash.pipelines.units.sinks.base import WriteMode
from mountainash.pipelines.units.sinks.parquet_dir import ParquetDirectorySink
from mountainash.pipelines.errors import UnsupportedValueKind

def _ctx(): return RunContext({}, None, {}, "p", "k", "r")

def test_replace_partition_clears_empty_partition(tmp_path):            # Review Focus #4
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p",))
    k.run({"s": Value.of(pl.DataFrame({"p": ["a", "b"], "v": [1, 2]}), Identity.of("i"), Coverage.source({"a", "b"}, {"a", "b"}, set()))}, _ctx())
    assert (tmp_path / "p=a").exists() and (tmp_path / "p=b").exists()
    k.run({"s": Value.of(pl.DataFrame({"p": ["a"], "v": [9]}), Identity.of("i"), Coverage.source({"a", "b"}, {"a", "b"}, set()))}, _ctx())
    assert not (tmp_path / "p=b").exists() and pl.read_parquet(tmp_path / "p=a" / "*.parquet")["v"].to_list() == [9]

def test_append_replace_and_upsert_unsupported(tmp_path, backend_name, backend_df):
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.APPEND)
    k.run({"s": Value.of(backend_df, Identity.of("i"))}, _ctx()); k.run({"s": Value.of(backend_df, Identity.of("i"))}, _ctx())
    assert len(list(tmp_path.glob("*.parquet"))) == 2
    r = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE)
    r.run({"s": Value.of(backend_df, Identity.of("i"))}, _ctx())
    assert len(list(tmp_path.glob("*.parquet"))) == 1
    with pytest.raises(UnsupportedValueKind):                                     # before key validation (F23)
        ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.UPSERT)

def test_composite_partition_directories(tmp_path):                                # F18
    k = ParquetDirectorySink(tmp_path, name="k", depends_on=("s",), mode=WriteMode.REPLACE_PARTITION, partition_columns=("p", "q"))
    df = pl.DataFrame({"p": ["a", "a"], "q": ["x", "y"], "v": [1, 2]})
    k.run({"s": Value.of(df, Identity.of("i"), Coverage.source({("a", "x"), ("a", "y")}, {("a", "x"), ("a", "y")}, set()))}, _ctx())
    k.run({"s": Value.of(pl.DataFrame({"p": ["a"], "q": ["x"], "v": [9]}), Identity.of("i"), Coverage.source({("a", "x")}, {("a", "x")}, set()))}, _ctx())
    assert pl.read_parquet(tmp_path / "p=a" / "q=y" / "*.parquet")["v"].to_list() == [2] and pl.read_parquet(tmp_path / "p=a" / "q=x" / "*.parquet")["v"].to_list() == [9]
