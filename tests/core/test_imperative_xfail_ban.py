"""Closed-by-default ban on raw imperative ``pytest.xfail()`` calls that encode
backend capabilities (spec 2026-08-01-spine-derived-test-expectations §3,
Task 9 / SP2-A retirement guard).

Census (``tests.fixtures.capability_census``) is the SCOPE authority; the
inventory (``tests.fixtures.capability_inventory``) is the WHITELIST. The
spec's closure guarantee is literally "guard allowlist = inventory": an
inventoried site is allowlisted **regardless of UNRESOLVED slots**;
inventoried UNRESOLVED rows are exactly the SP1 catalogue that SP2-B is
meant to drain. The UNRESOLVED-vs-unlisted distinction only classifies the
*reason* for sites that are NOT inventoried.

An imperative ``pytest.xfail()`` site is an OFFENDER iff:

  * the census classifies it as ``kind == "imperative-xfail"``, AND
  * its bucket is NOT ``non-capability`` (the SOLE confidently-non-capability
    bucket — API reachability, signature conformance, AST-internal nodes), AND
  * its identity is NOT in the inventory allowlist.

The two offender classes carry DISTINCT reason strings (M4): an UNRESOLVED
identity emits "UNRESOLVED identity — cannot be allowlisted...", while a
fully-resolved-but-unallowlisted entry emits "capability-encoding imperative
pytest.xfail() not in the inventory allowlist...". The teeth tests pin both
strings so a future bucket/UNRESOLVED reshape cannot silently collapse them.

Predicate (per the census ``_imperative_site`` / ``_non_capability_predicate``
and inventory ``_identity_key`` / ``_fully_resolved``):

  1. ``kind == "imperative-xfail"``              → in scope
  2. ``bucket == "non-capability"``               → explicitly non-capability; skip
  3. ``inventory_has(node_id, op, backend, param, option_value)`` is True
                                                    → allowlisted (legal, even
                                                      if slots are UNRESOLVED —
                                                      inventoried UNRESOLVED
                                                      rows are the SP1 catalogue)
  4. otherwise                                      → OFFENDER:
       * any UNRESOLVED slot                        → REASON_UNRESOLVED
       * else                                       → REASON_UNALLOWLISTED
"""
from tests.fixtures.capability_census import (
    UNRESOLVED,
    VALID_BUCKETS,
    CensusEntry,
    build_census,
)
from tests.fixtures.capability_inventory import (
    InventoryEntry,
    inventory_has,
    load_inventory,
)


# --- Reason strings (M4). The guard emits these verbatim; the teeth tests
# pin them so a future bucket/UNRESOLVED reshape cannot silently collapse
# the two classes into one. ---
REASON_UNRESOLVED = (
    "UNRESOLVED identity — cannot be allowlisted; convert to a "
    "collection-time strict marker / assert_capability_gated"
)
REASON_UNALLOWLISTED = (
    "capability-encoding imperative pytest.xfail() not in the "
    "inventory allowlist — convert it (SP2-B drains the allowlist)"
)


def _capability_imperative_offenders(
    census: list[CensusEntry] | None = None,
    inventory: dict[str, InventoryEntry] | None = None,
) -> list[tuple[str, str]]:
    """Return ``(site, reason)`` for every capability-encoding imperative
    ``pytest.xfail()`` that is NOT a sanctioned inventory-allowlisted
    grandfather. The inventory check is FIRST (the spec's closure guarantee
    is "guard allowlist = inventory"); an inventoried site is allowlisted
    regardless of UNRESOLVED slots. The UNRESOLVED-vs-unlisted reason
    classification only applies to sites that fail the inventory check."""
    if census is None:
        census = build_census()
    if inventory is None:
        inventory = load_inventory()  # preload once — avoid 386 YAML re-parses
    offenders: list[tuple[str, str]] = []
    for e in census:
        if e.kind != "imperative-xfail":
            continue
        if e.bucket == "non-capability":
            continue
        site = f"{e.path}:{e.line}"
        if inventory_has(
            e.node_id, e.operation_key, e.backend, e.param, e.option_value,
            inventory=inventory,
        ):
            continue  # inventoried → allowlisted (SP1 catalogue, even with UNRESOLVED)
        if UNRESOLVED in (e.operation_key, e.backend, e.param, e.option_value):
            offenders.append((site, REASON_UNRESOLVED))
        else:
            offenders.append((site, REASON_UNALLOWLISTED))
    return offenders


# ---------------------------------------------------------------------------
# M2: the set of legal buckets is closed. A future bucket cannot be silently
# treated as capability-encoding without a review of this guard.
# ---------------------------------------------------------------------------
def test_valid_buckets_is_closed():
    assert set(VALID_BUCKETS) == {"migrated", "retained", "inventoried", "non-capability"}


