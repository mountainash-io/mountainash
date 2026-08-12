# tests/core/test_upstream_registry_join.py
"""Typed YAML<->code join (spec Section 3, integrity guard #3).

Forward: every upstream_ref in code resolves to a YAML id.
Reverse: every YAML entry has code references OR a status that explains
zero references (closed-by-default: absence must be justified).
"""
from pathlib import Path

import yaml

from mountainash.core.capabilities import CapabilityRegistry
from mountainash.core.capabilities.bootstrap import load_all_capability_declarations

load_all_capability_declarations()

_REGISTRY_PATH = Path(__file__).resolve().parents[2] / "registry" / "upstream-issues.yaml"

# Statuses allowed to have zero code references (spec Section 3).
_ZERO_REF_OK = {
    "closed", "by_design", "needs_filing", "needs_investigation",
    "wont_fix", "resolved_in_mountainash",
}

_PENDING_DIVERGENCE_FACTS: dict[str, str] = {}

_PENDING_CAPABILITY_FACTS: dict[str, str] = {}

_PENDING_INTERNAL_GAPS: dict[str, str] = {
    # id -> reason. Internal-wiring gaps may never become facts.
    "MA-WIRE-01": "internal-wiring gap — bitwise operations are protocol stubs; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-02": "internal-wiring gap — shift operations are protocol stubs; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-03": "internal-wiring gap — conditional builder is not in _FLAT_NAMESPACES; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-06": "internal-wiring gap — aggregate signatures mismatch; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-08": "internal-wiring gap — aspirational protocol methods remain unwired; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-09": "internal-wiring gap — string tier3 operations are Polars-only; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-10": "internal-wiring gap — forward_fill/backward_fill are unwired for Ibis; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-11": "internal-wiring gap — median() is unavailable on col(); tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
}

# Pre-existing DivergenceFact/upstream-issues.yaml id collisions surfaced by
# test_no_divergence_id_collides_with_an_unrelated_yaml_entry the first time
# it ran (backlog item 84, 2026-08-13). Two originally-flagged instances
# (IB-STR-02, MA-STR-01) were resolved for real in the same change (renamed
# to IB-STR-11 / linked via upstream_ref respectively); these 16 were
# additionally discovered by the new detector and are grandfathered here,
# closed-by-default, pending individual triage (rename vs link) — tracked as
# backlog item 87, not silently dropped.
_KNOWN_ID_COLLISIONS: dict[str, str] = {
    "IB-LIST-01": "DivergenceFact describes ibis's broad missing-list-op surface; the yaml IB-LIST-01 entry describes the same 'ibis array namespace mostly missing' gap by a different enumeration — plausibly the same issue but not verified 1:1. Backlog item 87. Since 2026-08-13.",
    "IB-REL-07": "DivergenceFact (ibis-sqlite drop_nans/unpivot/melt) is unrelated to yaml IB-REL-07 (ArrayValue.sort() descending param) — needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "IB-REL-08": "DivergenceFact (asof join unreliable) is unrelated to yaml IB-REL-08 (backend rename mapping inverted, likely a mountainash visitor bug) — needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "IB-REL-09": "DivergenceFact (cross_join suffix disambiguation) and yaml IB-REL-09 (join() suffixes kwarg unsupported) both concern Ibis's suffixes kwarg — plausibly the same issue but not verified 1:1. Backlog item 87. Since 2026-08-13.",
    "IB-WIN-01": "DivergenceFact and yaml IB-WIN-01 both describe 'ibis-polars has no WindowFunction translation rule' near-verbatim — high-confidence same issue, needs upstream_ref linked. Backlog item 87. Since 2026-08-13.",
    "IB-WIN-02": "DivergenceFact and yaml IB-WIN-02 both describe 'ibis-duckdb/sqlite rank functions are 0-based not 1-based' near-verbatim — high-confidence same issue, needs upstream_ref linked. Backlog item 87. Since 2026-08-13.",
    "IB-WIN-03": "DivergenceFact (rank(method=average|max) has no SQL equivalent) is unrelated to yaml IB-WIN-03 (lead/lag/shift/cumulative/diff have no WindowFunction translation on ibis-duckdb/sqlite) — different op sets, needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "NW-AGG-01": "DivergenceFact (mode()/any_value() rejected on narwhals-lazy) is unrelated to yaml NW-AGG-01 (an already-RESOLVED variance()/.pow() bug) — needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "NW-DT-01": "DivergenceFact (week_of_year unsupported on pandas/narwhals) is unrelated to yaml NW-DT-01 (datetime offset ops require literal integers) — needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "NW-DT-02": "DivergenceFact (narwhals-pandas dt.date() raises) is unrelated to yaml NW-DT-02 (week_of_year not supported on pandas) — needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "NW-DT-03": "DivergenceFact (narwhals dt.time() unsupported) may or may not be the same as yaml NW-DT-03's vague 'various datetime enrichment ops raise on pandas, need to identify specific methods' — not verified 1:1. Backlog item 87. Since 2026-08-13.",
    "NW-LIST-05": "DivergenceFact describes narwhals's broad missing-list-op surface; the yaml NW-LIST-05 entry describes the same 'narwhals list namespace mostly missing' gap by a different enumeration — plausibly the same issue but not verified 1:1. Backlog item 87. Since 2026-08-13.",
    "NW-MATH-01": "DivergenceFact (cot() raises because tan() is missing) is plausibly explained by yaml NW-MATH-01 ('no trigonometric functions, incl. tan') but describes a different symptom (cot, not tan itself) — not verified 1:1. Backlog item 87. Since 2026-08-13.",
    "NW-MATH-02": "DivergenceFact (trig+angular+hyperbolic all raise) partially overlaps yaml NW-MATH-02 (hyperbolic functions only) — broader scope than the yaml entry, not verified 1:1. Backlog item 87. Since 2026-08-13.",
    "NW-WIN-01": "DivergenceFact (order-dependent window ops rejected on narwhals-lazy) is unrelated to yaml NW-WIN-01 (ntile() unsupported) — needs a rename to a free id. Backlog item 87. Since 2026-08-13.",
    "NW-WIN-02": "DivergenceFact (percent_rank/cume_dist/nth_value/diff(n>1) raise) partially overlaps yaml NW-WIN-02 (diff(n>1) only) — broader scope than the yaml entry, not verified 1:1. Backlog item 87. Since 2026-08-13.",
}


