from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import json
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError
from mountainash.typespec.descriptor_context import (
    DescriptorContext,
    DescriptorKind,
    DescriptorResolver,
    LocalDescriptorResolver,
)
from mountainash.typespec.spec import TypeSpec
from mountainash.typespec.errors import (
    DescriptorError,
    DescriptorReferenceInvalid,
    InvalidDescriptorStructure,
    TypeSpecError,
)
from mountainash.typespec.frictionless_invariants import (
    InvariantLocation,
    _PACKAGE_ALIASES,
    _PACKAGE_REQUIRED_FORMS,
    _RESOURCE_ALIASES,
    _RESOURCE_REQUIRED_FORMS,
    parse_descriptor_json,
    pydantic_structure_error,
    reject_typed_profile_at,
    reject_v1_markers_at,
    require_package_mapping,
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


def _validate_package_profile_input(value: Mapping[str, Any]) -> None:
    reject_v1_markers_at(
        value,
        descriptor_kind="package",
        location=InvariantLocation("$"),
    )
    resources = value.get("resources")
    if not isinstance(resources, list):
        return
    for index, resource in enumerate(resources):
        if not isinstance(resource, Mapping):
            continue
        location = InvariantLocation(
            f"$.resources[{index}]",
            resource.get("name") if isinstance(resource.get("name"), str) else None,
        )
        _validate_resource_profile_input(resource, location=location)


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

    _descriptor_context: DescriptorContext = PrivateAttr(
        default_factory=_default_descriptor_context
    )
    _package_resource_names: frozenset[str] = PrivateAttr(default_factory=frozenset)

    def __init__(self, **data: Any) -> None:
        location = InvariantLocation(
            "$",
            data.get("name") if isinstance(data.get("name"), str) else None,
        )
        _validate_resource_profile_input(data, location=location)
        validate_resource_source_shape(data, location=location)
        super().__init__(**data)

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> "DataResource":
        raw = (
            obj.model_dump(by_alias=True)
            if isinstance(obj, cls)
            else dict(obj)
            if isinstance(obj, Mapping)
            else None
        )
        resource_name = (
            raw.get("name") if isinstance(raw, Mapping) and isinstance(raw.get("name"), str) else None
        )
        if raw is not None:
            location = InvariantLocation("$", resource_name)
            _validate_resource_profile_input(raw, location=location)
            validate_resource_source_shape(raw, location=location)
        try:
            return super().model_validate(obj, **kwargs)
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

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        **kwargs: Any,
    ) -> "DataResource":
        raw = parse_descriptor_json(json_data, descriptor_kind="resource")
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
        _validate_resource_profile_input(raw, location=location)
        validate_resource_source_shape(raw, location=location)
        try:
            return super().model_validate_json(json_data, **kwargs)
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
            else self._descriptor_context.package_sources
        )
        return deepcopy(list(source_values))


    def to_descriptor(self) -> dict[str, Any]:
        from mountainash.typespec.frictionless_codec import _encode_resource_preserve

        return _encode_resource_preserve(self)

    def to_typespec(self) -> TypeSpec | None:
        if self.table_schema is None:
            return None
        if isinstance(self.table_schema, TypeSpec):
            return self.table_schema
        from mountainash.typespec.frictionless import typespec_from_frictionless
        from mountainash.typespec.frictionless_codec import (
            resolve_descriptor_mapping,
            validate_foreign_key_relationships,
        )

        source = self.table_schema
        raw = resolve_descriptor_mapping(
            source,
            context=self._descriptor_context,
            expected_kind=DescriptorKind.SCHEMA,
            descriptor_path="$.schema",
            resource_name=self.name,
        )
        try:
            validate_foreign_key_relationships(
                raw,
                resource_names=self._package_resource_names,
            )
            return typespec_from_frictionless(raw)
        except InvalidDescriptorStructure as exc:
            if not isinstance(source, str):
                raise
            raise DescriptorReferenceInvalid(
                "resolved schema has an invalid structure",
                descriptor_kind=DescriptorKind.SCHEMA.value,
                descriptor_path="$.schema",
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
                descriptor_path="$.schema",
                resource_name=self.name,
                rejected_value=raw,
                required_form="valid Table Schema mapping",
            ) from exc

    def to_dialect(self) -> TableDialect | None:
        if self.dialect is None:
            return None
        if isinstance(self.dialect, TableDialect):
            return self.dialect
        from mountainash.typespec.frictionless_codec import (
            resolve_descriptor_mapping,
            validate_dialect_family,
        )

        source = self.dialect
        raw = resolve_descriptor_mapping(
            source,
            context=self._descriptor_context,
            expected_kind=DescriptorKind.DIALECT,
            descriptor_path="$.dialect",
            resource_name=self.name,
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
                descriptor_path="$.dialect",
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




class DataPackage(BaseModel):
    """Frictionless Data Package — top-level container of DataResources."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        protected_namespaces=(),
        populate_by_name=True,
    )

    resources: list[DataResource]
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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, DataPackage):
            return self.model_dump() == other.model_dump()
        return super().__eq__(other)

    def model_post_init(self, _ctx: Any) -> None:
        if not self.resources:
            raise ValueError("DataPackage must have at least one resource")
        seen: set[str] = set()
        for r in self.resources:
            if r.name in seen:
                raise ValueError(f"duplicate resource name: {r.name!r}")
            seen.add(r.name)
        # FK references resolve to existing resource names (or None for a typed
        # self-reference — the canonical self-ref marker on ForeignKeyReference).
        valid = seen | {None}
        for r in self.resources:
            schema = r.table_schema  # DataResource attribute name (alias is "schema")
            if schema is None:
                continue
            for fk in (getattr(schema, "foreign_keys", None) or []):
                ref_resource = fk.reference.resource
                if ref_resource not in valid:
                    raise ValueError(
                        f"resource {r.name!r} foreignKey references unknown resource {ref_resource!r}"
                    )

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        **kwargs: Any,
    ) -> "DataPackage":
        # Task 5 will unify full package-content parity with codec/from_json.
        raw = require_package_mapping(parse_descriptor_json(json_data))
        _validate_package_profile_input(raw)
        if "resources" not in raw:
            raise InvalidDescriptorStructure(
                "package must declare resources",
                descriptor_kind="package",
                descriptor_path="$.resources",
                rejected_value=None,
                required_form="non-empty resource sequence",
            )
        resources = raw["resources"]
        if not isinstance(resources, list) or not resources:
            raise InvalidDescriptorStructure(
                "package resources must be a non-empty list",
                descriptor_kind="package",
                descriptor_path="$.resources",
                rejected_value=resources,
                required_form="non-empty resource sequence",
            )
        for index, resource in enumerate(resources):
            path = f"$.resources[{index}]"
            if not isinstance(resource, Mapping):
                raise InvalidDescriptorStructure(
                    "resource must be a mapping",
                    descriptor_kind="resource",
                    descriptor_path=path,
                    rejected_value=resource,
                    required_form="resource mapping",
                )
            resource_name = resource.get("name") if isinstance(resource.get("name"), str) else None
            location = InvariantLocation(path, resource_name)
            _validate_resource_profile_input(resource, location=location)
            validate_resource_source_shape(resource, location=location)
        try:
            return super().model_validate_json(json_data, **kwargs)
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

        # Constraint edges from foreignKeys (parsed straight out of the raw
        # schema dict — no need to round-trip through TypeSpec).
        valid_names = set(dag.relations.keys())
        for r in self.resources:
            schema = r.table_schema
            if not isinstance(schema, dict):
                continue
            for fk in schema.get("foreignKeys", []) or []:
                ref_resource = (fk.get("reference") or {}).get("resource", "")
                # Empty string means self-referencing; use the resource's own name
                target = ref_resource if ref_resource else r.name
                if target in valid_names and r.name in valid_names:
                    from mountainash.typespec.frictionless import foreign_key_from_dict

                    edge = (target, r.name)
                    dag.constraint_edges.add(edge)
                    # Preserve field-level FK detail beside the edge. For a
                    # pass-through resource this duplicates what its lossless
                    # table_schema already carries — benign and
                    # export-invisible (export never reads metadata for
                    # pass-through resources); it exists as the uniform FK
                    # store for validation / drift tooling.
                    structured = foreign_key_from_dict(fk)
                    bucket = dag.constraint_metadata.setdefault(edge, [])
                    if structured not in bucket:
                        bucket.append(structured)

        return dag
