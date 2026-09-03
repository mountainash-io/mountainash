from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass, replace
import json
from typing import Any, Optional, TYPE_CHECKING, cast

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError
from mountainash.typespec.descriptor_context import (
    DescriptorContext,
    DescriptorKind,
    DescriptorResolver,
    LocalDescriptorResolver,
)
from mountainash.typespec.spec import ForeignKey, TypeSpec
from mountainash.typespec.errors import (
    DescriptorError,
    DescriptorReferenceInvalid,
    InvalidDescriptorRelationship,
    InvalidDescriptorStructure,
    InvalidDescriptorSyntax,
    TypeSpecError,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    _PACKAGE_ALIASES,
    _PACKAGE_REQUIRED_FORMS,
    _RESOURCE_ALIASES,
    _RESOURCE_REQUIRED_FORMS,
    _structure_at,
    parse_descriptor_json,
    parse_foreign_keys_at,
    pydantic_structure_error,
    reject_typed_profile_at,
    reject_v1_markers_at,
    require_package_mapping,
    validate_foreign_key_targets,
    validate_resource_source_shape,
)
from mountainash.typespec.frictionless_codec import DescriptorWriteMode


if TYPE_CHECKING:
    from pathlib import Path

"""Frictionless Data Package types — TableDialect, DataResource, DataPackage."""


def _default_descriptor_context() -> DescriptorContext:
    return DescriptorContext(
        base_uri=None,
        resolver=LocalDescriptorResolver(),
        package_sources=(),
    )


def _parse_descriptor_json_input(
    json_data: str | bytes | bytearray,
    *,
    descriptor_kind: str,
) -> object:
    """Parse Pydantic's text-or-bytes input without widening the parser API."""
    if isinstance(json_data, str):
        return parse_descriptor_json(json_data, descriptor_kind=descriptor_kind)
    try:
        text = json_data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidDescriptorSyntax(
            "descriptor text is not valid JSON",
            descriptor_kind=descriptor_kind,
            descriptor_path="$",
            rejected_value=json_data,
            required_form="valid JSON text",
        ) from exc
    return parse_descriptor_json(text, descriptor_kind=descriptor_kind)



def _validate_resource_profile_input(
    value: Mapping[str, Any], *, location: InvariantLocation
) -> None:
    raw = dict(value)
    if "$schema" not in raw and "schema_url" in raw:
        raw["$schema"] = raw["schema_url"]
    reject_v1_markers_at(raw, descriptor_kind="resource", location=location)
    schema = raw.get("schema", raw.get("table_schema"))
    if isinstance(schema, Mapping):
        reject_v1_markers_at(
            schema,
            descriptor_kind="schema",
            location=location.child("schema"),
        )
    dialect = raw.get("dialect")
    if isinstance(dialect, Mapping):
        reject_v1_markers_at(
            dialect,
            descriptor_kind="dialect",
            location=location.child("dialect"),
        )



