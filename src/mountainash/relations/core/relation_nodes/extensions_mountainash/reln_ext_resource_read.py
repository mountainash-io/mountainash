"""ResourceReadRelNode — leaf node carrying a DataResource for storage-facade load."""
from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from mountainash.typespec.datapackage import DataResource
from ..reln_base import RelationNode


class ResourceReadRelNode(RelationNode):
    """Leaf node holding a DataResource for deferred materialization.

    At visit time, the per-backend ``visit_resource_read_rel`` implementation
    invokes the storage facade and the format-specific reader to produce a
    backend-native object (Polars LazyFrame, Ibis Table, etc.).
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    resource: DataResource

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_resource_read_rel(self)
