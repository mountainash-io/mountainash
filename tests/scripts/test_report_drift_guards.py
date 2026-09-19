"""Smoke tests for the drift guards report script."""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parent.parent.parent / "scripts" / "report_drift_guards.py"


def _load():
    import sys

    mod_name = "report_drift_guards"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_collect_kel_entries_reports_public_argument_restrictions_not_protections():
    entries = _load().collect_kel_entries()
    identities = {(entry.backend, entry.op_name, entry.param_name) for entry in entries}
    assert ("polars", "replace", "substring") in identities
    assert ("ibis-duckdb", "parse_xsd_duration", "*") not in identities
    assert ("polars", "regexp_replace", "position") not in identities


def test_collect_kel_entries_refuses_isolated_registry():
    from mountainash.core.capabilities import CapabilityRegistry

    snapshot = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        with pytest.raises(RuntimeError):
            _load().collect_kel_entries()
    finally:
        CapabilityRegistry.restore(snapshot)


@pytest.mark.parametrize("before", [False, True])
@pytest.mark.parametrize("mutation", ["reset", "restore"])
def test_collect_kel_entries_keeps_captured_generation_after_reset_restore(
    monkeypatch,
    before,
    mutation,
):
    from mountainash.core.capabilities import CapabilityRegistry

    mod = _load()
    expected = mod.collect_kel_entries()
    snapshot = CapabilityRegistry.snapshot()
    CapabilityRegistry.reset()
    isolated = CapabilityRegistry.snapshot()
    CapabilityRegistry.restore(snapshot)
    acquire = CapabilityRegistry._acquire_state

    def change():
        if mutation == "reset":
            CapabilityRegistry.reset()
        else:
            CapabilityRegistry.restore(isolated)

    def acquire_with_change(cls, *, enumeration=False):
        if before:
            change()
        state = acquire(enumeration=enumeration)
        if not before:
            change()
        return state

    monkeypatch.setattr(CapabilityRegistry, "_acquire_state", classmethod(acquire_with_change))
    try:
        if before:
            with pytest.raises(RuntimeError, match="ISOLATED"):
                mod.collect_kel_entries()
        else:
            entries = mod.collect_kel_entries()
            assert entries == expected
    finally:
        CapabilityRegistry.restore(snapshot)


def test_collect_fully_unsupported_finds_string_ops():
    mod = _load()
    gaps = mod.collect_fully_unsupported()
    assert len(gaps) > 0
    op_names = {g.op_name for g in gaps}
    assert "encode" in op_names
    assert "decode" in op_names
    for g in gaps:
        assert len(g.backends) > 0
        assert g.est_cases > 0


def test_collect_manual_xfail_blocks_finds_atan2():
    mod = _load()
    blocks = mod.collect_manual_xfail_blocks()
    names = {b.variable_name for b in blocks}
    assert "_ATAN2_NW_XFAIL" in names
    atan2 = next(b for b in blocks if b.variable_name == "_ATAN2_NW_XFAIL")
    assert atan2.active is True
    assert atan2.reason
    assert atan2.source_file == "test_arg_types_arithmetic.py"
