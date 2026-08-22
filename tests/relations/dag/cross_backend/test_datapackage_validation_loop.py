"""End-to-end: datapackage.json -> DataResource -> TypeSpec -> dag.validate.

Proves the vision's headline Phase-1 loop (item 8l) across all three
``dag.validate(backend=...)`` targets. ``specs = {r.name: r.to_typespec()
for r in pkg.resources}`` is the one seam this item adds; every other line
exercises already-correct, already-tested machinery
(``dag.validate``/``build_fk_checks``/``ValidationRunner``, per spec §7 —
out of scope to change here).
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from mountainash.typespec.datapackage import DataPackage

if TYPE_CHECKING:
    from pathlib import Path

# Canonical CONST_BACKEND names accepted by dag.validate(backend=...) — same
# axis as tests/relations/dag/cross_backend/test_empty_resource_collect.py:126.
_COLLECT_BACKENDS = ["polars", "narwhals", "ibis"]


def _descriptor() -> dict:
    return {
        "name": "loop-closure",
        "resources": [
            {
                "name": "parents",
                "type": "table",
                "data": [],
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {
                            "name": "name",
                            "type": "string",
                            "constraints": {"pattern": "^[a-z]+$"},
                        },
                        {
                            "name": "score",
                            "type": "integer",
                            "constraints": {"minimum": 0, "maximum": 100},
                        },
                    ],
                    "primaryKey": ["id"],
                },
            },
            {
                "name": "children",
                "type": "table",
                "data": [],
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "customer_id", "type": "integer"},
                        {
                            "name": "status",
                            "type": "string",
                            "constraints": {"enum": ["active", "inactive"]},
                        },
                    ],
                    "foreignKeys": [
                        {
                            "fields": ["customer_id"],
                            "reference": {"resource": "parents", "fields": ["id"]},
                        }
                    ],
                },
            },
        ],
    }


def _load_package(tmp_path: Path, *, parents: list[dict], children: list[dict]) -> DataPackage:
    """Write a real on-disk datapackage.json and load it via the Path branch
    of DataPackage.from_descriptor (not the dict branch every other existing
    test uses)."""
    descriptor = _descriptor()
    descriptor["resources"][0]["data"] = parents
    descriptor["resources"][1]["data"] = children
    p = tmp_path / "datapackage.json"
    p.write_text(json.dumps(descriptor))
    return DataPackage.from_path(p)


def _status(check_summaries, check_id: str) -> str:
    row = check_summaries.filter(check_summaries["check_id"] == check_id)
    assert row.height == 1, f"check {check_id!r} not found in {check_summaries['check_id'].to_list()}"
    return row.row(0, named=True)["status"]


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _COLLECT_BACKENDS)
def test_conforming_data_passes_cross_backend(tmp_path, backend_name):
    pkg = _load_package(
        tmp_path,
        parents=[
            {"id": 1, "name": "alice", "score": 50},
            {"id": 2, "name": "bob", "score": 80},
        ],
        children=[
            {"id": 10, "customer_id": 1, "status": "active"},
            {"id": 20, "customer_id": 2, "status": "inactive"},
        ],
    )
    dag = pkg.to_relation_dag()
    specs = {r.name: r.to_typespec() for r in pkg.resources}

    result = dag.validate(specs, backend=backend_name)

    assert result.passes is True
    assert result.fk_result.passes is True


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _COLLECT_BACKENDS)
def test_duplicate_primary_key_isolates_identity_failure(tmp_path, backend_name):
    """Item 8j's characterization: a declared primary_key resolving to keyed
    identity is isolated into that resource's own failing result
    (check_id="__identity__") rather than raised out of dag.validate — the
    batch still returns a DAGValidationResult (spec item 8j §3.2). This is
    the first check that a descriptor-sourced to_typespec() produces a
    TypeSpec whose primary_key still triggers that precondition, now
    surfaced through the DAG's per-resource isolation instead of a raise."""
    pkg = _load_package(
        tmp_path,
        parents=[
            {"id": 1, "name": "alice", "score": 50},
            {"id": 1, "name": "bob", "score": 60},
        ],
        children=[
            {"id": 10, "customer_id": 1, "status": "active"},
        ],
    )
    dag = pkg.to_relation_dag()
    specs = {r.name: r.to_typespec() for r in pkg.resources}

    result = dag.validate(specs, backend=backend_name)  # must not raise

    assert result.passes is False
    parents_summaries = result.results["parents"].check_summaries
    assert _status(parents_summaries, "__identity__") == "error"


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", _COLLECT_BACKENDS)
def test_drifting_data_reports_specific_checks_cross_backend(tmp_path, backend_name):
    """Identity holds (no duplicate parents.id); three independent violation
    kinds (range, enum, FK) fire in one dag.validate() call — proves which
    checks fired, not just that something failed.

    A fourth kind (pattern) is deliberately NOT asserted here: it exposed a
    genuine pre-existing defect on narwhals/ibis-duckdb (item 103, backlog) —
    the `pattern` check's NULL-on-no-match assumption doesn't hold on either
    backend, so it silently reports "passed" instead of "failed" there. See
    test_pattern_violation_detected_polars for the Polars-only proof; the
    other three violation kinds are confirmed correct on all 3 backends."""
    pkg = _load_package(
        tmp_path,
        parents=[
            {"id": 1, "name": "alice", "score": 150},  # score__le violation
            {"id": 2, "name": "bob", "score": 50},  # conforming
        ],
        children=[
            {"id": 10, "customer_id": 99, "status": "active"},  # FK orphan
            {"id": 20, "customer_id": 2, "status": "pending"},  # status__isin violation
        ],
    )
    dag = pkg.to_relation_dag()
    specs = {r.name: r.to_typespec() for r in pkg.resources}

    result = dag.validate(specs, backend=backend_name)

    assert result.passes is False
    assert result.fk_result.passes is False

    parents_summaries = result.results["parents"].check_summaries
    assert _status(parents_summaries, "score__le") == "failed"

    children_summaries = result.results["children"].check_summaries
    assert _status(children_summaries, "status__isin") == "failed"

    fk_summary = result.fk_result.check_summaries.row(0, named=True)
    assert fk_summary["check_id"] == "fk__children__customer_id__parents"
    assert fk_summary["status"] == "failed"
    assert fk_summary["fail_count"] == 1


