"""Core visit handlers for extension relation nodes.

Registered lazily by RelationVisitRegistry._ensure_initialized().
"""
from __future__ import annotations

from typing import Any


def _visit_ref_rel(node: Any, visitor: Any) -> Any:
    if visitor.ref_resolver is None:
        from mountainash.relations.dag.errors import RelationDAGRequired
        raise RelationDAGRequired(
            f"RefRelNode({node.name!r}) cannot be compiled standalone — "
            "use RelationDAG.collect() or supply ref_resolver explicitly"
        )
    return visitor.ref_resolver(node.name)


def _visit_resource_read_rel(node: Any, visitor: Any) -> Any:
    out = visitor.backend.read_resource(node.resource)
    if node.resource.table_schema is not None:
        out = visitor.apply_conform(out, node.resource.table_schema)
    return out


def _visit_source_rel(node: Any, visitor: Any) -> Any:
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress
    df = PydataIngress.convert(node.data)
    return visitor.backend.read(df)


def _register_core_handlers() -> None:
    from .visit_registry import RelationVisitRegistry
    from ..relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
    from ..relation_nodes.extensions_mountainash.reln_ext_resource_read import ResourceReadRelNode
    from ..relation_nodes.extensions_mountainash.reln_ext_source import SourceRelNode

    RelationVisitRegistry._handlers[RefRelNode] = _visit_ref_rel
    RelationVisitRegistry._handlers[ResourceReadRelNode] = _visit_resource_read_rel
    RelationVisitRegistry._handlers[SourceRelNode] = _visit_source_rel
