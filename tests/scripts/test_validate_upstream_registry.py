"""Tests for scripts/validate_upstream_registry.py — cross-field agreement rule.

These tests pin down the closed-by-default (status, root_cause) allow-set
introduced for the legacy-test retirement assessment. The validator must:
- admit every per-field-legal combination enumerated in COMPATIBLE_STATUS_ROOT_CAUSE
  (the allow-set captures every pair the live registry has ever used);
- reject every other per-field-legal combination, including the illustrative
  contradiction (resolved_in_mountainash, by_design) that is NOT in the live data.
"""

from __future__ import annotations

from itertools import product

import pytest

from scripts.validate_upstream_registry import (
    COMPATIBLE_STATUS_ROOT_CAUSE,
    VALID_ROOT_CAUSES,
    VALID_STATUSES,
    validate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Full set of REQUIRED_FIELDS (per scripts/validate_upstream_registry.py:74-84).
# A complete, per-field-valid entry — overrides let us probe individual fields
# without accidentally triggering other per-field rules.
_REQUIRED_FIELDS_FULL = {
    "id": "IB-CAST-02",
    "project": "ibis",
    "category": "cast-semantics",
    "summary": "Upstream registry validator cross-field test fixture.",
    "root_cause": "upstream_bug",
    "affected_backends": ["ibis-duckdb"],
    "status": "open",
    "our_workaround": "none",
    "last_verified": "2026-08-05",
}


def _entry(**overrides) -> dict:
    """Build a complete per-field-valid entry, with selected fields overridden."""
    base = dict(_REQUIRED_FIELDS_FULL)
    base.update(overrides)
    return {"issues": [base]}


# ---------------------------------------------------------------------------
# Per-field ground truth (regression guard)
# ---------------------------------------------------------------------------

def test_per_field_valid_entry_returns_no_errors():
    """Baseline: a complete, per-field-valid entry with an allowlisted
    (status, root_cause) pair must produce no errors."""
    # (open, upstream_bug) is in the live data — the baseline of admission.
    errs = validate(_entry())
    assert errs == [], f"unexpected errors for valid entry: {errs}"


# ---------------------------------------------------------------------------
# Closed-by-default allow-set: rejection
# ---------------------------------------------------------------------------

def test_rejects_resolved_with_by_design():
    """Illustrative contradiction: status=resolved_in_mountainash but
    root_cause=by_design. 'Resolved' is about a fix; 'by design' is about
    acceptance — they are mutually exclusive. Error must mention both
    field names so the operator can locate the disagreement."""
    errs = validate(_entry(status="resolved_in_mountainash", root_cause="by_design"))
    cross_field = [e for e in errs if "root_cause" in e and "status" in e]
    assert cross_field, (
        f"expected a cross-field error mentioning both 'status' and 'root_cause' "
        f"for (resolved_in_mountainash, by_design); got: {errs}"
    )


def test_allow_set_rejects_per_field_legal_pairs_whitelist_not_blacklist():
    """Whitelist proof: every (status, root_cause) pair in this cartesian
    product is per-field-legal — the only way validate() can reject one of
    them is via the cross-field rule. A blacklist of one known-bad pair
    would accept the rest; a whitelist rejects every pair not explicitly
    compatible. Assert at least one per-field-legal pair is rejected.
    """
    rejected = [
        (s, rc)
        for s, rc in product(sorted(VALID_STATUSES), sorted(VALID_ROOT_CAUSES))
        if validate(_entry(status=s, root_cause=rc))
    ]
    assert rejected, (
        "cross-field check accepts every per-field-legal (status, root_cause) "
        "pair — that is a blacklist, not the closed-by-default whitelist."
    )


# ---------------------------------------------------------------------------
# Closed-by-default allow-set: admission of every live (status, root_cause)
# ---------------------------------------------------------------------------

# The 15 (status, root_cause) pairs present in registry/upstream-issues.yaml
# at the time this test was authored. ALL of them must be admitted by the
# allow-set, or live `python scripts/validate_upstream_registry.py` regresses.
LIVE_REGISTRY_PAIRS: set[tuple[str, str]] = {
    ("needs_investigation", "upstream_feature_gap"),
    ("needs_filing", "upstream_feature_gap"),
    ("needs_investigation", "upstream_bug"),
    ("by_design", "by_design"),
    ("open", "mountainash_internal"),
    ("needs_investigation", "parameter_width"),
    ("resolved_in_mountainash", "upstream_feature_gap"),
    ("open", "parameter_width"),
    ("resolved_in_mountainash", "upstream_bug"),
    ("needs_investigation", "mountainash_internal"),
    ("open", "upstream_bug"),
    ("needs_filing", "upstream_bug"),
    ("resolved_in_mountainash", "mountainash_internal"),
    ("open", "upstream_feature_gap"),
    ("closed", "parameter_width"),
}


@pytest.mark.parametrize(
    "status, root_cause",
    sorted(LIVE_REGISTRY_PAIRS),
    ids=lambda v: str(v),
)
def test_admits_every_live_registry_pair(status, root_cause):
    """Every (status, root_cause) pair actually present in the live
    registry must be admitted. Regression guard: a future tweak to
    COMPATIBLE_STATUS_ROOT_CAUSE that drops one of these breaks live
    validation and must be caught here, not at CI."""
    errs = validate(_entry(status=status, root_cause=root_cause))
    cross_field = [e for e in errs if "root_cause" in e and "status" in e]
    assert cross_field == [], (
        f"live-registry pair (status={status!r}, root_cause={root_cause!r}) "
        f"was rejected: {cross_field}"
    )


# ---------------------------------------------------------------------------
# Allow-set structural properties
# ---------------------------------------------------------------------------

def test_allow_set_is_a_frozenset_of_tuples_of_strings():
    """COMPATIBLE_STATUS_ROOT_CAUSE must be a hashable container of
    (str, str) tuples — not a list, not a dict, not a string-keyed dict.
    Operators extend it; the type matters."""
    assert isinstance(COMPATIBLE_STATUS_ROOT_CAUSE, (set, frozenset)), (
        f"COMPATIBLE_STATUS_ROOT_CAUSE must be a set/frozenset, "
        f"got {type(COMPATIBLE_STATUS_ROOT_CAUSE).__name__}"
    )
    for pair in COMPATIBLE_STATUS_ROOT_CAUSE:
        assert isinstance(pair, tuple) and len(pair) == 2, (
            f"every allow-set entry must be a 2-tuple, got {pair!r}"
        )
        s, rc = pair
        assert isinstance(s, str) and isinstance(rc, str), (
            f"every allow-set entry must be (str, str), got ({type(s).__name__}, "
            f"{type(rc).__name__})"
        )
        assert s in VALID_STATUSES, f"allow-set contains unknown status {s!r}"
        assert rc in VALID_ROOT_CAUSES, (
            f"allow-set contains unknown root_cause {rc!r}"
        )


def test_allow_set_does_not_contain_illustrative_contradiction():
    """The brief's named contradiction (resolved_in_mountainash + by_design)
    must NOT be in the allow-set — that is what the closed-by-default rule
    is for. If a future refactor silently adds it, the whitelist is broken."""
    assert ("resolved_in_mountainash", "by_design") not in COMPATIBLE_STATUS_ROOT_CAUSE, (
        "the illustrative contradiction (resolved_in_mountainash, by_design) "
        "must not be in the allow-set — the rule is closed-by-default"
    )
