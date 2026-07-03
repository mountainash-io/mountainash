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
