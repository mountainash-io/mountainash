"""All relation operation definitions (spec §3.5).

Substrait metadata columns: ``substrait_rel`` is the Substrait Rel message
name; ``None`` marks a convenience variant with no direct mapping
(PROJECT_DROP, PROJECT_RENAME) — a future serializer must lower or reject
those explicitly. ``substrait_op`` carries message-level variants (SetRel).
Extension ops carry mountainash URIs.
"""
from __future__ import annotations

from mountainash.relations.core.relation_nodes import (
    AggregateRelNode,
    FetchRelNode,
    FilterRelNode,
    JoinRelNode,
    ProjectRelNode,
    ReadRelNode,
    SetRelNode,
    SortRelNode,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    ExtensionRelNode,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_conform import (
    ConformRelNode,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import (
    RefRelNode,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_resource_read import (
    ResourceReadRelNode,
)
from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_source import (
    SourceRelNode,
)
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash import (
    MountainashExtensionRelationSystemProtocol as ExtProto,
)
from mountainash.relations.core.relation_protocols.relation_systems.substrait import (
    SubstraitAggregateRelationSystemProtocol,
    SubstraitFetchRelationSystemProtocol,
    SubstraitFilterRelationSystemProtocol,
    SubstraitJoinRelationSystemProtocol,
    SubstraitProjectRelationSystemProtocol,
    SubstraitReadRelationSystemProtocol,
    SubstraitSetRelationSystemProtocol,
    SubstraitSortRelationSystemProtocol,
)
from ..relation_keys.enums import (
    MountainashRelExtension,
    RKEY_MOUNTAINASH_REL as RM,
    RKEY_SUBSTRAIT_REL as RS,
)
from . import handlers
from .registry import ArgBinding, ArgKind, RelationOperationDef, RelationOperationRegistry

_IN = ArgBinding("input", ArgKind.INPUT)


def _ext(key, method):
    """ExtensionRelNode ops: (input) positional + **options spread."""
    return RelationOperationDef(
        operation_key=key,
        node_type=ExtensionRelNode,
        is_extension=True,
        extension_uri=MountainashRelExtension.UTIL,
        protocol_method=method,
        args=(_IN,),
        options_field="options",
    )


SUBSTRAIT_OPERATIONS = [
    RelationOperationDef(
        operation_key=RS.READ,
        node_type=ReadRelNode,
        substrait_rel="ReadRel",
        protocol_method=SubstraitReadRelationSystemProtocol.read,
        args=(ArgBinding("dataframe", ArgKind.LITERAL),),
    ),
    RelationOperationDef(
        operation_key=RS.PROJECT_SELECT,
        node_type=ProjectRelNode,
        substrait_rel="ProjectRel",
        protocol_method=SubstraitProjectRelationSystemProtocol.project_select,
        args=(_IN, ArgBinding("expressions", ArgKind.EXPRESSION_LIST)),
    ),
    RelationOperationDef(
        operation_key=RS.PROJECT_WITH_COLUMNS,
        node_type=ProjectRelNode,
        substrait_rel="ProjectRel",
        protocol_method=SubstraitProjectRelationSystemProtocol.project_with_columns,
        args=(_IN, ArgBinding("expressions", ArgKind.EXPRESSION_LIST)),
    ),
    RelationOperationDef(
        operation_key=RS.PROJECT_DROP,
        node_type=ProjectRelNode,
        substrait_rel=None,
        lowers_to="ProjectRel",
        protocol_method=SubstraitProjectRelationSystemProtocol.project_drop,
        args=(_IN, ArgBinding("expressions", ArgKind.EXPRESSION_LIST)),
    ),
    RelationOperationDef(
        operation_key=RS.PROJECT_RENAME,
        node_type=ProjectRelNode,
        substrait_rel=None,
        lowers_to="ProjectRel",
        protocol_method=SubstraitProjectRelationSystemProtocol.project_rename,
        args=(_IN, ArgBinding("rename_mapping", ArgKind.LITERAL)),
    ),
    RelationOperationDef(
        operation_key=RS.FILTER,
        node_type=FilterRelNode,
        substrait_rel="FilterRel",
        protocol_method=SubstraitFilterRelationSystemProtocol.filter,
        args=(_IN, ArgBinding("predicate", ArgKind.EXPRESSION)),
    ),
    RelationOperationDef(
        operation_key=RS.SORT,
        node_type=SortRelNode,
        substrait_rel="SortRel",
        protocol_method=SubstraitSortRelationSystemProtocol.sort,
        args=(_IN, ArgBinding("sort_fields", ArgKind.LITERAL)),
    ),
    RelationOperationDef(
        operation_key=RS.FETCH,
        node_type=FetchRelNode,
        substrait_rel="FetchRel",
        protocol_method=SubstraitFetchRelationSystemProtocol.fetch,
        args=(_IN, ArgBinding("offset", ArgKind.LITERAL), ArgBinding("count", ArgKind.LITERAL)),
    ),
    RelationOperationDef(
        operation_key=RS.JOIN,
        node_type=JoinRelNode,
        substrait_rel="JoinRel",
        protocol_method=SubstraitJoinRelationSystemProtocol.join,
        handler=handlers.visit_join,  # cross-backend right-side coercion
    ),
    RelationOperationDef(
        operation_key=RS.AGGREGATE,
        node_type=AggregateRelNode,
        substrait_rel="AggregateRel",
        protocol_method=SubstraitAggregateRelationSystemProtocol.aggregate,
        args=(
            _IN,
            ArgBinding("keys", ArgKind.EXPRESSION_LIST),
            ArgBinding("measures", ArgKind.EXPRESSION_LIST),
        ),
    ),
    RelationOperationDef(
        operation_key=RS.DISTINCT,
        node_type=AggregateRelNode,
        substrait_rel="AggregateRel",  # groupings-only AggregateRel
        protocol_method=SubstraitAggregateRelationSystemProtocol.distinct,
        args=(_IN, ArgBinding("keys", ArgKind.EXPRESSION_LIST)),
    ),
    RelationOperationDef(
        operation_key=RS.UNION_ALL,
        node_type=SetRelNode,
        substrait_rel="SetRel",
        substrait_op="SET_OP_UNION_ALL",
        protocol_method=SubstraitSetRelationSystemProtocol.union_all,
        args=(ArgBinding("inputs", ArgKind.INPUT_LIST),),
    ),
    RelationOperationDef(
        operation_key=RS.UNION_DISTINCT,
        node_type=SetRelNode,
        substrait_rel="SetRel",
        substrait_op="SET_OP_UNION_DISTINCT",
        protocol_method=SubstraitSetRelationSystemProtocol.union_distinct,
        args=(ArgBinding("inputs", ArgKind.INPUT_LIST),),
    ),
]

MOUNTAINASH_OPERATIONS = [
    _ext(RM.DROP_NULLS, ExtProto.drop_nulls),
    _ext(RM.DROP_NANS, ExtProto.drop_nans),
    _ext(RM.WITH_ROW_INDEX, ExtProto.with_row_index),
    _ext(RM.EXPLODE, ExtProto.explode),
    _ext(RM.SAMPLE, ExtProto.sample),
    _ext(RM.UNPIVOT, ExtProto.unpivot),
    _ext(RM.PIVOT, ExtProto.pivot),
    _ext(RM.TOP_K, ExtProto.top_k),
    _ext(RM.UNNEST, ExtProto.unnest),
    RelationOperationDef(
        operation_key=RM.SOURCE,
        node_type=SourceRelNode,
        is_extension=True,
        extension_uri=MountainashRelExtension.UTIL,
        handler=handlers.visit_source,
    ),
    RelationOperationDef(
        operation_key=RM.REF,
        node_type=RefRelNode,
        is_extension=True,
        extension_uri=MountainashRelExtension.DAG,
        handler=handlers.visit_ref,
    ),
    RelationOperationDef(
        operation_key=RM.READ_RESOURCE,
        node_type=ResourceReadRelNode,
        is_extension=True,
        extension_uri=MountainashRelExtension.DAG,
        protocol_method=ExtProto.read_resource,
        handler=handlers.visit_resource_read,
    ),
    RelationOperationDef(
        operation_key=RM.CONFORM,
        node_type=ConformRelNode,
        is_extension=True,
        extension_uri=MountainashRelExtension.CONFORM,
        handler=handlers.visit_conform,
    ),
    RelationOperationDef(
        operation_key=RM.FETCH_FROM_END,
        node_type=FetchRelNode,
        substrait_rel=None,
        is_extension=True,
        extension_uri=MountainashRelExtension.UTIL,
        protocol_method=SubstraitFetchRelationSystemProtocol.fetch_from_end,
        args=(_IN, ArgBinding("count", ArgKind.LITERAL)),
    ),
    RelationOperationDef(
        operation_key=RM.JOIN_ASOF,
        node_type=JoinRelNode,
        substrait_rel=None,
        is_extension=True,
        extension_uri=MountainashRelExtension.UTIL,
        protocol_method=SubstraitJoinRelationSystemProtocol.join_asof,
        handler=handlers.visit_join_asof,
    ),
    RelationOperationDef(
        # No node type: invoked from the conform path, not node dispatch.
        # Registry row exists so the wiring audit covers the protocol method.
        operation_key=RM.EMPTY_FRAME,
        node_type=None,
        is_extension=True,
        extension_uri=MountainashRelExtension.CONFORM,
        protocol_method=ExtProto.empty_frame,
    ),
]


def register_all_relation_operations() -> None:
    for d in SUBSTRAIT_OPERATIONS + MOUNTAINASH_OPERATIONS:
        RelationOperationRegistry.register(d)
