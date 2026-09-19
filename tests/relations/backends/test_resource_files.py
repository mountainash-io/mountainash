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


NON_DEFAULT_DIALECT_VALUES = {
    "delimiter": ";",
    "line_terminator": "\r\n",
    "quote_char": "'",
    "double_quote": False,
    "escape_char": "\\",
    "null_sequence": "NULL",
    "skip_initial_space": True,
    "header": False,
    "header_rows": [2],
    "header_join": " / ",
    "comment_char": "#",
    "comment_rows": [2],
}


def _dialect_for_field(field: str) -> TableDialect:
    return TableDialect(**{field: NON_DEFAULT_DIALECT_VALUES[field]})


def _parse(resource):
    return rf.parse_resource_to_arrow(
        resource, dialect=resource.to_dialect()
    )


# ---- dialect mapping (pure; files present) --------------------------------

def test_csv_spec_from_none_dialect_is_defaults():
    spec = rf._csv_spec_from_dialect(None)
    assert spec.delimiter == ","
    assert spec.quote_char == '"'


def test_csv_spec_maps_full_dialect():
    d = TableDialect(delimiter=";", header=False, quote_char="|",
                     escape_char="\\", null_sequence="NA")
    spec = rf._csv_spec_from_dialect(d)
    assert spec.delimiter == ";"
    assert spec.header is False
    assert spec.quote_char == "|"
    assert spec.escape_char == "\\"
    assert spec.null_sequence == "NA"


def test_csv_spec_maps_comment_field():
    d = TableDialect(comment_char="#")
    assert rf._csv_spec_from_dialect(d).comment_char == "#"


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


# ---- dialect_native_safe (native-representable ⊊ CsvSpec-mappable) --------

@pytest.mark.parametrize("dialect,expected", [
    (None, True),
    (TableDialect(), True),
    (TableDialect(delimiter=";"), True),          # delimiter is native-safe
    (TableDialect(header=False), True),           # header is native-safe
    (TableDialect(quote_char="|"), True),         # quote_char is native-safe
    (TableDialect(null_sequence="NA"), True),     # null_sequence is native-safe
    (TableDialect(csvddf_version="1.2"), True),   # metadata does not force fallback
    (TableDialect(escape_char="\\"), False),      # NOT native-representable -> fallback
    (TableDialect(delimiter=";", escape_char="\\"), False),  # any escape -> fallback
])
def test_dialect_native_safe_semantics(dialect, expected):
    # escape_char is CsvSpec-mappable (ensure_dialect_supported allows it) but has
    # no correct pl.scan_csv target, so it must route to the fallback on every
    # backend rather than be read natively-and-wrong on Polars/Narwhals.
    assert rf.dialect_native_safe(dialect) is expected


@pytest.mark.parametrize("field", sorted(NON_DEFAULT_DIALECT_VALUES))
def test_dialect_native_safe_rejects_exactly_portable_only_fields(field):
    dialect = _dialect_for_field(field)
    assert rf.dialect_native_safe(dialect) is (
        field in rf._NATIVE_SAFE_DIALECT_FIELDS
    )


@pytest.mark.parametrize("field", sorted(NON_DEFAULT_DIALECT_VALUES))
def test_dialect_is_default_rejects_every_supported_non_default_setting(field):
    assert rf.dialect_is_default(_dialect_for_field(field)) is False


def test_ibis_default_dialect_semantics_remain_default():
    assert rf.dialect_is_default(TableDialect(delimiter=",")) is True
    assert rf.dialect_is_default(TableDialect(header=True)) is True


# ---- parse_resource_to_arrow (real local reads) ---------------------------

