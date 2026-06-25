"""Pure tier classification for tests. One tier per test, closed-by-default.

resolve_tier(nodeid) returns exactly one of TIERS, or None when the nodeid
matches no rule — None is the signal the taxonomy audit fails on.
"""
from __future__ import annotations

TIERS: tuple[str, ...] = ("unit", "cross_backend", "integration", "contract")

# Explicit file overrides win over path heuristics. Key = path prefix of the
# nodeid (everything before "::"). Add a dated reason in a comment.
_TIER_OVERRIDES: dict[str, str] = {
    "tests/core/test_signature_conformance.py": "contract",   # 2026-06-21 verification harness
    "tests/core/test_compile_smoke.py": "contract",            # 2026-06-21 wiring smoke
    "tests/core/test_rel_signature_conformance.py": "contract",
    "tests/core/test_rel_collect_smoke.py": "contract",
    "tests/test_exceptions_facade.py": "unit",                 # 2026-06-24 top-level facade smoke
    "tests/core/test_taxonomy_audit.py": "contract",           # 2026-06-24 self-test has pytestmark=contract; path rule gives unit
    "tests/core/test_selector_registry.py": "contract",        # 2026-06-24 self-test has pytestmark=contract; path rule gives unit
    "tests/fixtures/test_backend_scope.py": "contract",        # 2026-06-24 self-test has pytestmark=contract; path rule gives unit
}

# Ordered substring rules; first match wins. Most specific first.
_PATH_RULES: tuple[tuple[str, str], ...] = (
    ("/protocol_alignment/", "contract"),
    ("test_protocol_alignment", "contract"),
    ("/argument_types/", "contract"),
    ("test_wiring_audit", "contract"),
    ("test_coverage_guard", "contract"),
    ("/cross_backend/", "cross_backend"),
    ("/dag/", "integration"),
    ("/integration/", "integration"),
    ("/alignment/", "contract"),
    ("/ast/", "unit"),
    ("/pydata/mappers/", "unit"),
    ("/pydata/sanitizers/", "unit"),
    # Module-root fallbacks — EXPLICIT (not a silent default). Ordered last so
    # the specific rules above win. A test under a known module classifies as
    # unit; a test under an UNKNOWN root falls through to None and fails the
    # audit (closed-by-default). Backfill this list in Task 4/5 if the audit
    # surfaces a module whose non-special tests aren't unit.
    ("tests/expressions/", "unit"),
    ("tests/relations/", "unit"),
    ("tests/conform/", "unit"),
    ("tests/typespec/", "unit"),
    ("tests/pydata/", "unit"),
    ("tests/datacontracts/", "unit"),
    ("tests/pipelines/", "unit"),
    ("tests/core/", "unit"),
    ("tests/graph/", "unit"),
    ("tests/alignment/", "contract"),
    ("tests/scripts/", "unit"),        # 2026-06-24 script unit tests (catalog renderer, drift guards)
    ("tests/fixtures/", "unit"),       # 2026-06-24 self-tests for test fixture infrastructure
    ("tests/selection/", "contract"),  # 2026-06-24 taxonomy audit tests are contract-level
)


def _path_of(nodeid: str) -> str:
    return nodeid.split("::", 1)[0]


def resolve_tier(nodeid: str) -> str | None:
    path = _path_of(nodeid)
    if path in _TIER_OVERRIDES:
        return _TIER_OVERRIDES[path]
    for needle, tier in _PATH_RULES:
        if needle in nodeid:
            return tier
    # Closed-by-default: no rule matched. Return None so the taxonomy audit
    # (Task 5) FAILS and forces an explicit rule/override. Never silently
    # default a tier.
    return None
