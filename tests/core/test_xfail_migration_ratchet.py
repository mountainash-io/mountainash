"""Downward ratchet: hand-written static xfails migrate to
xfail_divergence/xfail_if_limited over time; the count may only fall.

Update BASELINE downward as markers migrate. Raising it requires a reasoned
new-divergence entry FIRST (declare the fact, use the helper) — a new
hand-written marker fails this test.
"""
import re
import subprocess
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]

# Set to the counted value at this task's execution time (see Step 4).
BASELINE = 90

_XFAIL_RE = re.compile(r"pytest\.mark\.xfail\(")
_HELPER_FILES = {"divergence_helpers.py", "_test_template.py", "test_capability_probes.py"}


def _count_static_xfails() -> int:
    count = 0
    for path in TESTS_ROOT.rglob("*.py"):
        if path.name in _HELPER_FILES:
            continue  # helpers CONSTRUCT marks; they are the migration target
        count += len(_XFAIL_RE.findall(path.read_text()))
    return count


def test_static_xfail_count_only_falls():
    count = _count_static_xfails()
    assert count <= BASELINE, (
        f"{count} hand-written pytest.mark.xfail markers (baseline {BASELINE}). "
        "New xfails must go through xfail_divergence()/xfail_if_limited() with a "
        "declared fact — or migrate an old marker to make room."
    )
    if count < BASELINE:
        # Not a failure — a reminder to ratchet the baseline down in the same PR.
        print(f"RATCHET: lower BASELINE to {count}")
