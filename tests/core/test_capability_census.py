"""Closed migration census — every capability-encoding expectation site is
discovered and classified into a valid bucket with an explicit reason
(spec 2026-08-01-spine-derived-test-expectations §3, Task 5)."""
from tests.fixtures.capability_census import build_census, VALID_BUCKETS


def test_every_site_classified_with_reason():
    census = build_census()
    assert census, "census discovered no capability-encoding sites"
    for e in census:
        assert e.bucket in VALID_BUCKETS, f"{e.path}:{e.line} bad bucket {e.bucket}"
        assert e.reason, f"{e.path}:{e.line} missing classification reason"
        if e.bucket in ("inventoried", "migrated"):
            assert e.operation_key is not None and e.backend, f"{e.path}:{e.line} needs op+backend"
