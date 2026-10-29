"""Shared AST naming boundary for aggregate keys and measures."""

from __future__ import annotations

from mountainash.relations.core.projection_names import normalize_projection
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_SUBSTRAIT_REL


def normalize_aggregate(keys, measures) -> tuple[list, list]:
    """Normalize the combined output namespace without mutating expressions."""
    combined = normalize_projection([*keys, *measures], operation=RKEY_SUBSTRAIT_REL.AGGREGATE)
    return combined[:len(keys)], combined[len(keys):]
