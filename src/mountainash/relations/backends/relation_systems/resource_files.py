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
    "dialect_native_safe",
    "ensure_dialect_supported",
    "NATIVE_UNSAFE_DIALECT_CONDITION",
    "IBIS_NON_DEFAULT_DIALECT_CONDITION",
]

# TableDialect fields the CsvSpec fallback (mountainash-files >=26.7.1) can
# express. This is the SEAM-supported set: anything outside it (plus ignored)
# fails closed uniformly in ensure_dialect_supported.
_MAPPABLE_DIALECT_FIELDS = frozenset(
    {
        "delimiter", "line_terminator", "header", "quote_char", "double_quote",
        "escape_char", "null_sequence", "skip_initial_space", "header_rows",
        "header_join", "comment_char", "comment_rows",
    }
)
# The STRICT subset a native Polars/Narwhals scan can represent *correctly* via
# TableDialect.to_polars_read_csv_kwargs. escape_char is CsvSpec-mappable but has
# NO correct native Polars target (pl.scan_csv has no escape parameter; the old
# escape_char->eol_char map was wrong), so an escape-bearing dialect must route to
# the CsvSpec fallback on EVERY backend -- never read natively-and-wrong on Polars/
# Narwhals while Ibis reads it correctly (consistency-guarantees).
_NATIVE_SAFE_DIALECT_FIELDS = frozenset(
    {"delimiter", "header", "quote_char", "null_sequence"}
)
# No descriptor dialect fields are ignored. ``extras`` is an implementation-only
# model field and is skipped explicitly in the loops below.
_IGNORED_DIALECT_FIELDS = frozenset()

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
        if name == "extras" or name in _MAPPABLE_DIALECT_FIELDS or name in _IGNORED_DIALECT_FIELDS:
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
        kwargs["header"] = False
    if dialect.quote_char is not None:
        kwargs["quote_char"] = dialect.quote_char
    if dialect.comment_char is not None:
        kwargs["comment_char"] = dialect.comment_char
    if dialect.comment_rows is not None:
        kwargs["comment_rows"] = tuple(dialect.comment_rows)
    if dialect.header_rows is not None:
        kwargs["header_rows"] = tuple(dialect.header_rows)
    if dialect.header_join is not None:
        kwargs["header_join"] = dialect.header_join
    if dialect.skip_initial_space is not None:
        kwargs["skip_initial_space"] = dialect.skip_initial_space
    if dialect.double_quote is not None:
        kwargs["double_quote"] = dialect.double_quote
    if dialect.line_terminator is not None:
        kwargs["line_terminator"] = dialect.line_terminator
    if dialect.escape_char is not None:
        kwargs["escape_char"] = dialect.escape_char
    if dialect.null_sequence is not None:
        kwargs["null_sequence"] = dialect.null_sequence
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
        if name == "extras" or name in {"delimiter", "header"} or name in _IGNORED_DIALECT_FIELDS:
            continue
        if getattr(dialect, name) is not None:
            return False
    return True


def dialect_native_safe(dialect: Any) -> bool:
    """True when every set field of ``dialect`` can be represented CORRECTLY by a
    native Polars/Narwhals ``scan_csv`` (via ``to_polars_read_csv_kwargs``).

    ``escape_char`` is CsvSpec-mappable (so ``ensure_dialect_supported`` allows it)
    but has no correct native Polars target, so a dialect that sets it returns
    False here and the Polars/Narwhals readers route it to the CsvSpec fallback --
    where it IS honoured -- matching Ibis (which fallback-routes any non-default
    dialect). Unmappable fields never reach this check (``ensure_dialect_supported``
    rejects them first); if one did, it returns False and the fallback's
    ``_csv_spec_from_dialect`` re-raises, so the answer stays consistent."""
    if dialect is None:
        return True
    for name in type(dialect).model_fields:
        if name == "extras" or name in _NATIVE_SAFE_DIALECT_FIELDS or name in _IGNORED_DIALECT_FIELDS:
            continue
        if getattr(dialect, name) is not None:
            return False
    return True


_PORTABLE_ONLY_DIALECT_FIELDS = tuple(sorted(
    _MAPPABLE_DIALECT_FIELDS - _NATIVE_SAFE_DIALECT_FIELDS
))


NATIVE_UNSAFE_DIALECT_CONDITION = " or ".join(
    f"resource.dialect.{field} is set"
    for field in _PORTABLE_ONLY_DIALECT_FIELDS
)


