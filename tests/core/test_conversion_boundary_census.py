"""Closed conversion-boundary census: exact inventory equality and wrapper
enforcement.

See ``mountainash-central/04.planning/mountainash/superpowers/specs/
2026-08-27-pandas-transit-elimination-design.md`` section 13.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from tests.core._transit_census import (
    RISKY_METHOD_NAMES,
    discover_transit_candidates,
    load_inventory,
)
from mountainash.core.transit import TransitClass

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src" / "mountainash"
_INVENTORY_PATH = _REPO_ROOT / "tests" / "fixtures" / "transit_inventory.json"


def test_current_transit_inventory_is_complete():
    discovered = discover_transit_candidates(_SRC_ROOT)
    inventoried = load_inventory(_INVENTORY_PATH)
    assert {item.identity for item in discovered} == {
        item.identity for item in inventoried
    }


def test_inventory_entries_have_policy_reason_and_date():
    entries = load_inventory(_INVENTORY_PATH)
    valid_classes = {member.name for member in TransitClass}
    for entry in entries:
        assert entry.transit_class in valid_classes, entry
        assert entry.reason.strip(), entry
        date.fromisoformat(entry.since)


def test_new_unwrapped_to_pandas_call_fails_closed(tmp_path):
    module = tmp_path / "new_route.py"
    module.write_text("def convert(frame):\n    return frame.to_pandas()\n")
    discovered = discover_transit_candidates(tmp_path)
    assert discovered[0].wrapped is False


def test_census_fixture_rejects_every_undeclared_dispatch_shape(tmp_path):
    """One fixture module exercising every pattern the closed census must
    catch even though none of them route through `transit_call()`:
    a Narwhals constructor with a literal pandas destination, a stored bound
    method used as a callback, a `transit_call()` invocation with a computed
    (non-literal) `BoundaryKey`, and an unwrapped `getattr()` dispatch."""
    module = tmp_path / "undeclared.py"
    module.write_text(
        "import narwhals as nw\n"
        "from mountainash.core.transit import transit_call\n"
        "\n"
        "def convert(value, dynamic_key, values):\n"
        "    data = nw.from_dict({'a': [1]}, backend='pandas')\n"
        "    callback = value.to_pandas\n"
        "    mapped = list(map(callback, values))\n"
        "    result = transit_call(dynamic_key, value.execute)\n"
        "    other = getattr(value, 'execute')\n"
        "    return data, mapped, result, other\n"
    )
    discovered = discover_transit_candidates(tmp_path)
    by_callee = {}
    for candidate in discovered:
        by_callee.setdefault(candidate.callee, []).append(candidate)

    assert "from_dict" in by_callee
    assert all(not c.wrapped for c in by_callee["from_dict"])

    assert "to_pandas" in by_callee
    assert all(not c.wrapped for c in by_callee["to_pandas"])

    assert "execute" in by_callee
    assert len(by_callee["execute"]) == 2
    assert all(not c.wrapped for c in by_callee["execute"]), (
        "a computed BoundaryKey must never count as wrapped"
    )


def test_every_wrapped_candidate_uses_a_literal_boundary_key(tmp_path):
    """A `transit_call()` site is `wrapped=True` only when its key is a
    literal `BoundaryKey.MEMBER` attribute access."""
    module = tmp_path / "wrapped.py"
    module.write_text(
        "from mountainash.core.transit import BoundaryKey, transit_call\n"
        "\n"
        "def convert(value):\n"
        "    return transit_call(BoundaryKey.IBIS_NATIVE_CACHE, value.execute)\n"
    )
    discovered = discover_transit_candidates(tmp_path)
    assert len(discovered) == 1
    assert discovered[0].wrapped is True
    assert discovered[0].callee == "execute"


def test_risky_method_names_cover_the_documented_generic_set():
    assert RISKY_METHOD_NAMES == {
        "execute",
        "to_pandas",
        "to_pandas_batches",
        "from_pandas",
        "collect",
        "to_native",
        "to_polars",
        "to_arrow",
        "to_pyarrow",
        "memtable",
    }


def test_every_inventory_boundary_key_has_a_reason_when_internal_execution_transit():
    """Every prohibited (INTERNAL_EXECUTION_TRANSIT) row documents the
    specific reason it is prohibited, not a generic placeholder."""
    entries = load_inventory(_INVENTORY_PATH)
    prohibited = [
        entry for entry in entries if entry.transit_class == "INTERNAL_EXECUTION_TRANSIT"
    ]
    assert prohibited, "expected at least one INTERNAL_EXECUTION_TRANSIT row"
    for entry in prohibited:
        assert entry.legacy_unwrapped is True, entry
        assert len(entry.reason) > 20, entry
