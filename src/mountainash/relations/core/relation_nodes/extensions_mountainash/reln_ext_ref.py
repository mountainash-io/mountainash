"""RefRelNode — placeholder for dag.ref(name); resolved at visit time via ref_resolver."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import ConfigDict

from ..reln_base import RelationNode


class RefRelNode(RelationNode):
    """Leaf node referencing another named relation in a RelationDAG.

    Cannot be compiled standalone — requires a UnifiedRelationVisitor instantiated
    with a ``ref_resolver`` callback (see RelationDAG.collect()).

    The output_schema field is intentionally typed Any so it accepts either a
    raw Frictionless schema dict or a TypeSpec, mirroring DataResource.table_schema.
    """

    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)

    name: str
    output_schema: Optional[Any] = None

    def accept(self, visitor: Any) -> Any:
        return visitor.visit_ref_rel(self)
