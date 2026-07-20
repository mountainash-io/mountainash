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

_PENDING_DIVERGENCE_FACTS: dict[str, str] = {
    # id -> reason. Genuine result divergences become DivergenceFacts in Phase 3.
    "IB-CTE-01": "result divergence — Ibis strips RECURSIVE from CTE SQL → DivergenceFact in Phase 3. Since 2026-07-20.",
}

_PENDING_CAPABILITY_FACTS: dict[str, str] = {
    # id -> reason. Capability gaps become CapabilityFacts in Phase 3.
    "IB-AGG-02": "capability gap — no mode aggregate → CapabilityFact in Phase 3. Since 2026-07-20.",
    "IB-REL-01": "capability gap — window functions unsupported on ibis-polars → CapabilityFact in Phase 3. Since 2026-07-20.",
    "NW-MATH-03": "capability gap — is_finite/is_infinite gaps → CapabilityFact in Phase 3. Since 2026-07-20.",
    "NW-LIST-04": "capability gap — list.get() rejects negative indices → CapabilityFact in Phase 3. Since 2026-07-20.",
    "NW-LIST-06": "capability gap — list.last() fails through get(-1) → CapabilityFact in Phase 3. Since 2026-07-20.",
}

_PENDING_INTERNAL_GAPS: dict[str, str] = {
    # id -> reason. Internal-wiring gaps may never become facts.
    "MA-WIRE-01": "internal-wiring gap — bitwise operations are protocol stubs; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-02": "internal-wiring gap — shift operations are protocol stubs; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-03": "internal-wiring gap — conditional builder is not in _FLAT_NAMESPACES; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-04": "internal-wiring gap — is_dst rejects options=None; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-06": "internal-wiring gap — aggregate signatures mismatch; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-08": "internal-wiring gap — aspirational protocol methods remain unwired; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-09": "internal-wiring gap — string tier3 operations are Polars-only; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-10": "internal-wiring gap — forward_fill/backward_fill are unwired for Ibis; tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
    "MA-WIRE-11": "internal-wiring gap — median() is unavailable on col(); tracked as wiring backlog — may not become a fact. Since 2026-07-20.",
}


def _yaml_entries() -> dict[str, dict]:
    data = yaml.safe_load(_REGISTRY_PATH.read_text())
    return {e["id"]: e for e in data["issues"]}


def _code_refs() -> set[str]:
    return {
        f.upstream_ref for f in CapabilityRegistry.facts() if f.upstream_ref is not None
    }


def test_every_code_ref_resolves_to_a_yaml_entry():
    unresolved = sorted(_code_refs() - set(_yaml_entries()))
    assert not unresolved, (
        f"upstream_ref values with no registry/upstream-issues.yaml entry: {unresolved}"
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
