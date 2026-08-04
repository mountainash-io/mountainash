"""Identity-keyed capability inventory — the closed allowlist Task 7's
compile_smoke harness consumes as an inline closed rule
(spec 2026-08-01-spine-derived-test-expectations, Task 6)."""
import dataclasses

import pytest
import yaml

from tests.fixtures.capability_census import UNRESOLVED
from tests.fixtures.capability_inventory import (
    VALID_CLASSIFICATIONS,
    VALID_FOUND_VIA,
    InventoryError,
    _identity_key,
    inventory_has,
    load_inventory,
)


def _slotted_unresolved(entry) -> bool:
    return UNRESOLVED in (
        entry.operation_key,
        entry.backend,
        entry.param,
        entry.option_value,
    )


def test_entries_are_well_formed():
    inv = load_inventory()
    assert inv, "inventory is empty"
    for entry in inv.values():
        assert entry.classification in VALID_CLASSIFICATIONS, entry.classification
        assert entry.found_via in VALID_FOUND_VIA, entry.found_via
        assert isinstance(entry.runtime_observable, bool)
        assert entry.since, "missing since marker"
        assert ":" in entry.display_site, entry.display_site
        # the composite key is the identity of its own slots
        assert entry.key == _identity_key(
            entry.node_id,
            entry.operation_key,
            entry.backend,
            entry.param,
            entry.option_value,
        )


def test_load_inventory_raises_on_duplicate_key(tmp_path):
    entry = next(iter(load_inventory().values()))
    row = dataclasses.asdict(entry)
    path = tmp_path / "dup.yaml"
    path.write_text(yaml.safe_dump([row, dict(row)], sort_keys=False))
    with pytest.raises(InventoryError):
        load_inventory(path)


def test_unresolved_slotted_rows_are_not_runtime_observable():
    inv = load_inventory()
    # invariant holds across the committed catalogue
    for entry in inv.values():
        if _slotted_unresolved(entry):
            assert entry.runtime_observable is False, entry.key


def test_unresolved_runtime_observable_row_is_rejected(tmp_path):
    unresolved = next(
        e for e in load_inventory().values() if _slotted_unresolved(e)
    )
    row = dataclasses.asdict(unresolved)
    row["runtime_observable"] = True
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump([row], sort_keys=False))
    with pytest.raises(InventoryError):
        load_inventory(path)


def test_inventory_has_matches_exact_identity_and_rejects_near_miss():
    inv = load_inventory()
    entry = next(iter(inv.values()))
    assert inventory_has(
        entry.node_id,
        entry.operation_key,
        entry.backend,
        entry.param,
        entry.option_value,
    )
    # a near-miss on any single slot is not a member
    assert not inventory_has(
        entry.node_id + "~miss",
        entry.operation_key,
        entry.backend,
        entry.param,
        entry.option_value,
    )
    assert not inventory_has(
        entry.node_id,
        entry.operation_key,
        entry.backend + "~miss",
        entry.param,
        entry.option_value,
    )
