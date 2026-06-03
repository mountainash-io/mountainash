"""ResourceRef - uniform wrapper for tabular and non-tabular resources."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.typespec.datapackage import DataResource


_TABULAR_FORMATS: frozenset[str] = frozenset({
    "csv",
    "tsv",
    "json",
    "ndjson",
    "parquet",
    "jsonl",
})


class ResourceRef:
    """Uniform wrapper around a DataResource."""

    def __init__(self, resource: DataResource) -> None:
        self.resource = resource

    @property
    def is_tabular(self) -> bool:
        if self.resource.type == "table":
            return True
        if self.resource.format and self.resource.format.lower() in _TABULAR_FORMATS:
            return True
        if self.resource.data is not None and self.resource.format == "json":
            return True
        return False

    def read_bytes(self) -> bytes:
        if self.resource.data is not None:
            raise ValueError(
                f"resource {self.resource.name!r} has inline data, not bytes"
            )
        path: Any = self.resource.path
        if isinstance(path, list):
            path = path[0]
        from mountainash.core.io import facade_read_bytes, is_remote

        if is_remote(path):
            return facade_read_bytes(path)
        return Path(path).read_bytes()

    def relation(self) -> Relation:
        from mountainash.relations.dag.packaging import resource_to_relation

        return resource_to_relation(self)
