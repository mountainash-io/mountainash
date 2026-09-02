"""Shared Frictionless descriptor profile and error-location policies.

This module deliberately depends only on the public descriptor exceptions and
scalar values.  Codec and typed-model adapters use it to keep v1 marker
recognition and error context identical across representation boundaries.
"""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, replace
import json
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from mountainash.typespec.errors import (
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    UnsupportedDescriptorVersion,
)

if TYPE_CHECKING:
    from mountainash.typespec.spec import ForeignKey


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


def _foreign_key_location(
    location: InvariantLocation, index: int
) -> InvariantLocation:
    """Return the location for one raw ``foreignKeys`` entry."""
    return location.child(f"foreignKeys[{index}]")


def _validate_raw_foreign_key(
    value: object, *, location: InvariantLocation
) -> None:
    """Validate one raw foreign-key mapping before typed normalization."""
    if not isinstance(value, Mapping):
        raise _structure_at(
            location,
            "",
            value,
            "foreign-key mapping",
            descriptor_kind="schema",
        )

    fields = value.get("fields")
    if isinstance(fields, list) and not fields:
        raise _structure_at(
            location,
            ".fields",
            fields,
            "field name string or non-empty field name list",
            descriptor_kind="schema",
        )

    reference = value.get("reference")
    if not isinstance(reference, Mapping):
        raise _structure_at(
            location,
            ".reference",
            reference,
            "foreign-key reference mapping",
            descriptor_kind="schema",
        )

    if "resource" in reference and not isinstance(reference["resource"], str):
        raise _structure_at(
            location,
            ".reference.resource",
            reference["resource"],
            "resource name string",
            descriptor_kind="schema",
        )


def parse_foreign_keys_at(
    raw: Mapping[str, object], *, location: InvariantLocation
) -> tuple[ForeignKey, ...]:
    """Validate and normalize raw ``foreignKeys`` at a descriptor location."""
    if "foreignKeys" not in raw:
        return ()
    value = raw["foreignKeys"]
    if not isinstance(value, list):
        raise _structure_at(
            location,
            ".foreignKeys",
            value,
            "foreign-key list",
            descriptor_kind="schema",
        )

    from mountainash.typespec.frictionless import foreign_key_from_dict

    parsed: list[ForeignKey] = []
    for index, item in enumerate(value):
        item_location = _foreign_key_location(location, index)
        _validate_raw_foreign_key(item, location=item_location)
        parsed.append(foreign_key_from_dict(item))
    return tuple(parsed)