def _yaml_entries() -> dict[str, dict]:
    data = yaml.safe_load(_REGISTRY_PATH.read_text())
    return {e["id"]: e for e in data["issues"]}


def _code_refs() -> set[str]:
    from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES

    refs = {
        f.upstream_ref for f in CapabilityRegistry.facts() if f.upstream_ref is not None
    }
    refs |= {divergence.upstream_ref for divergence in KNOWN_DIVERGENCES if divergence.upstream_ref}
    return refs


def test_every_code_ref_resolves_to_a_yaml_entry():
    unresolved = sorted(_code_refs() - set(_yaml_entries()))
    assert not unresolved, (
        f"upstream_ref values with no registry/upstream-issues.yaml entry: {unresolved}"
    )


def test_no_divergence_id_collides_with_an_unrelated_yaml_entry():
    """Backlog item 84 — DivergenceFact.id and upstream-issues.yaml's id both
    use the PROJ-CAT-NN grammar but are independent namespaces with no
    enforced cross-reference. test_upstream_ref_is_self_ref_or_absent
    (test_divergence_facts.py) already forbids a MISMATCHED upstream_ref,
    and test_every_code_ref_resolves_to_a_yaml_entry above already forbids a
    DANGLING one — but neither catches the case that actually bit item 83's
    investigation: a DivergenceFact.id string that happens to equal an
    unrelated yaml entry's id, with upstream_ref left None (allowed by the
    self-ref-or-absent rule) rather than pointing at it. That silent id
    reuse is exactly the failure mode item 84 was filed to close: a human or
    agent greps upstream-issues.yaml for an id seen in test output and gets
    a wrong-but-plausible unrelated entry instead of a "not found"."""
    from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES

    yaml_ids = set(_yaml_entries())
    collisions = sorted(
        d.id
        for d in KNOWN_DIVERGENCES
        if d.id in yaml_ids
        and d.upstream_ref != d.id
        and d.id not in _KNOWN_ID_COLLISIONS
    )
    assert not collisions, (
        "DivergenceFact id(s) reuse an unrelated upstream-issues.yaml entry's "
        "id string without self-referencing it via upstream_ref — rename the "
        "DivergenceFact id to a free one (and file/point at a new yaml entry "
        "if it needs one), or set upstream_ref=id if it is genuinely the same "
        f"upstream issue, or grandfather it in _KNOWN_ID_COLLISIONS with a "
        f"dated reason: {collisions}"
    )


