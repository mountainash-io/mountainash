"""Descriptor URI context and controlled reference resolvers."""
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
from urllib.parse import urljoin, urlsplit, urlunsplit

try:
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python 3.10 compatibility
    class StrEnum(str, Enum):
        pass

from mountainash.core.io import facade_read_bytes
from mountainash_transport.location import (
    LocationNotAllowed,
    confine_local,
    identify_scheme,
    local_path,
    require_known_scheme,
)
from mountainash.typespec.errors import (
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    InvalidDescriptorStructure,
    MissingDescriptorBase,
)

try:
    from mountainash_transport._core.exceptions import (
        PathNotFoundError as _TransportPathNotFoundError,
    )
except ImportError:  # pragma: no cover - optional storage dependency
    _STORAGE_NOT_FOUND_ERRORS = (FileNotFoundError,)
else:
    _STORAGE_NOT_FOUND_ERRORS = (FileNotFoundError, _TransportPathNotFoundError)


if TYPE_CHECKING:
    from mountainash_transport.location import LocationPolicy


class DescriptorKind(StrEnum):
    SCHEMA = "schema"
    DIALECT = "dialect"


class DescriptorResolver(Protocol):
    def resolve(
        self,
        reference: str,
        *,
        base_uri: str | None,
        expected_kind: DescriptorKind,
        policy: "LocationPolicy | None" = None,
    ) -> Mapping[str, Any]:
        raise NotImplementedError


@dataclass(frozen=True)
class DescriptorContext:
    base_uri: str | None
    resolver: DescriptorResolver
    package_sources: tuple[Mapping[str, Any], ...]
    policy: "LocationPolicy | None" = None


def _base_error(value: object, message: str) -> InvalidDescriptorStructure:
    return InvalidDescriptorStructure(
        message,
        descriptor_path="$base_uri",
        rejected_value=value,
        required_form="absolute hierarchical URI or absolute local path",
    )


def _invalid_reference(
    reference: str,
    *,
    normalized_reference: str | None = None,
    message: str = "local descriptor reference must not contain a query or fragment",
) -> DescriptorReferenceInvalid:
    return DescriptorReferenceInvalid(
        message,
        reference=reference,
        normalized_reference=normalized_reference,
        required_form="local JSON document URI without query or fragment",
    )


def _normalize_remote_path(path: str, *, trailing_slash: bool = False) -> str:
    """Apply RFC 3986 section 5.2.4 without collapsing empty segments."""
    if not path:
        return "/" if trailing_slash else ""

    input_buffer = path
    output_buffer: list[str] = []

    def remove_last_segment() -> None:
        while output_buffer and output_buffer[-1] != "/":
            output_buffer.pop()
        if output_buffer:
            output_buffer.pop()

    while input_buffer:
        if input_buffer.startswith("../"):
            input_buffer = input_buffer[3:]
        elif input_buffer.startswith("./"):
            input_buffer = input_buffer[2:]
        elif input_buffer.startswith("/./"):
            input_buffer = "/" + input_buffer[3:]
        elif input_buffer == "/.":
            input_buffer = "/"
        elif input_buffer.startswith("/../"):
            input_buffer = "/" + input_buffer[4:]
            remove_last_segment()
        elif input_buffer == "/..":
            input_buffer = "/"
            remove_last_segment()
        elif input_buffer in (".", ".."):
            input_buffer = ""
        elif input_buffer.startswith("/"):
            slash = input_buffer.find("/", 1)
            if slash == -1:
                output_buffer.extend(input_buffer)
                input_buffer = ""
            else:
                output_buffer.extend(input_buffer[:slash])
                input_buffer = input_buffer[slash:]
        else:
            slash = input_buffer.find("/")
            if slash == -1:
                output_buffer.extend(input_buffer)
                input_buffer = ""
            else:
                output_buffer.extend(input_buffer[:slash])
                input_buffer = input_buffer[slash:]

    normalized = "".join(output_buffer)
    if trailing_slash and normalized and not normalized.endswith("/"):
        normalized += "/"
    if trailing_slash and not normalized:
        normalized = "/"
    return normalized

