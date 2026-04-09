"""CSV reader for DataResource. Routes remote paths through the storage facade."""
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
    from mountainash_utils_files.constants import CONST_STORAGE_PROVIDER_TYPE  # type: ignore[import-not-found]
    from mountainash_utils_files.storage_facade.facade import StorageFacade  # type: ignore[import-not-found]

    if path.startswith("s3://"):
        provider = CONST_STORAGE_PROVIDER_TYPE.S3
    elif path.startswith("r2://"):
        provider = CONST_STORAGE_PROVIDER_TYPE.R2
    elif path.startswith("minio://"):
        provider = CONST_STORAGE_PROVIDER_TYPE.MINIO
    else:
        # http:// or https:// — use HTTP/HTTPS provider if available, else S3
        # For HTTP/HTTPS we fall back to a simple urllib read to avoid
        # requiring a registered HTTP backend.
        import urllib.request

        with urllib.request.urlopen(path) as response:  # noqa: S310
            return response.read()

    facade = StorageFacade(provider)
    return facade.read(path)


def _scan_one(path: str, kwargs: dict[str, Any]) -> pl.LazyFrame:
    if _is_remote(path):
        return pl.read_csv(io.BytesIO(_facade_read_bytes(path)), **kwargs).lazy()
    return pl.scan_csv(path, **kwargs)


def read_csv(res: DataResource) -> pl.LazyFrame:
    """Read a CSV DataResource into a Polars LazyFrame."""
    kwargs = res.dialect.to_polars_read_csv_kwargs() if res.dialect else {}
    raw_path = res.path
    assert raw_path is not None, f"DataResource '{res.name}' has no path"
    paths: list[str] = raw_path if isinstance(raw_path, list) else [raw_path]
    frames = [_scan_one(p, kwargs) for p in paths]
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="vertical")