def test_pattern_violation_detected_polars(tmp_path):
    """Polars-only: the `pattern` check correctly reports "failed" for a
    value violating the constraint. Narrowed from the cross-backend test
    above — narwhals/ibis-duckdb both silently report "passed" instead
    (item 103, backlog: `pattern-constraint-check-silently-passes-narwhals-ibis-duckdb.md`),
    a genuine pre-existing defect unrelated to this item's `to_typespec()`
    seam and explicitly out of scope to fix here (spec §7)."""
    pkg = _load_package(
        tmp_path,
        parents=[
            {"id": 1, "name": "alice", "score": 50},  # conforming
            {"id": 2, "name": "BOB2", "score": 50},  # name__pattern violation
        ],
        children=[
            {"id": 10, "customer_id": 1, "status": "active"},
            {"id": 20, "customer_id": 2, "status": "active"},
        ],
    )
    dag = pkg.to_relation_dag()
    specs = {r.name: r.to_typespec() for r in pkg.resources}

    result = dag.validate(specs, backend="polars")

    assert result.passes is False
    parents_summaries = result.results["parents"].check_summaries
    assert _status(parents_summaries, "name__pattern") == "failed"


def test_to_contract_round_trip_via_datapackage(tmp_path):
    """Single-backend unit assertion (never touches a backend): to_contract()
    delegates through the same to_typespec() seam."""
    pkg = _load_package(
        tmp_path,
        parents=[{"id": 1, "name": "alice", "score": 50}],
        children=[{"id": 10, "customer_id": 1, "status": "active"}],
    )
    resource = pkg.resources[0]
    assert resource.to_contract().to_typespec().fields == resource.to_typespec().fields