class TableDialect(BaseModel):
    """Frictionless Table Dialect spec — closed schema, unknown keys are dropped."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    schema_url: Optional[str] = Field(default=None, alias="$schema")
    delimiter: Optional[str] = None
    line_terminator: Optional[str] = Field(default=None, alias="lineTerminator")
    quote_char: Optional[str] = Field(default=None, alias="quoteChar")
    double_quote: Optional[bool] = Field(default=None, alias="doubleQuote")
    escape_char: Optional[str] = Field(default=None, alias="escapeChar")
    null_sequence: Optional[str] = Field(default=None, alias="nullSequence")
    skip_initial_space: Optional[bool] = Field(default=None, alias="skipInitialSpace")
    header: Optional[bool] = None
    header_rows: Optional[list[int]] = Field(default=None, alias="headerRows")
    header_join: Optional[str] = Field(default=None, alias="headerJoin")
    comment_char: Optional[str] = Field(default=None, alias="commentChar")
    comment_rows: Optional[list[int]] = Field(default=None, alias="commentRows")
    item_type: Optional[str] = Field(default=None, alias="itemType")
    item_keys: Optional[list[str]] = Field(default=None, alias="itemKeys")
    property: Optional[str] = None
    sheet_name: Optional[str] = Field(default=None, alias="sheetName")
    sheet_number: Optional[int] = Field(default=None, alias="sheetNumber")
    table: Optional[str] = None
    extras: dict[str, Any] = Field(default_factory=dict)
    def __setattr__(self, name: str, value: Any) -> None:
        if name == "schema_url" and "schema_url" in self.__dict__:
            raise TypeError("TableDialect.schema_url is immutable after construction")
        super().__setattr__(name, value)

    @classmethod
    def _validate_profile_input(cls, value: Any) -> None:
        if isinstance(value, cls):
            raw = value.model_dump(by_alias=True)
        elif isinstance(value, Mapping):
            raw = dict(value)
        else:
            return
        reject_v1_markers_at(
            raw,
            descriptor_kind="dialect",
            location=InvariantLocation("$"),
        )
        reject_typed_profile_at(
            raw.get("$schema", raw.get("schema_url")),
            descriptor_kind="dialect",
            extras=raw.get("extras") if isinstance(raw.get("extras"), Mapping) else None,
            location=InvariantLocation("$"),
        )

    def __init__(self, **data: Any) -> None:
        self._validate_profile_input(data)
        super().__init__(**data)
        reject_typed_profile_at(
            self.schema_url,
            descriptor_kind="dialect",
            extras=self.extras,
            location=InvariantLocation("$"),
        )

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "TableDialect":
        cls._validate_profile_input(obj)
        result = super().model_validate(obj, **kwargs)
        reject_typed_profile_at(
            result.schema_url,
            descriptor_kind="dialect",
            extras=result.extras,
            location=InvariantLocation("$"),
        )
        return result

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        **kwargs: Any,
    ) -> "TableDialect":
        try:
            parsed = json.loads(json_data)
        except (TypeError, ValueError):
            parsed = None
        if isinstance(parsed, Mapping):
            cls._validate_profile_input(parsed)
        result = super().model_validate_json(json_data, **kwargs)
        reject_typed_profile_at(
            result.schema_url,
            descriptor_kind="dialect",
            extras=result.extras,
            location=InvariantLocation("$"),
        )
        return result


    @classmethod
    def from_descriptor(cls, raw: Mapping[str, Any]) -> "TableDialect":
        return cls.model_validate(dict(raw))

    def to_descriptor(self) -> dict[str, Any]:
        reject_typed_profile_at(
            self.schema_url,
            descriptor_kind="dialect",
            extras=self.extras,
            location=InvariantLocation("$"),
        )
        out = self.model_dump(by_alias=True, exclude_none=True)
        extras = out.pop("extras", None)
        if extras:
            out.update(deepcopy(extras))
        return out

    def to_polars_read_csv_kwargs(self) -> dict[str, Any]:
        """Translate to ``polars.read_csv`` kwargs. Unsupported keys are dropped silently."""
        out: dict[str, Any] = {}
        if self.delimiter is not None:
            out["separator"] = self.delimiter
        if self.header is not None:
            out["has_header"] = self.header
        if self.quote_char is not None:
            out["quote_char"] = self.quote_char
        # NOTE: escape_char is intentionally NOT mapped -- pl.scan_csv has no
        # escape parameter (the former escape_char->eol_char map was wrong; eol_char
        # is the line terminator). Escape-bearing dialects route to the CsvSpec
        # fallback (see resource_files.dialect_native_safe), which honours them.
        if self.comment_char is not None:
            out["comment_prefix"] = self.comment_char
        if self.null_sequence is not None:
            out["null_values"] = [self.null_sequence]
        return out

_RESOURCE_PUBLIC_FIELDS = frozenset(
    {
        "name",
        "path",
        "data",
        "type",
        "dialect",
        "schema",
        "$schema",
        "homepage",
        "title",
        "description",
        "format",
        "mediatype",
        "encoding",
        "bytes",
        "hash",
        "sources",
        "licenses",
    }
)


def _marker_values(raw: Mapping[str, object]) -> dict[str, object]:
    marker_values = dict(raw)
    extras = marker_values.pop("extras", None)
    if isinstance(extras, Mapping):
        for key, value in extras.items():
            marker_values.setdefault(key, value)
    return marker_values
def _capture_resource_values(raw: Mapping[str, object]) -> dict[str, object]:
    extras_value = raw.get("extras")
    extras = dict(extras_value) if isinstance(extras_value, Mapping) else {}
    values: dict[str, object] = {}
    for key, value in raw.items():
        if key == "extras":
            continue
        if key in _RESOURCE_PUBLIC_FIELDS:
            values[key] = value
        else:
            extras[key] = value
    if extras:
        values["extras"] = extras
    return values



_PACKAGE_PUBLIC_FIELDS = frozenset(
    {
        "name",
        "id",
        "licenses",
        "$schema",
        "title",
        "description",
        "homepage",
        "version",
        "created",
        "keywords",
        "contributors",
        "sources",
        "image",
        "resources",
    }
)


def _capture_package_values(raw: Mapping[str, object]) -> dict[str, object]:
    extras_value = raw.get("extras")
    extras = dict(extras_value) if isinstance(extras_value, Mapping) else {}
    values: dict[str, object] = {}
    for key, value in raw.items():
        if key == "extras":
            continue
        if key in _PACKAGE_PUBLIC_FIELDS:
            values[key] = value if key == "resources" else deepcopy(value)
        else:
            extras[key] = value
    values["extras"] = deepcopy(extras)
    return values

def _resource_public_values(
    value: Mapping[str, object] | DataResource,
) -> dict[str, object]:
    """Return resource values using descriptor-facing aliases."""
    if isinstance(value, DataResource):
        raw = value.model_dump(by_alias=True, exclude_none=True)
        if isinstance(value.table_schema, TypeSpec):
            raw["schema"] = value.table_schema
        if isinstance(value.dialect, TableDialect):
            raw["dialect"] = value.dialect
    elif isinstance(value, Mapping):
        raw = dict(value)
    else:
        raise TypeError("resource must be a mapping or DataResource")
    for field_name, alias in _RESOURCE_ALIASES.items():
        if field_name in raw:
            if alias not in raw:
                raw[alias] = raw[field_name]
            del raw[field_name]
    return raw


def _owned_resource_values(
    raw: Mapping[str, object],
    *,
    retain_data_identity: bool,
    copy_typed_declarations: bool = False,
) -> dict[str, object]:
    """Copy descriptor metadata while optionally preserving resource data."""
    return {
        key: (
            value
            if key == "data" and retain_data_identity
            else value
            if not copy_typed_declarations and isinstance(value, (TypeSpec, TableDialect))
            else deepcopy(value)
        )
        for key, value in raw.items()
    }


def _validate_schema_storage(
    value: object,
    *,
    location: InvariantLocation,
) -> None:
    if value is None or isinstance(value, TypeSpec):
        return
    if isinstance(value, str) and value:
        return
    if isinstance(value, Mapping):
        parse_foreign_keys_at(value, location=location.child("schema"))
        return
    raise _structure_at(
        location,
        ".schema",
        value,
        "schema mapping, reference string, or TypeSpec",
    )


def _validate_dialect_storage(
    value: object,
    *,
    location: InvariantLocation,
) -> None:
    if value is None or isinstance(value, TableDialect):
        return
    if isinstance(value, str) and value:
        return
    if isinstance(value, Mapping):
        return
    raise _structure_at(
        location,
        ".dialect",
        value,
        "dialect mapping, reference string, or TableDialect",
    )


def _prepare_resource_input(
    value: Mapping[str, object] | DataResource,
    *,
    location: InvariantLocation,
    copy_typed_declarations: bool = False,
) -> dict[str, object]:
    raw = _resource_public_values(value)
    marker_values = _marker_values(raw)
    _validate_resource_profile_input(marker_values, location=location)
    reject_v1_markers_at(marker_values, descriptor_kind="resource", location=location)
    validate_resource_source_shape(marker_values, location=location)
    _validate_schema_storage(marker_values.get("schema"), location=location)
    _validate_dialect_storage(marker_values.get("dialect"), location=location)
    return _owned_resource_values(
        _capture_resource_values(raw),
        retain_data_identity=True,
        copy_typed_declarations=copy_typed_declarations,
    )

def _normalize_resource_update_names(
    update: Mapping[str, object],
) -> dict[str, object]:
    return {
        _RESOURCE_ALIASES.get(key, key): value
        for key, value in update.items()
    }



@dataclass(frozen=True)
class _ValidatedSchemaDeclaration:
    value: Mapping[str, object] | TypeSpec | None
    foreign_keys: tuple[ForeignKey, ...]


class DataResource(BaseModel):
    """Frictionless Data Resource — wraps a TypeSpec with resource-level metadata."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        protected_namespaces=(),
        populate_by_name=True,
    )

    name: str
    path: Optional[str | list[str]] = None
    data: Optional[Any] = None
    type: Optional[str] = None
    dialect: dict[str, Any] | str | TableDialect | None = None
    # 'schema' shadows BaseModel.schema() — use table_schema internally, alias "schema"
    table_schema: dict[str, Any] | str | TypeSpec | None = Field(
        default=None,
        alias="schema",
    )
    schema_url: Optional[str] = Field(default=None, alias="$schema")
    homepage: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None
    mediatype: Optional[str] = None
    encoding: Optional[str] = None
    # 'bytes' is a Python builtin — use bytes_ internally, alias "bytes"
    bytes_: Optional[int] = Field(default=None, alias="bytes")
    hash: Optional[str] = None
    sources: Optional[list[dict[str, Any]]] = None
    licenses: Optional[list[dict[str, Any]]] = None
    extras: dict[str, Any] = Field(default_factory=dict)

    _invariant_location: InvariantLocation = PrivateAttr(
        default_factory=lambda: InvariantLocation("$")
    )
    _descriptor_context: DescriptorContext = PrivateAttr(
        default_factory=_default_descriptor_context
    )
    _package_resource_names: frozenset[str] = PrivateAttr(default_factory=frozenset)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "name" and "name" in self.__dict__:
            raise TypeError("DataResource.name is immutable after construction")
        super().__setattr__(name, value)

    def __init__(self, **data: Any) -> None:
        resource_name = data.get("name") if isinstance(data.get("name"), str) else None
        location = InvariantLocation("$", resource_name)
        prepared = _prepare_resource_input(data, location=location)
        try:
            super().__init__(**prepared)
        except ValidationError as exc:
            raise pydantic_structure_error(
                exc,
                descriptor_kind="resource",
                base_path="$",
                resource_name=resource_name,
                reference=None,
                aliases=_RESOURCE_ALIASES,
                required_forms=_RESOURCE_REQUIRED_FORMS,
            ) from exc
        self._invariant_location = location
        self._package_resource_names = frozenset()

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "DataResource":
        raw = (
            _resource_public_values(obj)
            if isinstance(obj, cls)
            else dict(obj)
            if isinstance(obj, Mapping)
            else None
        )
        resource_name: str | None = None
        if isinstance(raw, Mapping):
            candidate_name = raw.get("name")
            if isinstance(candidate_name, str):
                resource_name = candidate_name
        if raw is not None:
            location = InvariantLocation("$", resource_name)
            obj = _prepare_resource_input(raw, location=location)
        try:
            result = super().model_validate(obj, **kwargs)
        except ValidationError as exc:
            errors = exc.errors()
            nested_error = (
                errors[0].get("ctx", {}).get("error")
                if errors and isinstance(errors[0], Mapping)
                else None
            )
            if isinstance(nested_error, InvalidDescriptorStructure):
                raise nested_error from exc
            raise pydantic_structure_error(
                exc,
                descriptor_kind="resource",
                base_path="$",
                resource_name=resource_name,
                reference=None,
                aliases=_RESOURCE_ALIASES,
                required_forms=_RESOURCE_REQUIRED_FORMS,
            ) from exc
        result._invariant_location = InvariantLocation("$", resource_name)
        result._descriptor_context = _default_descriptor_context()
        result._package_resource_names = frozenset()
        return result

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        **kwargs: Any,
    ) -> "DataResource":
        raw = _parse_descriptor_json_input(json_data, descriptor_kind="resource")
        if not isinstance(raw, Mapping):
            raise InvalidDescriptorStructure(
                "resource descriptor must be a mapping",
                descriptor_kind="resource",
                descriptor_path="$",
                rejected_value=raw,
                required_form="resource mapping",
            )
        resource_name = raw.get("name") if isinstance(raw.get("name"), str) else None
        location = InvariantLocation("$", resource_name)
        _prepare_resource_input(raw, location=location)
        try:
            result = super().model_validate_json(json_data, **kwargs)
        except ValidationError as exc:
            errors = exc.errors()
            nested_error = (
                errors[0].get("ctx", {}).get("error")
                if errors and isinstance(errors[0], Mapping)
                else None
            )
            if isinstance(nested_error, InvalidDescriptorStructure):
                raise nested_error from exc
            raise pydantic_structure_error(
                exc,
                descriptor_kind="resource",
                base_path="$",
                resource_name=resource_name,
                reference=None,
                aliases=_RESOURCE_ALIASES,
                required_forms=_RESOURCE_REQUIRED_FORMS,
            ) from exc
        result._invariant_location = location
        result._descriptor_context = _default_descriptor_context()
        result._package_resource_names = frozenset()
        return result

    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> DataResource:
        if deep:
            raise ValueError("Mountainash model_copy does not support deep=True")
        values = _resource_public_values(self)
        if update:
            values.update(_normalize_resource_update_names(update))
        values = _owned_resource_values(
            values,
            retain_data_identity=True,
            copy_typed_declarations=True,
        )
        return type(self).model_validate(values)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DataResource):
            return self.model_dump() == other.model_dump()
        return super().__eq__(other)
    @property
    def effective_sources(self) -> list[dict[str, Any]]:
        """Return independently owned resource or package source metadata."""
        source_values = (
            self.sources
            if self.sources is not None
            else tuple(
                dict(source) for source in self._descriptor_context.package_sources
            )
        )
        return deepcopy(list(source_values))


    def to_descriptor(self) -> dict[str, Any]:
        from mountainash.typespec.frictionless_codec import _encode_resource_preserve

        return _encode_resource_preserve(self)

    def _validated_schema_declaration(self) -> _ValidatedSchemaDeclaration:
        source = self.table_schema
        if source is None:
            return _ValidatedSchemaDeclaration(None, ())

        source_location = self._invariant_location.child("schema")
        if isinstance(source, TypeSpec):
            value: Mapping[str, object] | TypeSpec = source
            foreign_keys = tuple(source.foreign_keys or ())
            policy_location = source_location
        else:
            from mountainash.typespec.frictionless_resolution import (
                resolve_descriptor_mapping,
            )

            value = resolve_descriptor_mapping(
                source,
                context=self._descriptor_context,
                expected_kind=DescriptorKind.SCHEMA,
                location=source_location,
            )
            policy_location = (
                InvariantLocation("$", self.name, source)
                if isinstance(source, str)
                else source_location
            )
            foreign_keys = parse_foreign_keys_at(value, location=policy_location)

        validate_foreign_key_targets(
            foreign_keys,
            child_name=self.name,
            resource_names=self._package_resource_names,
            location=policy_location,
        )
        return _ValidatedSchemaDeclaration(value, foreign_keys)

    def _validated_foreign_keys(self) -> tuple[ForeignKey, ...]:
        return self._validated_schema_declaration().foreign_keys

    def to_typespec(self) -> TypeSpec | None:
        declaration = self._validated_schema_declaration()
        if declaration.value is None:
            return None
        if isinstance(declaration.value, TypeSpec):
            return declaration.value

        from mountainash.typespec.frictionless import typespec_from_frictionless

        source = self.table_schema
        source_location = self._invariant_location.child("schema")
        raw = declaration.value
        try:
            return typespec_from_frictionless(raw)
        except InvalidDescriptorStructure as exc:
            if not isinstance(source, str):
                raise
            raise DescriptorReferenceInvalid(
                "resolved schema has an invalid structure",
                descriptor_kind=DescriptorKind.SCHEMA.value,
                descriptor_path=source_location.descriptor_path,
                resource_name=self.name,
                reference=source,
                expected_kind=DescriptorKind.SCHEMA.value,
                rejected_value=exc.rejected_value,
                required_form=exc.required_form,
            ) from exc
        except TypeSpecError:
            # Typed structural errors (field/type/key shape, field-match) pass
            # through unchanged — never wrapped as descriptor errors.
            raise
        except DescriptorError:
            raise
        except Exception as exc:
            error_type = (
                DescriptorReferenceInvalid
                if isinstance(source, str)
                else InvalidDescriptorStructure
            )
            raise error_type(
                "schema mapping could not be converted",
                descriptor_kind=DescriptorKind.SCHEMA.value,
                descriptor_path=source_location.descriptor_path,
                resource_name=self.name,
                rejected_value=raw,
                required_form="valid Table Schema mapping",
            ) from exc

    def to_dialect(self) -> TableDialect | None:
        if self.dialect is None:
            return None
        if isinstance(self.dialect, TableDialect):
            return self.dialect
        from mountainash.typespec.frictionless_codec import validate_dialect_family
        from mountainash.typespec.frictionless_resolution import (
            resolve_descriptor_mapping,
        )

        source = self.dialect
        source_location = self._invariant_location.child("dialect")
        raw = resolve_descriptor_mapping(
            source,
            context=self._descriptor_context,
            expected_kind=DescriptorKind.DIALECT,
            location=source_location,
        )
        try:
            validate_dialect_family(raw, resource_format=self.format)
            return TableDialect.from_descriptor(raw)
        except DescriptorError:
            raise
        except Exception as exc:
            error_type = (
                DescriptorReferenceInvalid
                if isinstance(source, str)
                else InvalidDescriptorStructure
            )
            raise error_type(
                "dialect mapping could not be converted",
                descriptor_kind=DescriptorKind.DIALECT.value,
                descriptor_path=source_location.descriptor_path,
                resource_name=self.name,
                rejected_value=raw,
                required_form="valid Table Dialect mapping",
            ) from exc

    def to_contract(self, *, name: Optional[str] = None) -> Any:
        spec = self.to_typespec()
        if spec is None:
            raise ValueError(
                f"DataResource {self.name!r} has no table_schema — cannot build a contract"
            )
        return spec.to_contract(name=name)


