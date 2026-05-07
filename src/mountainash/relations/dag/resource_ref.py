"""ResourceRef — uniform wrapper for tabular and non-tabular resources."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.typespec.datapackage import DataResource


_TABULAR_FORMATS: frozenset[str] = frozenset({
    "csv", "tsv", "json", "ndjson", "parquet", "jsonl",
})


class ResourceRef:
    """Uniform wrapper around a DataResource.

    All resources expose ``.read_bytes()`` (when not inline). Tabular resources
    additionally expose ``.relation()``, which wraps the resource in a
    ``ResourceReadRelNode`` so it can flow through the relation pipeline.
    """

    def __init__(self, resource: DataResource) -> None:
        self.resource = resource

    @property
    def is_tabular(self) -> bool:
        if self.resource.type == "table":
            return True
        if self.resource.format and self.resource.format.lower() in _TABULAR_FORMATS:
            return True
        # Heuristic: inline data with format=json is tabular
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
        from mountainash.core.io import is_remote, facade_read_bytes
        if is_remote(path):
            return facade_read_bytes(path)
        return Path(path).read_bytes()

    def relation(self) -> "Relation":
        if not self.is_tabular:
            raise ValueError(
                f"resource {self.resource.name!r} is not tabular"
            )
        from mountainash.relations.core.relation_api.relation import Relation
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ResourceReadRelNode,
        )
        node = ResourceReadRelNode(resource=self.resource)
        return Relation(node)