def validate_foreign_key_targets(
    foreign_keys: tuple[ForeignKey, ...],
    *,
    child_name: str,
    resource_names: frozenset[str],
    location: InvariantLocation,
) -> None:
    """Validate every explicit foreign-key target against package resources."""
    for index, foreign_key in enumerate(foreign_keys):
        target = foreign_key.reference.resource
        if target is None:
            continue
        if target not in resource_names:
            raise _relationship_at(
                location,
                index,
                target,
                "empty self-reference or package resource name",
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


def _is_remote_path(value: str) -> bool:
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return bool(parts.scheme and (parts.netloc or parts.scheme.lower() not in {"", "file"}))


def _validate_resource_path(value: object, *, location: InvariantLocation) -> None:
    values = value if isinstance(value, list) else [value]
    if isinstance(value, list) and not value:
        raise _structure_at(
            location,
            ".path",
            value,
            "non-empty string or non-empty list of strings",
        )
    if not isinstance(value, (str, list)) or any(not isinstance(item, str) for item in values):
        raise _structure_at(
            location,
            ".path",
            value,
            "string or non-empty list of strings",
        )
    if any(item == "" for item in values):
        raise _structure_at(location, ".path", value, "non-empty path string")
    for item in values:
        if _is_remote_path(item):
            continue
        if item.startswith("/"):
            raise _structure_at(location, ".path", value, "relative local path")
        if any(segment in {".", ".."} or segment.startswith(".") for segment in item.split("/")):
            raise _structure_at(
                location,
                ".path",
                value,
                "local path without hidden, ., or .. segments",
            )


def validate_resource_source_shape(
    raw: Mapping[str, object], *, location: InvariantLocation
) -> None:
    """Validate the resource source declaration without Pydantic coercion."""
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise _structure_at(location, ".name", name, "non-empty string resource name")
    has_path = "path" in raw and raw["path"] is not None
    has_data = "data" in raw and raw["data"] is not None
    if has_path == has_data:
        raise _structure_at(location, "", raw, "exactly one of path or data")
    if has_path:
        _validate_resource_path(raw["path"], location=location)
    if raw.get("type") is not None and raw.get("type") != "table":
        raise _structure_at(location, ".type", raw["type"], "absent or 'table'")


def parse_descriptor_json(text: str, *, descriptor_kind: str = "package") -> object:
    """Parse descriptor JSON and normalize syntax failures."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as exc:
        raise InvalidDescriptorSyntax(
            "descriptor text is not valid JSON",
            descriptor_kind=_descriptor_kind(descriptor_kind),
            descriptor_path="$",
            rejected_value=text,
            required_form="valid JSON text",
        ) from exc


def require_package_mapping(raw: object) -> Mapping[str, object]:
    """Require a package descriptor root mapping."""
    if not isinstance(raw, Mapping):
        raise InvalidDescriptorStructure(
            "package descriptor must be a mapping",
            descriptor_kind="package",
            descriptor_path="$",
            rejected_value=raw,
            required_form="package descriptor mapping",
        )
    return raw


def _pydantic_path(
    location: object, *, base_path: str, aliases: Mapping[str, str]
) -> str:
    path = base_path
    for part in location if isinstance(location, (tuple, list)) else (location,):
        if isinstance(part, int):
            path += f"[{part}]"
        elif part != "__root__":
            path += f".{aliases.get(str(part), str(part))}"
    return path


def pydantic_structure_error(
    exc: Exception,
    *,
    descriptor_kind: str,
    base_path: str,
    resource_name: str | None,
    reference: str | None,
    aliases: Mapping[str, str],
    required_forms: Mapping[str, str],
) -> InvalidDescriptorStructure:
    """Translate the first Pydantic field-shape error to a descriptor error."""
    errors = getattr(exc, "errors", lambda: ())()
    first = errors[0] if errors else {}
    location = first.get("loc", ()) if isinstance(first, Mapping) else ()
    descriptor_path = _pydantic_path(
        location,
        base_path=base_path,
        aliases=aliases,
    )
    raw_property_name = next(
        (
            str(part)
            for part in reversed(location)
            if isinstance(part, str) and part != "__root__"
        ),
        None,
    ) if isinstance(location, (tuple, list)) else None
    property_name = (
        aliases.get(raw_property_name, raw_property_name)
        if raw_property_name is not None
        else None
    )
    error_type = first.get("type") if isinstance(first, Mapping) else None
    unknown_keyword = error_type == "extra_forbidden"
    property_form = (
        required_forms.get(property_name)
        if property_name is not None
        else None
    )
    if property_form is None and raw_property_name is not None:
        property_form = required_forms.get(raw_property_name)
    required_form = (
        f"valid {_descriptor_kind(descriptor_kind)} property value"
        if unknown_keyword or property_form is None
        else property_form
    )
    rejected_value = first.get("input") if isinstance(first, Mapping) else None
    return InvalidDescriptorStructure(
        f"invalid {_descriptor_kind(descriptor_kind)} descriptor structure",
        descriptor_kind=_descriptor_kind(descriptor_kind),
        descriptor_path=descriptor_path,
        resource_name=resource_name,
        reference=reference,
        rejected_value=rejected_value,
        required_form=required_form,
    )


_RESOURCE_ALIASES = {
    "table_schema": "schema",
    "schema_url": "$schema",
    "bytes_": "bytes",
}
_RESOURCE_REQUIRED_FORMS = {
    "name": "non-empty string resource name",
    "path": "string or non-empty list of strings",
    "data": "resource data value",
    "type": "absent or 'table'",
    "dialect": "dialect mapping or reference string",
    "schema": "Table Schema mapping or reference string",
    "$schema": "profile URI string",
    "homepage": "string",
    "title": "string",
    "description": "string",
    "format": "string",
    "mediatype": "string",
    "encoding": "string",
    "bytes": "integer",
    "hash": "v2 hash string",
    "sources": "list of objects",
    "licenses": "list of objects",
}
_PACKAGE_ALIASES = {"dollar_schema": "$schema"}
_PACKAGE_REQUIRED_FORMS = {
    "$schema": "profile URI string",
    "name": "string",
    "id": "string",
    "licenses": "list of objects",
    "title": "string",
    "description": "string",
    "homepage": "string",
    "version": "string",
    "created": "RFC 3339 date-time string",
    "keywords": "non-empty list of strings",
    "contributors": "list of objects",
    "sources": "list of objects",
    "image": "string",
    "resources": "non-empty resource sequence",
}


__all__ = [
    "InvariantLocation",
    "is_recognized_v1_profile",
    "reject_v1_markers_at",
    "reject_typed_profile_at",
    "validate_resource_source_shape",
    "parse_descriptor_json",
    "require_package_mapping",
    "pydantic_structure_error",
    "parse_foreign_keys_at",
    "validate_foreign_key_targets",
    "_structure_at",
    "_relationship_at",
    "_foreign_key_location",
    "_validate_raw_foreign_key",
]
