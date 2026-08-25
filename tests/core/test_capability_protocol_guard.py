"""Closed-by-default guards for the declaration protocol (spec rev 3, §7)."""
from __future__ import annotations

import importlib
import subprocess
import sys
import textwrap

import pytest

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityLevel,
    CapabilityRegistry,
    Domain,
    load_all_capability_declarations,
)
from mountainash.core.capabilities.bootstrap import discover_declaration_modules
from mountainash.core.capabilities.declarations import classify_domain
from mountainash.core.capabilities.retired import assert_no_active_retired_overlap


# Spec §3 placement decision table — closed leaf set. Every declaration module
# the spec mandates lives in this tuple; the protocol guard (M-4 folded into
# I-1) refuses to discover anything outside it, so a stray _-prefix rename
# or a missing module flips the assertion to red instead of silently slipping
# through the lax `>= 12` count.
EXPECTED_DECLARATION_MODULES = (
    # expressions/backends/capabilities/
    "mountainash.expressions.backends.capabilities.arithmetic",
    "mountainash.expressions.backends.capabilities.boolean",
    "mountainash.expressions.backends.capabilities.categorical",
    "mountainash.expressions.backends.capabilities.datetime.any",
    "mountainash.expressions.backends.capabilities.datetime.default",
    "mountainash.expressions.backends.capabilities.datetime.extract",
    "mountainash.expressions.backends.capabilities.datetime.options",
    "mountainash.expressions.backends.capabilities.datetime.rounding",
    "mountainash.expressions.backends.capabilities.datetime.strptime",
    "mountainash.expressions.backends.capabilities.datetime.value_classes_ma",
    "mountainash.expressions.backends.capabilities.datetime.value_classes_substrait",
    "mountainash.expressions.backends.capabilities.datetime.xsd",
    "mountainash.expressions.backends.capabilities.geospatial",
    "mountainash.expressions.backends.capabilities.ibis",
    "mountainash.expressions.backends.capabilities.list",
    "mountainash.expressions.backends.capabilities.narwhals",
    "mountainash.expressions.backends.capabilities.polars",
    "mountainash.expressions.backends.capabilities.polymorphic",
    "mountainash.expressions.backends.capabilities.string",
    "mountainash.expressions.backends.capabilities.struct",
    # relations/backends/capabilities/
    "mountainash.relations.backends.capabilities.ibis",
    "mountainash.relations.backends.capabilities.narwhals",
    "mountainash.relations.backends.capabilities.polars",
)


def test_every_discovered_module_is_well_formed():
    discovered = discover_declaration_modules()
    assert discovered == EXPECTED_DECLARATION_MODULES
    for name in discovered:
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
# Each row: module-leaf -> predicate(fact) that every fact in the module must
# satisfy. The predicate encodes BOTH the OWNER column (where the fact lives,
# derived from `operation_key`'s enum membership or the backend match) AND
# the GRAIN column (the discriminator that pins that owner — option_value set,
# value_class set, param == WILDCARD_PARAM, or level+annotation). The table
# is the single source — no separately maintained guard map (review I-1).
#
# | Fact grain (GRAIN column)                       | Owner (OWNER column)                          |
# |--------------------------------------------------|-----------------------------------------------|
# | option_value set                                 | domain module (string / arithmetic / datetime |
# |                                                  |   /options/strptime)                          |
# | param == WILDCARD_PARAM (GATE, op-level wildcard)| domain module                                 |
# | value-agnostic positional-arg option fact        | domain module                                 |
# | value_class set                                  | datetime/value_classes_ma|substrait.py        |
# | level == LITERAL_ONLY / EXPR_CAPABLE refinement  | backend module (polars / narwhals / ibis, expr)|
# | level == POLYMORPHIC                             | polymorphic.py                                |
# | RKEY (any grain)                                 | relations/backends/capabilities/{backend}.py  |
# | ROUTER_METADATA / MATERIALIZE_RESIDUE            | backend module (root per FKEY/RKEY as above)  |


