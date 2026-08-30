"""ResourceReadRelNode — leaf node carrying a DataResource for storage-facade load."""
from __future__ import annotations

from enum import Enum
from typing import ClassVar, Optional

from pydantic import ConfigDict, Field

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)
from mountainash.typespec.datapackage import DataResource
from ..reln_base import RelationNode


class ResourceReadRelNode(RelationNode):
    """Leaf node holding a DataResource for deferred materialization.

    At visit time, the per-backend ``visit_resource_read_rel`` implementation
    invokes the storage facade and the format-specific reader to produce a
    backend-native object (Polars LazyFrame, Ibis Table, etc.).
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    _operation_key: ClassVar[Optional[Enum]] = RKEY_MOUNTAINASH_REL.READ_RESOURCE

    resource: DataResource
    provider_binding: object | str | None = Field(
        default=None,
        exclude=True,
        repr=False,
    )
    apply_schema_conform: bool = True
