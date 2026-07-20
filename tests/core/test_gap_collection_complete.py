"""Closed-by-default coverage for the shared KnownGap collection."""

import core.test_protocol_alignment as pa
from expressions.argument_types import test_coverage_guard as cg
import relations.test_rel_wiring_audit_registry as rw

from mountainash.core.capabilities import KnownGap
from tests.fixtures.gap_collection import collect_all_gap_sets


def test_every_core_known_gap_dict_is_collected():
    """Every module-level core KnownGap dict must be exposed for reporting."""
    gap_modules = (pa, cg, rw)
    discovered = {
        id(value): f"{module.__name__}.{name}"
        for module in gap_modules
        for name, value in vars(module).items()
        if isinstance(value, dict)
        and value
        and all(isinstance(gap, KnownGap) for gap in value.values())
    }
    collected = {id(gap_set) for gap_set in collect_all_gap_sets().values()}

    missing = set(discovered) - collected
    assert not missing, "\n".join(
        "core-KnownGap dict "
        f"{discovered[gap_id]} is not in collect_all_gap_sets() — add it "
        "(closed-by-default)"
        for gap_id in sorted(missing, key=discovered.__getitem__)
    )
