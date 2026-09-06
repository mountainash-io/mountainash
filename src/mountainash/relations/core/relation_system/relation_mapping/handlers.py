"""Handler-routed relation operations (spec §3.5).

Operations with genuine transformation logic — cross-backend right-side
coercion for joins, conform application, ref resolution, Python-data
ingress, resource reads — dispatch through these handlers, referenced from
their RelationOperationRegistry defs. Purely declarative operations do NOT
appear here; they bind through ArgBinding specs in definitions.py.
"""
from __future__ import annotations

from typing import Any

from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
    RKEY_SUBSTRAIT_REL,
)


def visit_join(node: Any, visitor: Any) -> Any:
    left = visitor.visit(node.left)
    right = visitor._visit_and_coerce_right(node.right, left)
    visitor._prepare_transport_lineage(node)
    return visitor._enrich_native_call(
        node, RKEY_SUBSTRAIT_REL.JOIN,
        lambda: visitor.backend.join(
            left, right,
            join_type=node.join_type,
            on=node.on, left_on=node.left_on,
            right_on=node.right_on, suffix=node.suffix,
        ),
    )


def visit_join_asof(node: Any, visitor: Any) -> Any:
    left = visitor.visit(node.left)
    right = visitor._visit_and_coerce_right(node.right, left)
    visitor._prepare_transport_lineage(node)
    return visitor._enrich_native_call(
        node, RKEY_MOUNTAINASH_REL.JOIN_ASOF,
        lambda: visitor.backend.join_asof(
            left, right,
            on=node.on[0] if node.on else node.left_on[0],
            by=node.by, strategy=node.strategy or "backward",
            tolerance=node.tolerance,
        ),
    )


def visit_ref(node: Any, visitor: Any) -> Any:
    if visitor.ref_resolver is None:
        from mountainash.relations.dag.errors import RelationDAGRequired
        raise RelationDAGRequired(
            f"RefRelNode({node.name!r}) cannot be compiled standalone — "
            "use RelationDAG.collect() or supply ref_resolver explicitly"
        )
    resolved = visitor.ref_resolver(node.name)
    from mountainash.relations.core.structured_lineage import StructuredPlanResolver

    if isinstance(visitor.ref_resolver, StructuredPlanResolver):
        plans = visitor.ref_resolver.structured_plans(node.name)
        visitor._ref_plans_by_node[id(node)] = plans
        # A bare RefRelNode has no wrapping parent to merge this via
        # _complete_transport_lineage (that mechanism only runs for nodes
        # dispatched through _dispatch); when this ref IS the compile's own
        # root -- e.g. dag.ref(name) used directly as a top-level target,
        # not chained under .filter()/.select() -- its own egress boundary
        # must see the referenced resource's transport state directly.
        visitor.structured_field_plans = plans
    return resolved


def visit_resource_read(node: Any, visitor: Any) -> Any:
    def _read_and_conform():
        out = visitor.backend.read_resource(node.resource)
        spec = node.resource.to_typespec()
        if spec is not None and node.apply_schema_conform:
            out = visitor.apply_conform(
                out,
                spec,
                empty_from_schema=True,
                resource_name=node.resource.name,
                owner_node=node,
            )
        return out
    return visitor._enrich_native_call(node, RKEY_MOUNTAINASH_REL.READ_RESOURCE, _read_and_conform)


def visit_source(node: Any, visitor: Any) -> Any:
    from mountainash.pydata.ingress.pydata_ingress import PydataIngress
    df = PydataIngress.convert(node.data)
    return visitor._enrich_native_call(
        node, RKEY_MOUNTAINASH_REL.SOURCE,
        lambda: visitor.backend.read(df),
    )


def visit_conform(node: Any, visitor: Any) -> Any:
    native = visitor.visit(node.input)
    return visitor._enrich_native_call(
        node,
        RKEY_MOUNTAINASH_REL.CONFORM,
        lambda: visitor.apply_conform(
            native,
            node.spec,
            contract=node.contract,
            owner_node=node,
            apply_value_transforms=node.apply_value_transforms,
        ),
    )
