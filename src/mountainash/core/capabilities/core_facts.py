"""Core polymorphic declarations — replaces the visitor's hardcoded
_raw_value_functions set (spec Section 2). These are AST-shape semantics
shared by every family, so one fact is registered per family."""
from __future__ import annotations

from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import CapabilityFact, CapabilityLevel
from mountainash.core.constants import CONST_BACKEND

_REGISTERED = False


def register_core_polymorphic_facts() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_SET,
        FKEY_MOUNTAINASH_SCALAR_TERNARY,
    )

    polymorphic = [
        # (operation_key, param) — LIST-wrapper literal marker semantics
        # per arguments-vs-options.md §Polymorphic Parameters.
        (FKEY_MOUNTAINASH_SCALAR_TERNARY.COLLECT_VALUES, "*"),
        (FKEY_MOUNTAINASH_SCALAR_SET.IS_IN, "haystack"),
        (FKEY_MOUNTAINASH_SCALAR_SET.IS_NOT_IN, "haystack"),
    ]
    for family in (CONST_BACKEND.POLARS, CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS):
        CapabilityRegistry.register_backend(
            family,
            [
                CapabilityFact(
                    operation_key=op, param=param,
                    level=CapabilityLevel.POLYMORPHIC, backend=family,
                    message="literal collections unwrap to raw values; "
                            "expressions compile through (LIST-wrapper marker)",
                    since="2026-07-05",
                    probe_exempt="polymorphic — both paths supported by design",
                )
                for op, param in polymorphic
            ],
        )
    _REGISTERED = True
