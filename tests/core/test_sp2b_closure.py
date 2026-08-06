"""SP2-B machine-checked closure validator (plan Task 5.1 / M7).

The terminal deliverable of the imperative-xfail drain is a *structural*
end-state, not a passing count. This module is the single consolidating guard
that asserts that end-state machine-readably, so "closure achieved" is one
reviewable artifact rather than an implicit property spread across the drain's
many per-wave guards. Each test binds one plan-Task-5.1 invariant (a)-(h) and
reds if the drain regresses (a new imperative xfail, an unused or dangling
fact, a returning bare capability marker, a silently-dropped backend, ...).

Invariants whose *full* evidence ledger lives in central docs (the SP2-A
verdict doc's contingent rows, the crosswalk's RETIRE evidence) are asserted
here by their **repo-checkable projection**; the central ledger stays
authoritative and is cited in the relevant docstring.

Scope note: the "affected set" is the drain-migrated routing tree -- every
`tests/{expressions,relations,conform,validation}/**/test_*.py` that routes
through the spine surface (`xfail_divergence` / `assert_capability_gated`).
Native-library-gap markers in files SP2-B never migrated are out of scope by
design (census 2026-08-01, scope note), exactly as the census intends.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import yaml

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.gap_collection import collect_all_gap_sets
from mountainash.core.capabilities.divergences import KNOWN_DIVERGENCES, divergence_by_id
from tests.core.test_compile_smoke import _KNOWN_SMOKE_FAILURES
from tests.core.test_imperative_xfail_ban import _capability_imperative_offenders
from tests.fixtures.capability_census import build_census
from tests.fixtures.capability_inventory import load_inventory

_TESTS_DIR = Path(__file__).resolve().parents[1]
_ROUTING_DIRS = ("expressions", "relations", "conform", "validation")
_SP2B_SINCE = "2026-08-06"
# The spine-object reason references that make a marker capability-encoding
# (mirrors capability_census._SPINE_REFS -- kept local so this guard is
# self-contained and does not couple to a census private).
_SPINE_REFS = frozenset({"fact", "limitation", "residue", "wildcard_residue", "divergence"})
_ID_RE = re.compile(r"^[A-Z]+-[A-Z]+-\d+$")
_PARK_REGISTRY = _TESTS_DIR / "_sp2b_park_registry.yaml"


# ---------------------------------------------------------------------------
# Affected-set discovery + small AST predicates.
# ---------------------------------------------------------------------------
def _affected_routing_files() -> list[Path]:
    """Every migrated routing test file: one that routes through the spine
    surface. Discovered (not hard-coded) so the set stays self-maintaining."""
    out: list[Path] = []
    for d in _ROUTING_DIRS:
        for p in (_TESTS_DIR / d).rglob("test_*.py"):
            txt = p.read_text()
            if "capability_gating" in txt and (
                "xfail_divergence" in txt or "assert_capability_gated" in txt
            ):
                out.append(p)
    return out


def _rel(p: Path) -> str:
    return p.resolve().relative_to(_TESTS_DIR.parent).as_posix()


def _is_mark_xfail(node: ast.AST) -> bool:
    """A literal ``pytest.mark.xfail(...)`` call (NOT ``xfail_divergence(...)``,
    whose ``func`` is a plain ``Name``)."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "xfail"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "mark"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "pytest"
    )


def _marker_signals(node: ast.Call) -> tuple[frozenset[str], frozenset[str], object]:
    """``(raises_names, reason_refs, strict)`` for a ``pytest.mark.xfail`` call."""
    raises: set[str] = set()
    refs: set[str] = set()
    strict: object = None
    for k in node.keywords:
        if k.arg == "raises":
            elts = k.value.elts if isinstance(k.value, (ast.Tuple, ast.List)) else [k.value]
            for e in elts:
                if isinstance(e, ast.Name):
                    raises.add(e.id)
                elif isinstance(e, ast.Attribute):
                    raises.add(e.attr)
        elif k.arg == "reason":
            for s in ast.walk(k.value):
                if isinstance(s, ast.Name):
                    refs.add(s.id)
        elif k.arg == "strict" and isinstance(k.value, ast.Constant):
            strict = k.value.value
    return frozenset(raises), frozenset(refs), strict


