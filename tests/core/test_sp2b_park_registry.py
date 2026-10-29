"""PARK registry integrity guard (SP2-B plan Task 0.5, spec 2.1).

Every sanctioned last-resort PARK-AS-MARKER is recorded in
``tests/_sp2b_park_registry.yaml`` AND must appear as a well-formed, tracked
marker in its target file: ``strict=True`` always, and — for a *gate* park —
``raises=BackendCapabilityError`` (so it keys as a ``static-marker`` census row
rather than rotting silently). This guard binds each registry entry 1:1 to its
live marker by the marker's ``reason=`` string and rejects a bare / non-strict /
missing / duplicated park.

The registry is EMPTY on baseline (this guard passes vacuously); populated only
when Phase 2 meets an un-fact-able gap. Absent this guard, PARK is prohibited.
"""
from __future__ import annotations

import ast
from pathlib import Path

import yaml

_TESTS_DIR = Path(__file__).resolve().parents[1]
_REGISTRY_PATH = _TESTS_DIR / "_sp2b_park_registry.yaml"
_REQUIRED_FIELDS = ("target", "qualname", "backend", "kind", "reason", "since", "owner", "reprobe")
_VALID_KINDS = ("gate", "divergence")


def _load_registry() -> list[dict]:
    raw = yaml.safe_load(_REGISTRY_PATH.read_text()) or []
    assert isinstance(raw, list), f"park registry must be a YAML list, got {type(raw).__name__}"
    return raw


def _marker_facts(node: ast.Call) -> dict:
    """Extract ``{reason, strict, raises}`` from a ``pytest.mark.xfail(...)`` call."""
    reason = None
    strict = False
    raises: set[str] = set()
    for kw in node.keywords:
        if kw.arg == "reason" and isinstance(kw.value, ast.Constant):
            reason = kw.value.value
        elif kw.arg == "strict" and isinstance(kw.value, ast.Constant):
            strict = kw.value.value is True
        elif kw.arg == "raises":
            elts = kw.value.elts if isinstance(kw.value, (ast.Tuple, ast.List)) else [kw.value]
            for elt in elts:
                if isinstance(elt, ast.Name):
                    raises.add(elt.id)
                elif isinstance(elt, ast.Attribute):
                    raises.add(elt.attr)
    return {"reason": reason, "strict": strict, "raises": raises}


def _is_mark_xfail(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "xfail"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "mark"
    )


def _file_markers(rel: str) -> list[dict]:
    tree = ast.parse((_TESTS_DIR / rel).read_text(), filename=rel)
    return [_marker_facts(n) for n in ast.walk(tree) if _is_mark_xfail(n)]


def _registered_park_offenders(
    registry: list[dict],
    markers_by_target: dict[str, list[dict]],
) -> list[str]:
    """Pure predicate (testable with synthetic inputs): each registry entry MUST
    bind to exactly one marker (by ``reason`` string) in its target file, that
    marker MUST be ``strict=True``, and a ``gate`` park MUST raise
    ``BackendCapabilityError``. Returns one message per violation."""
    offenders: list[str] = []
    for i, entry in enumerate(registry):
        missing = [f for f in _REQUIRED_FIELDS if f not in entry]
        if missing:
            offenders.append(f"registry[{i}] missing fields {missing}")
            continue
        if entry["kind"] not in _VALID_KINDS:
            offenders.append(f"registry[{i}] {entry['target']}: bad kind {entry['kind']!r}")
        markers = markers_by_target.get(entry["target"], [])
        matches = [m for m in markers if m["reason"] == entry["reason"]]
        if len(matches) != 1:
            offenders.append(
                f"registry[{i}] {entry['target']} :: {entry['qualname']}: expected exactly one "
                f"pytest.mark.xfail with reason=={entry['reason']!r}, found {len(matches)}"
            )
            continue
        m = matches[0]
        if not m["strict"]:
            offenders.append(
                f"registry[{i}] {entry['target']}: park marker is not strict=True "
                "(a non-strict park swallows unrelated failures and XPASSes silently)"
            )
        if entry["kind"] == "gate" and "BackendCapabilityError" not in m["raises"]:
            offenders.append(
                f"registry[{i}] {entry['target']}: gate park must raise BackendCapabilityError, "
                f"got raises={sorted(m['raises'])}"
            )
    return offenders


def test_park_registry_is_wellformed_and_bound():
    """Baseline: empty registry passes. Once populated, every entry binds 1:1 to
    a live strict (gate → raises=BackendCapabilityError) marker in its target."""
    registry = _load_registry()
    markers_by_target = {e["target"]: _file_markers(e["target"]) for e in registry if "target" in e}
    offenders = _registered_park_offenders(registry, markers_by_target)
    assert not offenders, "PARK registry integrity violations:\n" + "\n".join(offenders)


# --- Teeth: the predicate rejects malformed parks (synthetic inputs). ---

def _entry(**kw) -> dict:
    base = {
        "target": "tests/x/test_y.py", "qualname": "TestZ::test_w", "backend": "ibis-polars",
        "kind": "gate", "reason": "R", "since": "2026-08-06", "owner": "o", "reprobe": "later",
    }
    base.update(kw)
    return base


def test_bare_gate_park_is_offender():
    """A gate park whose marker lacks raises=BackendCapabilityError is rejected."""
    markers = {"tests/x/test_y.py": [{"reason": "R", "strict": True, "raises": set()}]}
    off = _registered_park_offenders([_entry()], markers)
    assert any("must raise BackendCapabilityError" in o for o in off), off


def test_nonstrict_park_is_offender():
    """A strict=False park is rejected (silent-XPASS hazard)."""
    markers = {"tests/x/test_y.py": [{"reason": "R", "strict": False, "raises": {"BackendCapabilityError"}}]}
    off = _registered_park_offenders([_entry()], markers)
    assert any("not strict=True" in o for o in off), off


def test_missing_park_marker_is_offender():
    """A registry entry with no matching live marker is rejected."""
    off = _registered_park_offenders([_entry()], {"tests/x/test_y.py": []})
    assert any("expected exactly one" in o for o in off), off


def test_wellformed_gate_park_is_not_offender():
    """A strict gate park with raises=BackendCapabilityError passes."""
    markers = {"tests/x/test_y.py": [{"reason": "R", "strict": True, "raises": {"BackendCapabilityError"}}]}
    assert _registered_park_offenders([_entry()], markers) == []
