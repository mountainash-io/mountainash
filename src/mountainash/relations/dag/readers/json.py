"""JSON reader for DataResource. Routes remote paths through the storage facade."""
from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from mountainash.typespec.datapackage import DataResource

_REMOTE_SCHEMES: tuple[str, ...] = (
    "http://",
    "https://",
    "s3://",
    "r2://",
    "minio://",
)


def _is_remote(path: str) -> bool:
    return any(path.startswith(s) for s in _REMOTE_SCHEMES)


def _facade_read_bytes(path: str) -> bytes:
    """Read bytes via mountainash_utils_files storage facade. Lazy import.

    Dispatches to the appropriate backend based on URL scheme.
    """
    from mountainash_utils_files.constants import CONST_STORAGE_PROVIDER_TYPE
    from mountainash_utils_files.storage_facade.facade import StorageFacade

    if path.startswith("s3://"):
        provider = CONST_STORAGE_PROVIDER_TYPE.S3
    elif path.startswith("r2://"):
        provider = CONST_STORAGE_PROVIDER_TYPE.R2
    elif path.startswith("minio://"):
        provider = CONST_STORAGE_PROVIDER_TYPE.MINIO
    else:
        import urllib.request

        with urllib.request.urlopen(path) as response:  # noqa: S310
            return response.read()

    facade = StorageFacade(provider)
    return facade.read(path)


def _scan_one(path: str, kwargs: dict[str, Any]) -> pl.LazyFrame:
    # Polars has no scan_json for general newline-delimited JSON; use read_json → lazy
    if _is_remote(path):
        raw = _facade_read_bytes(path)
    else:
        with open(path, "rb") as f:
            raw = f.read()
    return pl.read_json(io.BytesIO(raw), **kwargs).lazy()


def read_json(res: DataResource) -> pl.LazyFrame:
    """Read a JSON DataResource into a Polars LazyFrame."""
    kwargs: dict[str, Any] = {}
    paths = res.path if isinstance(res.path, list) else [res.path]
    frames = [_scan_one(p, kwargs) for p in paths]
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="vertical")
