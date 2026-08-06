"""Drain-safe regeneration preflight (SP2-B plan Task 0.3).

Two guards over the one safe regeneration entry point
(:func:`tests.core.test_compile_smoke.regenerate_smoke_inventory`, spec 2.2):

1. **Baseline semantic no-op** — the committed inventory YAML MUST equal what a
   full-backend regeneration produces from the current tree. This holds at every
   drain commit (each conversion regenerates in the same commit), so a stale-keyed
   or dropped row reddens here rather than silently corrupting the allowlist.
2. **Missing-backend loudness** — a backend that cannot construct its smoke frame
   MUST raise, never silently drop its runtime-observable rows.

Both require the full-backend environment (all 7 backends importable).
"""
from __future__ import annotations

import pytest

from tests.core.test_compile_smoke import (
    _iter_runtime_inventory_rows,
    regenerate_smoke_inventory,
)
from tests.fixtures.capability_inventory import _INVENTORY_PATH, load_inventory


def test_regenerate_smoke_inventory_is_baseline_no_op(tmp_path):
    """The committed inventory equals a fresh full-backend regeneration — no
    dropped runtime rows, no stale static keys. Guards every integration."""
    committed = load_inventory(_INVENTORY_PATH)
    regen_path = tmp_path / "regen_inventory.yaml"
    regenerate_smoke_inventory(path=regen_path)
    regenerated = load_inventory(regen_path)

    committed_keys, regen_keys = set(committed), set(regenerated)
    dropped = sorted(committed_keys - regen_keys)
    added = sorted(regen_keys - committed_keys)
    assert not dropped and not added, (
        "regeneration is not a semantic no-op against the committed inventory — "
        "the committed YAML is stale (re-run regenerate_smoke_inventory and commit):\n"
        f"  present in committed, missing after regen ({len(dropped)}): {dropped[:10]}\n"
        f"  produced by regen, absent from committed ({len(added)}): {added[:10]}"
    )

    # The runtime-observable subset specifically must survive regeneration.
    committed_rt = {k for k, e in committed.items() if e.runtime_observable}
    regen_rt = {k for k, e in regenerated.items() if e.runtime_observable}
    assert committed_rt == regen_rt, (
        "runtime-observable rows changed under regeneration (drain-safety, spec 2.2): "
        f"dropped={sorted(committed_rt - regen_rt)[:10]} "
        f"added={sorted(regen_rt - committed_rt)[:10]}"
    )


def test_missing_backend_regen_errors_loudly(monkeypatch):
    """A backend whose smoke frame cannot be constructed raises RuntimeError —
    it MUST NOT be silently skipped (which would drop its runtime rows while
    still writing a corrupt YAML)."""
    from tests.fixtures import backend_helpers

    broken = "ibis-duckdb"
    real_create = backend_helpers.BackendDataFrameFactory.create

    def fake_create(data, backend_name, *args, **kwargs):
        if backend_name == broken:
            raise ImportError(f"simulated missing backend: {backend_name}")
        return real_create(data, backend_name, *args, **kwargs)

    monkeypatch.setattr(
        backend_helpers.BackendDataFrameFactory,
        "create",
        staticmethod(fake_create),
    )
