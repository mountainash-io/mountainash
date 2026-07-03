"""Relation operation key enums (RKEYs).

The relations analog of the expressions FKEY enums (function-key-enums
principle, extended to relations by the relations-dispatch-parity spec §3.4).
Deliberately avoids the expressions-side warts: uniform auto() values,
uniform RKEY_ prefixes.

Namespace rule: an RKEY lives in the namespace of the protocol file that
owns its method. Substrait-namespace RKEYs without a direct Substrait
mapping (FETCH_FROM_END, JOIN_ASOF, PROJECT_DROP, PROJECT_RENAME) record
that via ``substrait_rel=None`` in their registry defs.
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Union


class MountainashRelExtension:
    """Extension URIs for mountainash relation operations (Substrait
    extension-relation serialization targets)."""

    UTIL = "file://extensions/relations/mountainash_util.yaml"
    DAG = "file://extensions/relations/mountainash_dag.yaml"
    CONFORM = "file://extensions/relations/mountainash_conform.yaml"


class RKEY_SUBSTRAIT_REL(Enum):
    """Substrait-namespace relation operations."""

    READ = auto()
    PROJECT_SELECT = auto()
    PROJECT_WITH_COLUMNS = auto()
    PROJECT_DROP = auto()
    PROJECT_RENAME = auto()
    FILTER = auto()
    SORT = auto()
    FETCH = auto()
    FETCH_FROM_END = auto()
    JOIN = auto()
    JOIN_ASOF = auto()
    AGGREGATE = auto()
    DISTINCT = auto()
    UNION_ALL = auto()
    UNION_DISTINCT = auto()


class RKEY_MOUNTAINASH_REL(Enum):
    """Mountainash extension relation operations.

    SOURCE and CONFORM are new members with no legacy discriminator-enum
    ancestor — those operations already used dedicated node classes.
    """

    DROP_NULLS = auto()
    DROP_NANS = auto()
    WITH_ROW_INDEX = auto()
    EXPLODE = auto()
    SAMPLE = auto()
    UNPIVOT = auto()
    PIVOT = auto()
    TOP_K = auto()
    UNNEST = auto()
    SOURCE = auto()
    REF = auto()
    READ_RESOURCE = auto()
    CONFORM = auto()
    EMPTY_FRAME = auto()


RelationKeyEnum = Union[RKEY_SUBSTRAIT_REL, RKEY_MOUNTAINASH_REL]

__all__ = [
    "MountainashRelExtension",
    "RKEY_SUBSTRAIT_REL",
    "RKEY_MOUNTAINASH_REL",
    "RelationKeyEnum",
]
