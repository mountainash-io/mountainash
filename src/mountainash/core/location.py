"""Storage-location helpers for descriptor-bound resources (spec §5)."""
from __future__ import annotations

import os
import posixpath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash_transport.location import LocationPolicy


def resource_policy(resource: Any) -> "LocationPolicy | None":
    """Return the resource's active location policy, or None (programmatic or opted out)."""
    ctx = getattr(resource, "_descriptor_context", None)
    pol = getattr(ctx, "policy", None)
    return pol if pol is not None and pol.active else None


def resolve_resource_location(resource: Any, path: str) -> str:
    """Join a resource path to its descriptor base (spec §5): bare paths literally, URIs hierarchically.

    Applies whether or not confinement is active: opting out of confinement does not
    opt out of descriptor-relative resolution. Without a base, a loader policy's root
    is the base; programmatic contexts (no policy) return the path unchanged.
    """
    from urllib.parse import urlsplit, urlunsplit

    from mountainash_transport.location import identify_scheme, local_path

    ctx = getattr(resource, "_descriptor_context", None)
    base = getattr(ctx, "base_uri", None)
    if base is None:
        pol = getattr(ctx, "policy", None)
        base = getattr(pol, "root", None)
    if base is None or identify_scheme(path) != "" or os.path.isabs(path):
        return path
    if identify_scheme(str(base)) in ("", "file"):
        return os.path.join(local_path(str(base)), path)
    from mountainash.typespec.descriptor_context import _normalize_remote_path

    parts = urlsplit(base)
    joined = posixpath.join(parts.path or "/", path)
    return urlunsplit((parts.scheme, parts.netloc, _normalize_remote_path(joined), "", ""))
