"""Closed-by-default guards for the declaration protocol (spec rev 3, §7)."""
from __future__ import annotations

import importlib
import subprocess
import sys
import textwrap

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityRegistry,
    Domain,
    load_all_capability_declarations,
)
from mountainash.core.capabilities.bootstrap import discover_declaration_modules
from mountainash.core.capabilities.declarations import (
    classify_domain,
    classify_source,
)
from mountainash.core.capabilities.retired import assert_no_active_retired_overlap
from mountainash.core.capabilities.schema import WILDCARD_PARAM


def test_every_discovered_module_is_well_formed():
    names = discover_declaration_modules()
    assert len(names) >= 12  # string, arithmetic, 4x datetime, polymorphic,
                             # 3x expr-backend, 3x relation-backend
    for name in names:
        module = importlib.import_module(name)
        decls = module.DECLARATIONS
        assert isinstance(decls, tuple) and decls, name
        for d in decls:
            assert isinstance(d, CapabilityDeclaration), (name, d)


def test_same_key_declarations_have_distinct_evidence():
    for name in discover_declaration_modules():
        module = importlib.import_module(name)
        seen: dict[tuple, list] = {}
        for d in module.DECLARATIONS:
            seen.setdefault((d.backend, d.source, d.domain), []).append(d.evidence)
        for key, evidences in seen.items():
            assert len(evidences) == len(set(evidences)), (
                f"{name}: same-key declarations {key} share evidence — "
                "one declaration per probe wave"
            )


# Placement decision table (spec §3) — THE guard config, nothing else.
# module-leaf -> predicate(fact) that every fact in the module must satisfy.
def _is_domain_module_fact(module_leaf: str):
    domains = {
        "string": Domain.STRING, "arithmetic": Domain.ARITHMETIC,
        "options": Domain.DATETIME, "value_classes_ma": Domain.DATETIME,
        "value_classes_substrait": Domain.DATETIME, "strptime": Domain.DATETIME,
    }
    want = domains[module_leaf]
    return lambda f: classify_domain(f.operation_key) is want


_BACKEND_MODULES = {"polars", "narwhals", "ibis"}


def test_placement_decision_table():
    for name in discover_declaration_modules():
        leaf = name.rsplit(".", 1)[1]
        module = importlib.import_module(name)
        facts = [f for d in module.DECLARATIONS for f in d.facts]
        if ".relations." in name:
            assert all(
                classify_domain(f.operation_key) is Domain.RELATION for f in facts
            ), name
        elif leaf in _BACKEND_MODULES:
            # backend modules: the backend is the module's namesake
            assert all(f.backend.value == leaf for f in facts), name
        elif leaf == "polymorphic":
            assert all(
                classify_domain(f.operation_key) in (Domain.SET, Domain.TERNARY)
                for f in facts
            ), name
        else:
            pred = _is_domain_module_fact(leaf)
            assert all(pred(f) for f in facts), name


_SUBPROCESS_PRELUDE = """
import sys

class _Block:
    def __init__(self, names): self.names = names
    def find_module(self, fullname, path=None):
        return self if fullname.split(".")[0] in self.names else None
    def load_module(self, fullname):
        raise ImportError(f"blocked optional backend: {fullname}")

sys.meta_path.insert(0, _Block({"ibis", "narwhals"}))
"""


def test_import_safety_without_optional_backends():
    code = _SUBPROCESS_PRELUDE + textwrap.dedent("""
        from mountainash.core.capabilities.bootstrap import (
            discover_declaration_modules,
        )
        import importlib
        total = 0
        for name in discover_declaration_modules():
            module = importlib.import_module(name)
            total += len(module.DECLARATIONS)
        print("OK", total)
    """)
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=180
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.startswith("OK "), out.stdout


def test_no_registration_side_effects_on_import():
    code = textwrap.dedent("""
        import importlib
        from mountainash.core.capabilities.bootstrap import (
            discover_declaration_modules,
        )
        from mountainash.core.capabilities.registry import CapabilityRegistry
        for name in discover_declaration_modules():
            importlib.import_module(name)
        assert CapabilityRegistry._facts == {}, "import side-effect registration"
        assert CapabilityRegistry._value_class_facts == {}
        print("OK")
    """)
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=180
    )
    assert out.returncode == 0, out.stderr


def test_no_fact_simultaneously_active_and_retired():
    load_all_capability_declarations()
    assert_no_active_retired_overlap(CapabilityRegistry)