def test_known_id_collisions_are_still_live_and_justified():
    """Closed-by-default companion to the grandfather set above — an entry
    that stops colliding (resolved by a future rename/link) must be removed
    from _KNOWN_ID_COLLISIONS, not left to rot as a stale exception that
    would silently hide a REAL new collision reusing the same id later."""
    from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES

    yaml_ids = set(_yaml_entries())
    by_id = {d.id: d for d in KNOWN_DIVERGENCES}
    stale = []
    for entry_id, reason in _KNOWN_ID_COLLISIONS.items():
        assert reason.strip(), f"grandfathered collision {entry_id} has an empty reason"
        d = by_id.get(entry_id)
        if d is None or d.id not in yaml_ids or d.upstream_ref == d.id:
            stale.append(entry_id)
    assert not stale, (
        f"grandfathered id(s) no longer collide — remove from "
        f"_KNOWN_ID_COLLISIONS: {stale}"
    )


def test_every_open_yaml_entry_is_referenced_from_code():
    entries = _yaml_entries()
    refs = _code_refs()
    orphaned = sorted(
        entry_id
        for entry_id, entry in entries.items()
        if (
            entry_id not in refs
            and entry_id not in _PENDING_DIVERGENCE_FACTS
            and entry_id not in _PENDING_CAPABILITY_FACTS
            and entry_id not in _PENDING_INTERNAL_GAPS
            and entry["status"] not in _ZERO_REF_OK
        )
    )
    assert not orphaned, (
        "Open YAML entries with no code reference — add upstream_ref to the "
        "relevant fact/xfail, or correct the entry's status: "
        f"{orphaned}"
    )


def test_pending_entries_are_real_open_and_justified():
    entries = _yaml_entries()
    all_pending = {
        **_PENDING_DIVERGENCE_FACTS,
        **_PENDING_CAPABILITY_FACTS,
        **_PENDING_INTERNAL_GAPS,
    }
    # No id appears in two buckets.
    keys = (
        list(_PENDING_DIVERGENCE_FACTS)
        + list(_PENDING_CAPABILITY_FACTS)
        + list(_PENDING_INTERNAL_GAPS)
    )
    assert len(keys) == len(set(keys)), "an id is parked in more than one bucket"
    for entry_id, reason in all_pending.items():
        assert entry_id in entries, f"parked id not in registry: {entry_id}"
        assert entries[entry_id]["status"] not in _ZERO_REF_OK, (
            f"parked {entry_id} has a zero-ref-OK status ({entries[entry_id]['status']}) "
            "— it does not need parking; remove it from the pending set"
        )
        assert reason.strip(), f"parked {entry_id} has an empty reason"

    # Each bucket's reasons must carry the bucket's classification descriptor,
    # so a future misparking (e.g. a divergence-worded reason in the capability
    # bucket) is caught here rather than silently misleading Phase 3's draining.
    for entry_id, reason in _PENDING_DIVERGENCE_FACTS.items():
        assert "divergence" in reason, f"{entry_id}: divergence bucket reason must say 'divergence'"
    for entry_id, reason in _PENDING_CAPABILITY_FACTS.items():
        assert "capability gap" in reason, (
            f"{entry_id}: capability bucket reason must say 'capability gap'"
        )
        assert "result divergence" not in reason, (
            f"{entry_id}: capability-bucket entry is mislabelled 'result divergence'"
        )
    for entry_id, reason in _PENDING_INTERNAL_GAPS.items():
        assert "internal-wiring gap" in reason, (
            f"{entry_id}: internal bucket reason must say 'internal-wiring gap'"
        )