def _dag_constraint_edge(
    resource: DataResource,
    foreign_key: ForeignKey,
    *,
    index: int,
    relation_names: frozenset[str],
) -> tuple[str, str]:
    """Return the tabular DAG edge for one validated foreign key.

    Package validation guarantees that an explicit target names a package
    resource.  DAG extraction adds the stronger requirement that both
    endpoints are tabular relations rather than assets.
    """
    child = resource.name
    target = foreign_key.reference.resource or child
    schema_reference = (
        resource.table_schema
        if isinstance(resource.table_schema, str)
        else resource._invariant_location.reference
    )
    if child not in relation_names:
        raise InvalidDescriptorRelationship(
            "foreign key between tabular package resources",
            descriptor_kind="schema",
            descriptor_path=(
                f"{resource._invariant_location.descriptor_path}"
                f".schema.foreignKeys[{index}]"
            ),
            resource_name=child,
            reference=schema_reference,
            rejected_value=child,
            required_form="foreign key between tabular package resources",
        )
    if target not in relation_names:
        raise InvalidDescriptorRelationship(
            "foreign key between tabular package resources",
            descriptor_kind="schema",
            descriptor_path=(
                f"{resource._invariant_location.descriptor_path}"
                f".schema.foreignKeys[{index}].reference.resource"
            ),
            resource_name=child,
            reference=schema_reference,
            rejected_value=target,
            required_form="foreign key between tabular package resources",
        )
    return target, child


