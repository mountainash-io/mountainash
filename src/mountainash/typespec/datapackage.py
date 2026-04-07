"""Frictionless Data Package types — TableDialect, DataResource, DataPackage."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())

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
        from mountainash.typespec.frictionless import typespec_from_frictionless

        kwargs: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for k, v in raw.items():
            if k in _KNOWN_RESOURCE_FIELDS:
                kwargs[k] = v
            else:
                extras[k] = v
        if "dialect" in kwargs and isinstance(kwargs["dialect"], dict):
            kwargs["dialect"] = TableDialect.from_descriptor(kwargs["dialect"])
        if "schema" in kwargs and isinstance(kwargs["schema"], dict):
            kwargs["schema"] = typespec_from_frictionless(kwargs["schema"])
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
            out["schema"] = typespec_to_frictionless(self.table_schema)
        out.update(self.extras)
        return out