def _backend_predicate(leaf: str):
    """expr- or relation-backend module. LITERAL_ONLY or EXPR_CAPABLE
    refinement for arg-type gates; UNSUPPORTED is also legal — for whole-op
    WILDCARD_PARAM GATE facts and the ROUTER_METADATA / MATERIALIZE_RESIDUE
    row of the spec §3 table. NOT value_class; backend matches the module's
    leaf name."""
    return lambda f: (
        f.backend.value == leaf
        and f.value_class is None
        and f.level in (
            CapabilityLevel.LITERAL_ONLY,
            CapabilityLevel.EXPR_CAPABLE,
            CapabilityLevel.UNSUPPORTED,
        )
    )


def _polymorphic_predicate():
    """polymorphic module. level == POLYMORPHIC."""
    return lambda f: f.level is CapabilityLevel.POLYMORPHIC


def _value_class_predicate():
    """value-class module. every fact has value_class is not None."""
    return lambda f: f.value_class is not None


def _domain_predicate(leaf: str):
    """domain module. operation_key classifies to the module's domain; NOT
    value_class (domain modules allow option-value / WILDCARD_PARAM / value-
    agnostic / positional grains only); NOT POLYMORPHIC level (POLYMORPHIC
    marker facts live in polymorphic.py per spec §3)."""
    domains = {
        "boolean": Domain.BOOLEAN,
        "categorical": Domain.CATEGORICAL,
        "geospatial": Domain.GEOSPATIAL,
        "list": Domain.LIST,
        "struct": Domain.STRUCT,
        "string": Domain.STRING, "arithmetic": Domain.ARITHMETIC,
        "any": Domain.DATETIME, "default": Domain.DATETIME,
        "xsd": Domain.DATETIME, "options": Domain.DATETIME,
        "strptime": Domain.DATETIME, "extract": Domain.DATETIME,
        "rounding": Domain.DATETIME,
    }
    want = domains[leaf]
    return lambda f: (
        classify_domain(f.operation_key) is want
        and f.value_class is None
        and f.level is not CapabilityLevel.POLYMORPHIC
    )


def test_placement_decision_table():
    discovered = discover_declaration_modules()
    assert discovered == EXPECTED_DECLARATION_MODULES, (
        f"discovered modules differ from spec §3 leaf set:\n"
        f"  extra:   {set(discovered) - set(EXPECTED_DECLARATION_MODULES)}\n"
        f"  missing: {set(EXPECTED_DECLARATION_MODULES) - set(discovered)}"
    )
    for name in EXPECTED_DECLARATION_MODULES:
        module = importlib.import_module(name)
        facts = [f for d in module.DECLARATIONS for f in d.facts]
        if ".relations." in name:
            # Relation facts (RKEY) live in the relations-backends module of
            # their restricted backend; the spec grants "any grain" — the
            # test pins only the OWNER column (Domain.RELATION) here. The
            # backend and grain rows above also apply transitively, but this
            # branch is the spec's own row for RKEY_ facts.
            assert all(
                classify_domain(f.operation_key) is Domain.RELATION for f in facts
            ), name
        elif name.endswith(".polymorphic"):
            assert all(_polymorphic_predicate()(f) for f in facts), name
        elif any(name.endswith(s) for s in (
            ".value_classes_ma", ".value_classes_substrait"
        )):
            assert all(_value_class_predicate()(f) for f in facts), name
        elif any(name.endswith(s) for s in (".ibis", ".narwhals", ".polars")):
            leaf = name.rsplit(".", 1)[1]
            assert all(_backend_predicate(leaf)(f) for f in facts), name
        else:
            leaf = name.rsplit(".", 1)[1]
            assert all(_domain_predicate(leaf)(f) for f in facts), name


_SUBPROCESS_PRELUDE = """
import sys

class _Block:
    def __init__(self, names): self.names = names
    def find_spec(self, fullname, path=None, target=None):
        # Modern meta-path hook (find_module/load_module were removed in 3.12);
        # raising here surfaces as the import's ModuleNotFoundError.
        if fullname.split(".")[0] in self.names:
            raise ModuleNotFoundError(f"blocked optional backend: {fullname}")
        return None

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
        assert CapabilityRegistry._predicate_facts == []
        assert CapabilityRegistry._kinds == {}
        print("OK")
    """)
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=180
    )
    assert out.returncode == 0, out.stderr


def test_no_fact_simultaneously_active_and_retired():
    load_all_capability_declarations()
    assert_no_active_retired_overlap(CapabilityRegistry)
