"""Known coverage gaps register (spec 2026-08-07, §4.2).

Mirrors the KNOWN_DIVERGENCES pattern in divergences.py: one module, one
tuple. Ships empty; entries are added when a gap is consciously accepted
rather than fixed. Rendered in docs/reference/expression-coverage.md.
"""
from __future__ import annotations

from mountainash.core.capabilities.schema import GapKind, KnownGap

KNOWN_GAPS: tuple[KnownGap, ...] = (
    KnownGap(
        gap_kind=GapKind.OTHER,
        reason=(
            "ibis-sqlite's TimestampBucket has no compilation rule, so a "
            "multi-digit MA-wrapper duration string (e.g. dt.truncate('2d')) "
            "on ibis-sqlite raises a raw native OperationNotDefinedError "
            "rather than a clean BackendCapabilityError. A "
            "DURATION_MULTIPLIER-class fact for this would need a "
            "corresponding class-backed OptionCell, which the 4-fixture "
            "argument-type matrix cannot instantiate for ibis-sqlite (same "
            "structural limit as test_option_fact_integrity.py's "
            "_MATRIX_UNREACHABLE_DIALECT_FACTS) -- see backlog item 99."
        ),
        since="2026-08-16",
    ),
)
