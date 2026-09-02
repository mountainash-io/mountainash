"""Shared Frictionless descriptor profile and error-location policies.

This module deliberately depends only on the public descriptor exceptions and
scalar values.  Codec and typed-model adapters use it to keep v1 marker
recognition and error context identical across representation boundaries.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any
from urllib.parse import urlsplit

from mountainash.typespec.errors import (
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    UnsupportedDescriptorVersion,
)


_V1_PROFILE_PATHS_BY_HOST: dict[str, frozenset[str]] = {
    "datapackage.org": frozenset(
        f"/profiles/1.0/{name}.json"
        for name in ("datapackage", "dataresource", "tabledialect", "tableschema")
    ),
    "specs.frictionlessdata.io": frozenset(
        f"/schemas/{name}.json"
        for name in (
            "data-package",
            "data-resource",
            "tabular-data-resource",
            "tabular-data-package",
            "fiscal-data-package",
            "table-schema",
            "csv-dialect",
        )
    ),
    "frictionlessdata.io": frozenset(
        f"/schemas/{name}.json"
        for name in (
            "data-package",
            "data-resource",
            "tabular-data-resource",
            "tabular-data-package",
            "fiscal-data-package",
            "table-schema",
            "csv-dialect",
        )
    ),
}

_PRESENCE_MARKERS: dict[str, tuple[tuple[str, str], ...]] = {
    "package": (("profile", "remove profile and use a v2 $schema URI, or omit $schema"),),
    "resource": (("profile", "remove profile and use a v2 $schema URI, or omit $schema"),),
    "dialect": (
        ("caseSensitiveHeader", "v2 dialect properties"),
        ("csvddfVersion", "v2 dialect properties"),
    ),
}


@dataclass(frozen=True)
class InvariantLocation:
    """Immutable descriptor location shared by all invariant adapters."""

    descriptor_path: str
    resource_name: str | None = None
    reference: str | None = None

    def child(self, alias: str) -> "InvariantLocation":
        return replace(self, descriptor_path=f"{self.descriptor_path}.{alias}")

    def with_reference(self, reference: str, *, root: str = "$") -> "InvariantLocation":
        return InvariantLocation(root, self.resource_name, reference)


def _descriptor_kind(value: object) -> str:
    return str(getattr(value, "value", value))




def _structure_at(
    location: InvariantLocation,
    suffix: str,
    rejected_value: Any,
    required_form: str,
    *,
    descriptor_kind: str = "resource",
) -> InvalidDescriptorStructure:
    """Build a structural error at ``location`` plus a property suffix."""
    path = f"{location.descriptor_path}{suffix}"
    return InvalidDescriptorStructure(
        f"invalid {descriptor_kind} descriptor structure",
        descriptor_kind=_descriptor_kind(descriptor_kind),
        descriptor_path=path,
        resource_name=location.resource_name,
        reference=location.reference,
        rejected_value=rejected_value,
        required_form=required_form,
    )


def _relationship_at(
    location: InvariantLocation,
    foreign_key_index: int,
    rejected_value: Any,
    required_form: str,
) -> InvalidDescriptorRelationship:
    """Build a relationship error for one foreign-key record."""
    return InvalidDescriptorRelationship(
        "foreign key references an unknown resource",
        descriptor_kind="schema",
        descriptor_path=f"{location.descriptor_path}.foreignKeys[{foreign_key_index}].reference.resource",
        resource_name=location.resource_name,
        reference=location.reference,
        rejected_value=rejected_value,
        required_form=required_form,
    )


def is_recognized_v1_profile(value: object) -> bool:
    """Return whether *value* has an exact recognized Frictionless v1 identity."""
    if not isinstance(value, str):
        return False
    try:
        parts = urlsplit(value)
        host = (parts.hostname or "").casefold()
    except ValueError:
        return False
    if parts.scheme.casefold() not in {"http", "https"}:
        return False
    if host in {"www.specs.frictionlessdata.io", "www.frictionlessdata.io"}:
        host = host[4:]
    return parts.path in _V1_PROFILE_PATHS_BY_HOST.get(host, frozenset())


def _schema_value(raw: Mapping[str, Any], *, descriptor_kind: str, location: InvariantLocation) -> None:
    if "$schema" not in raw:
        return
    value = raw["$schema"]
    if not isinstance(value, str):
        raise _structure_at(
            location,
            ".$schema",
            value,
            "profile URI string",
            descriptor_kind=descriptor_kind,
        )
    if is_recognized_v1_profile(value):
        raise UnsupportedDescriptorVersion(
            "recognized v1 profile URI is not supported",
            descriptor_kind=_descriptor_kind(descriptor_kind),
            descriptor_path=f"{location.descriptor_path}.$schema",
            resource_name=location.resource_name,
            reference=location.reference,
            rejected_value=value,
            required_form="v2 profile URI or omitted $schema",
        )


def _version_error(
    marker: str,
    rejected_value: Any,
    required_form: str,
    location: InvariantLocation,
    *,
    descriptor_kind: str,
) -> UnsupportedDescriptorVersion:
    return UnsupportedDescriptorVersion(
        f"v1 descriptor marker {marker!r} is not supported",
        descriptor_kind=_descriptor_kind(descriptor_kind),
        descriptor_path=f"{location.descriptor_path}.{marker}",
        resource_name=location.resource_name,
        reference=location.reference,
        rejected_value=rejected_value,
        required_form=required_form,
    )


def reject_v1_markers_at(
    raw: Mapping[str, Any],
    *,
    descriptor_kind: str,
    location: InvariantLocation,
) -> None:
    """Reject recognized v1 profile identities and location-specific markers."""
    kind = _descriptor_kind(descriptor_kind)
    _schema_value(raw, descriptor_kind=kind, location=location)
    for marker, required_form in _PRESENCE_MARKERS.get(kind, ()):
        if marker in raw:
            raise _version_error(
                marker,
                raw[marker],
                required_form,
                location,
                descriptor_kind=kind,
            )


def reject_typed_profile_at(
    schema_url: object,
    *,
    descriptor_kind: str,
    extras: Mapping[str, Any] | None,
    location: InvariantLocation,
) -> None:
    """Apply profile policy to a typed ``$schema`` and extension mapping."""
    if schema_url is not None:
        _schema_value(
            {"$schema": schema_url},
            descriptor_kind=descriptor_kind,
            location=location,
        )
    if extras is not None and isinstance(extras, Mapping):
        kind = _descriptor_kind(descriptor_kind)
        for marker, required_form in _PRESENCE_MARKERS.get(kind, ()):
            if marker in extras:
                raise _version_error(
                    marker,
                    extras[marker],
                    required_form,
                    location,
                    descriptor_kind=kind,
                )


__all__ = [
    "InvariantLocation",
    "is_recognized_v1_profile",
    "reject_v1_markers_at",
    "reject_typed_profile_at",
    "_structure_at",
    "_relationship_at",
]
