"""Public DataPackage -> RelationDAG structured (ARRAY/OBJECT) smoke test
(Task 10 step 2).

Proves the vision's headline Phase-1 loop (item 8l, mirrored from
test_datapackage_validation_loop.py) closes for structured JSON-text
resources specifically: a real datapackage.json describing an ARRAY field
and an OBJECT field, loaded through the public ``DataPackage`` ->
``RelationDAG`` -> ``ValidationRunner`` surface, produces identical
validation statuses, logical values, and deterministic failures on every
backend -- and the same DAG's native ``collect()``/``collect_with_drift()``
terminals fail closed for an applied JSON-text transport plan (zero
requested-resource materialization before the error) while succeeding
natively for `evolve` and structural-only conform plans.
"""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.relations import LogicalTerminalRequired
from mountainash.relations.dag.dag import RelationDAG
from mountainash.typespec.datapackage import DataPackage

from fixtures.backend_registry import ALL_BACKENDS


def _descriptor() -> dict:
    return {
        "name": "structured-loop",
        "resources": [
            {
                "name": "items",
                "type": "table",
                "data": [],
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "tags", "type": "array"},
                    ],
                    "primaryKey": ["id"],
                },
            },
            {
                "name": "profiles",
                "type": "table",
                "data": [],
                "schema": {
                    "fields": [
                        {"name": "id", "type": "integer"},
                        {"name": "meta", "type": "object"},
                    ],
                    "primaryKey": ["id"],
                },
            },
        ],
    }


def _status(check_summaries, check_id: str) -> str:
    row = check_summaries.filter(check_summaries["check_id"] == check_id)
    assert row.height == 1, f"check {check_id!r} not found in {check_summaries['check_id'].to_list()}"
    return row.row(0, named=True)["status"]


def _items_and_profiles(backend_name, backend_factory, *, duplicate_id: bool = False):
    items = backend_factory.create(
        {"id": [1, 2 if not duplicate_id else 1], "tags": ["[1, 2]", "[3, 4]"]}, backend_name,
    )
    profiles = backend_factory.create(
        {"id": [1, 2], "meta": ['{"a": 1}', '{"a": 2}']}, backend_name,
    )
    return items, profiles


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestPublicDataPackageStructuredLoop:
    def test_validation_status_and_logical_values_match_cross_backend(
        self, backend_name, backend_factory
    ):
        pkg = DataPackage.from_descriptor(_descriptor())
        items, profiles = _items_and_profiles(backend_name, backend_factory)
        dag = pkg.to_relation_dag(overrides={"items": items, "profiles": profiles})
        specs = {r.name: r.to_typespec() for r in pkg.resources}

        result = dag.validate(specs)

        assert result.passes is True, backend_name
        assert _status(result.results["items"].check_summaries, "primary_key_unique") == "passed", backend_name
        assert _status(result.results["profiles"].check_summaries, "primary_key_unique") == "passed", backend_name

    def test_duplicate_primary_key_reports_the_same_deterministic_failure_cross_backend(
        self, backend_name, backend_factory
    ):
        """Item 8j's characterization (mirrored from
        test_datapackage_validation_loop.py): a declared primary_key
        resolving to keyed identity is isolated into that resource's own
        failing result (check_id="__identity__") rather than raised out of
        dag.validate -- the batch still returns a DAGValidationResult, and
        the sibling resource's own independent primary key is untouched."""
        pkg = DataPackage.from_descriptor(_descriptor())
        items, profiles = _items_and_profiles(backend_name, backend_factory, duplicate_id=True)
        dag = pkg.to_relation_dag(overrides={"items": items, "profiles": profiles})
        specs = {r.name: r.to_typespec() for r in pkg.resources}

        result = dag.validate(specs)  # must not raise

        assert result.passes is False, backend_name
        items_result = result.results["items"]
        assert _status(items_result.check_summaries, "__identity__") == "error", backend_name
        # profiles carries its own independent primary key -- untouched by
        # items' duplicate (spec item 8j §3.2 isolation).
        assert _status(result.results["profiles"].check_summaries, "primary_key_unique") == "passed", backend_name

    def test_one_materialization_per_resource(self, backend_name, backend_factory, monkeypatch):
        import mountainash.relations.core.materialization as materialization_module

        pkg = DataPackage.from_descriptor(_descriptor())
        items, profiles = _items_and_profiles(backend_name, backend_factory)
        dag = pkg.to_relation_dag(overrides={"items": items, "profiles": profiles})
        specs = {r.name: r.to_typespec() for r in pkg.resources}

        calls: list[str] = []
        original = materialization_module.materialize_native

        def spy(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(materialization_module, "materialize_native", spy)

        dag.validate(specs)

        # One materialization per DAG-registered resource -- the shared
        # session cache (spec 10.2/10.3) never re-collects "items" or
        # "profiles" once each is compiled.
        assert len(calls) == 2, backend_name


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestPublicDataPackageNativeTerminals:
    """Native ``collect()``/``collect_with_drift()`` terminal behavior over
    the SAME DataPackage-declared structured schema (public ``RelationDAG``
    API, spec Task 9 step 6): fail closed for an applied JSON-text
    transport plan, and succeed natively for `evolve` and structural-only
    conform -- across the complete backend matrix."""

    def _dag(self, backend_name, backend_factory, *, action="coerce", apply_value_transforms=True):
        pkg = DataPackage.from_descriptor(_descriptor())
        spec = next(r.to_typespec() for r in pkg.resources if r.name == "profiles")
        df = backend_factory.create({"id": [1, 2], "meta": ['{"a": 1}', '{"a": 2}']}, backend_name)
        rel = ma.relation(df).conform(
            spec, contract={"data_type": action}, apply_value_transforms=apply_value_transforms
        )
        dag = RelationDAG()
        dag.add("profiles", rel)
        return dag

    @pytest.mark.parametrize("terminal", ["collect", "collect_with_drift"])
    def test_native_terminal_fails_closed_for_applied_transport(
        self, backend_name, backend_factory, terminal
    ):
        dag = self._dag(backend_name, backend_factory)
        with pytest.raises(LogicalTerminalRequired):
            getattr(dag, terminal)("profiles")

    def test_zero_materialization_before_the_native_terminal_error(
        self, backend_name, backend_factory, monkeypatch
    ):
        import mountainash.relations.core.materialization as materialization_module

        dag = self._dag(backend_name, backend_factory)
        calls: list[str] = []
        original = materialization_module.materialize_native

        def spy(*args, **kwargs):
            calls.append(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(materialization_module, "materialize_native", spy)

        with pytest.raises(LogicalTerminalRequired):
            dag.collect("profiles")
        assert calls == [], backend_name

    def test_evolve_collects_natively(self, backend_name, backend_factory):
        dag = self._dag(backend_name, backend_factory, action="evolve")
        result = dag.collect("profiles")
        assert result is not None, backend_name

    def test_structural_only_collects_natively(self, backend_name, backend_factory):
        dag = self._dag(backend_name, backend_factory, apply_value_transforms=False)
        result = dag.collect("profiles")
        assert result is not None, backend_name
