"""Meta-test: every argument-kind protocol param must appear in exactly one TESTED_PARAMS list."""
from __future__ import annotations

import importlib

from cross_backend.argument_types._introspection import introspect_protocols

_CATEGORY_MODULES = [
    "test_arg_types_string",
    "test_arg_types_arithmetic",
    "test_arg_types_comparison",
    "test_arg_types_boolean",
    "test_arg_types_null",
    "test_arg_types_rounding",
    "test_arg_types_logarithmic",
    "test_arg_types_datetime",
    "test_arg_types_name",
    "test_arg_types_window",
    "test_arg_types_aggregate",
    "test_arg_types_misc",
]


def _collect_tested_params() -> set[tuple[str, str]]:
    tested: set[tuple[str, str]] = set()
    for modname in _CATEGORY_MODULES:
        try:
            mod = importlib.import_module(f"cross_backend.argument_types.{modname}")
        except ImportError:
            continue
        for fkey, pname in getattr(mod, "TESTED_PARAMS", []):
            op_name = fkey.name.lower() if hasattr(fkey, "name") else str(fkey)
            tested.add((op_name, pname))
    return tested


def test_every_argument_param_is_tested():
    introspected = {
        (p.op_name, p.param_name)
        for p in introspect_protocols()
        if p.kind == "argument"
    }
    tested = _collect_tested_params()
    missing = {(op, pname) for op, pname in introspected if (op, pname) not in tested}
    extra = {(op, pname) for op, pname in tested if (op, pname) not in introspected}
    assert not missing, f"Argument params with no test: {sorted(missing)}"
    assert not extra, f"Tested params with no protocol: {sorted(extra)}"


def test_no_unclassified_params():
    unclassified = [p for p in introspect_protocols() if p.kind == "unclassified"]
    assert not unclassified, (
        f"Protocol params with ambiguous typing (fix in Phase 0): "
        f"{[(p.protocol_name, p.op_name, p.param_name, p.annotation) for p in unclassified]}"
    )
