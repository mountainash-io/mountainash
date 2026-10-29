"""Predicate registry for capability value classes (spec 2026-07-25).

Each ValueClass maps to one pure str->bool predicate and a representative
slice (>=2 canonical members) used by the agreement probe. Predicates test
*support-relevant membership*, never mere shape (an IANA name must resolve in
the tz database, not just look like one) — see spec Section 2/3.2.1.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, available_timezones

if TYPE_CHECKING:
    from collections.abc import Callable

from mountainash.core.capabilities.schema import ValueClass

# Canonical single-unit tokens shared with _UNIT_DURATION (api-builder side).
MULTIPLIER_UNITS = frozenset({"y", "mo", "w", "d", "h", "m", "s", "ms", "us", "q"})

_MULT_RE = re.compile(r"^([2-9]|[1-9][0-9]+)(y|mo|w|d|h|m|s|ms|us|q)$")
_OFFSET_RE = re.compile(r"^-?(\d+(y|mo|w|d|h|m|s|ms|us|ns))+$")

_TZ_NAMES = available_timezones()


def _is_multiplier(value: str) -> bool:
    return bool(_MULT_RE.fullmatch(value))


def _is_iana(value: str) -> bool:
    # Membership in the tz database — shape is necessary but not sufficient.
    if value not in _TZ_NAMES:
        return False
    try:
        ZoneInfo(value)
    except Exception:
        return False
    return True


def _is_polars_offset(value: str) -> bool:
    return bool(_OFFSET_RE.fullmatch(value))


# No STRFTIME_PATTERN predicate: strftime is open (unvalidated) so no total
# predicate exists; it gates value-agnostically (spec §3.2 box). Adding a
# partial-match class here would leave non-matching unsupported patterns
# ungated (design-review round-2, I-2).
_PREDICATES: dict[ValueClass, Callable[[str], bool]] = {
    ValueClass.DURATION_MULTIPLIER: _is_multiplier,
    ValueClass.IANA_TIMEZONE: _is_iana,
    ValueClass.POLARS_OFFSET: _is_polars_offset,
}

REPRESENTATIVE_SLICES: dict[ValueClass, tuple[str, ...]] = {
    # Slices span each class's MEANINGFUL axes (spec 3.2.1) — obscure/DST-edge
    # zones, composite+signed offsets — not just easy members.
    ValueClass.DURATION_MULTIPLIER: ("2d", "3h", "12mo"),
    ValueClass.IANA_TIMEZONE: (
        "UTC",
        "Australia/Sydney",
        "America/New_York",
        "Pacific/Kiritimati",
    ),
    ValueClass.POLARS_OFFSET: ("1d", "-3mo", "2h30m"),
}


def predicate_for(vc: ValueClass) -> Callable[[str], bool]:
    return _PREDICATES[vc]


def matches(vc: ValueClass, value: str) -> bool:
    return _PREDICATES[vc](value)
