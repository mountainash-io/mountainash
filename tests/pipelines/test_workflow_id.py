from datetime import date, datetime

from mountainash.pipelines.orchestration.workflow_id import compute_workflow_id
from mountainash.pipelines.core.capabilities import ResolvedPredicates, PushedParam


def test_deterministic_same_inputs():
    rp = ResolvedPredicates(
        params={"start": PushedParam(value=date(2026, 1, 1), operator="gte")},
        resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0),
    )
    config = {"storage_path": "/data/fitbit"}

    id1 = compute_workflow_id("wearables", "1.0.0", "user_abc", rp, config)
    id2 = compute_workflow_id("wearables", "1.0.0", "user_abc", rp, config)
    assert id1 == id2


def test_different_users_different_ids():
    rp = ResolvedPredicates(resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0))
    config = {}

    id1 = compute_workflow_id("p", "1.0.0", "user_a", rp, config)
    id2 = compute_workflow_id("p", "1.0.0", "user_b", rp, config)
    assert id1 != id2


def test_different_versions_different_ids():
    rp = ResolvedPredicates(resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0))
    config = {}

    id1 = compute_workflow_id("p", "1.0.0", "u", rp, config)
    id2 = compute_workflow_id("p", "2.0.0", "u", rp, config)
    assert id1 != id2


def test_different_predicates_different_ids():
    rp1 = ResolvedPredicates(
        params={"start": PushedParam(value=date(2026, 1, 1), operator="gte")},
        resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0),
    )
    rp2 = ResolvedPredicates(
        params={"start": PushedParam(value=date(2026, 3, 1), operator="gte")},
        resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0),
    )
    config = {}

    id1 = compute_workflow_id("p", "1.0.0", "u", rp1, config)
    id2 = compute_workflow_id("p", "1.0.0", "u", rp2, config)
    assert id1 != id2


def test_different_config_different_ids():
    rp = ResolvedPredicates(resolution_timestamp=datetime(2026, 5, 13, 10, 0, 0))

    id1 = compute_workflow_id("p", "1.0.0", "u", rp, {"path": "/a"})
    id2 = compute_workflow_id("p", "1.0.0", "u", rp, {"path": "/b"})
    assert id1 != id2
