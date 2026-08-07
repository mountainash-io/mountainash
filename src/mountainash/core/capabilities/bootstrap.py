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
    "mountainash.expressions.backends.expression_systems.strptime_format_capabilities",
    "mountainash.expressions.backends.expression_systems.polars.base",
    "mountainash.expressions.backends.expression_systems.ibis_capabilities",
    "mountainash.expressions.backends.expression_systems.narwhals.base",
    "mountainash.relations.backends.relation_systems.narwhals.base",
    "mountainash.relations.backends.relation_systems.polars.base",
    "mountainash.relations.backends.relation_systems.ibis_relation_capabilities",
    "mountainash.core.capabilities.core_facts",
)


def _load_into_registry() -> None:
    """Import every declaration module and register (registry-internal hook;
    called ONLY by CapabilityRegistry under its load lock)."""
    for module in _DECLARATION_MODULES:
        importlib.import_module(module)
    from mountainash.core.capabilities.core_facts import register_core_polymorphic_facts

    register_core_polymorphic_facts()


def load_all_capability_declarations() -> None:
    """Public entry: enumerating consumers call this; queries autoload it."""
    from mountainash.core.capabilities.registry import CapabilityRegistry, _LoadState

    state = CapabilityRegistry._load_state
    if state is _LoadState.LOADED:
        return
    if state is _LoadState.ISOLATED:
        raise RuntimeError(
            "registry is ISOLATED (reset() without restore()); refusing to "
            "load production declarations into an isolated registry"
        )
    CapabilityRegistry._ensure_loaded()


def __getattr__(name: str):
    """Backward-compat shim for the pre-Task-4 module-level `_loaded` flag.

    The state machine replaced the one-shot `_loaded` guard; the cold-path
    test in tests/core/test_capability_gate.py still inspects this name, so
    expose it as a derived view of `_load_state`.
    """
    if name == "_loaded":
        from mountainash.core.capabilities.registry import (
            CapabilityRegistry,
            _LoadState,
        )

        return CapabilityRegistry._load_state is _LoadState.LOADED
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
