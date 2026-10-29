"""Shared storage helpers — thin wrappers around mountainash_transport.StorageFacade."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash_transport import POLICY_UNSET

if TYPE_CHECKING:
    from mountainash_transport.location import PolicyOverride


def is_remote(path: str) -> bool:
    """Return True if path uses a recognised non-local storage scheme.

    Delegates to ``mountainash_transport.location.identify_scheme``: ``""`` is a
    bare path, ``"file"`` a file URI, ``None`` an unrecognised scheme (treated as
    local so the filesystem or the policy surfaces a clear error).
    """
    from mountainash_transport.location import identify_scheme

    return identify_scheme(path) not in ("", "file", None)


def bound_access(context: Any, location: str) -> dict[str, Any]:
    """Storage/auth profiles a runtime context contributes to ``location``.

    A bound storage profile applies only to a location served by its own provider
    family (S3-compatible schemes share one); any other location is read with transport's
    default access for its scheme, so a local reference never builds a remote client and a
    reference to an unrelated provider never inherits another provider's credentials. A
    bound auth profile without a storage profile applies to remote locations only.
    """
    storage_profile = getattr(context, "storage_profile", None)
    auth_profile = getattr(context, "auth_profile", None)
    if storage_profile is None and auth_profile is None:
        return {}
    if storage_profile is None:
        return {"auth_profile": auth_profile} if is_remote(location) else {}

    from mountainash_transport import detect_provider_from_path
    from mountainash_transport.location import _S3_FAMILY

    try:
        provider = detect_provider_from_path(location)
    except ValueError:
        return {}
    profile_provider = getattr(getattr(storage_profile, "__spec__", None), "provider_type", None)
    same = profile_provider is None or provider == profile_provider or (
        provider in _S3_FAMILY and profile_provider in _S3_FAMILY
    )
    if not same:
        return {}
    return {"storage_profile": storage_profile, "auth_profile": auth_profile}


def facade_read_bytes(
    path: str,
    policy: PolicyOverride = POLICY_UNSET,
    *,
    storage_profile: Any = None,
    auth_profile: Any = None,
) -> bytes:
    """Read a remote path via StorageFacade.from_path().

    Auto-detects the provider from the URL scheme. Supports all
    transport-registered schemes including HTTP/HTTPS. The facade is owned by this
    call and closed before it returns.
    """
    from mountainash_transport import StorageFacade

    with StorageFacade.from_path(
        path, storage_profile, auth_profile=auth_profile, policy=policy
    ) as facade:
        return facade.read(path)
