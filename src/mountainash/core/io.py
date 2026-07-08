"""Shared storage helpers — thin wrappers around mountainash_transport.StorageFacade."""
from __future__ import annotations


def is_remote(path: str) -> bool:
    """Return True if path uses a non-local storage scheme.

    Delegates to mountainash_transport's scheme registry
    (``StoragePath.identify_scheme``), which automatically recognises every
    scheme the transport layer supports — S3-family (s3/r2/minio/b2/s3express),
    HTTP/HTTPS, SSH/SFTP/FTP, GCS, Azure, and any future providers.

    ``identify_scheme`` returns ``""`` for bare/local paths, ``"file"`` for
    ``file://`` URLs, the canonical scheme token for known remotes, and
    ``None`` for an unrecognised scheme. Only a recognised non-local scheme is
    treated as remote; an unknown scheme falls through to a local read that
    surfaces a clear filesystem error rather than a silent remote misroute.

    Falls back to a simple prefix check if mountainash_transport is not
    installed, so local-path detection never requires the optional package.
    """
    try:
        from mountainash_transport.storage.path_helpers.storage_path import (
            StoragePath,
        )

        scheme = StoragePath.identify_scheme(path)
        return scheme not in ("", "file", None)
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
            "azure://",
            "ssh://",
            "sftp://",
            "ftp://",
            "ftps://",
        )
        return any(path.startswith(s) for s in _FALLBACK_REMOTE_PREFIXES)


def _ensure_storage_facade() -> None:
    """Raise a descriptive error if mountainash_transport is missing."""
    try:
        import mountainash_transport  # noqa: F401
    except ImportError:
        raise ImportError(
            "Remote storage requires the 'storage' extra. "
            "Install it with: pip install mountainash[storage]"
        ) from None


def facade_read_bytes(path: str) -> bytes:
    """Read a remote path via StorageFacade.from_path().

    Auto-detects the provider from the URL scheme. Supports all
    transport-registered schemes including HTTP/HTTPS.
    """
    _ensure_storage_facade()
    from mountainash_transport.storage.facade.facade import StorageFacade

    facade = StorageFacade.from_path(path)
    return facade.read(path)
