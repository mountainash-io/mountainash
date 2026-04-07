"""Format dispatch for DataResource → Polars LazyFrame.

Entry point: :func:`read_resource_to_polars`.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from mountainash.relations.dag.errors import UnsupportedResourceFormat

from .csv import read_csv
from .inline import read_inline
from .json import read_json
from .parquet import read_parquet

if TYPE_CHECKING:
    from mountainash.typespec.datapackage import DataResource


def _detect_format(res: DataResource) -> str:
    """Infer format from declared format, mediatype, or path extension."""
    if res.format:
        return res.format.lower()
    if res.mediatype:
        mt = res.mediatype.lower()
        if "csv" in mt:
            return "csv"
        if "json" in mt:
            return "json"
        if "parquet" in mt:
            return "parquet"
    if isinstance(res.path, str) and "." in res.path:
        return res.path.rsplit(".", 1)[-1].lower()
    if isinstance(res.path, list) and res.path and "." in res.path[0]:
        return res.path[0].rsplit(".", 1)[-1].lower()
    raise UnsupportedResourceFormat(
        f"cannot detect format for resource {res.name!r}"
    )


def read_resource_to_polars(res: DataResource) -> pl.LazyFrame:
    """Dispatch a DataResource to the appropriate format reader.

    - ``data`` field present → inline reader (pydata ingress)
    - ``format``/``mediatype``/path extension → csv / json / parquet reader
    - Remote paths (http/https/s3/r2/minio) are routed through the storage facade.
    - Multi-file ``path: [...]`` arrays are vertically concatenated.

    Raises
    ------
    UnsupportedResourceFormat
        When no reader exists for the detected format.
    """
    if res.data is not None:
        return read_inline(res)
    fmt = _detect_format(res)
    if fmt == "csv":
        return read_csv(res)
    if fmt == "json":
        return read_json(res)
    if fmt == "parquet":
        return read_parquet(res)
    raise UnsupportedResourceFormat(
        f"no reader for format {fmt!r} (resource {res.name!r})"
    )


__all__ = ["read_resource_to_polars"]
