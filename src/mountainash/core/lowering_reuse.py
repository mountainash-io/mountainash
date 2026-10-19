"""Internal permissions for reusing lowering, distinct from evaluating its result."""

from dataclasses import dataclass
from enum import Enum, auto


class ReuseCase(Enum):
    REPEATABLE = auto()
    DEFERRED_ONLY = auto()
    OCCURRENCE = auto()


@dataclass(frozen=True)
class LoweringDescriptor:
    reuse: ReuseCase
    materializes_input: bool = False


REPEATABLE = LoweringDescriptor(ReuseCase.REPEATABLE)
DEFERRED_ONLY = LoweringDescriptor(ReuseCase.DEFERRED_ONLY)
OCCURRENCE = LoweringDescriptor(ReuseCase.OCCURRENCE)


def declare_lowering(function, descriptor=None):
    """Mark this exact built-in implementation, optionally overriding its definition."""
    function.__lowering_reuse__ = (function, descriptor)
    return function


def selected_lowering(method, definition=None):
    """Replacements (including wrappers copying attributes) gain no permission."""
    function = getattr(method, "__func__", method)
    marker = getattr(function, "__lowering_reuse__", None)
    if marker is None or marker[0] is not function:
        return OCCURRENCE
    return marker[1] or definition or OCCURRENCE


def deferred_value(value):
    """Use native form only; never inspect or execute an opaque native plan."""
    from mountainash.core.types import (
        is_ibis_table, is_narwhals_lazyframe, is_polars_lazyframe,
    )

    return is_polars_lazyframe(value) or is_narwhals_lazyframe(value) or is_ibis_table(value)


def fold_lowering(owner, descriptor, *, deferred=True):
    """Conjoin a selected call with facts accumulated on its existing visitor."""
    repeatable = descriptor.reuse is ReuseCase.REPEATABLE
    reusable = repeatable or (descriptor.reuse is ReuseCase.DEFERRED_ONLY and deferred)
    if descriptor.materializes_input or not deferred:
        reusable &= owner.repeatable_result
    owner.reusable_lowering &= reusable
    owner.repeatable_result &= repeatable
