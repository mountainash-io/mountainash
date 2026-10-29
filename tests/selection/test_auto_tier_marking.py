import pytest

pytestmark = pytest.mark.contract


def test_no_untagged_tests_after_collection(request):
    # The hook records nodeids that resolve_tier could not classify.
    untagged = getattr(request.config, "_ma_tier_untagged", None)
    assert untagged == [], f"{len(untagged or [])} untagged tests: {(untagged or [])[:20]}"


def test_no_multi_tagged_tests(request):
    # The hook records nodeids carrying more than one tier marker.
    multi = getattr(request.config, "_ma_tier_multi", None)
    assert multi == [], f"multi-tagged tests (spec: exactly one tier): {multi}"
