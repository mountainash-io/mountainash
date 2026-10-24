"""Numeric conversion validity for Narwhals-native expressions and series.

Narwhals' `cast` has no strict mode, and supported storage behavior differs:
Polars and Arrow-backed pandas raise on integer overflow, NumPy- and nullable-
backed pandas wrap it, and Float32 narrowing can turn finite values into infinity.
The checks here are expressed with Narwhals' own vector primitives, so
they apply to an `nw.Expr` or to an `nw.Series` alike and never reach a provider
object.

A check is planned from source and target type domains alone; a conversion that
the target's domain contains has an empty plan and receives no predicate.
"""
from __future__ import annotations

from typing import Any, Callable

import narwhals as nw

from mountainash.core.dtypes import MountainashDtype, StructDtype, TypeTarget, UnknownDtypeError, registry

D = MountainashDtype

_INTEGER_DOMAINS: dict[MountainashDtype, tuple[int, int]] = {
    D.I8: (-(2**7), 2**7 - 1),
    D.I16: (-(2**15), 2**15 - 1),
    D.I32: (-(2**31), 2**31 - 1),
    D.I64: (-(2**63), 2**63 - 1),
    D.U8: (0, 2**8 - 1),
    D.U16: (0, 2**16 - 1),
    D.U32: (0, 2**32 - 1),
    D.U64: (0, 2**64 - 1),
}
_FLOAT_MANTISSA_BITS = {D.FP32: 24, D.FP64: 53}

# Storage whose native integer cast wraps instead of raising.
WRAPPING_STORAGE = frozenset({"pandas_numpy", "pandas_nullable"})

_Check = tuple[str, Any]


def numeric_target(native_target: Any) -> MountainashDtype | None:
    """The canonical target when this is an integer or Float32 conversion."""
    canonical = _canonical(native_target)
    if canonical in _INTEGER_DOMAINS or canonical is D.FP32:
        return canonical
    return None


def source_of(native_dtype: Any) -> MountainashDtype | None:
    """The canonical numeric family of a native source dtype, else None."""
    canonical = _canonical(native_dtype)
    if canonical in _INTEGER_DOMAINS or canonical in _FLOAT_MANTISSA_BITS:
        return canonical
    return None


def _canonical(native: Any) -> MountainashDtype | None:
    if native is None:
        return None
    try:
        decoded = registry.from_native(native)
    except (UnknownDtypeError, TypeError, ValueError):
        return None
    return decoded if isinstance(decoded, MountainashDtype) else None


def checks(source: MountainashDtype, target: MountainashDtype) -> tuple[_Check, ...]:
    """The invalidity conditions a source-to-target conversion needs, if any."""
    if target is D.FP32:
        return (("overflow", None),) if source is D.FP64 else ()
    low, high = _INTEGER_DOMAINS[target]
    if source in _INTEGER_DOMAINS:
        source_low, source_high = _INTEGER_DOMAINS[source]
        planned: list[_Check] = []
        if source_low < low:
            planned.append(("lt", low))
        if source_high > high:
            planned.append(("gt", high))
        return tuple(planned)
    if source in _FLOAT_MANTISSA_BITS:
        # Truncation toward zero decides representability, so a fractional
        # value just outside the bounds is not newly invalid. The limits are
        # exact powers of two; `low - 1` is only used where the float holds it.
        exact_below = abs(low - 1) <= 2 ** _FLOAT_MANTISSA_BITS[source]
        lower: _Check = ("le", float(low - 1)) if exact_below else ("lt", float(low))
        return (lower, ("ge", float(high + 1)))
    return ()


_COMPARISONS: dict[str, Callable[[Any, Any], Any]] = {
    "lt": lambda x, bound: x < bound,
    "le": lambda x, bound: x <= bound,
    "gt": lambda x, bound: x > bound,
    "ge": lambda x, bound: x >= bound,
}


def checked_cast(
    x: Any,
    native_target: Any,
    source: MountainashDtype,
    target: MountainashDtype,
) -> Any:
    """Cast `x`, rejecting rows whose conversion would be newly invalid.

    The exhaustive replacement raises for invalid rows. Lazy expressions retain
    a value dependency on that guard through distinct branches; eager series
    have already evaluated the guard. Select the candidate without additional
    arithmetic, which can turn valid Arrow-backed pandas NaNs into nulls.
    """
    candidate = x.cast(native_target)
    invalid: Any = None
    for kind, bound in checks(source, target):
        if kind == "overflow":
            condition = x.is_finite() & ~candidate.is_finite()
        else:
            condition = _COMPARISONS[kind](x, bound)
        invalid = condition if invalid is None else invalid | condition
    if invalid is None:
        return candidate
    valid = invalid.fill_null(False).replace_strict({False: True}, return_dtype=nw.Boolean)
    if isinstance(candidate, nw.Series):
        return candidate.zip_with(valid, candidate)
    return nw.when(valid).then(candidate).otherwise(nw.lit(0, dtype=native_target))


def _is_float32(native: Any) -> bool:
    return native is nw.Float32 or isinstance(native, nw.Float32)


def checked_member(
    expr: Any, source: Any, target: Any, cast: Callable[[Any, Any], Any],
) -> Any | None:
    """The scalar-checked conversion of one struct member, or None if native suffices.

    Only Narwhals vector primitives and the scalar owner above are used, from the
    operand's own native dtype. Integer overflow already raises natively, so a
    Float32 leaf (directly or through nested structs) is the only member that
    needs a predicate. List items are left to the native cast: Narwhals has no
    element-wise list expression.
    """
    if _is_float32(target):
        origin = source_of(source)
        if origin is not None and checks(origin, D.FP32):
            return checked_cast(expr, target, origin, D.FP32)
        return None
    if isinstance(target, nw.Struct) and not isinstance(source, nw.Struct):
        # Operand evidence keeps its actual carrier dtype (for example an
        # Arrow-backed pandas struct). Decode structure through the shared
        # registry rather than mistaking that carrier for unknown metadata.
        try:
            canonical = registry.from_native(source)
        except (UnknownDtypeError, TypeError, ValueError):
            return None
        if isinstance(canonical, StructDtype):
            source = registry.to_native_schema(canonical, TypeTarget.NARWHALS)
    if isinstance(source, nw.Struct) and isinstance(target, nw.Struct):
        members = {
            field.name: (expr.struct.field(field.name), field.dtype)
            for field in source.fields
        }
        return checked_struct(expr, target, members, cast)
    return None


def checked_struct(
    parent: Any,
    target: Any,
    members: dict[str, tuple[Any, Any | None]],
    cast: Callable[[Any, Any], Any],
) -> Any | None:
    """Rebuild `target` from `members` (name -> expression, source dtype), or None.

    Follows the native struct-cast policy: target order, source-only members are
    projected away, absent target members are null, and a null parent stays null.
    Returns None when no member needs a validity predicate.
    """
    rebuilt: dict[str, Any] = {}
    changed = False
    for field in target.fields:
        if field.name not in members:
            rebuilt[field.name] = nw.lit(None, dtype=field.dtype)
            continue
        child, source = members[field.name]
        converted = None if source is None else checked_member(child, source, field.dtype, cast)
        changed = changed or converted is not None
        rebuilt[field.name] = child if converted is None else converted
    if not changed:
        return None
    result = cast(nw.struct(**rebuilt), target)
    return nw.when(parent.is_null()).then(nw.lit(None, dtype=target)).otherwise(result)
