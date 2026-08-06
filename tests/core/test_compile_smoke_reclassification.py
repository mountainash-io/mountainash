"""Compile-smoke primitive reclassification (SP2-B plan Task 0.4 / review B2).

`tests/core/test_compile_smoke.py` carries two `pytest.xfail()` primitives that
are NOT imperative-drain targets and must never re-enter the imperative-xfail
manifest:

- the `_KNOWN_SMOKE_FAILURES` park (`pytest.xfail(expected_reason)`): a NATIVE,
  non-`BackendCapabilityError` compile failure the harness expects; and
- the dynamic catch-all absorber (`pytest.xfail("undeclared gap (inventoried,
  pending SP2): …")`): the runtime primitive that consumes inventoried gaps via
  an `inventory_has()` lookup — its absorbed gaps are the `found_via=catch-all`
  rows, not this static site.

The census reclassifies both as `non-capability`; these guards pin that, and pin
that the native-failure park stays distinct from the capability catch-all branch.
"""
from __future__ import annotations

from tests.core.test_compile_smoke import _KNOWN_SMOKE_FAILURES
from tests.fixtures.capability_census import build_census
from tests.fixtures.capability_inventory import load_inventory

_SMOKE_REL = "tests/core/test_compile_smoke.py"


def test_compile_smoke_primitives_are_non_capability():
    """Both compile_smoke `pytest.xfail` primitives classify as `non-capability`
    (never `inventoried`), so they carry no `found_via: imperative-xfail` row."""
    smoke = [e for e in build_census() if e.path == _SMOKE_REL]
    assert smoke, "census found no compile_smoke sites"
    non_cap = [e for e in smoke if e.bucket == "non-capability"]
    inventoried = [e for e in smoke if e.bucket == "inventoried"]
    assert len(non_cap) == len(smoke) and not inventoried, (
        "compile_smoke harness primitives must all be non-capability, not drain "
        f"targets: non-capability={[e.line for e in non_cap]}, "
        f"inventoried={[(e.line, e.reason) for e in inventoried]}"
    )

    inv = load_inventory()
    smoke_imperative = [
        e for e in inv.values()
        if e.found_via == "imperative-xfail" and e.node_id.startswith(_SMOKE_REL)
    ]
    assert not smoke_imperative, (
        "compile_smoke must contribute zero imperative-xfail inventory rows; got "
        f"{[e.node_id for e in smoke_imperative]}"
    )


def test_known_smoke_failures_disjoint_from_catalogued_capability_gaps():
    """The native-failure park branch stays distinct from the capability
    catch-all branch: a `_KNOWN_SMOKE_FAILURES` (fkey, backend) — a native,
    non-capability failure — must never also be catalogued as a capability
    inventory row (imperative-xfail or catch-all). Overlap would mean a native
    failure is being absorbed as a capability gap (a misfiled park)."""
    park_keys = set(_KNOWN_SMOKE_FAILURES)
    inv = load_inventory()
    catalogued = {
        (e.operation_key, e.backend)
        for e in inv.values()
        if e.found_via in ("imperative-xfail", "catch-all")
    }
    overlap = {k for k in park_keys if k in catalogued}
    assert not overlap, (
        "native-failure park keys are also catalogued as capability gaps — the "
        f"park and capability branches have collapsed: {sorted(overlap)[:10]}"
    )