# ---------------------------------------------------------------------------
# Main guard: every capability-encoding imperative pytest.xfail() in the
# repo must either be in the inventory allowlist (regardless of UNRESOLVED
# slots) or be a "non-capability" site. A site that is NEITHER inventoried
# NOR non-capability is an offender (closed-by-default: any UNRESOLVED slot
# in such a site is reported as REASON_UNRESOLVED; fully-resolved unlisted
# sites are reported as REASON_UNALLOWLISTED).
# ---------------------------------------------------------------------------
def test_no_unlisted_or_unresolved_capability_imperative_xfail():
    offenders = _capability_imperative_offenders()
    assert not offenders, "Banned imperative pytest.xfail() sites:\n" + "\n".join(
        f"  {s}: {why}" for s, why in offenders
    )


# ---------------------------------------------------------------------------
# Teeth tests: prove the guard is closed against crafted CensusEntry inputs.
# The offender function accepts optional ``census`` and ``inventory`` parameters
# so each scenario exercises the predicate in isolation from the live tree.
# ---------------------------------------------------------------------------
def _entry(
    *,
    path: str = "tests/fake/synthetic.py",
    line: int = 1,
    kind: str = "imperative-xfail",
    bucket: str = "inventoried",
    operation_key: str = "UNRESOLVED",
    backend: str = "UNRESOLVED",
    param: str = "UNRESOLVED",
    option_value: str | None = None,
    current_reason: str = "synthetic",
    node_id: str | None = None,
) -> CensusEntry:
    nid = node_id or f"{path}::synthetic::L{line}[{backend}]"
    return CensusEntry(
        node_id=nid,
        path=path, line=line, kind=kind, operation_key=operation_key, backend=backend,
        param=param, option_value=option_value, current_reason=current_reason,
        bucket=bucket, reason="synthetic",
    )


def test_capability_imperative_absent_from_inventory_is_offender():
    """(a) A capability-encoding imperative site that is NOT in the inventory
    allowlist and has fully-resolved identity slots IS an offender with the
    UNALLOWLISTED reason."""
    synthetic = _entry(
        path="tests/fake/missing_from_inventory.py", line=42,
        bucket="inventoried",
        operation_key="FKEY_SYNTHETIC_OP", backend="polars", param="p",
    )
    offenders = _capability_imperative_offenders(census=[synthetic])
    assert len(offenders) == 1
    site, reason = offenders[0]
    assert site == "tests/fake/missing_from_inventory.py:42"
    assert reason == REASON_UNALLOWLISTED


def test_unresolved_identity_is_offender_with_distinct_reason():
    """(b) A site that is NOT in the inventory allowlist and carries an
    UNRESOLVED identity slot IS an OFFENDER with the UNRESOLVED reason —
    distinct from (a) (M4)."""
    synthetic = _entry(
        path="tests/fake/unresolved.py", line=7,
        bucket="inventoried",
        operation_key="UNRESOLVED", backend="UNRESOLVED", param="UNRESOLVED",
    )
    offenders = _capability_imperative_offenders(census=[synthetic])
    assert len(offenders) == 1
    site, reason = offenders[0]
    assert site == "tests/fake/unresolved.py:7"
    assert reason == REASON_UNRESOLVED
    # Pin the distinct reason against the unallowlisted class (M4)
    assert REASON_UNRESOLVED != REASON_UNALLOWLISTED


def test_non_capability_imperative_is_not_an_offender():
    """(c) The "non-capability" bucket is the SOLE confidently-non-capability
    bucket; sites in it are NOT offenders (e.g. API reachability, signature
    conformance, AST-internal nodes)."""
    synthetic = _entry(
        path="tests/fake/non_capability.py", line=99,
        kind="imperative-xfail", bucket="non-capability",
    )
    offenders = _capability_imperative_offenders(census=[synthetic])
    assert offenders == []


def test_inventory_listed_capability_entry_is_not_an_offender():
    """(d) A capability-encoding imperative site whose identity IS in the
    inventory allowlist is a sanctioned grandfather (SP2-B drains it) —
    regardless of UNRESOLVED slots. The real-world case is an UNRESOLVED-
    slotted inventoried row (census ``_imperative_site`` always emits
    ``operation_key=UNRESOLVED`` / ``param=UNRESOLVED``); we use a realistic
    such row, not a synthetic fully-resolved one, because that is the case
    the guard must allowlist in practice."""
    real_entry = next(
        e for e in load_inventory().values() if e.found_via == "imperative-xfail"
    )
    display_path, _, display_line = real_entry.display_site.rpartition(":")
    synthetic = _entry(
        path=display_path, line=int(display_line), bucket="inventoried",
        operation_key=real_entry.operation_key, backend=real_entry.backend,
        param=real_entry.param, option_value=real_entry.option_value,
        node_id=real_entry.node_id,
    )
    offenders = _capability_imperative_offenders(
        census=[synthetic],
        inventory={real_entry.key: real_entry},
    )
    assert offenders == []
