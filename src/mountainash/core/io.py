"""Shared storage helpers — thin wrappers around mountainash_utils_files.StorageFacade."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import BinaryIO


def is_remote(path: str) -> bool:
    """Return True if path uses a non-local storage scheme.

    Delegates to StorageFacade's scheme registry — automatically picks up
    new backends (B2, S3Express, HTTP/HTTPS, future providers) as the
    facade adds them.

    Falls back to a simple prefix check if mountainash_utils_files is not
    installed, so local-path detection never requires the optional package.
    """
    try:
        from mountainash_utils_files.path_helpers.scheme import StoragePath

        scheme = StoragePath.identify_scheme(path)
        return scheme is not None and scheme != "file"
    except ImportError:
        _FALLBACK_REMOTE_PREFIXES = (
            "http://",
            "https://",
            "s3://",
            "r2://",
            "minio://",
            "b2://",
            "s3express://",
            "gs://",
            "az://",
        )
        return any(path.startswith(s) for s in _FALLBACK_REMOTE_PREFIXES)


def _ensure_storage_facade() -> None:
    """Raise a descriptive error if mountainash_utils_files is missing."""
    try:
        import mountainash_utils_files  # noqa: F401
    except ImportError:
        raise ImportError(
            "Remote storage requires the 'storage' extra. "
            "Install it with: pip install mountainash[storage]"
        ) from None


def facade_read_bytes(path: str) -> bytes:
    """Read a remote path via StorageFacade.from_path().

    Auto-detects provider from URL scheme. Supports all facade-registered
    schemes including HTTP/HTTPS.
    """
    _ensure_storage_facade()
    from mountainash_utils_files.storage_facade.facade import StorageFacade

    facade = StorageFacade.from_path(path)
    return facade.read(path)


def facade_read_stream(path: str) -> BinaryIO:
    """Return a streaming read handle via StorageFacade.from_path()."""
    _ensure_storage_facade()
    from mountainash_utils_files.storage_facade.facade import StorageFacade

    facade = StorageFacade.from_path(path)
    return facade.read_stream(path)
