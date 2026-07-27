"""Load every capability declaration in the codebase.

Any consumer that enumerates CapabilityRegistry.facts() (probes, integrity
guards, upstream-join tests, report generators, plan validation) calls this
first. Declaration modules are import-safe pure data and are loaded
unconditionally, so capability facts register even when an optional native
backend (e.g. ibis) is not installed. The declaration modules import no
backend library themselves; a backend's native library is imported only when
that backend is actually available (its implementation package probes the
dependency and skips cleanly when absent).
"""
from __future__ import annotations

import importlib

_DECLARATION_MODULES = (
    "mountainash.expressions.backends.expression_systems.arithmetic_option_capabilities",
    "mountainash.expressions.backends.expression_systems.string_option_capabilities",
    "mountainash.expressions.backends.expression_systems.datetime_option_capabilities",
    "mountainash.expressions.backends.expression_systems.datetime_value_class_capabilities_ma",
    "mountainash.expressions.backends.expression_systems.datetime_value_class_capabilities_substrait",
    "mountainash.expressions.backends.expression_systems.polars.base",
    "mountainash.expressions.backends.expression_systems.ibis_capabilities",
    "mountainash.expressions.backends.expression_systems.narwhals.base",
    "mountainash.relations.backends.relation_systems.narwhals.base",
    "mountainash.relations.backends.relation_systems.polars.base",
    "mountainash.relations.backends.relation_systems.ibis_relation_capabilities",
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
