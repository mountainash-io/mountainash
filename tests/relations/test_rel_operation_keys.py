"""RKEY enum structure (spec §3.4): uniform auto(), RKEY_ prefix, no warts."""
from __future__ import annotations

from enum import Enum


def test_substrait_rkey_members():
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_SUBSTRAIT_REL,
    )
    expected = {
        "READ", "PROJECT_SELECT", "PROJECT_WITH_COLUMNS", "PROJECT_DROP",
        "PROJECT_RENAME", "FILTER", "SORT", "FETCH", "FETCH_FROM_END",
        "JOIN", "JOIN_ASOF", "AGGREGATE", "DISTINCT",
        "UNION_ALL", "UNION_DISTINCT",
    }
    assert {m.name for m in RKEY_SUBSTRAIT_REL} == expected


def test_mountainash_rkey_members():
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        RKEY_MOUNTAINASH_REL,
    )
    expected = {
        "DROP_NULLS", "DROP_NANS", "WITH_ROW_INDEX", "EXPLODE", "SAMPLE",
        "UNPIVOT", "PIVOT", "TOP_K", "UNNEST",
        "SOURCE", "REF", "READ_RESOURCE", "CONFORM", "EMPTY_FRAME",
    }
    assert {m.name for m in RKEY_MOUNTAINASH_REL} == expected


def test_all_values_are_auto_not_strings():
    from mountainash.relations.core.relation_system.relation_keys import enums
    for cls_name in ("RKEY_SUBSTRAIT_REL", "RKEY_MOUNTAINASH_REL"):
        cls = getattr(enums, cls_name)
        assert issubclass(cls, Enum)
        assert all(isinstance(m.value, int) for m in cls), cls_name


def test_extension_uris_exist():
    from mountainash.relations.core.relation_system.relation_keys.enums import (
        MountainashRelExtension,
    )
    assert MountainashRelExtension.UTIL.startswith("file://extensions/")
    assert MountainashRelExtension.DAG.startswith("file://extensions/")
    assert MountainashRelExtension.CONFORM.startswith("file://extensions/")


import polars as pl

from mountainash.core.constants import (
    ExtensionRelOperation,
    JoinType,
    ProjectOperation,
    SetType,
)


def _read(df=None):
    from mountainash.relations.core.relation_nodes import ReadRelNode
    return ReadRelNode(dataframe=df if df is not None else pl.DataFrame({"a": [1]}))


class TestOperationKeyDerivation:
    def test_simple_classvar_nodes(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL as RS,
        )
        from mountainash.relations.core.relation_nodes import (
            FilterRelNode, SortRelNode,
        )
        assert _read().operation_key is RS.READ
        assert FilterRelNode(input=_read(), predicate="a").operation_key is RS.FILTER
        assert SortRelNode(input=_read(), sort_fields=[]).operation_key is RS.SORT

    def test_project_variants(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL as RS,
        )
        from mountainash.relations.core.relation_nodes import ProjectRelNode
        n = ProjectRelNode(input=_read(), expressions=["a"], operation=ProjectOperation.SELECT)
        assert n.operation_key is RS.PROJECT_SELECT
        n = ProjectRelNode(
            input=_read(), expressions=[], operation=ProjectOperation.RENAME,
            rename_mapping={"a": "b"},
        )
        assert n.operation_key is RS.PROJECT_RENAME

    def test_fetch_variants(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL as RS,
        )
        from mountainash.relations.core.relation_nodes import FetchRelNode
        assert FetchRelNode(input=_read(), count=3).operation_key is RS.FETCH
        assert FetchRelNode(input=_read(), count=3, from_end=True).operation_key is RS.FETCH_FROM_END

    def test_join_variants_and_by_field(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL as RS,
        )
        from mountainash.relations.core.relation_nodes import JoinRelNode
        j = JoinRelNode(left=_read(), right=_read(), join_type=JoinType.INNER, on=["a"])
        assert j.operation_key is RS.JOIN
        a = JoinRelNode(
            left=_read(), right=_read(), join_type=JoinType.ASOF, on=["a"], by=["g"],
        )
        assert a.operation_key is RS.JOIN_ASOF
        assert a.by == ["g"]

    def test_aggregate_vs_distinct(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL as RS,
        )
        from mountainash.relations.core.relation_nodes import AggregateRelNode
        assert AggregateRelNode(input=_read(), keys=["a"], measures=[]).operation_key is RS.DISTINCT
        assert AggregateRelNode(input=_read(), keys=["a"], measures=["m"]).operation_key is RS.AGGREGATE

    def test_set_variants(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_SUBSTRAIT_REL as RS,
        )
        from mountainash.relations.core.relation_nodes import SetRelNode
        assert SetRelNode(inputs=[_read()], set_type=SetType.UNION_ALL).operation_key is RS.UNION_ALL
        assert SetRelNode(inputs=[_read()], set_type=SetType.UNION_DISTINCT).operation_key is RS.UNION_DISTINCT

    def test_extension_ops_map_by_name(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL as RM,
        )
        from mountainash.relations.core.relation_nodes.extensions_mountainash import (
            ExtensionRelNode,
        )
        n = ExtensionRelNode(
            input=_read(), operation=ExtensionRelOperation.DROP_NULLS, options={}
        )
        assert n.operation_key is RM.DROP_NULLS

    def test_dedicated_extension_nodes(self):
        from mountainash.relations.core.relation_system.relation_keys.enums import (
            RKEY_MOUNTAINASH_REL as RM,
        )
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_ref import RefRelNode
        from mountainash.relations.core.relation_nodes.extensions_mountainash.reln_ext_source import SourceRelNode
        assert RefRelNode(name="x").operation_key is RM.REF
        # SourceRelNode requires detected_format; build via the public API path instead:
        import mountainash as ma
        rel = ma.relation([{"a": 1}])
        assert rel._node.operation_key is RM.SOURCE

    def test_base_default_is_none(self):
        from mountainash.relations.core.relation_nodes.reln_base import RelationNode

        class Rogue(RelationNode):
            # accept() is still abstract until Task 4's shim lands
            def accept(self, visitor):
                return visitor.visit(self)

        assert Rogue().operation_key is None