def _normalize_remote_netloc(parts: Any) -> str:
    hostname = parts.hostname
    if hostname is None:
        raise ValueError("hierarchical URI has no host")
    hostname = hostname.lower()
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    userinfo = ""
    if parts.username is not None:
        userinfo = parts.username
        if parts.password is not None:
            userinfo += f":{parts.password}"
        userinfo += "@"

    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("URI has an invalid port") from exc
    default_port = (parts.scheme.lower() == "http" and port == 80) or (
        parts.scheme.lower() == "https" and port == 443
    )
    if port is None or default_port:
        return f"{userinfo}{hostname}"
    return f"{userinfo}{hostname}:{port}"


def _canonical_remote_uri(value: str, *, trailing_slash: bool = False) -> str:
    parts = urlsplit(value)
    scheme = parts.scheme.lower()
    if not parts.netloc:
        raise ValueError("absolute URI is not hierarchical")
    netloc = _normalize_remote_netloc(parts)
    path = _normalize_remote_path(parts.path, trailing_slash=trailing_slash)
    return urlunsplit((scheme, netloc, path, parts.query, parts.fragment))


def _file_uri_path(value: str, *, reference: str) -> Path:
    """Decode a ``file:`` URI via transport ``local_path`` (descriptor errors preserved)."""
    try:
        return Path(local_path(value)).resolve()
    except LocationNotAllowed as exc:
        raise _invalid_reference(
            reference,
            normalized_reference=value,
            message=f"invalid file URI: {exc}",
        ) from exc


def normalize_base_uri(value: str | Path | None) -> str | None:
    """Return a canonical absolute directory URI."""
    if value is None:
        return None
    if isinstance(value, Path):
        if not value.is_absolute():
            raise _base_error(value, "descriptor base URI must be absolute")
        return value.resolve().as_uri() + "/"

    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise _base_error(value, "descriptor base URI is malformed") from exc
    if not parts.scheme:
        path = Path(value)
        if not path.is_absolute():
            raise _base_error(value, "descriptor base URI must be absolute")
        return path.resolve().as_uri() + "/"

    scheme = parts.scheme.lower()
    if scheme == "file":
        if parts.query or parts.fragment:
            raise _base_error(value, "local descriptor base URI must not contain a query or fragment")
        try:
            return _file_uri_path(value, reference=value).as_uri() + "/"
        except DescriptorReferenceInvalid as exc:
            raise _base_error(value, str(exc)) from exc

    if not parts.netloc:
        raise _base_error(value, "descriptor base URI must be hierarchical")
    try:
        return _canonical_remote_uri(value, trailing_slash=True)
    except ValueError as exc:
        raise _base_error(value, str(exc)) from exc


def normalize_document_uri(reference: str, *, base_uri: str | None) -> str:
    """Return one canonical absolute document URI."""
    try:
        parts = urlsplit(reference)
    except ValueError as exc:
        raise DescriptorReferenceInvalid(
            "descriptor reference is malformed",
            reference=reference,
        ) from exc
    if not parts.scheme:
        path = Path(reference)
        if path.is_absolute():
            return path.resolve().as_uri()
        if base_uri is None:
            raise MissingDescriptorBase(
                "relative descriptor reference requires a base URI",
                reference=reference,
                required_form="absolute URI or relative reference with base URI",
            )
        normalized_base = normalize_base_uri(base_uri)
        assert normalized_base is not None
        joined = urljoin(normalized_base, reference)
        joined_parts = urlsplit(joined)
        if joined_parts.scheme.lower() == "file":
            return _file_uri_path(joined, reference=reference).as_uri()
        try:
            return _canonical_remote_uri(joined)
        except ValueError as exc:
            raise DescriptorReferenceInvalid(
                "descriptor reference is not a hierarchical URI",
                reference=reference,
                normalized_reference=joined,
            ) from exc

    scheme = parts.scheme.lower()
    if scheme == "file":
        return _file_uri_path(reference, reference=reference).as_uri()
    try:
        return _canonical_remote_uri(reference)
    except ValueError as exc:
        # Keep absolute non-hierarchical references representable so the
        # resolver can apply its scheme policy (which denies them by default).
        if parts.scheme and not parts.netloc:
            return urlunsplit((scheme, parts.netloc, parts.path, parts.query, parts.fragment))
        raise DescriptorReferenceInvalid(
            "descriptor reference is not a hierarchical URI",
            reference=reference,
        ) from exc