def _copy_resource_for_package(
    value: Mapping[str, object] | DataResource,
    *,
    location: InvariantLocation,
) -> DataResource:
    raw = _prepare_resource_input(
        value,
        location=location,
        copy_typed_declarations=True,
    )
    resource = DataResource.model_validate(raw)
    resource._invariant_location = location
    return resource


def _resource_name(value: Mapping[str, object] | DataResource) -> str | None:
    if isinstance(value, DataResource):
        return value.name
    name = value.get("name")
    return name if isinstance(name, str) else None


def _scan_package_markers(raw: Mapping[str, object]) -> None:
    package_values = _marker_values(raw)
    reject_v1_markers_at(
        package_values,
        descriptor_kind="package",
        location=InvariantLocation("$"),
    )
    resources = package_values.get("resources")
    if not isinstance(resources, Sequence) or isinstance(resources, (str, bytes, bytearray)):
        return
    for index, resource in enumerate(resources):
        if not isinstance(resource, (Mapping, DataResource)):
            continue
        resource_values = _marker_values(_resource_public_values(resource))
        location = InvariantLocation(
            f"$.resources[{index}]",
            _resource_name(resource),
        )
        reject_v1_markers_at(
            resource_values,
            descriptor_kind="resource",
            location=location,
        )
        schema = resource_values.get("schema")
        if isinstance(schema, Mapping):
            reject_v1_markers_at(
                schema,
                descriptor_kind="schema",
                location=location.child("schema"),
            )
        dialect = resource_values.get("dialect")
        if isinstance(dialect, Mapping):
            reject_v1_markers_at(
                dialect,
                descriptor_kind="dialect",
                location=location.child("dialect"),
            )


