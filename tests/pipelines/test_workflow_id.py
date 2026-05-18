from datetime import date

from mountainash.pipelines.orchestration.workflow_id import compute_workflow_id


def test_deterministic_same_inputs():
    params = {"start": str(date(2026, 1, 1))}
    config = {"storage_path": "/data/fitbit"}

    id1 = compute_workflow_id("wearables", "1.0.0", "user_abc", params, config)
    id2 = compute_workflow_id("wearables", "1.0.0", "user_abc", params, config)
    assert id1 == id2


def test_different_users_different_ids():
    params = {}
    config = {}

    id1 = compute_workflow_id("p", "1.0.0", "user_a", params, config)
    id2 = compute_workflow_id("p", "1.0.0", "user_b", params, config)
    assert id1 != id2


def test_different_versions_different_ids():
    params = {}
    config = {}

    id1 = compute_workflow_id("p", "1.0.0", "u", params, config)
    id2 = compute_workflow_id("p", "2.0.0", "u", params, config)
    assert id1 != id2


def test_different_params_different_ids():
    params1 = {"start": str(date(2026, 1, 1))}
    params2 = {"start": str(date(2026, 3, 1))}
    config = {}

    id1 = compute_workflow_id("p", "1.0.0", "u", params1, config)
    id2 = compute_workflow_id("p", "1.0.0", "u", params2, config)
    assert id1 != id2


def test_different_config_different_ids():
    params = {}

    id1 = compute_workflow_id("p", "1.0.0", "u", params, {"path": "/a"})
    id2 = compute_workflow_id("p", "1.0.0", "u", params, {"path": "/b"})
    assert id1 != id2