def _id_literals(tree: ast.AST) -> set[str]:
    """Every fact-ID-grammar string literal passed as a call argument (direct or
    inside a list/tuple arg, e.g. ``_win("IB-WIN-03")`` / ``xfail_divergence("NW-DT-05", ...)``)."""
    out: set[str] = set()
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        for a in list(n.args) + [k.value for k in n.keywords]:
            elts = a.elts if isinstance(a, (ast.List, ast.Tuple)) else [a]
            for e in elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str) and _ID_RE.match(e.value):
                    out.add(e.value)
    return out


def _routing_used_ids() -> set[str]:
    used: set[str] = set()
    for d in _ROUTING_DIRS:
        for p in (_TESTS_DIR / d).rglob("test_*.py"):
            used |= _id_literals(ast.parse(p.read_text()))
    return used


# ---------------------------------------------------------------------------
# (a) Closure: zero capability-encoding imperative xfail; zero imperative-xfail
#     inventory rows. THE terminal deliverable (design §8).
# ---------------------------------------------------------------------------
def test_a_zero_imperative_xfail_closure():
    offenders = _capability_imperative_offenders()
    assert offenders == [], (
        "capability-encoding imperative pytest.xfail() offenders remain (drain "
        "not closed):\n" + "\n".join(f"{s}: {r}" for s, r in offenders)
    )
    inv = load_inventory()
    imperative = sorted(e.node_id for e in inv.values() if e.found_via == "imperative-xfail")
    assert imperative == [], (
        "inventory still holds found_via=imperative-xfail rows:\n" + "\n".join(imperative)
    )


# ---------------------------------------------------------------------------
# (b) Every routed divergence id in the affected set resolves to a LIVE fact.
#     A dangling id would already break collection (xfail_divergence calls
#     divergence_by_id); this asserts it explicitly and closed-by-default.
# ---------------------------------------------------------------------------
def test_b_every_routed_id_resolves_live():
    routed: set[str] = set()
    for p in _affected_routing_files():
        routed |= _id_literals(ast.parse(p.read_text()))
    assert routed, "affected set routes no divergence ids -- discovery is broken"
    dangling = []
    for rid in sorted(routed):
        try:
            divergence_by_id(rid)
        except KeyError:
            dangling.append(rid)
    assert dangling == [], f"routed ids resolve to no live divergence: {dangling}"


# ---------------------------------------------------------------------------
# (c) No unused SP2-B fact: every DivergenceFact SP2-B minted (since=2026-08-06)
#     is referenced by at least one route. A minted-but-unwired fact is dead
#     weight and a sign a conversion was dropped.
# ---------------------------------------------------------------------------
def test_c_no_unused_sp2b_divergence_fact():
    used = _routing_used_ids()
    sp2b = [d.id for d in KNOWN_DIVERGENCES if d.since == _SP2B_SINCE]
    assert sp2b, "no SP2-B-minted divergences found -- since-key drift?"
    unused = sorted(i for i in sp2b if i not in used)
    assert unused == [], f"SP2-B minted these divergences but no route references them: {unused}"


