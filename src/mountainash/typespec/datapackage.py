from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from pathlib import Path
    # from upath import Path


"""Frictionless Data Package types — TableDialect, DataResource, DataPackage."""

class TableDialect(BaseModel):
    """Frictionless Table Dialect spec — closed schema, unknown keys are dropped."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

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
    case_sensitive_header: Optional[bool] = Field(default=None, alias="caseSensitiveHeader")
    csvddf_version: Optional[str] = Field(default=None, alias="csvddfVersion")

    @classmethod
    def from_descriptor(cls, raw: dict[str, Any]) -> "TableDialect":
        return cls.model_validate(raw)

    def to_descriptor(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_polars_read_csv_kwargs(self) -> dict[str, Any]:
        """Translate to ``polars.read_csv`` kwargs. Unsupported keys are dropped silently."""
        out: dict[str, Any] = {}
        if self.delimiter is not None:
            out["separator"] = self.delimiter
        if self.header is not None:
            out["has_header"] = self.header
        if self.quote_char is not None:
            out["quote_char"] = self.quote_char
        if self.escape_char is not None:
            out["eol_char"] = self.escape_char
        if self.comment_char is not None:
            out["comment_prefix"] = self.comment_char
        if self.null_sequence is not None:
            out["null_values"] = [self.null_sequence]
        return out


_KNOWN_RESOURCE_FIELDS = {
    "name", "path", "data", "type", "dialect", "schema",
    "title", "description", "format", "mediatype", "encoding",
    "bytes", "hash", "sources", "licenses",
}


class DataResource(BaseModel):
    """Frictionless Data Resource — wraps a TypeSpec with resource-level metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=(), populate_by_name=True)

    name: str
    path: Optional[str | list[str]] = None
    data: Optional[Any] = None
    type: Optional[str] = None
    dialect: Optional[TableDialect] = None
    # 'schema' shadows BaseModel.schema() — use table_schema internally, alias "schema"
    table_schema: Optional[Any] = Field(default=None, alias="schema")
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

    def model_post_init(self, _ctx: Any) -> None:
        has_path = self.path is not None
        has_data = self.data is not None
        if has_path == has_data:  # both true OR both false
            raise ValueError(
                f"DataResource '{self.name}' must declare exactly one of path or data"
            )

    @classmethod
    def from_descriptor(cls, raw: dict[str, Any]) -> "DataResource":
        kwargs: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for k, v in raw.items():
            if k in _KNOWN_RESOURCE_FIELDS:
                kwargs[k] = v
            else:
                extras[k] = v
        if "dialect" in kwargs and isinstance(kwargs["dialect"], dict):
            kwargs["dialect"] = TableDialect.from_descriptor(kwargs["dialect"])
        # Store schema as raw dict for lossless round-trip; callers that need
        # a TypeSpec can call typespec_from_frictionless(resource.table_schema).
        kwargs["extras"] = extras
        return cls.model_validate(kwargs)

    def to_descriptor(self) -> dict[str, Any]:
        from mountainash.typespec.frictionless import typespec_to_frictionless

        out: dict[str, Any] = {"name": self.name}
        if self.path is not None:
            out["path"] = self.path
        if self.data is not None:
            out["data"] = self.data
        for k in ("type", "title", "description", "format", "mediatype",
                  "encoding", "hash", "sources", "licenses"):
            v = getattr(self, k)
            if v is not None:
                out[k] = v
        if self.bytes_ is not None:
            out["bytes"] = self.bytes_
        if self.dialect is not None:
            d = self.dialect.to_descriptor()
            if d:
                out["dialect"] = d
        if self.table_schema is not None:
            if isinstance(self.table_schema, dict):
                out["schema"] = self.table_schema
            else:
                out["schema"] = typespec_to_frictionless(self.table_schema)
        out.update(self.extras)
        return out


_KNOWN_PACKAGE_FIELDS = {
    "name", "id", "licenses", "$schema", "profile",
    "title", "description", "homepage", "version", "created",
    "keywords", "contributors", "sources", "image", "resources",
}


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
    profile: Optional[str] = None
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

    def model_post_init(self, _ctx: Any) -> None:
        if not self.resources:
            raise ValueError("DataPackage must have at least one resource")
        seen: set[str] = set()
        for r in self.resources:
            if r.name in seen:
                raise ValueError(f"duplicate resource name: {r.name!r}")
            seen.add(r.name)
        # FK references resolve to existing resource names (or "" for self-ref)
        valid = seen | {""}
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
    def from_descriptor(cls, raw: "dict[str, Any] | str | Path") -> "DataPackage":
        from pathlib import Path
        import json
        if isinstance(raw, (str, Path)):
            p = Path(raw)
            if p.exists():
                raw = json.loads(p.read_text())
            else:
                raw = json.loads(str(raw))
        assert isinstance(raw, dict)
        kwargs: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for k, v in raw.items():
            if k in _KNOWN_PACKAGE_FIELDS:
                kwargs[k] = v
            else:
                extras[k] = v
        kwargs["resources"] = [DataResource.from_descriptor(r) for r in kwargs["resources"]]
        kwargs["extras"] = extras
        return cls.model_validate(kwargs)

    def to_descriptor(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.dollar_schema is not None:
            out["$schema"] = self.dollar_schema
        for k in ("name", "id", "title", "description", "homepage", "version",
                  "created", "keywords", "contributors", "sources", "image",
                  "licenses", "profile"):
            v = getattr(self, k)
            if v is not None:
                out[k] = v
        out["resources"] = [r.to_descriptor() for r in self.resources]
        out.update(self.extras)
        return out

    def write(self, path: "str | Path") -> None:
        from pathlib import Path
        import json
        Path(path).write_text(json.dumps(self.to_descriptor(), indent=2))

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
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )
        from mountainash.relations.dag.dag import RelationDAG
        from mountainash.relations.dag.resource_ref import ResourceRef
        import mountainash as ma

        overrides = overrides or {}
        dag = RelationDAG()

        for r in self.resources:
            ref = ResourceRef(r)
            if not ref.is_tabular:
                dag.assets[r.name] = ref
                continue
            if r.name in overrides:
                dag.add(r.name, ma.relation(overrides[r.name]))
            else:
                dag.add(r.name, Relation(ResourceReadRelNode(resource=r)))

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
                    dag.constraint_edges.add((target, r.name))

        return dag
