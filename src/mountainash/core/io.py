"""Shared storage helpers — thin wrappers around mountainash_transport.StorageFacade."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash_transport.location import LocationPolicy


def is_remote(path: str) -> bool:
    """Return True if path uses a recognised non-local storage scheme.

    Delegates to ``mountainash_transport.location.identify_scheme``: ``""`` is a
    bare path, ``"file"`` a file URI, ``None`` an unrecognised scheme (treated as
    local so the filesystem or the policy surfaces a clear error).
    """
    from mountainash_transport.location import identify_scheme

    return identify_scheme(path) not in ("", "file", None)


def facade_read_bytes(path: str, policy: LocationPolicy | None = None) -> bytes:
    """Read a remote path via StorageFacade.from_path().

    Auto-detects the provider from the URL scheme. Supports all
    transport-registered schemes including HTTP/HTTPS.
    """
    from mountainash_transport.storage.facade.facade import StorageFacade

    facade = StorageFacade.from_path(path, policy=policy)
    return facade.read(path)