def _validate_package_resource_container(raw: Mapping[str, object]) -> Sequence[object]:
    if "resources" not in raw:
        raise InvalidDescriptorStructure(
            "package must declare resources",
            descriptor_kind="package",
            descriptor_path="$.resources",
            rejected_value=None,
            required_form="non-empty resource sequence",
        )
    resources = raw["resources"]
    if not isinstance(resources, Sequence) or isinstance(resources, (str, bytes, bytearray)):
        raise InvalidDescriptorStructure(
            "package resources must be a resource sequence",
            descriptor_kind="package",
            descriptor_path="$.resources",
            rejected_value=resources,
            required_form="resource sequence",
        )
    if not resources:
        raise InvalidDescriptorStructure(
            "package resources must contain at least one resource",
            descriptor_kind="package",
            descriptor_path="$.resources",
            rejected_value=resources,
            required_form="non-empty resource sequence",
        )
    return resources


def _validated_package_resource_values(
    values: Sequence[object],
) -> list[Mapping[str, object] | DataResource]:
    """Narrow validated package entries before resource finalization."""
    typed_values: list[Mapping[str, object] | DataResource] = []
    for index, value in enumerate(values):
        if not isinstance(value, (Mapping, DataResource)):
            location = InvariantLocation(f"$.resources[{index}]")
            raise InvalidDescriptorStructure(
                "resource must be a mapping",
                descriptor_kind="resource",
                descriptor_path=location.descriptor_path,
                rejected_value=value,
                required_form="resource mapping",
            )
        typed_values.append(value)
    return typed_values


