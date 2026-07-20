"""One reporting surface over every named known-gap set."""
from __future__ import annotations

from typing import Any

from mountainash.core.capabilities import KnownGap


def collect_all_gap_sets() -> dict[str, dict[Any, KnownGap]]:
    """Return all named known-gap sets without introducing import-time cycles."""
    import core.test_protocol_alignment as pa
    from expressions.argument_types import test_coverage_guard as cg
    import relations.test_rel_wiring_audit_registry as rw

    return {
        "expr.aspirational": pa.KNOWN_ASPIRATIONAL,
        "expr.aspirational_and_tested": pa.KNOWN_ASPIRATIONAL_AND_TESTED,
        "rel.aspirational": rw.KNOWN_ASPIRATIONAL,
        "argtypes.untested_argument": cg._KNOWN_UNTESTED_ARGUMENT_PARAMS,
        "argtypes.metadata_only": cg._KNOWN_METADATA_ONLY_TESTED_PARAMS,
        "argtypes.untested_option": cg._KNOWN_UNTESTED_OPTION_PARAMS,
        "argtypes.unwired_ops": cg._KNOWN_UNWIRED_TESTED_OPS,
        "argtypes.unresolved_params": cg._KNOWN_UNRESOLVED_TESTED_PARAMS,
        "argtypes.special_node_unwired_ops": cg._KNOWN_SPECIAL_NODE_UNWIRED_OPS,
        "argtypes.unresolved_param_gaps": cg._KNOWN_UNRESOLVED_TESTED_ARGUMENT_PARAM_GAPS,
        "argtypes.allowed_cross_category": cg._ALLOWED_CROSS_CATEGORY_TESTED_PARAMS,
    }
