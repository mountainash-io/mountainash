"""Closed migration census — every capability-encoding expectation site is
discovered and classified into a valid bucket with an explicit reason
(spec 2026-08-01-spine-derived-test-expectations §3, Task 5)."""
import ast
from pathlib import Path

from tests.fixtures.capability_census import build_census, VALID_BUCKETS

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_every_site_classified_with_reason():
    census = build_census()
    assert census, "census discovered no capability-encoding sites"
    for e in census:
        assert e.bucket in VALID_BUCKETS, f"{e.path}:{e.line} bad bucket {e.bucket}"
        assert e.reason, f"{e.path}:{e.line} missing classification reason"
        if e.bucket in ("inventoried", "migrated"):
            assert e.operation_key is not None and e.backend, f"{e.path}:{e.line} needs op+backend"


def _imperative_xfail_lines(tree: ast.AST) -> list[int]:
    """Lines of raw imperative ``pytest.xfail(...)`` calls (NOT the
    ``pytest.mark.xfail`` marker, whose ``func.value`` is an Attribute)."""
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "xfail"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pytest"
    ]


def _handcoded_gate_raises_lines(tree: ast.AST) -> list[int]:
    """Lines of hand-coded ``pytest.raises(BackendCapabilityError)`` gate
    reconstructions — the expectation ``assert_capability_gated`` now owns."""
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "raises"
        and any(
            isinstance(a, ast.Name) and a.id == "BackendCapabilityError"
            for a in node.args
        )
    ]


def test_no_migrated_site_carries_a_raw_capability_form():
    """Task 8 completeness gate: every migrated-bucket TEST site now routes its
    capability expectation through the spine helpers (``assert_capability_gated``
    / ``xfail_divergence`` / a ``CapabilityFact``-derived mark). No migrated test
    file may keep a raw imperative ``pytest.xfail(`` or a hand-coded
    ``pytest.raises(BackendCapabilityError)`` gate reconstruction. The src
    production map (``manual-map``) is the single source and is exempt."""
    census = build_census()
    test_files = sorted(
        {e.path for e in census if e.bucket == "migrated" and not e.path.startswith("src/")}
    )
    assert test_files, "no migrated test sites discovered"
    offenders: list[str] = []
    for rel in test_files:
        tree = ast.parse((_REPO_ROOT / rel).read_text(), filename=rel)
        offenders += [f"{rel}:{ln} raw imperative pytest.xfail() at a migrated site"
                      for ln in _imperative_xfail_lines(tree)]
        offenders += [f"{rel}:{ln} hand-coded pytest.raises(BackendCapabilityError) at a migrated site"
                      for ln in _handcoded_gate_raises_lines(tree)]
    assert not offenders, "raw capability forms remain at migrated sites:\n" + "\n".join(offenders)
