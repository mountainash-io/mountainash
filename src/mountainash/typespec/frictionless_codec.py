"""Frictionless v2 descriptor decoding.

This module owns the descriptor boundary.  Storage models retain the owned
input graph; typed schema and dialect conversion remains lazy.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import replace
from enum import StrEnum
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

if TYPE_CHECKING:
    from mountainash.typespec.datapackage import DataPackage, DataResource
from mountainash.typespec.descriptor_context import (
    DescriptorContext,
    DescriptorKind,
    build_descriptor_context,
    DescriptorResolver,
)
from mountainash.typespec.spec import TypeSpec
from mountainash.typespec.errors import (
    DescriptorError,
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    UnsupportedResourceDialect,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    is_recognized_v1_profile,
    parse_descriptor_json,
    pydantic_structure_error,
    reject_typed_profile_at,
    reject_v1_markers_at,
    require_package_mapping,
    validate_resource_source_shape,
)
# or an empty hash value.
V2_HASH_PATTERN = re.compile(r"^([^:]+:[a-fA-F0-9]+|[a-fA-F0-9]{32}|)$")
_CREATED_ADAPTER = TypeAdapter(AwareDatetime)

_PACKAGE_FIELDS = {
    "name", "id", "licenses", "$schema", "title", "description", "homepage",
    "version", "created", "keywords", "contributors", "sources", "image", "resources",
}
_RESOURCE_FIELDS = {
    "name", "path", "data", "type", "dialect", "schema", "$schema", "homepage",
    "title", "description", "format", "mediatype", "encoding", "bytes", "hash",
    "sources", "licenses",
}

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
_DIALECT_DELIMITED = {
    "delimiter", "lineTerminator", "quoteChar", "doubleQuote", "escapeChar",
    "nullSequence", "skipInitialSpace",
}
_DIALECT_STRUCTURED = {"property", "itemType", "itemKeys"}
_DIALECT_SPREADSHEET = {"sheetName", "sheetNumber"}
_DIALECT_DATABASE = {"table"}
_DIALECT_SHARED = {"header", "headerRows", "headerJoin", "commentChar", "commentRows"}


class _ContributorDescriptor(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    title: str | None = None
    given_name: str | None = Field(default=None, alias="givenName")
    family_name: str | None = Field(default=None, alias="familyName")
    organization: str | None = None
    path: str | None = None
    email: str | None = None
    roles: list[str] | None = None
    role: str | None = None


class _LicenseDescriptor(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str | None = None
    path: str | None = None
    title: str | None = None


class _SourceDescriptor(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    title: str | None = None
    path: str | None = None
    email: str | None = None


def _structure_error(
    message: str,
    *,
    descriptor_path: str,
    rejected_value: Any = None,
    required_form: str | None = None,
    descriptor_kind: str | None = None,
    resource_name: str | None = None,
) -> InvalidDescriptorStructure:
    return InvalidDescriptorStructure(
        message,
        descriptor_kind=descriptor_kind,
        descriptor_path=descriptor_path,
        resource_name=resource_name,
        rejected_value=rejected_value,
        required_form=required_form,
    )




def read_local_package_text(path: str | Path) -> tuple[Path, str]:
    """Read a local package descriptor and return its absolute path and text."""
    try:
        candidate = Path(path)
        absolute_path = candidate.resolve()
        text = absolute_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidDescriptorSyntax(
            "package descriptor text is not valid UTF-8 JSON",
            descriptor_kind="package",
            descriptor_path="$",
            rejected_value=path,
            required_form="UTF-8 JSON text",
        ) from exc
    except (TypeError, ValueError) as exc:
        raise _structure_error(
            "package descriptor path must be a local path",
            descriptor_path="$path",
            rejected_value=path,
            required_form="local filesystem path",
            descriptor_kind="package",
        ) from exc
    except (FileNotFoundError, OSError) as exc:
        raise DescriptorReferenceNotFound(
            "package descriptor path does not exist",
            descriptor_kind="package",
            descriptor_path="$path",
            rejected_value=path,
            required_form="existing local JSON file",
        ) from exc
    return absolute_path, text


def _reject_v1_markers(owned: Mapping[str, Any]) -> None:
    """Reject explicit v1 markers before any known-field validation."""
    reject_v1_markers_at(
        owned,
        descriptor_kind="package",
        location=InvariantLocation("$"),
    )
    resources = owned.get("resources")
    if not isinstance(resources, list):
        return
    for index, resource in enumerate(resources):
        if not isinstance(resource, Mapping):
            continue
        resource_path = f"$.resources[{index}]"
        resource_name = resource.get("name") if isinstance(resource.get("name"), str) else None
        resource_location = InvariantLocation(resource_path, resource_name)
        reject_v1_markers_at(resource, descriptor_kind="resource", location=resource_location)
        schema = resource.get("schema")
        if isinstance(schema, Mapping):
            reject_v1_markers_at(
                schema,
                descriptor_kind="schema",
                location=resource_location.child("schema"),
            )
        dialect = resource.get("dialect")
        if isinstance(dialect, Mapping):
            reject_v1_markers_at(
                dialect,
                descriptor_kind="dialect",
                location=resource_location.child("dialect"),
            )

def _ensure_string(mapping: Mapping[str, Any], key: str, path: str, *, kind: str, resource_name: str | None = None) -> None:
    if key in mapping and not isinstance(mapping[key], str):
        raise _structure_error(
            f"{key} must be a string",
            descriptor_path=f"{path}.{key}",
            rejected_value=mapping[key],
            required_form="string",
            descriptor_kind=kind,
            resource_name=resource_name,
        )


def _validate_metadata_models(
    value: Any,
    *,
    path: str,
    model: type[BaseModel],
    kind: str,
    resource_name: str | None = None,
) -> None:
    if not isinstance(value, list):
        raise _structure_error(
            "metadata property must be a list of objects",
            descriptor_path=path,
            rejected_value=value,
            required_form="list of objects",
            descriptor_kind=kind,
            resource_name=resource_name,
        )
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not isinstance(item, Mapping):
            raise _structure_error(
                "metadata item must be an object",
                descriptor_path=item_path,
                rejected_value=item,
                required_form="mapping",
                descriptor_kind=kind,
                resource_name=resource_name,
            )
        if model is _ContributorDescriptor:
            known_keys = ("givenName", "familyName", "title", "organization", "path", "email", "roles", "role")
        elif model is _LicenseDescriptor:
            known_keys = ("name", "path", "title")
        else:
            known_keys = ("title", "path", "email")
        for key in known_keys:
            if key in item and item[key] is None:
                raise _structure_error(
                    "metadata properties must not be null",
                    descriptor_path=f"{item_path}.{key}",
                    rejected_value=None,
                    required_form="string or list value",
                    descriptor_kind=kind,
                    resource_name=resource_name,
                )
        if model is _ContributorDescriptor and not item:
            raise _structure_error(
                "contributor must contain at least one property",
                descriptor_path=item_path,
                rejected_value=item,
                required_form="non-empty contributor object",
                descriptor_kind=kind,
                resource_name=resource_name,
            )
        if model is _LicenseDescriptor and not ("name" in item or "path" in item):
            raise _structure_error(
                "license must contain name or path",
                descriptor_path=item_path,
                rejected_value=item,
                required_form="license object with name or path",
                descriptor_kind=kind,
                resource_name=resource_name,
            )
        if model is _SourceDescriptor and not item:
            raise _structure_error(
                "source must contain at least one property",
                descriptor_path=item_path,
                rejected_value=item,
                required_form="non-empty source object",
                descriptor_kind=kind,
                resource_name=resource_name,
            )
        try:
            validated = model.model_validate(item)
        except ValidationError as exc:
            raise _structure_error(
                "metadata object has an invalid shape",
                descriptor_path=item_path,
                rejected_value=item,
                required_form=f"valid {model.__name__[1:-10].lower()} object",
                descriptor_kind=kind,
                resource_name=resource_name,
            ) from exc
        if model is _ContributorDescriptor and validated.roles is not None and not validated.roles:
            raise _structure_error(
                "contributor roles must not be empty",
                descriptor_path=f"{item_path}.roles",
                rejected_value=validated.roles,
                required_form="non-empty list of strings",
                descriptor_kind=kind,
                resource_name=resource_name,
            )



def _validate_dialect(value: Any, *, path: str, resource_name: str | None) -> None:
    if isinstance(value, str):
        return
    if not isinstance(value, Mapping):
        raise _structure_error(
            "dialect must be a mapping or reference string",
            descriptor_path=path,
            rejected_value=value,
            required_form="dialect mapping or reference string",
            descriptor_kind="resource",
            resource_name=resource_name,
        )
    _ensure_string(value, "$schema", path, kind="dialect", resource_name=resource_name)
    if "resources" in value or "fields" in value:
        bad_key = "resources" if "resources" in value else "fields"
        raise _structure_error(
            "dialect mapping has the wrong document kind",
            descriptor_path=f"{path}.{bad_key}",
            rejected_value=value[bad_key],
            required_form="dialect mapping without resources or fields",
            descriptor_kind="dialect",
            resource_name=resource_name,
        )
    families = []
    for family, triggers in (
        ("delimited text", _DIALECT_DELIMITED),
        ("structured", _DIALECT_STRUCTURED),
        ("spreadsheet", _DIALECT_SPREADSHEET),
        ("database", _DIALECT_DATABASE),
    ):
        if any(key in value for key in triggers):
            families.append(family)
    if len(families) > 1:
        raise UnsupportedResourceDialect(
            "dialect combines incompatible format families",
            descriptor_kind="dialect",
            descriptor_path=path,
            resource_name=resource_name,
            rejected_value=value,
            required_form="properties from one exclusive dialect family",
        )


def _validate_schema(value: Any, *, path: str, resource_name: str | None) -> None:
    if isinstance(value, str):
        return
    if not isinstance(value, Mapping):
        raise _structure_error(
            "schema must be a mapping or reference string",
            descriptor_path=path,
            rejected_value=value,
            required_form="Table Schema mapping or reference string",
            descriptor_kind="schema",
            resource_name=resource_name,
        )
    _ensure_string(value, "$schema", path, kind="schema", resource_name=resource_name)
    if "resources" in value:
        raise _structure_error(
            "schema mapping has the wrong document kind",
            descriptor_path=f"{path}.resources",
            rejected_value=value["resources"],
            required_form="Table Schema mapping",
            descriptor_kind="schema",
            resource_name=resource_name,
        )
    if "fields" not in value or not isinstance(value["fields"], list):
        raise _structure_error(
            "schema mapping must contain a fields list",
            descriptor_path=f"{path}.fields",
            rejected_value=value.get("fields"),
            required_form="Table Schema mapping with fields list",
            descriptor_kind="schema",
            resource_name=resource_name,
        )
    for index, field in enumerate(value["fields"]):
        if not isinstance(field, Mapping):
            raise _structure_error(
                "schema fields must be objects",
                descriptor_path=f"{path}.fields[{index}]",
                rejected_value=field,
                required_form="field mapping",
                descriptor_kind="schema",
                resource_name=resource_name,
            )
        if "name" not in field or not isinstance(field["name"], str):
            raise _structure_error(
                "schema field must have a string name",
                descriptor_path=f"{path}.fields[{index}].name",
                rejected_value=field.get("name"),
                required_form="string field name",
                descriptor_kind="schema",
                resource_name=resource_name,
            )
    foreign_keys = value.get("foreignKeys")
    if foreign_keys is not None and not isinstance(foreign_keys, list):
        raise _structure_error(
            "schema foreignKeys must be a list",
            descriptor_path=f"{path}.foreignKeys",
            rejected_value=foreign_keys,
            required_form="list of foreign-key mappings",
            descriptor_kind="schema",
            resource_name=resource_name,
        )

def _dialect_family_names(value: Mapping[str, Any]) -> list[str]:
    families: list[str] = []
    for family, triggers in (
        ("delimited text", _DIALECT_DELIMITED),
        ("structured", _DIALECT_STRUCTURED),
        ("spreadsheet", _DIALECT_SPREADSHEET),
        ("database", _DIALECT_DATABASE),
    ):
        if any(key in value for key in triggers):
            families.append(family)
    return families


def _reject_resolved_v1_markers(
    raw: Mapping[str, Any],
    *,
    expected_kind: DescriptorKind,
    descriptor_path: str,
    resource_name: str,
) -> None:
    reject_v1_markers_at(
        raw,
        descriptor_kind=expected_kind.value,
        location=InvariantLocation(descriptor_path, resource_name),
    )


def validate_resolved_mapping(
    raw: Mapping[str, Any],
    *,
    expected_kind: DescriptorKind,
    descriptor_path: str,
    resource_name: str,
) -> None:
    """Validate one resolved standalone schema or dialect document."""
    if not isinstance(raw, Mapping):
        raise _structure_error(
            "resolved descriptor must have a mapping root",
            descriptor_path=descriptor_path,
            rejected_value=raw,
            required_form=f"{expected_kind.value} mapping",
            descriptor_kind=expected_kind.value,
            resource_name=resource_name,
        )
    _reject_resolved_v1_markers(
        raw,
        expected_kind=expected_kind,
        descriptor_path=descriptor_path,
        resource_name=resource_name,
    )
    nested_key = expected_kind.value
    if isinstance(raw.get(nested_key), str):
        raise _structure_error(
            f"resolved {nested_key} must not be another reference",
            descriptor_path=f"{descriptor_path}.{nested_key}",
            rejected_value=raw[nested_key],
            required_form=f"inline {nested_key} mapping",
            descriptor_kind=expected_kind.value,
            resource_name=resource_name,
        )
    if expected_kind is DescriptorKind.SCHEMA:
        _validate_schema(raw, path=descriptor_path, resource_name=resource_name)
    else:
        if not raw:
            raise _structure_error(
                "resolved dialect mapping must not be empty",
                descriptor_path=descriptor_path,
                rejected_value=raw,
                required_form="non-empty Table Dialect mapping",
                descriptor_kind="dialect",
                resource_name=resource_name,
            )
        _validate_dialect(raw, path=descriptor_path, resource_name=resource_name)


def resolve_descriptor_mapping(
    value: Mapping[str, Any] | str,
    *,
    context: DescriptorContext,
    expected_kind: DescriptorKind,
    descriptor_path: str,
    resource_name: str,
) -> Mapping[str, Any]:
    is_reference = isinstance(value, str)
    if is_reference:
        try:
            raw = context.resolver.resolve(
                value,
                base_uri=context.base_uri,
                expected_kind=expected_kind,
            )
        except DescriptorError:
            raise
        except Exception as exc:
            raise DescriptorReferenceInvalid(
                "descriptor reference could not be resolved",
                descriptor_kind=expected_kind.value,
                descriptor_path=descriptor_path,
                resource_name=resource_name,
                reference=value,
                expected_kind=expected_kind.value,
                rejected_value=value,
                required_form=f"resolvable {expected_kind.value} JSON reference",
            ) from exc
    else:
        raw = value

    try:
        validate_resolved_mapping(
            raw,
            expected_kind=expected_kind,
            descriptor_path=descriptor_path,
            resource_name=resource_name,
        )
    except InvalidDescriptorStructure as exc:
        if not is_reference:
            raise
        raise DescriptorReferenceInvalid(
            "resolved descriptor has an invalid structure",
            descriptor_kind=expected_kind.value,
            descriptor_path=descriptor_path,
            resource_name=resource_name,
            reference=value,
            expected_kind=expected_kind.value,
            rejected_value=exc.rejected_value,
            required_form=exc.required_form,
        ) from exc
    return raw


def validate_foreign_key_relationships(
    raw: Mapping[str, Any],
    *,
    resource_names: frozenset[str],
) -> None:
    """Validate resolved schema foreign-key targets against package resources."""
    foreign_keys = raw.get("foreignKeys") or []
    for fk_index, foreign_key in enumerate(foreign_keys):
        path = f"$.foreignKeys[{fk_index}]"
        if not isinstance(foreign_key, Mapping):
            raise _structure_error(
                "foreign key must be a mapping",
                descriptor_path=path,
                rejected_value=foreign_key,
                required_form="foreign-key mapping",
                descriptor_kind="schema",
            )
        reference = foreign_key.get("reference")
        if not isinstance(reference, Mapping):
            raise _structure_error(
                "foreign key reference must be a mapping",
                descriptor_path=f"{path}.reference",
                rejected_value=reference,
                required_form="foreign-key reference mapping",
                descriptor_kind="schema",
            )
        target = reference.get("resource", "")
        if not isinstance(target, str):
            raise _structure_error(
                "foreign key reference resource must be a string",
                descriptor_path=f"{path}.reference.resource",
                rejected_value=target,
                required_form="resource name string",
                descriptor_kind="schema",
            )
        if target and target not in resource_names:
            raise InvalidDescriptorRelationship(
                "foreign key references an unknown resource",
                descriptor_kind="schema",
                descriptor_path=f"{path}.reference.resource",
                rejected_value=target,
                required_form="empty self-reference or package resource name",
            )


def validate_dialect_family(
    raw: Mapping[str, Any],
    *,
    resource_format: str | None,
) -> None:
    """Validate dialect document shape and compatibility with resource format."""
    if not isinstance(raw, Mapping):
        _validate_dialect(raw, path="$.dialect", resource_name=None)
        return
    if not raw:
        raise _structure_error(
            "dialect mapping must not be empty",
            descriptor_path="$.dialect",
            rejected_value=raw,
            required_form="non-empty Table Dialect mapping",
            descriptor_kind="dialect",
        )
    _validate_dialect(raw, path="$.dialect", resource_name=None)
    families = _dialect_family_names(raw)
    if not families or resource_format is None:
        return
    format_name = resource_format.lower().lstrip(".")
    format_family = {
        "csv": "delimited text",
        "tsv": "delimited text",
        "tab": "delimited text",
        "txt": "delimited text",
        "json": "structured",
        "jsonl": "structured",
        "ndjson": "structured",
        "geojson": "structured",
        "xls": "spreadsheet",
        "xlsx": "spreadsheet",
        "xlsm": "spreadsheet",
        "ods": "spreadsheet",
        "db": "database",
        "sqlite": "database",
        "sql": "database",
    }.get(format_name)
    if format_family is not None and families[0] != format_family:
        raise UnsupportedResourceDialect(
            "dialect family is incompatible with resource format",
            descriptor_kind="dialect",
            descriptor_path="$.dialect",
            rejected_value=raw,
            required_form=f"{format_family} dialect properties for format {resource_format!r}",
        )



def _validate_resource(raw: Mapping[str, Any], *, path: str) -> None:
    resource_name = raw.get("name") if isinstance(raw.get("name"), str) else None
    validate_resource_source_shape(
        raw,
        location=InvariantLocation(path, resource_name),
    )
    resource_name = raw["name"]
    for key in ("title", "description", "homepage", "format", "mediatype", "encoding", "hash"):
        _ensure_string(raw, key, path, kind="resource", resource_name=resource_name)
    _ensure_string(raw, "$schema", path, kind="resource", resource_name=resource_name)
    if "bytes" in raw and (isinstance(raw["bytes"], bool) or not isinstance(raw["bytes"], int)):
        raise _structure_error(
            "resource bytes must be an integer",
            descriptor_path=f"{path}.bytes",
            rejected_value=raw["bytes"],
            required_form="integer",
            descriptor_kind="resource",
            resource_name=resource_name,
        )
    if "hash" in raw and (not isinstance(raw["hash"], str) or V2_HASH_PATTERN.fullmatch(raw["hash"]) is None):
        raise _structure_error(
            "resource hash has an invalid shape",
            descriptor_path=f"{path}.hash",
            rejected_value=raw["hash"],
            required_form="v2 hash string",
            descriptor_kind="resource",
            resource_name=resource_name,
        )
    for key, model in (("licenses", _LicenseDescriptor), ("sources", _SourceDescriptor)):
        if key in raw:
            _validate_metadata_models(raw[key], path=f"{path}.{key}", model=model, kind="resource", resource_name=resource_name)
    if "schema" in raw:
        _validate_schema(raw["schema"], path=f"{path}.schema", resource_name=resource_name)
    if "dialect" in raw:
        _validate_dialect(raw["dialect"], path=f"{path}.dialect", resource_name=resource_name)


def _validate_package(owned: Mapping[str, Any]) -> None:
    if "resources" not in owned:
        raise _structure_error(
            "package must declare resources",
            descriptor_path="$.resources",
            rejected_value=None,
            required_form="non-empty resource sequence",
            descriptor_kind="package",
        )
    resources = owned["resources"]
    if not isinstance(resources, list) or not resources:
        raise _structure_error(
            "package resources must be a non-empty list",
            descriptor_path="$.resources",
            rejected_value=resources,
            required_form="non-empty resource sequence",
            descriptor_kind="package",
        )
    _ensure_string(owned, "$schema", "$", kind="package")
    for key in ("name", "id", "title", "description", "homepage", "version", "image"):
        _ensure_string(owned, key, "$", kind="package")
    if "created" in owned:
        if not isinstance(owned["created"], str):
            raise _structure_error(
                "package created must be an RFC 3339 date-time string",
                descriptor_path="$.created",
                rejected_value=owned["created"],
                required_form="RFC 3339 date-time string",
                descriptor_kind="package",
            )
        try:
            _CREATED_ADAPTER.validate_python(owned["created"])
        except ValidationError as exc:
            raise _structure_error(
                "package created must be an RFC 3339 date-time string",
                descriptor_path="$.created",
                rejected_value=owned["created"],
                required_form="RFC 3339 date-time string",
                descriptor_kind="package",
            ) from exc
    if "keywords" in owned:
        if not isinstance(owned["keywords"], list) or not owned["keywords"] or any(not isinstance(item, str) for item in owned["keywords"]):
            raise _structure_error(
                "package keywords must be a non-empty list of strings",
                descriptor_path="$.keywords",
                rejected_value=owned["keywords"],
                required_form="non-empty list of strings",
                descriptor_kind="package",
            )
    for key, model in (("contributors", _ContributorDescriptor), ("licenses", _LicenseDescriptor), ("sources", _SourceDescriptor)):
        if key in owned:
            _validate_metadata_models(owned[key], path=f"$.{key}", model=model, kind="package")
    seen_names: set[str] = set()
    for index, resource in enumerate(resources):
        path = f"$.resources[{index}]"
        if not isinstance(resource, Mapping):
            raise _structure_error(
                "resource must be a mapping",
                descriptor_path=path,
                rejected_value=resource,
                required_form="resource mapping",
                descriptor_kind="package",
            )
        name = resource.get("name")
        if isinstance(name, str) and name in seen_names:
            raise _structure_error(
                "resource names must be unique",
                descriptor_path=f"{path}.name",
                rejected_value=name,
                required_form="unique resource name",
                descriptor_kind="resource",
                resource_name=name,
            )
        if isinstance(name, str):
            seen_names.add(name)
        _validate_resource(resource, path=path)

def _capture_package_kwargs(owned: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    kwargs = {key: value for key, value in owned.items() if key in _PACKAGE_FIELDS}
    extras = {key: value for key, value in owned.items() if key not in _PACKAGE_FIELDS and key != "profile"}
    kwargs["extras"] = extras
    return kwargs, extras


def _capture_resource_kwargs(raw: Mapping[str, Any]) -> dict[str, Any]:
    kwargs = {key: value for key, value in raw.items() if key in _RESOURCE_FIELDS}
    kwargs["extras"] = {key: value for key, value in raw.items() if key not in _RESOURCE_FIELDS and key != "profile"}
    return kwargs

def _decode_owned_package(owned: Mapping[str, Any], *, context: DescriptorContext) -> DataPackage:
    """Decode an already-owned mapping without making another defensive copy."""
    from mountainash.typespec.datapackage import DataPackage, DataResource
    # 1. Confirm the required document kind.
    owned = require_package_mapping(owned)
    # 2. Reject all recognized v1 markers.
    _reject_v1_markers(owned)
    # 3. Validate known property and container shapes.
    _validate_package(owned)
    # 4. Capture unknown extension properties.
    package_kwargs, _ = _capture_package_kwargs(owned)
    resource_models: list[DataResource] = []
    for raw_resource in owned["resources"]:
        resource_kwargs = _capture_resource_kwargs(raw_resource)
        try:
            resource_models.append(DataResource.model_validate(resource_kwargs))
        except ValidationError as exc:
            raise pydantic_structure_error(
                exc,
                descriptor_kind="resource",
                base_path=f"$.resources[{len(resource_models)}]",
                resource_name=raw_resource.get("name") if isinstance(raw_resource.get("name"), str) else None,
                reference=None,
                aliases=_RESOURCE_ALIASES,
                required_forms=_RESOURCE_REQUIRED_FORMS,
            ) from exc
        except ValueError as exc:
            raise _structure_error(
                "resource model has an invalid shape",
                descriptor_path=f"$.resources[{len(resource_models)}]",
                rejected_value=raw_resource,
                required_form="valid Data Resource mapping",
                descriptor_kind="resource",
                resource_name=raw_resource.get("name") if isinstance(raw_resource.get("name"), str) else None,
            ) from exc
    package_kwargs["resources"] = resource_models
    try:
        package = DataPackage.model_validate(package_kwargs)
    except ValidationError as exc:
        raise pydantic_structure_error(
            exc,
            descriptor_kind="package",
            base_path="$",
            resource_name=None,
            reference=None,
            aliases=_PACKAGE_ALIASES,
            required_forms=_PACKAGE_REQUIRED_FORMS,
        ) from exc
    except ValueError as exc:
        raise _structure_error(
            "package model has an invalid shape",
            descriptor_path="$",
            rejected_value=owned,
            required_form="valid Data Package mapping",
            descriptor_kind="package",
        ) from exc
    # 6. Bind one shared final context with storage-owned package sources.
    package_sources = tuple(owned.get("sources", ()))
    final_context = replace(context, package_sources=package_sources)
    package._descriptor_context = final_context
    resource_names = frozenset(resource.name for resource in package.resources)
    for resource in package.resources:
        resource._descriptor_context = final_context
        resource._package_resource_names = resource_names
    # 7. Validate inline foreign-key resource targets.
    _validate_inline_foreign_keys(owned["resources"], resource_names)
    return package


def _validate_inline_foreign_keys(resources: list[Any], resource_names: frozenset[str]) -> None:
    for resource_index, resource in enumerate(resources):
        if not isinstance(resource, Mapping):
            continue
        schema = resource.get("schema")
        if not isinstance(schema, Mapping):
            continue
        foreign_keys = schema.get("foreignKeys") or []
        for fk_index, foreign_key in enumerate(foreign_keys):
            if not isinstance(foreign_key, Mapping):
                raise _structure_error(
                    "foreign key must be a mapping",
                    descriptor_path=f"$.resources[{resource_index}].schema.foreignKeys[{fk_index}]",
                    rejected_value=foreign_key,
                    required_form="foreign-key mapping",
                    descriptor_kind="schema",
                    resource_name=resource.get("name"),
                )
            reference = foreign_key.get("reference")
            if not isinstance(reference, Mapping):
                raise _structure_error(
                    "foreign key reference must be a mapping",
                    descriptor_path=f"$.resources[{resource_index}].schema.foreignKeys[{fk_index}].reference",
                    rejected_value=reference,
                    required_form="foreign-key reference mapping",
                    descriptor_kind="schema",
                    resource_name=resource.get("name"),
                )
            target = reference.get("resource", "")
            if not isinstance(target, str):
                raise _structure_error(
                    "foreign key reference resource must be a string",
                    descriptor_path=f"$.resources[{resource_index}].schema.foreignKeys[{fk_index}].reference.resource",
                    rejected_value=target,
                    required_form="resource name string",
                    descriptor_kind="schema",
                    resource_name=resource.get("name"),
                )
            if target and target not in resource_names:
                raise InvalidDescriptorRelationship(
                    "foreign key references an unknown resource",
                    descriptor_kind="schema",
                    descriptor_path=f"$.resources[{resource_index}].schema.foreignKeys[{fk_index}].reference.resource",
                    resource_name=resource.get("name"),
                    rejected_value=target,
                    required_form="empty self-reference or package resource name",
                )


def decode_package_descriptor(
    raw: Mapping[str, Any],
    *,
    base_uri: str | Path | None = None,
    resolver: DescriptorResolver | None = None,
) -> DataPackage:
    mapping = require_package_mapping(raw)
    context = build_descriptor_context(
        base_uri=base_uri,
        resolver=resolver,
        package_sources=(),
    )
    return _decode_owned_package(deepcopy(mapping), context=context)


def decode_package_json(
    text: str,
    *,
    base_uri: str | Path | None = None,
    resolver: DescriptorResolver | None = None,
) -> DataPackage:
    raw = parse_descriptor_json(text)
    return decode_package_descriptor(raw, base_uri=base_uri, resolver=resolver)


def decode_package_path(
    path: str | Path,
    *,
    resolver: DescriptorResolver | None = None,
) -> DataPackage:
    absolute_path, text = read_local_package_text(path)
    return decode_package_json(
        text,
        base_uri=absolute_path.parent,
        resolver=resolver,
    )


class DescriptorWriteMode(StrEnum):
    PRESERVE = "preserve"
    CANONICAL = "canonical"


_PACKAGE_PROFILE = "https://datapackage.org/profiles/2.0/datapackage.json"
_RESOURCE_PROFILE = "https://datapackage.org/profiles/2.0/dataresource.json"
_SCHEMA_PROFILE = "https://datapackage.org/profiles/2.0/tableschema.json"
_DIALECT_PROFILE = "https://datapackage.org/profiles/2.0/tabledialect.json"


def _encode_resource_preserve(resource: DataResource) -> dict[str, Any]:
    """Encode one resource while owning every value in the returned graph."""
    from mountainash.typespec.datapackage import TableDialect
    from mountainash.typespec.frictionless import typespec_to_frictionless
    location = InvariantLocation("$", resource.name)
    reject_typed_profile_at(
        resource.schema_url,
        descriptor_kind="resource",
        extras=resource.extras,
        location=location,
    )
    if isinstance(resource.dialect, Mapping):
        reject_v1_markers_at(
            resource.dialect,
            descriptor_kind="dialect",
            location=location.child("dialect"),
        )
    if isinstance(resource.table_schema, Mapping):
        reject_v1_markers_at(
            resource.table_schema,
            descriptor_kind="schema",
            location=location.child("schema"),
        )

    out: dict[str, Any] = {"name": deepcopy(resource.name)}
    for field in (
        "path",
        "data",
        "type",
        "homepage",
        "title",
        "description",
        "format",
        "mediatype",
        "encoding",
        "hash",
        "sources",
        "licenses",
    ):
        value = getattr(resource, field)
        if value is not None:
            out[field] = deepcopy(value)
    if resource.schema_url is not None:
        out["$schema"] = deepcopy(resource.schema_url)
    if resource.bytes_ is not None:
        out["bytes"] = deepcopy(resource.bytes_)

    if resource.dialect is not None:
        if isinstance(resource.dialect, TableDialect):
            dialect = resource.dialect.to_descriptor()
        else:
            dialect = resource.dialect
        out["dialect"] = deepcopy(dialect)
    if resource.table_schema is not None:
        if isinstance(resource.table_schema, TypeSpec):
            schema = typespec_to_frictionless(resource.table_schema)
        else:
            schema = resource.table_schema
        out["schema"] = deepcopy(schema)
    out.update(deepcopy(resource.extras))
    return out


def _encode_package_preserve(package: DataPackage) -> dict[str, Any]:
    """Encode a package without normalizing authored consumer-facing forms."""
    reject_typed_profile_at(
        package.dollar_schema,
        descriptor_kind="package",
        extras=package.extras,
        location=InvariantLocation("$"),
    )
    out: dict[str, Any] = {}
    if package.dollar_schema is not None:
        out["$schema"] = deepcopy(package.dollar_schema)
    for field in (
        "name",
        "id",
        "title",
        "description",
        "homepage",
        "version",
        "created",
        "keywords",
        "contributors",
        "sources",
        "image",
        "licenses",
    ):
        value = getattr(package, field)
        if value is not None:
            out[field] = deepcopy(value)
    out["resources"] = [_encode_resource_preserve(resource) for resource in package.resources]
    out.update(deepcopy(package.extras))
    return out


def _canonical_profile(value: Any, standard: str) -> Any:
    if value is None or value == standard or is_recognized_v1_profile(value):
        return standard
    return deepcopy(value)


def _as_string_list(value: Any) -> Any:
    if isinstance(value, str):
        return [value]
    return deepcopy(value)


def _canonicalize_contributors(value: Any) -> Any:
    if not isinstance(value, list):
        return deepcopy(value)
    result: list[Any] = []
    for contributor in value:
        if not isinstance(contributor, Mapping):
            result.append(deepcopy(contributor))
            continue
        owned = deepcopy(dict(contributor))
        roles = owned.get("roles")
        if roles is None and owned.get("role") is not None:
            roles = [owned["role"]]
        owned.pop("role", None)
        if roles is not None:
            owned["roles"] = deepcopy(roles)
        result.append(owned)
    return result


def _canonicalize_dialect(value: Any) -> Any:
    if not isinstance(value, Mapping):
        return deepcopy(value)
    result = deepcopy(dict(value))
    for marker in ("caseSensitiveHeader", "csvddfVersion"):
        result.pop(marker, None)
    result["$schema"] = _canonical_profile(result.get("$schema"), _DIALECT_PROFILE)
    return result


def _canonicalize_schema(value: Any, *, resource_name: str) -> Any:
    if not isinstance(value, Mapping):
        return deepcopy(value)
    result = deepcopy(dict(value))
    result["$schema"] = _canonical_profile(result.get("$schema"), _SCHEMA_PROFILE)
    if "primaryKey" in result:
        result["primaryKey"] = _as_string_list(result["primaryKey"])
    foreign_keys = result.get("foreignKeys")
    if isinstance(foreign_keys, list):
        normalized: list[Any] = []
        for foreign_key in foreign_keys:
            if not isinstance(foreign_key, Mapping):
                normalized.append(deepcopy(foreign_key))
                continue
            owned_fk = deepcopy(dict(foreign_key))
            if "fields" in owned_fk:
                owned_fk["fields"] = _as_string_list(owned_fk["fields"])
            reference = owned_fk.get("reference")
            if isinstance(reference, Mapping):
                owned_reference = deepcopy(dict(reference))
                if "fields" in owned_reference:
                    owned_reference["fields"] = _as_string_list(owned_reference["fields"])
                if owned_reference.get("resource") in ("", resource_name):
                    owned_reference.pop("resource", None)
                owned_fk["reference"] = owned_reference
            normalized.append(owned_fk)
        result["foreignKeys"] = normalized
    return result


def _encode_package_canonical(package: DataPackage) -> dict[str, Any]:
    """Encode a package with the section 10.2 canonical normalizations."""
    result = _encode_package_preserve(package)
    result["$schema"] = _canonical_profile(result.get("$schema"), _PACKAGE_PROFILE)
    if "contributors" in result:
        result["contributors"] = _canonicalize_contributors(result["contributors"])
    for resource in result["resources"]:
        resource["$schema"] = _canonical_profile(resource.get("$schema"), _RESOURCE_PROFILE)
        if resource.get("type") != "table":
            resource.pop("type", None)
        if "dialect" in resource:
            resource["dialect"] = _canonicalize_dialect(resource["dialect"])
        if "schema" in resource:
            resource["schema"] = _canonicalize_schema(
                resource["schema"],
                resource_name=resource.get("name", ""),
            )
        resource.pop("profile", None)
    result.pop("profile", None)
    return result


def encode_package_descriptor(
    package: DataPackage,
    *,
    mode: DescriptorWriteMode,
) -> dict[str, Any]:
    if mode is DescriptorWriteMode.PRESERVE:
        return _encode_package_preserve(package)
    return _encode_package_canonical(package)


__all__ = [
    "DescriptorWriteMode",
    "encode_package_descriptor",
    "decode_package_descriptor",
    "decode_package_json",
    "decode_package_path",
    "read_local_package_text",
    "V2_HASH_PATTERN",
]
