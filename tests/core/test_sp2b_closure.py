"""Closed expectation accounting for scoped observers and capability gates."""

from __future__ import annotations

import ast
from pathlib import Path


from mountainash.core.capabilities.registry import CapabilityRegistry
from tests.fixtures.verification_bindings import capture_bindings, observer_specs
from tests.core.test_compile_smoke import _KNOWN_SMOKE_FAILURES
from tests.core.test_imperative_xfail_ban import _capability_imperative_offenders
from tests.fixtures.capability_census import build_census
from tests.fixtures.capability_inventory import load_inventory

_TESTS_DIR = Path(__file__).resolve().parents[1]
_ROUTING_DIRS = ("expressions", "relations", "conform", "validation")
# The spine-object reason references that make a marker capability-encoding
# (mirrors capability_census._SPINE_REFS -- kept local so this guard is
# self-contained and does not couple to a census private).
_SPINE_REFS = frozenset({"fact", "limitation", "residue", "wildcard_residue", "divergence"})
_PARK_REGISTRY = _TESTS_DIR / "_sp2b_park_registry.yaml"


# ---------------------------------------------------------------------------
# Affected-set discovery + small AST predicates.
# ---------------------------------------------------------------------------
def _affected_routing_files() -> list[Path]:
    """Every migrated routing test file: one that routes through the spine
    surface. Discovered (not hard-coded) so the set stays self-maintaining."""
    out = {_TESTS_DIR.parent / spec.path for spec in observer_specs()}
    for d in _ROUTING_DIRS:
        for p in (_TESTS_DIR / d).rglob("test_*.py"):
            txt = p.read_text()
            if "assert_capability_gated" in txt:
                out.add(p)
    return sorted(out)


def _rel(p: Path) -> str:
    return p.resolve().relative_to(_TESTS_DIR.parent).as_posix()


def _is_mark_xfail(node: ast.AST) -> bool:
    """A literal ``pytest.mark.xfail(...)`` call."""
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
    assert imperative == [], "inventory still holds found_via=imperative-xfail rows:\n" + "\n".join(imperative)


def test_observer_references_resolve_to_actual_functions_and_claims():
    specs = observer_specs()
    capture_bindings(CapabilityRegistry.capture(), specs)
    trees = {}
    for spec in specs:
        if spec.path not in trees:
            trees[spec.path] = ast.parse((_TESTS_DIR.parent / spec.path).read_text())
        node = trees[spec.path]
        for part in spec.function.split("."):
            matches = [
                child
                for child in node.body
                if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == part
            ]
            assert len(matches) == 1, f"missing or ambiguous observer: {spec.path}::{spec.function}"
            node = matches[0]
        names = {arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)}
        assert {name for name, _ in spec.parameters} <= names, (
            f"observer parameters changed: {spec.path}::{spec.function}"
        )


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
# (f) No silently-dropped backend: every backend in ALL_BACKENDS is exercised
#     somewhere in the migrated set. A whole backend absent would mask its gaps.
# ---------------------------------------------------------------------------
def test_f_no_silent_backend_skip(request):
    paths = {_rel(path) for path in _affected_routing_files()}
    seen = set()
    for item in request.session.items:
        if item.path.resolve().relative_to(_TESTS_DIR.parent).as_posix() in paths:
            params = getattr(getattr(item, "callspec", None), "params", {})
            if "backend_name" in params:
                seen.add(params["backend_name"])
    # A selected core-only invocation has no operational cells to inspect.
    # Full collection, including every migrated provider, enforces this check.
    if seen:
        from fixtures.backend_registry import active_scope, resolve_backend_scope

        assert set(resolve_backend_scope(active_scope())) <= seen


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
    catalogued = {(e.operation_key, e.backend) for e in inv.values() if e.found_via in ("catch-all", "static-marker")}
    overlap = sorted(k for k in _KNOWN_SMOKE_FAILURES if k in catalogued)
    assert not overlap, f"native-failure park keys also catalogued as capability gaps: {overlap[:10]}"