def _validate_package_metadata(raw: Mapping[str, object]) -> None:
    from mountainash.typespec.frictionless_codec import (
        _CREATED_ADAPTER,
        _ContributorDescriptor,
        _LicenseDescriptor,
        _SourceDescriptor,
        _ensure_string,
        _validate_metadata_models,
    )

    _ensure_string(raw, "$schema", "$", kind="package")
    for key in ("name", "id", "title", "description", "homepage", "version", "image"):
        _ensure_string(raw, key, "$", kind="package")
    if "created" in raw:
        created = raw["created"]
        if not isinstance(created, str):
            raise _structure_at(
                InvariantLocation("$"),
                ".created",
                created,
                "RFC 3339 date-time string",
                descriptor_kind="package",
            )
        try:
            _CREATED_ADAPTER.validate_python(created)
        except ValidationError as exc:
            raise _structure_at(
                InvariantLocation("$"),
                ".created",
                created,
                "RFC 3339 date-time string",
                descriptor_kind="package",
            ) from exc
    if "keywords" in raw:
        keywords = raw["keywords"]
        if (
            not isinstance(keywords, list)
            or not keywords
            or any(not isinstance(item, str) for item in keywords)
        ):
            raise _structure_at(
                InvariantLocation("$"),
                ".keywords",
                keywords,
                "non-empty list of strings",
                descriptor_kind="package",
            )
    for key, model in (
        ("contributors", _ContributorDescriptor),
        ("licenses", _LicenseDescriptor),
        ("sources", _SourceDescriptor),
    ):
        if key in raw:
            _validate_metadata_models(
                raw[key],
                path=f"$.{key}",
                model=cast(type[BaseModel], model),
                kind="package",
            )


def _validate_package_resource_metadata(
    value: Mapping[str, object] | DataResource,
    *,
    location: InvariantLocation,
) -> None:
    from mountainash.typespec.frictionless_codec import (
        V2_HASH_PATTERN,
        _LicenseDescriptor,
        _SourceDescriptor,
        _ensure_string,
        _validate_dialect,
        _validate_metadata_models,
        _validate_schema,
    )

    raw = _resource_public_values(value)
    name = _resource_name(value)
    for key in ("title", "description", "homepage", "format", "mediatype", "encoding", "hash"):
        _ensure_string(raw, key, location.descriptor_path, kind="resource", resource_name=name)
    _ensure_string(raw, "$schema", location.descriptor_path, kind="resource", resource_name=name)
    if "bytes" in raw and (
        isinstance(raw["bytes"], bool) or not isinstance(raw["bytes"], int)
    ):
        raise _structure_at(
            location,
            ".bytes",
            raw["bytes"],
            "integer",
        )
    if "hash" in raw and (
        not isinstance(raw["hash"], str)
        or V2_HASH_PATTERN.fullmatch(raw["hash"]) is None
    ):
        raise _structure_at(location, ".hash", raw["hash"], "v2 hash string")
    for key, model in (
        ("licenses", _LicenseDescriptor),
        ("sources", _SourceDescriptor),
    ):
        if key in raw:
            _validate_metadata_models(
                raw[key],
                path=f"{location.descriptor_path}.{key}",
                model=model,
                kind="resource",
                resource_name=name,
            )
    schema = raw.get("schema")
    if isinstance(schema, Mapping):
        _validate_schema(
            schema,
            path=f"{location.descriptor_path}.schema",
            resource_name=name,
        )
    dialect = raw.get("dialect")
    if isinstance(dialect, Mapping):
        _validate_dialect(
            dialect,
            path=f"{location.descriptor_path}.dialect",
            resource_name=name,
        )


def _validate_unique_resource_names(
    resources: Sequence[DataResource],
) -> frozenset[str]:
    names: set[str] = set()
    for resource in resources:
        if resource.name in names:
            location = resource._invariant_location
            raise InvalidDescriptorStructure(
                "duplicate resource name",
                descriptor_kind="resource",
                descriptor_path=f"{location.descriptor_path}.name",
                resource_name=resource.name,
                rejected_value=resource.name,
                required_form="unique resource name",
            )
        names.add(resource.name)
    return frozenset(names)


def _bind_resource(
    resource: DataResource,
    *,
    context: DescriptorContext,
    resource_names: frozenset[str],
) -> None:
    resource._descriptor_context = context
    resource._package_resource_names = resource_names


