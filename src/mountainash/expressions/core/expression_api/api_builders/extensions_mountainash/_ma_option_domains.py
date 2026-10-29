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
# (see the plan / spec); the divergent members (1w, 1q) are legal input but declared
# per-backend by capability facts (Task 3). Multiplier > 1 is deliberately excluded.
# `1ns`/`nanosecond` are excluded entirely: polars `round("1ns")` triggers an uncatchable
# pyo3 PanicException (divisor-by-zero) and datetime is microsecond-precision in practice,
# so nanosecond rounding is degenerate — rejected uniformly at the api-builder.
_UNIT_DURATION = frozenset({"1y", "1mo", "1w", "1d", "1h", "1m", "1s", "1ms", "1us", "1q"})

# Friendly aliases -> canonical duration. Applied before validation/dispatch.
_UNIT_FRIENDLY = {
    "year": "1y", "quarter": "1q", "month": "1mo", "week": "1w", "day": "1d",
    "hour": "1h", "minute": "1m", "second": "1s",
    "millisecond": "1ms", "microsecond": "1us",
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
    if legal is not None:
        # Branch 1: finite canonical / friendly domain.
        if normalized in legal:
            return normalized
        # Branch 2: open multiplier class (>= 2) — pass through un-enumerated.
        if option_name == "unit":
            from mountainash.core.capabilities.schema import ValueClass
            from mountainash.core.capabilities.value_classes import matches

            if matches(ValueClass.DURATION_MULTIPLIER, str(value)):
                return str(value)
        # Branch 3: reject.
        raise InvalidOptionValueError(
            f"invalid {option_name}={value!r} for {op_name}; legal: {sorted(legal)} "
            f"(or integer multiplier ≥2 like '2d', '3h')"
        )
    return normalized



def validate_open_value(value_class: Any, param: str, value: Any, op: str) -> Any:
    """Reject an open-value option whose value fails its value-class predicate.

    Used for timezone (IANA_TIMEZONE) and offset (POLARS_OFFSET) at the builder
    boundary. strftime is NOT validated here (open domain — spec §4.2).
    """
    from mountainash.core.capabilities.value_classes import matches

    if not matches(value_class, value):
        raise InvalidOptionValueError(
            f"{op}: invalid {param} {value!r} (expected {value_class.value})"
        )
    return value



import re as _re  # noqa: E402 -- module-local, avoids widening the top-level import block

# Canonical Substrait unit each MA duration suffix maps to. "q" (quarter)
# maps to MONTH -- its multiplier is folded to a multiple-of-3 by
# parse_ma_unit below (real Substrait has no QUARTER unit; item 74 spec §3.2).
_MA_SUFFIX_TO_CANONICAL = {
    "y": "YEAR", "mo": "MONTH", "q": "MONTH", "w": "WEEK", "d": "DAY",
    "h": "HOUR", "m": "MINUTE", "s": "SECOND", "ms": "MILLISECOND", "us": "MICROSECOND",
}
_MA_CALENDAR_UNITS = frozenset({"YEAR", "MONTH", "WEEK"})
_MA_UNIT_RE = _re.compile(r"^(\d+)([a-z]+)$")


def parse_ma_unit(value: str) -> tuple[int, str, str]:
    """Parse an already-validated, alias-normalized MA duration string (e.g.
    "2d" -> (2, "DAY", "temporal") or "1mo" -> (1, "MONTH", "calendar")) for
    the round_temporal/round_calendar redirect (item 74). `value` must
    already be normalize_unit()-normalized (friendly words resolved to their
    duration form) and validate_ma_option()-validated (multiplier + suffix
    known-legal) -- this function does not itself validate.

    "1q" (quarter) folds to (3, "MONTH", "calendar") -- multiplier composes
    for multi-digit quarter input too, e.g. "2q" -> (6, "MONTH", "calendar").
    """
    match = _MA_UNIT_RE.match(value)
    if match is None:
        raise InvalidOptionValueError(f"cannot parse MA duration unit {value!r}")
    multiplier = int(match.group(1))
    suffix = match.group(2)
    canonical = _MA_SUFFIX_TO_CANONICAL.get(suffix)
    if canonical is None:
        raise InvalidOptionValueError(f"unknown MA duration suffix {suffix!r} in {value!r}")
    if suffix == "q":
        multiplier *= 3
    family = "calendar" if canonical in _MA_CALENDAR_UNITS else "temporal"
    return multiplier, canonical, family
