"""Shared DataResource -> pyarrow.Table reader via mountainash-files (item 32).

Consumed by every backend's ``read_resource`` FALLBACK branch. Native local
scans and inline reads do NOT come here. Lazy import so a base install without
the ``files`` extra never imports mountainash-files at module load; a missing
dependency (direct or transitive, at import or during parse) surfaces as
``MissingFilesDependency``.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.relations.dag.errors import (
    MissingFilesDependency,
    UnsupportedResourceFormat,
)

if TYPE_CHECKING:
    import pyarrow as pa

__all__ = [
    "MissingFilesDependency",
    "parse_resource_to_arrow",
    "dialect_is_default",
    "ensure_dialect_supported",
]

# TableDialect fields CsvSpec (mountainash-files >=26.7.1) can express.
_MAPPABLE_DIALECT_FIELDS = frozenset(
    {"delimiter", "header", "quote_char", "escape_char", "null_sequence"}
)
# Fields that are metadata (do not affect parsing) -> neither mapped nor fatal.
_IGNORED_DIALECT_FIELDS = frozenset({"csvddf_version"})

_GLOB_CHARS = frozenset("*?[")
# suffix -> archive kind
_COMPRESSION_SUFFIXES = (".gz", ".zip")


def _require_files():
    """Import the mountainash-files symbols under one guard.

    Returns ``(parse, FileSourceSpec, CsvSpec, GzipCompression, ZipArchive)``.
    Any ImportError -- including a transitive one raised while importing the
    chain -- becomes MissingFilesDependency (spec §A.2/D1)."""
    try:
        from mountainash_files import FileSourceSpec, parse
        from mountainash_files.formats.csv import CsvSpec
        from mountainash_files.specs.archive import GzipCompression, ZipArchive
    except ImportError as exc:
        raise MissingFilesDependency(
            "reading this resource needs the file-reading extra; "
            "install mountainash[files]"
        ) from exc
    return parse, FileSourceSpec, CsvSpec, GzipCompression, ZipArchive


def ensure_dialect_supported(dialect: Any) -> None:
    """Raise UnsupportedResourceFormat if ``dialect`` sets a field the CsvSpec
    fallback cannot carry (spec §A.3.1). PURE (no files import) so it holds even
    without the extra. Applied on EVERY backend before routing so a rare
    unmappable field fails closed UNIFORMLY -- never read natively on Polars
    while raising on Ibis (consistency-guarantees). The supported-dialect
    surface is the cross-backend intersection = what CsvSpec can carry."""
    if dialect is None:
        return
    for name in type(dialect).model_fields:
        value = getattr(dialect, name)
        if value is None:
            continue
        if name in _MAPPABLE_DIALECT_FIELDS or name in _IGNORED_DIALECT_FIELDS:
            continue
        raise UnsupportedResourceFormat(
            f"CSV dialect field {name!r} is not supported by the "
            "mountainash-files reader"
        )


def _csv_spec_from_dialect(dialect: Any):
    """Map a Frictionless TableDialect onto a mountainash-files CsvSpec (>=26.7.1).
    Fail-closed on unmappable fields via ensure_dialect_supported (spec §A.3.1)."""
    ensure_dialect_supported(dialect)
    _parse, _FileSourceSpec, CsvSpec, _Gzip, _Zip = _require_files()
    if dialect is None:
        return CsvSpec()
    kwargs: dict[str, Any] = {}
    if dialect.delimiter is not None:
        kwargs["delimiter"] = dialect.delimiter
    if dialect.header is False:
        kwargs["header_row"] = None  # autogenerate column names
    if dialect.quote_char is not None:
        kwargs["quote_char"] = dialect.quote_char
    if dialect.escape_char is not None:
        kwargs["escape_char"] = dialect.escape_char
    if dialect.null_sequence is not None:
        kwargs["null_values"] = (dialect.null_sequence,)
    return CsvSpec(**kwargs)


def dialect_is_default(dialect: Any) -> bool:
    """True when ``dialect`` requires no non-default CSV parse option, so a
    native ``con.read_csv`` (which ignores our dialect) is safe. Default means:
    delimiter is comma-or-unset, header is present-or-unset, everything else
    unset. Metadata-only fields (csvddf_version) do not force the fallback."""
    if dialect is None:
        return True
    if dialect.delimiter not in (None, ","):
        return False
    if dialect.header not in (None, True):
        return False
    for name in type(dialect).model_fields:
        if name in {"delimiter", "header"} or name in _IGNORED_DIALECT_FIELDS:
            continue
        if getattr(dialect, name) is not None:
            return False
    return True


def _normalise_format(resource: Any, path_for_suffix: str) -> str | None:
    """Frictionless format/mediatype/suffix -> mountainash-files format key, or
    None to let parse() infer. Precedence: format -> mediatype -> path suffix."""
    if resource.format:
        return resource.format.lower()
    mt = (resource.mediatype or "").lower()
    if "csv" in mt:
        return "csv"
    if "parquet" in mt:
        return "parquet"
    if "json" in mt:
        return "json"
    low = path_for_suffix.lower()
    if low.endswith(".csv"):
        return "csv"
    if low.endswith(".parquet"):
        return "parquet"
    if low.endswith((".json", ".ndjson")):
        return "json"
    return None


def _split_glob(path: str) -> tuple[str, str | None]:
    """If ``path`` contains glob metacharacters, split into (base_dir, pattern).
    Otherwise (path, None). base_dir is the leading non-glob segments."""
    parts = path.split("/")
    for i, part in enumerate(parts):
        if _GLOB_CHARS & frozenset(part):
            base = "/".join(parts[:i]) or "."
            pattern = "/".join(parts[i:])
            return base, pattern
    return path, None


def _archive_and_stem(name: str, gzip_cls, zip_cls):
    """Detect a compression suffix. Returns (archive_obj_or_None, stem) where
    stem has the compression suffix stripped so format inference sees the inner
    suffix (data.csv.gz -> csv). Archive classes are passed in from the single
    guarded import so no un-guarded mountainash_files import happens here."""
    low = name.lower()
    for suffix in _COMPRESSION_SUFFIXES:
        if low.endswith(suffix):
            archive = gzip_cls() if suffix == ".gz" else zip_cls()
            return archive, name[: -len(suffix)]
    return None, name


def _file_source_specs(resource: Any) -> list[Any]:
    """One FileSourceSpec per path entry (spec §A.3). Handles glob + gzip/zip.
    Single-path resources yield a one-element list.

    NOT supported (and out of scope): globbing *inside* an archive
    (e.g. ``a.zip/*.csv``) -- glob resolves filesystem paths, archive members
    are selected by ``ZipArchive.file_pattern``; the two do not compose here."""
    _parse, FileSourceSpec, _CsvSpec, GzipCompression, ZipArchive = _require_files()
    raw = resource.path
    paths = raw if isinstance(raw, list) else [raw]
    specs: list[Any] = []
    for entry in paths:
        base, pattern = _split_glob(entry)
        # Compression suffix lives on the filename-bearing part.
        name_for_suffix = pattern if pattern is not None else base
        archive, stem = _archive_and_stem(name_for_suffix, GzipCompression, ZipArchive)
        fmt = _normalise_format(resource, stem)
        format_arg: Any = fmt
        if fmt == "csv":
            format_arg = _csv_spec_from_dialect(resource.dialect)
        specs.append(
            FileSourceSpec(path=base, glob=pattern, format=format_arg,
                           archive=archive)
        )
    return specs


def parse_resource_to_arrow(resource: Any) -> "pa.Table":
    """Read a DataResource's file(s) into one pyarrow.Table via mountainash-files.

    EAGER (full materialization). Local vs remote, glob, and archive expansion
    are handled inside ``parse()`` via the shared StorageFacade. Raises
    ``MissingFilesDependency`` if the chain is unavailable (direct/transitive,
    at import or during parse), ``UnsupportedResourceFormat`` if the format or
    dialect cannot be resolved.
    """
    import pyarrow as pa

    parse, _FileSourceSpec, _CsvSpec, _Gzip, _Zip = _require_files()
    try:
        tables: list[pa.Table] = []
        for spec in _file_source_specs(resource):
            for part in parse(spec):
                tables.append(part.data)
    except ImportError as exc:  # transitive dep surfacing during parse()
        raise MissingFilesDependency(
            f"reading resource {resource.name!r} needs the file-reading extra; "
            "install mountainash[files]"
        ) from exc
    if not tables:
        raise UnsupportedResourceFormat(
            f"resource {resource.name!r} produced no tables"
        )
    if len(tables) == 1:
        return tables[0]
    return pa.concat_tables(tables, promote_options="default")