def descriptor_cache_key(
    reference: str,
    *,
    base_uri: str | None,
    expected_kind: DescriptorKind,
) -> tuple[str, DescriptorKind]:
    return (
        normalize_document_uri(reference, base_uri=base_uri),
        expected_kind,
    )


def _expected_kind_value(expected_kind: DescriptorKind) -> str:
    return expected_kind.value if isinstance(expected_kind, DescriptorKind) else str(expected_kind)


def _parse_descriptor_bytes(
    payload: bytes,
    *,
    reference: str,
    normalized_reference: str,
    expected_kind: DescriptorKind,
) -> Mapping[str, Any]:
    try:
        descriptor = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise DescriptorReferenceInvalid(
            "resolved descriptor is not valid JSON",
            reference=reference,
            normalized_reference=normalized_reference,
            expected_kind=_expected_kind_value(expected_kind),
        ) from exc
    if not isinstance(descriptor, Mapping):
        raise DescriptorReferenceInvalid(
            "resolved descriptor must have a mapping root",
            reference=reference,
            normalized_reference=normalized_reference,
            expected_kind=_expected_kind_value(expected_kind),
        )
    return descriptor


class DefaultDescriptorResolver:
    """Resolve JSON descriptors under the context ``LocationPolicy``.

    Local results are confined to the policy root; remote results go through the
    storage facade, which enforces the remote allow-list before any request. With
    no policy (programmatic, no base) local reads are allowed and remote is denied.
    """

    def resolve(
        self,
        reference: str,
        *,
        base_uri: str | None,
        expected_kind: DescriptorKind,
        policy: "LocationPolicy | None" = None,
    ) -> Mapping[str, Any]:
        normalized = normalize_document_uri(reference, base_uri=base_uri)
        try:
            require_known_scheme(normalized, policy)
            if identify_scheme(normalized) in ("", "file"):
                path = confine_local(
                    str(_file_uri_path(normalized, reference=reference)), policy
                )
                payload = Path(path).read_bytes()
            else:
                if policy is None:
                    raise LocationNotAllowed(reference, "remote not allowed")
                payload = facade_read_bytes(normalized, policy)
        except _STORAGE_NOT_FOUND_ERRORS as exc:
            raise DescriptorReferenceNotFound(
                "descriptor reference does not exist",
                reference=reference,
                normalized_reference=normalized,
                expected_kind=_expected_kind_value(expected_kind),
            ) from exc
        return _parse_descriptor_bytes(
            payload,
            reference=reference,
            normalized_reference=normalized,
            expected_kind=expected_kind,
        )


def build_descriptor_context(
    *,
    base_uri: str | Path | None = None,
    resolver: DescriptorResolver | None = None,
    package_sources: Iterable[Mapping[str, Any]] = (),
    policy: "LocationPolicy | None" = None,
) -> DescriptorContext:
    """Build a context with canonical base and owned package-source storage."""
    frozen_sources = tuple(deepcopy(dict(source)) for source in package_sources)
    return DescriptorContext(
        base_uri=normalize_base_uri(base_uri),
        resolver=resolver if resolver is not None else DefaultDescriptorResolver(),
        package_sources=frozen_sources,
        policy=policy,
    )


def loader_policy(
    base_uri: str | Path | None,
    policy: "LocationPolicy | None",
) -> "LocationPolicy":
    """Return the loader's policy with its root declared (explicit root wins).

    A local base roots at that base; no base or a remote base roots at the
    load-time working directory. A remote base grants no permission.
    """
    import os

    from mountainash_transport.location import LocationPolicy

    normalized = normalize_base_uri(base_uri)  # existing descriptor errors fire first
    declared = os.getcwd()
    if normalized is not None and urlsplit(normalized).scheme == "file":
        declared = local_path(normalized)
    return (policy or LocationPolicy()).with_declared_root(declared)


__all__ = [
    "DescriptorKind",
    "DescriptorResolver",
    "DescriptorContext",
    "build_descriptor_context",
    "loader_policy",
    "normalize_base_uri",
    "normalize_document_uri",
    "descriptor_cache_key",
    "DefaultDescriptorResolver",
]