def test_parse_local_csv_to_arrow(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("a,b\n1,x\n2,y\n")
    res = DataResource(name="d", path=str(p), format="csv")
    table = _parse(res)
    assert isinstance(table, pa.Table)
    assert table.column_names == ["a", "b"]
    assert table.num_rows == 2


def test_parse_multipath_concats(tmp_path):
    p1 = tmp_path / "a.csv"; p1.write_text("a\n1\n")
    p2 = tmp_path / "b.csv"; p2.write_text("a\n2\n")
    res = DataResource(name="d", path=[str(p1), str(p2)], format="csv")
    table = _parse(res)
    assert sorted(table.column("a").to_pylist()) == [1, 2]


def test_parse_glob_expands(tmp_path):
    (tmp_path / "p1.csv").write_text("a\n1\n")
    (tmp_path / "p2.csv").write_text("a\n2\n")
    res = DataResource(name="d", path=f"{tmp_path}/*.csv", format="csv")
    table = _parse(res)
    assert sorted(table.column("a").to_pylist()) == [1, 2]


def test_parse_gzip_csv_with_dialect(tmp_path):
    # gzip + dialect together: the CsvSpec must reach the decompressed member.
    p = tmp_path / "d.csv.gz"
    p.write_bytes(gzip.compress(b"a;b\n1;NA\n"))
    res = DataResource(name="d", path=str(p), format="csv",
                       dialect=TableDialect(delimiter=";", null_sequence="NA"))
    table = _parse(res)
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
        _parse(res)


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
        _parse(res)


# ---- JSON: non-Arrow ParseResult.data normalises to a pa.Table -------------

def test_parse_local_json_records_to_arrow(tmp_path):
    # mountainash_files' json_parse returns raw Python records (list[dict]), not
    # a pa.Table -- the seam must lift them into Arrow (regression: pl.from_arrow
    # on a raw list raised TypeError).
    p = tmp_path / "d.json"
    p.write_text('[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]')
    res = DataResource(name="d", path=str(p), format="json")
    table = _parse(res)
    assert isinstance(table, pa.Table)
    assert table.column_names == ["a", "b"]
    assert table.column("a").to_pylist() == [1, 2]


def test_parse_single_json_object_is_one_row(tmp_path):
    # A top-level JSON object (dict, not list) is treated as a single record.
    p = tmp_path / "d.json"
    p.write_text('{"a": 1, "b": "x"}')
    res = DataResource(name="d", path=str(p), format="json")
    table = _parse(res)
    assert table.num_rows == 1
    assert table.column("a").to_pylist() == [1]


def test_json_array_of_scalars_fails_closed(tmp_path):
    # A JSON array of non-objects is not tabular -> clean UnsupportedResourceFormat
    # (not an opaque pyarrow AttributeError).
    p = tmp_path / "d.json"
    p.write_text("[1, 2, 3]")
    res = DataResource(name="d", path=str(p), format="json")
    with pytest.raises(UnsupportedResourceFormat, match="non-record"):
        _parse(res)


# ---- mountainash-files error types normalise to mountainash's hierarchy ----

def test_unknown_format_normalises_to_unsupported(tmp_path):
    # An unrecognised format string must surface as UnsupportedResourceFormat,
    # not a bare mountainash_files.FormatError (typed-error-hierarchy).
    p = tmp_path / "d.bogus"; p.write_text("whatever")
    res = DataResource(name="d", path=str(p), format="bogusfmt")
    with pytest.raises(UnsupportedResourceFormat):
        _parse(res)


def test_missing_format_dependency_normalises_to_missing_files(monkeypatch, tmp_path):
    # A mountainash_files.MissingDependencyError (optional-format dep, e.g. xlsx)
    # is NOT an ImportError; it must still normalise to MissingFilesDependency.
    from mountainash_files import MissingDependencyError
    import mountainash.relations.backends.relation_systems.resource_files as mod

    def boom(_spec):
        raise MissingDependencyError("XLSX parsing", "xlsx")

    real = mod._require_files()
    monkeypatch.setattr(mod, "_require_files", lambda: (boom, *real[1:]))
    p = tmp_path / "d.csv"; p.write_text("a\n1\n")
    res = DataResource(name="d", path=str(p), format="csv")
    with pytest.raises(MissingFilesDependency, match=r"mountainash\[files\]|optional"):
        _parse(res)



