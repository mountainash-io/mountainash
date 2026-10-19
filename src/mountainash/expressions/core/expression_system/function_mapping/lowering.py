"""Concrete built-in expression implementation declarations."""

from mountainash.core.lowering_reuse import (
    DEFERRED_ONLY,
    OCCURRENCE,
    REPEATABLE,
    declare_lowering,
)


def declare_builtin_expression_system(system_type, backend_type):
    """Annotate each composed builtin method selected by the expression registry."""
    from . import definitions
    from ..function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME,
        FKEY_MOUNTAINASH_SCALAR_LIST,
    )

    # Share the cached authoritative builtin group builder with registration.
    for definition in definitions._builtin_function_definitions():
        method = definition.protocol_method
        if method is None:
            continue
        implementation = getattr(system_type, method.__name__, None)
        if implementation is None:
            continue
        if definition.function_key is FKEY_MOUNTAINASH_SCALAR_LIST.SAMPLE:
            declare_lowering(implementation, DEFERRED_ONLY)
        elif definition.function_key is FKEY_MOUNTAINASH_SCALAR_DATETIME.TODAY:
            declare_lowering(implementation, OCCURRENCE)
        elif definition.function_key is FKEY_MOUNTAINASH_SCALAR_DATETIME.NOW:
            declare_lowering(
                implementation,
                DEFERRED_ONLY if backend_type == "ibis" else OCCURRENCE,
            )
        else:
            declare_lowering(implementation)
    for method_name in ("lit", "col", "if_then_else", "is_in", "apply_window"):
        implementation = getattr(system_type, method_name, None)
        if implementation is not None:
            declare_lowering(implementation, REPEATABLE)
    for method_name in (
        "prepare_call_arguments",
        "prepare_coalesce_arguments",
        "normalize_conditional_branch",
        "normalize_conditional_result",
    ):
        declare_lowering(getattr(system_type, method_name), REPEATABLE)
    for method_name in dir(system_type):
        if method_name.startswith("_prepare_call_"):
            declare_lowering(getattr(system_type, method_name), REPEATABLE)