def _finalize_package_resources(
    values: Sequence[Mapping[str, object] | DataResource],
    *,
    context: DescriptorContext,
) -> tuple[DataResource, ...]:
    owned: list[DataResource] = []
    for index, value in enumerate(values):
        location = InvariantLocation(
            f"$.resources[{index}]",
            _resource_name(value) if isinstance(value, (Mapping, DataResource)) else None,
        )
        if not isinstance(value, (Mapping, DataResource)):
            raise InvalidDescriptorStructure(
                "resource must be a mapping",
                descriptor_kind="resource",
                descriptor_path=location.descriptor_path,
                rejected_value=value,
                required_form="resource mapping",
            )
        _validate_package_resource_metadata(value, location=location)
        owned.append(_copy_resource_for_package(value, location=location))
    owned_tuple = tuple(owned)
    resource_names = _validate_unique_resource_names(owned_tuple)
    for resource in owned_tuple:
        _bind_resource(
            resource,
            context=context,
            resource_names=resource_names,
        )
    for resource in owned_tuple:
        # Referenced schemas remain lazy; inline and authored declarations
        # validate their relationship targets after package context binding.
        if not isinstance(resource.table_schema, str):
            resource._validated_schema_declaration()
    return owned_tuple


def _package_public_values(package: DataPackage) -> dict[str, object]:
    values: dict[str, object] = {}
    for field_name, field in type(package).model_fields.items():
        alias = field.alias or field_name
        value = getattr(package, field_name)
        if field_name == "resources":
            values[alias] = tuple(value)
        elif value is not None:
            values[alias] = deepcopy(value)
    return values

def _normalize_package_update_names(
    update: Mapping[str, object],
) -> dict[str, object]:
    return {
        _PACKAGE_ALIASES.get(key, key): value
        for key, value in update.items()
    }


def _copy_context_for_package(
    context: DescriptorContext,
    package_sources: object,
) -> DescriptorContext:
    source_values = context.package_sources if package_sources is None else package_sources
    if not isinstance(source_values, Sequence) or isinstance(
        source_values, (str, bytes, bytearray)
    ):
        source_values = ()
    return replace(
        context,
        package_sources=tuple(
            deepcopy(dict(source))
            for source in source_values
            if isinstance(source, Mapping)
        ),
    )


def _prepare_package_input(
    value: Mapping[str, object] | DataPackage,
    *,
    context: DescriptorContext,
) -> tuple[dict[str, object], DescriptorContext]:
    if isinstance(value, DataPackage):
        raw = _package_public_values(value)
    elif isinstance(value, Mapping):
        raw = dict(value)
    else:
        raise InvalidDescriptorStructure(
            "package input must be a mapping or DataPackage instance",
            descriptor_kind="package",
            descriptor_path="$",
            rejected_value=value,
            required_form="mapping or DataPackage instance",
        )
    for field_name, alias in _PACKAGE_ALIASES.items():
        if field_name in raw:
            if alias not in raw:
                raw[alias] = raw[field_name]
            del raw[field_name]
    _scan_package_markers(raw)
    resources = _validate_package_resource_container(raw)
    _validate_package_metadata(raw)
    for index, resource in enumerate(resources):
        if isinstance(resource, (Mapping, DataResource)):
            _validate_package_resource_metadata(
                resource,
                location=InvariantLocation(
                    f"$.resources[{index}]",
                    _resource_name(resource),
                ),
            )
    typed_resources = _validated_package_resource_values(resources)
    final_context = _copy_context_for_package(context, raw.get("sources"))
    prepared = _capture_package_values(raw)
    prepared["resources"] = _finalize_package_resources(
        typed_resources,
        context=final_context,
    )
    return prepared, final_context
def _package_validation_error(exc: ValidationError) -> InvalidDescriptorStructure:
    return pydantic_structure_error(
        exc,
        descriptor_kind="package",
        base_path="$",
        resource_name=None,
        reference=None,
        aliases=_PACKAGE_ALIASES,
        required_forms=_PACKAGE_REQUIRED_FORMS,
    )


