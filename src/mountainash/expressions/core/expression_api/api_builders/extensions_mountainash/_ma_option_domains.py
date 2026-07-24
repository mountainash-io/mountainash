"""Packaged MountainAsh-extension option domains (friendly-value) + runtime validation.

Physically separate from the Substrait `_option_domains.py` (substrait-vs-mountainash):
MA-extension ops (e.g. the datetime `unit` rounding options) validate against these
friendly-value domains, NOT the Substrait enum domains. Keys are the protocol op-name
(post-rename: round_dt/ceil_dt/floor_dt/truncate)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mountainash.core.errors import InvalidOptionValueError

if TYPE_CHECKING:
    from mountainash.expressions.core.expression_system.function_keys.enums import (
        FKEY_MOUNTAINASH_SCALAR_DATETIME,
    )

# Canonical duration forms (single-multiplier named units). Portable core is a subset
# (see the plan / spec); the divergent members (1w, 1q, 1ns) are legal input but declared
# per-backend by capability facts (Task 3). Multiplier > 1 is deliberately excluded.
_UNIT_DURATION = frozenset({"1y", "1mo", "1w", "1d", "1h", "1m", "1s", "1ms", "1us", "1q", "1ns"})

# Friendly aliases -> canonical duration. Applied before validation/dispatch.
_UNIT_FRIENDLY = {
    "year": "1y", "quarter": "1q", "month": "1mo", "week": "1w", "day": "1d",
    "hour": "1h", "minute": "1m", "second": "1s",
    "millisecond": "1ms", "microsecond": "1us", "nanosecond": "1ns",
}

# Legal input set = duration forms + friendly aliases.
_UNIT = frozenset(_UNIT_DURATION | set(_UNIT_FRIENDLY))

MA_OPTION_DOMAINS: dict[tuple[str, str], frozenset[str]] = {
    ("truncate", "unit"): _UNIT,
    ("round_dt", "unit"): _UNIT,
    ("ceil_dt", "unit"): _UNIT,
    ("floor_dt", "unit"): _UNIT,
}


def normalize_unit(value: str) -> str:
    """Friendly word -> canonical duration; duration strings pass through unchanged."""
    return _UNIT_FRIENDLY.get(value, value)


def _op_name_for_fkey(fkey: FKEY_MOUNTAINASH_SCALAR_DATETIME) -> str:
    from mountainash.expressions.core.expression_system.function_mapping import (
        FunctionRegistry,
    )
    return FunctionRegistry.get(fkey).protocol_method.__name__


def validate_ma_option(
    fkey: FKEY_MOUNTAINASH_SCALAR_DATETIME, option_name: str, value: Any  # noqa: ANN401
) -> str:
    """Normalize (friendly->duration) then reject values outside the MA domain.

    Keyed by FKEY (design-review I2): resolves the protocol op-name via the registry so
    the domain lookup matches the introspected op-name the disposition guard uses, even
    though the public api-builder method name differs (round vs round_dt)."""
    op_name = _op_name_for_fkey(fkey)
    normalized = normalize_unit(str(value))
    legal = MA_OPTION_DOMAINS.get((op_name, option_name))
    if legal is not None and normalized not in legal:
        raise InvalidOptionValueError(
            f"invalid {option_name}={value!r} for {op_name}; legal: {sorted(legal)} "
            f"(multiplier>1 not supported — see backlog capability-value-predicate-mechanism)"
        )
    return normalized