# ---------------------------------------------------------------------------
# (d) No bare capability xfail marker in the affected set: no literal
#     pytest.mark.xfail that is census-INVISIBLE (no raises=, no spine-object
#     reason ref) yet non-strict -- the forbidden untracked state (rev-4 M2).
#     A raises=/spine-ref marker is census-visible (tracked); a strict=True
#     self-healing probe is justified non-capability -- both allowed.
# ---------------------------------------------------------------------------
def test_d_no_census_invisible_bare_marker_in_affected_set():
    offenders: list[str] = []
    for p in _affected_routing_files():
        tree = ast.parse(p.read_text())
        for n in ast.walk(tree):
            if not _is_mark_xfail(n):
                continue
            raises, refs, strict = _marker_signals(n)
            if not raises and not (refs & _SPINE_REFS) and strict is not True:
                offenders.append(f"{_rel(p)}:{n.lineno}")
    assert offenders == [], (
        "census-invisible bare xfail markers remain in the migrated set (route "
        "them through a fact, register them in the PARK registry, or make them "
        "strict=True self-healing probes):\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# (e) Every retirement-verdict marker is well-formed: it names a justification.
#     Repo projection of the RETIRE evidence ledger (full evidence: crosswalk).
# ---------------------------------------------------------------------------
def test_e_retirement_verdict_markers_are_wellformed():
    marker = "retirement-verdict:"
    found = 0
    malformed: list[str] = []
    for p in _TESTS_DIR.rglob("*.py"):
        for i, line in enumerate(p.read_text().splitlines(), 1):
            if marker in line:
                found += 1
                justification = line.split(marker, 1)[1].strip()
                if not justification:
                    malformed.append(f"{_rel(p)}:{i}")
    assert found, "no retirement-verdict markers found -- contingent deletions unrecorded"
    assert malformed == [], "retirement-verdict markers with no justification:\n" + "\n".join(malformed)


# ---------------------------------------------------------------------------
# (f) No silently-dropped backend: every backend in ALL_BACKENDS is exercised
#     somewhere in the migrated set. A whole backend absent would mask its gaps.
# ---------------------------------------------------------------------------
def test_f_no_silent_backend_skip():
    seen: set[str] = set()
    for p in _affected_routing_files():
        txt = p.read_text()
        for b in ALL_BACKENDS:
            if f'"{b}"' in txt or f"'{b}'" in txt:
                seen.add(b)
    missing = [b for b in ALL_BACKENDS if b not in seen]
    assert missing == [], f"backends never exercised across the migrated set: {missing}"


# ---------------------------------------------------------------------------
# (g) The 348 compile-smoke catch-all identities stay consumed + stale-detected
#     (plan Task 0.4): the catch-all primitive is non-capability, its absorbed
#     gaps are catalogued, the native-failure park is disjoint from capability
#     gaps, and the staleness surface is live.
# ---------------------------------------------------------------------------
def test_g_catch_all_consumed_and_stale_detected():
    smoke_rel = "tests/core/test_compile_smoke.py"
    smoke = [e for e in build_census() if e.path == smoke_rel]
    assert smoke and all(e.bucket == "non-capability" for e in smoke), (
        "compile-smoke primitives must all classify non-capability (never drain targets)"
    )
    inv = load_inventory()
    assert any(e.found_via == "catch-all" for e in inv.values()), (
        "no catch-all inventory rows -- the runtime absorber consumes nothing"
    )
    catalogued = {
        (e.operation_key, e.backend)
        for e in inv.values()
        if e.found_via in ("catch-all", "static-marker")
    }
    overlap = sorted(k for k in _KNOWN_SMOKE_FAILURES if k in catalogued)
    assert not overlap, f"native-failure park keys also catalogued as capability gaps: {overlap[:10]}"
    gaps = collect_all_gap_sets()
    assert gaps and any(g for g in gaps.values()), "gap-staleness surface is empty"


# ---------------------------------------------------------------------------
# (h) Contingent-deletion closure (repo projection; full ledger = SP2-A verdict
#     doc). The IB-WIN-03 delete-with-survivor carries its retirement-verdict
#     marker and binds a live fact; W3 (verdict 4.1-W3) is retained whole.
# ---------------------------------------------------------------------------
def test_h_contingent_deletions_bound_to_live_facts():
    win = (_TESTS_DIR / "expressions/cross_backend/test_window_results.py").read_text()
    assert "retirement-verdict" in win and "IB-WIN-03" in win, (
        "IB-WIN-03 guard deletion lost its retirement-verdict binding"
    )
    divergence_by_id("IB-WIN-03")  # the surviving catcher's fact is live
    w3 = _TESTS_DIR / "expressions/argument_types/test_registered_option_probes.py"
    assert w3.exists(), "W3 (verdict 4.1-W3) was retained whole but its file is gone"


# ---------------------------------------------------------------------------
# The PARK registry integrity is enforced by test_sp2b_park_registry; here we
# only assert the registry file remains loadable, so (b)'s "resolve to a
# registered PARK" alternative target is structurally available.
# ---------------------------------------------------------------------------
def test_park_registry_loadable():
    raw = yaml.safe_load(_PARK_REGISTRY.read_text()) or []
    assert isinstance(raw, list), "PARK registry must be a YAML list"