class DataPackage(BaseModel):
    """Frictionless Data Package — top-level container of DataResources."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        protected_namespaces=(),
        populate_by_name=True,
    )

    resources: tuple[DataResource, ...]
    name: Optional[str] = None
    id: Optional[str] = None
    licenses: Optional[list[dict[str, Any]]] = None
    dollar_schema: Optional[str] = Field(default=None, alias="$schema")
    title: Optional[str] = None
    description: Optional[str] = None
    homepage: Optional[str] = None
    version: Optional[str] = None
    created: Optional[str] = None
    keywords: Optional[list[str]] = None
    contributors: Optional[list[dict[str, Any]]] = None
    sources: Optional[list[dict[str, Any]]] = None
    image: Optional[str] = None
    extras: dict[str, Any] = Field(default_factory=dict)
    _descriptor_context: DescriptorContext = PrivateAttr(
        default_factory=_default_descriptor_context
    )

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "resources" and "resources" in self.__dict__:
            raise TypeError("DataPackage.resources is immutable after construction")
        super().__setattr__(name, value)

    def __init__(self, **data: Any) -> None:
        prepared, context = _prepare_package_input(
            data,
            context=_default_descriptor_context(),
        )
        try:
            super().__init__(**prepared)
        except ValidationError as exc:
            raise _package_validation_error(exc) from exc
        self._descriptor_context = context

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DataPackage):
            return self.model_dump() == other.model_dump()
        return super().__eq__(other)

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "DataPackage":
        if not isinstance(obj, (Mapping, cls)):
            raise InvalidDescriptorStructure(
                "package input must be a mapping or DataPackage instance",
                descriptor_kind="package",
                descriptor_path="$",
                rejected_value=obj,
                required_form="mapping or DataPackage instance",
            )
        prepared, context = _prepare_package_input(
            obj,
            context=_default_descriptor_context(),
        )
        try:
            result = super().model_validate(prepared, **kwargs)
        except ValidationError as exc:
            raise _package_validation_error(exc) from exc
        result._descriptor_context = context
        return result

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        **kwargs: Any,
    ) -> "DataPackage":
        raw = require_package_mapping(
            _parse_descriptor_json_input(json_data, descriptor_kind="package")
        )
        prepared, context = _prepare_package_input(
            raw,
            context=_default_descriptor_context(),
        )
        try:
            result = super().model_validate(prepared, **kwargs)
        except ValidationError as exc:
            raise _package_validation_error(exc) from exc
        result._descriptor_context = context
        return result

    @classmethod
    def _from_owned_descriptor(
        cls,
        owned: Mapping[str, object],
        *,
        context: DescriptorContext,
    ) -> "DataPackage":
        return cls._from_owned_values(owned, context=context)

    @classmethod
    def _from_owned_values(
        cls,
        values: Mapping[str, object],
        *,
        context: DescriptorContext,
    ) -> "DataPackage":
        prepared, final_context = _prepare_package_input(values, context=context)
        package = cls.__new__(cls)
        try:
            BaseModel.__init__(package, **prepared)
        except ValidationError as exc:
            raise _package_validation_error(exc) from exc
        package._descriptor_context = final_context
        return package

    def model_copy(
        self,
        *,
        update: Mapping[str, object] | None = None,
        deep: bool = False,
    ) -> "DataPackage":
        if deep:
            raise ValueError("Mountainash model_copy does not support deep=True")
        values = _package_public_values(self)
        if update:
            values.update(_normalize_package_update_names(update))
        context = _copy_context_for_package(
            self._descriptor_context,
            values.get("sources"),
        )
        return type(self)._from_owned_values(values, context=context)

    @classmethod
    def from_descriptor(
        cls,
        raw: Mapping[str, Any],
        *,
        base_uri: str | Path | None = None,
        resolver: DescriptorResolver | None = None,
    ) -> DataPackage:
        from mountainash.typespec.frictionless_codec import decode_package_descriptor

        return decode_package_descriptor(raw, base_uri=base_uri, resolver=resolver)

    @classmethod
    def from_json(
        cls,
        text: str,
        *,
        base_uri: str | Path | None = None,
        resolver: DescriptorResolver | None = None,
    ) -> DataPackage:
        from mountainash.typespec.frictionless_codec import decode_package_json

        return decode_package_json(text, base_uri=base_uri, resolver=resolver)

    @classmethod
    def from_path(
        cls,
        path: str | Path,
        *,
        resolver: DescriptorResolver | None = None,
    ) -> DataPackage:
        from mountainash.typespec.frictionless_codec import decode_package_path

        return decode_package_path(path, resolver=resolver)

    def to_descriptor(self) -> dict[str, Any]:
        from mountainash.typespec.frictionless_codec import encode_package_descriptor

        return encode_package_descriptor(self, mode=DescriptorWriteMode.PRESERVE)

    def to_canonical_descriptor(self) -> dict[str, Any]:
        from mountainash.typespec.frictionless_codec import encode_package_descriptor

        return encode_package_descriptor(self, mode=DescriptorWriteMode.CANONICAL)

    def write(
        self,
        path: str | Path,
        *,
        mode: DescriptorWriteMode = DescriptorWriteMode.PRESERVE,
    ) -> None:
        import json
        from pathlib import Path
        from mountainash.typespec.frictionless_codec import encode_package_descriptor

        descriptor = encode_package_descriptor(self, mode=mode)
        Path(path).write_text(json.dumps(descriptor, indent=2), encoding="utf-8")

    def to_relation_dag(
        self,
        overrides: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Build a RelationDAG from this package's resources.

        Tabular resources become named relations wrapping a ResourceReadRelNode.
        Non-tabular resources become asset entries on the DAG. Foreign keys
        populate ``dag.constraint_edges`` (NOT ``dependency_edges``).

        The ``overrides`` mapping replaces a resource's data with an in-memory
        DataFrame, useful for testing or for substituting trusted local data.
        """
        from mountainash.core.resource_ref import ResourceRef
        from mountainash.relations.dag.dag import RelationDAG
        from mountainash.relations.dag.packaging import resource_to_relation
        import mountainash as ma

        overrides = overrides or {}
        dag = RelationDAG()

        for r in self.resources:
            ref = ResourceRef(r)
            if not ref.is_tabular:
                dag.assets[r.name] = ref
                continue
            if r.name in overrides:
                relation = ma.relation(overrides[r.name])
                spec = r.to_typespec()
                if spec is not None:
                    relation = relation.conform(spec)
                dag.add(r.name, relation)
            else:
                dag.add(r.name, resource_to_relation(r))

        relation_names = frozenset(dag.relations)
        for resource in self.resources:
            for index, foreign_key in enumerate(resource._validated_foreign_keys()):
                edge = _dag_constraint_edge(
                    resource,
                    foreign_key,
                    index=index,
                    relation_names=relation_names,
                )
                dag._record_constraint(edge, foreign_key)

        return dag
