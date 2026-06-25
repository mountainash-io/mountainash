import pytest
from scripts.audit_test_taxonomy import audit

pytestmark = pytest.mark.contract


def test_every_collected_test_has_a_resolvable_tier():
    # audit() with no args collects the live suite via --collect-only.
    result = audit()
    assert result.untagged == [], (
        f"{len(result.untagged)} tests resolve to no tier: {result.untagged[:20]}"
    )


def test_no_unregistered_markers_in_use():
    result = audit()
    assert result.unregistered_markers == set(), (
        f"markers used but not in pytest.ini: {sorted(result.unregistered_markers)}"
    )


def test_no_unused_registered_markers():
    # A registered marker that nothing uses is dead config (spec A2), unless
    # listed in the dated KNOWN_UNUSED_MARKERS exception set.
    result = audit()
    assert result.unused_registered == set(), (
        f"registered but unused markers (remove or add to KNOWN_UNUSED_MARKERS): "
        f"{sorted(result.unused_registered)}"
    )
