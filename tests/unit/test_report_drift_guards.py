"""Smoke tests for the drift guards report script."""
import importlib.util
from pathlib import Path

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


def test_collect_protocol_alignment_returns_entries():
    mod = _load()
    gaps = mod.collect_protocol_alignment()
    assert len(gaps) > 0
    g = gaps[0]
    assert g.protocol_name
    assert g.method_name
    assert g.reason
    assert g.since


def test_collect_kel_entries_returns_entries_for_each_backend():
    mod = _load()
    entries = mod.collect_kel_entries()
    assert len(entries) > 0
    backends_found = {e.backend for e in entries}
    assert "polars" in backends_found
    assert "narwhals" in backends_found
    assert "ibis" in backends_found
    e = entries[0]
    assert e.op_name
    assert e.param_name
    assert e.message
    assert e.est_cases > 0


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
