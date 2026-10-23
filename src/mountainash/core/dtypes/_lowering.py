# src/mountainash/core/dtypes/_lowering.py
"""Backend-independent checks shared by the native type adapters.

Nothing here inspects a concrete native library object: it only reads the
canonical descriptor (its native refinement and target identity) and the
adapter's own mapping tables.
"""
from __future__ import annotations

from typing import Any, Mapping

from .canonical import MountainashDtype, NativeDtype
from .errors import DtypeMappingError
from .targets import TypeTarget


def native_of(dtype: Any) -> NativeDtype | None:
    """The native refinement a descriptor carries (the descriptor itself if native)."""
    native = dtype if isinstance(dtype, NativeDtype) else getattr(dtype, "native", None)
    return native if isinstance(native, NativeDtype) else None


def native_refinement(dtype: Any, target: TypeTarget) -> NativeDtype | None:
    """Refinement owned by ``target``; a refinement of another target is an error.

    Adapters call this for every descriptor they lower, so a nested native
    override receives the same target-identity check as a top-level one.
    """
    native = native_of(dtype)
    if native is not None and native.target is not target:
        raise DtypeMappingError(
            f"Native refinement targets {native.target.value}, not {target.value}"
        )
    return native


def lower_scalar(schema_types: Mapping[MountainashDtype, Any], dtype: Any, target: TypeTarget) -> Any:
    """Look up a bare canonical dtype in an adapter's schema table."""
    if not isinstance(dtype, MountainashDtype):
        raise DtypeMappingError(
            f"No lossless {target.value} schema mapping for parameterized dtype {dtype!r}"
        )
    try:
        return schema_types[dtype]
    except KeyError:
        raise DtypeMappingError(
            f"No {target.value} schema mapping for {dtype.value!r}. "
            f"Supported: {sorted(d.value for d in schema_types)}"
        ) from None


def reject_bare_container_cast(
    dtype: Any,
    target: TypeTarget,
    schema_types: Mapping[MountainashDtype, Any],
    unsupported: frozenset[MountainashDtype],
) -> None:
    """Bare canonical containers are schema types but not cast targets."""
    if isinstance(dtype, MountainashDtype) and dtype in unsupported:
        supported = sorted(d.value for d in schema_types if d not in unsupported)
        raise DtypeMappingError(
            f"{dtype.value!r} is not a valid bare cast target on "
            f"{target.value} (a container cast needs an element type — "
            f"pass a native dtype for a parameterized cast). "
            f"Supported cast targets: {supported}"
        )