IBIS_NON_DEFAULT_DIALECT_CONDITION = " or ".join(
    (
        "resource.dialect.delimiter is non-default"
        if field == "delimiter"
        else "resource.dialect.header is false"
        if field == "header"
        else f"resource.dialect.{field} is set"
    )
    for field in sorted(_MAPPABLE_DIALECT_FIELDS)
)


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


def _file_source_specs(resource: Any, dialect: Any) -> list[Any]:
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
            format_arg = _csv_spec_from_dialect(dialect)
        specs.append(
            FileSourceSpec(path=base, glob=pattern, format=format_arg,
                           archive=archive)
        )
    return specs


def _part_data_to_arrow(data: Any, resource_name: str) -> "pa.Table":
    """Normalise a ``ParseResult.data`` payload to a ``pa.Table``.

    ``mountainash_files`` parsers return format-dependent payloads: CSV/Parquet
    yield a ``pa.Table`` directly, but JSON/NDJSON yield raw Python records
    (``list``/``dict``) -- ``ParseResult.data`` is typed ``Any``. Record
    payloads are lifted into Arrow here (a single dict is treated as one row).
    Conform-after-read on the visitor casts final types; this only needs a
    faithful tabular Arrow frame."""
    import pyarrow as pa

    if isinstance(data, pa.Table):
        return data
    if isinstance(data, dict):
        return pa.Table.from_pylist([data])
    if isinstance(data, list):
        if data and not all(isinstance(row, dict) for row in data):
            # A JSON array of scalars (e.g. ``[1, 2, 3]``) is not tabular;
            # pa.Table.from_pylist would raise an opaque AttributeError.
            raise UnsupportedResourceFormat(
                f"resource {resource_name!r} produced a JSON array of "
                "non-record values; expected an array of objects"
            )
        return pa.Table.from_pylist(data)
    raise UnsupportedResourceFormat(
        f"resource {resource_name!r} produced a {type(data).__name__} payload "
        "that is not tabular (expected pyarrow.Table or JSON records)"
    )


def parse_resource_to_arrow(resource: Any, *, dialect: Any) -> "pa.Table":
    """Read a DataResource's file(s) into one pyarrow.Table via mountainash-files.

    EAGER (full materialization). Local vs remote, glob, and archive expansion
    are handled inside ``parse()`` via the shared StorageFacade. Non-Arrow
    payloads (JSON records) are normalised to Arrow via ``_part_data_to_arrow``.
    Raises ``MissingFilesDependency`` if the chain is unavailable
    (direct/transitive, at import or during parse, OR an optional-format dep
    reported by mountainash-files), ``UnsupportedResourceFormat`` if the format
    or dialect cannot be resolved (unknown/ambiguous format, or unreadable
    contents). All mountainash-files exceptions are normalised here so no
    foreign error type escapes the seam (typed-error-hierarchy).
    """
    import pyarrow as pa

    parse, _FileSourceSpec, _CsvSpec, _Gzip, _Zip = _require_files()
    # Safe now that _require_files() confirmed the chain imports (a direct import
    # miss already raised MissingFilesDependency above -- no bare ImportError).
    from mountainash_files import FormatError, MissingDependencyError

    try:
        tables: list[pa.Table] = []
        for spec in _file_source_specs(resource, dialect):
            for part in parse(spec):
                tables.append(_part_data_to_arrow(part.data, resource.name))
    except ImportError as exc:  # transitive dep surfacing during parse()
        raise MissingFilesDependency(
            f"reading resource {resource.name!r} needs the file-reading extra; "
            "install mountainash[files]"
        ) from exc
    except MissingDependencyError as exc:  # optional-format dep (e.g. xlsx) absent
        raise MissingFilesDependency(
            f"reading resource {resource.name!r} needs an optional file-format "
            f"dependency: {exc}"
        ) from exc
    except FormatError as exc:  # unknown/ambiguous format, or unreadable contents
        raise UnsupportedResourceFormat(
            f"resource {resource.name!r} (format={resource.format!r}) could not "
            f"be read by the mountainash-files reader: {exc}"
        ) from exc
    if not tables:
        raise UnsupportedResourceFormat(
            f"resource {resource.name!r} produced no tables"
        )
    if len(tables) == 1:
        return tables[0]
    return pa.concat_tables(tables, promote_options="default")
