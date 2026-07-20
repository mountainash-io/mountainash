"""Load every capability declaration in the codebase.

Any consumer that enumerates CapabilityRegistry.facts() (probes, integrity
guards, upstream-join tests, report generators, plan validation) calls this
first. Backends whose optional dependency is absent are skipped — their
facts simply don't load, matching how the backend itself behaves.
"""
from __future__ import annotations

import importlib

_DECLARATION_MODULES = (
    "mountainash.expressions.backends.expression_systems.polars.base",
    "mountainash.expressions.backends.expression_systems.ibis.base",
    "mountainash.expressions.backends.expression_systems.narwhals.base",
    "mountainash.relations.backends.relation_systems.polars.base",
    "mountainash.relations.backends.relation_systems.ibis.base",
    "mountainash.relations.backends.relation_systems.narwhals.base",
    "mountainash.core.capabilities.core_facts",
)

_loaded = False


def load_all_capability_declarations() -> None:
    """Import every declaration module (idempotent). Optional backends whose
    dependency is missing are skipped, exactly as the backend itself would be.
    """
    global _loaded
    if _loaded:
        return
    for module in _DECLARATION_MODULES:
        try:
            importlib.import_module(module)
        except ImportError:
            continue  # optional backend not installed — its facts don't apply
    from mountainash.core.capabilities.core_facts import register_core_polymorphic_facts

    register_core_polymorphic_facts()
    _loaded = True
