"""RefRelNode — placeholder for dag.ref(name); resolved at visit time via ref_resolver."""
from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar, Optional

from pydantic import ConfigDict

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)

from ..reln_base import RelationNode


class RefRelNode(RelationNode):
    """Leaf node referencing another named relation in a RelationDAG.

    Cannot be compiled standalone — requires a UnifiedRelationVisitor instantiated
    with a ``ref_resolver`` callback (see RelationDAG.collect()).

    The output_schema field is intentionally typed Any so it accepts either a
    raw Frictionless schema dict or a TypeSpec, mirroring DataResource.table_schema.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    _operation_key: ClassVar[Optional[Enum]] = RKEY_MOUNTAINASH_REL.REF

    name: str
    output_schema: Optional[Any] = None
