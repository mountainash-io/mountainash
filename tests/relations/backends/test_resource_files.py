"""Unit tests for the shared DataResource -> Arrow reader (item 32 seam)."""
from __future__ import annotations

import gzip

import pyarrow as pa
import pytest

from mountainash.relations.dag.errors import (
    MissingFilesDependency,
    UnsupportedResourceFormat,
)
from mountainash.typespec.datapackage import DataResource, TableDialect
from mountainash.relations.backends.relation_systems import resource_files as rf


# ---- dialect mapping (pure; files present) --------------------------------

def test_csv_spec_from_none_dialect_is_defaults():
    spec = rf._csv_spec_from_dialect(None)
    assert spec.delimiter == ","
    assert spec.quote_char is None


def test_csv_spec_maps_full_dialect():
    d = TableDialect(delimiter=";", header=False, quote_char="|",
                     escape_char="\\", null_sequence="NA")
    spec = rf._csv_spec_from_dialect(d)
    assert spec.delimiter == ";"
    assert spec.header_row is None            # header=False -> autogenerate
    assert spec.quote_char == "|"
    assert spec.escape_char == "\\"
    assert spec.null_values == ("NA",)


def test_csv_spec_fails_closed_on_unmappable_field():
    # comment_char has no CsvSpec counterpart in 26.7.1 -> fail-closed. This is
    # a PURE check (no files import needed) so it holds even without the extra.
    d = TableDialect(comment_char="#")
    with pytest.raises(UnsupportedResourceFormat, match="comment_char"):
        rf._csv_spec_from_dialect(d)


def test_csv_spec_ignores_metadata_only_field():
    # csvddf_version is metadata, not a parse option -> neither mapped nor fatal.
    d = TableDialect(csvddf_version="1.2")
    spec = rf._csv_spec_from_dialect(d)
    assert spec.delimiter == ","


# ---- dialect_is_default (semantic, not literal-all-None) ------------------

@pytest.mark.parametrize("dialect,expected", [
    (None, True),
    (TableDialect(), True),
    (TableDialect(header=True), True),          # header=True IS the default
    (TableDialect(delimiter=","), True),        # comma IS the default
    (TableDialect(header=False), False),
    (TableDialect(delimiter=";"), False),
    (TableDialect(quote_char="|"), False),
    (TableDialect(csvddf_version="1.2"), True), # metadata does not force fallback
])
def test_dialect_is_default_semantics(dialect, expected):
    assert rf.dialect_is_default(dialect) is expected


# ---- parse_resource_to_arrow (real local reads) ---------------------------

def test_parse_local_csv_to_arrow(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a,b\n1,x\n2,y\n")
    res = DataResource(name="d", path=str(p), format="csv")
    table = rf.parse_resource_to_arrow(res)
    assert isinstance(table, pa.Table)
    assert table.column_names == ["a", "b"]
    assert table.num_rows == 2


def test_parse_multipath_concats(tmp_path):
    p1 = tmp_path / "a.csv"; p1.write_text("a\n1\n")
    p2 = tmp_path / "b.csv"; p2.write_text("a\n2\n")
    res = DataResource(name="d", path=[str(p1), str(p2)], format="csv")
    table = rf.parse_resource_to_arrow(res)
    assert sorted(table.column("a").to_pylist()) == [1, 2]


def test_parse_glob_expands(tmp_path):
    (tmp_path / "p1.csv").write_text("a\n1\n")
    (tmp_path / "p2.csv").write_text("a\n2\n")
    res = DataResource(name="d", path=f"{tmp_path}/*.csv", format="csv")
    table = rf.parse_resource_to_arrow(res)
    assert sorted(table.column("a").to_pylist()) == [1, 2]


def test_parse_gzip_csv_with_dialect(tmp_path):
    # gzip + dialect together: the CsvSpec must reach the decompressed member.
    p = tmp_path / "d.csv.gz"
    p.write_bytes(gzip.compress(b"a;b\n1;NA\n"))
    res = DataResource(name="d", path=str(p), format="csv",
                       dialect=TableDialect(delimiter=";", null_sequence="NA"))
    table = rf.parse_resource_to_arrow(res)
    assert table.column_names == ["a", "b"]
    assert table.column("a").to_pylist() == [1]
    assert table.column("b").to_pylist() == [None]


# ---- degradation: direct AND transitive import failure --------------------

def test_missing_files_direct_import_is_typed(monkeypatch, tmp_path):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "mountainash_files" or name.startswith("mountainash_files."):
            raise ImportError("No module named 'mountainash_files'")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    p = tmp_path / "d.csv"; p.write_text("a\n1\n")
    res = DataResource(name="d", path=str(p), format="csv")
    with pytest.raises(MissingFilesDependency, match=r"mountainash\[files\]"):
        rf.parse_resource_to_arrow(res)


def test_missing_transitive_dep_during_parse_is_typed(monkeypatch, tmp_path):
    # A transitive dep that fails only when parse() EXECUTES (a lazy inner import
    # inside mountainash_files, e.g. transport) must still normalize -- not just
    # an import-time miss. Keep the REAL spec classes so _file_source_specs
    # builds a valid FileSourceSpec; only `parse` raises, exercising the second
    # guard in parse_resource_to_arrow (not the import guard).
    from mountainash_files import FileSourceSpec
    from mountainash_files.formats.csv import CsvSpec
    from mountainash_files.specs.archive import GzipCompression, ZipArchive
    p = tmp_path / "d.csv"; p.write_text("a\n1\n")
    res = DataResource(name="d", path=str(p), format="csv")
    import mountainash.relations.backends.relation_systems.resource_files as mod

    def boom(_spec):
        raise ImportError("No module named 'mountainash_transport'")

    monkeypatch.setattr(
        mod, "_require_files",
        lambda: (boom, FileSourceSpec, CsvSpec, GzipCompression, ZipArchive),
    )
    with pytest.raises(MissingFilesDependency, match=r"mountainash\[files\]"):
        rf.parse_resource_to_arrow(res)


# ---- JSON: non-Arrow ParseResult.data normalises to a pa.Table -------------

def test_parse_local_json_records_to_arrow(tmp_path):
    # mountainash_files' json_parse returns raw Python records (list[dict]), not
    # a pa.Table -- the seam must lift them into Arrow (regression: pl.from_arrow
    # on a raw list raised TypeError).
    p = tmp_path / "d.json"
    p.write_text('[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]')
    res = DataResource(name="d", path=str(p), format="json")
    table = rf.parse_resource_to_arrow(res)
    assert isinstance(table, pa.Table)
    assert table.column_names == ["a", "b"]
    assert table.column("a").to_pylist() == [1, 2]


def test_parse_single_json_object_is_one_row(tmp_path):
    # A top-level JSON object (dict, not list) is treated as a single record.
    p = tmp_path / "d.json"
    p.write_text('{"a": 1, "b": "x"}')
    res = DataResource(name="d", path=str(p), format="json")
    table = rf.parse_resource_to_arrow(res)
    assert table.num_rows == 1
    assert table.column("a").to_pylist() == [1]
