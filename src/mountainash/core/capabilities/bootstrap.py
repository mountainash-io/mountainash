"""Load every capability declaration in the codebase.

Any consumer that enumerates CapabilityRegistry.facts() (probes, integrity
guards, upstream-join tests, report generators, plan validation) calls this
first. Declaration modules are import-safe pure data and are loaded
unconditionally. Optional native backends are imported only by their
implementation classes, not here.
"""
from __future__ import annotations

import importlib

_DECLARATION_MODULES = (
    "mountainash.expressions.backends.expression_systems.polars.base",
    "mountainash.expressions.backends.expression_systems.ibis_capabilities",
    "mountainash.expressions.backends.expression_systems.narwhals.base",
    "mountainash.relations.backends.relation_systems.narwhals.base",
    "mountainash.core.capabilities.core_facts",
)

_loaded = False


def load_all_capability_declarations() -> None:
    """Import every declaration module unconditionally and idempotently."""
    global _loaded
    if _loaded:
        return
    for module in _DECLARATION_MODULES:
        importlib.import_module(module)
    from mountainash.core.capabilities.core_facts import register_core_polymorphic_facts

    register_core_polymorphic_facts()
    _loaded = True
