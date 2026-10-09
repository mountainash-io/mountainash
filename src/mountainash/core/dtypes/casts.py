# src/mountainash/core/dtypes/casts.py
"""Structural cast-safety table over the canonical vocabulary.

Pairs not listed in SAFE_CASTS are unsafe — same conservative default as
the old typespec is_safe_cast.
"""
from __future__ import annotations

from enum import Enum

from .canonical import MountainashDtype as D

_INT_WIDENING: set[tuple[D, D]] = {
    (a, b)
    for chain in ([D.I8, D.I16, D.I32, D.I64], [D.U8, D.U16, D.U32, D.U64])
    for i, a in enumerate(chain)
    for b in chain[i + 1:]
}

_TO_STRING: set[tuple[D, D]] = {
    (d, D.STRING)
    for d in (D.BOOL, D.I8, D.I16, D.I32, D.I64, D.U8, D.U16, D.U32, D.U64,
              D.FP32, D.FP64, D.DATE, D.TIME, D.TIMESTAMP, D.DURATION)
}

SAFE_CASTS: frozenset[tuple[D, D]] = frozenset(
    _INT_WIDENING
    | _TO_STRING
    | {
        (D.FP32, D.FP64),
        # ints → fp64 (exact through 2^53; same judgment as the old
        # INTEGER→NUMBER safe entry)
        (D.I8, D.FP64), (D.I16, D.FP64), (D.I32, D.FP64), (D.I64, D.FP64),
        (D.U8, D.FP64), (D.U16, D.FP64), (D.U32, D.FP64), (D.U64, D.FP64),
        (D.I8, D.FP32), (D.I16, D.FP32), (D.U8, D.FP32), (D.U16, D.FP32),
        # temporal
        (D.DATE, D.TIMESTAMP), (D.TIMESTAMP, D.DATE),
        # bool → int
        (D.BOOL, D.I8), (D.BOOL, D.I16), (D.BOOL, D.I32), (D.BOOL, D.I64),
    }
)

UNSAFE_CASTS: frozenset[tuple[D, D]] = frozenset({
    (D.FP64, D.I64), (D.FP32, D.I64), (D.FP64, D.FP32),
    (D.STRING, D.I64), (D.STRING, D.FP64), (D.STRING, D.BOOL),
    (D.STRING, D.DATE), (D.STRING, D.TIME), (D.STRING, D.TIMESTAMP),
})


def is_safe_cast(from_type: D, to_type: D) -> bool:
    if from_type is to_type:
        return True
    return (from_type, to_type) in SAFE_CASTS


class CastSafety(Enum):
    """Classification of actual -> declared casts for drift detection.

    Binary today: every pair in the canonical vocabulary is either backed
    by an entry in SAFE_CASTS (or is an identity cast) or it is not. There
    is no independent judgment of "lossy" or "narrowing" here beyond what
    the structural table already encodes.

    LOSSY/NARROWING are room-to-grow members for a later, more granular
    classification (e.g. distinguishing "narrows precision" from "cannot
    parse") without breaking existing consumers — until that lands, callers
    must not assume UNSAFE means anything more specific than "not in
    SAFE_CASTS and not identity."
    """

    SAFE = "safe"
    UNSAFE = "unsafe"


def classify_cast(from_type: D, to_type: D) -> CastSafety:
    """Classify a cast from `from_type` to `to_type` in canonical space.

    Delegates directly to `is_safe_cast`, which already treats identity
    casts as safe and defaults unlisted pairs to unsafe. This function only
    wraps that boolean judgment in an enum so downstream consumers (e.g.
    `TypeDrift.safety`) get a typed, self-describing value instead of a
    bare bool.
    """
    if is_safe_cast(from_type, to_type):
        return CastSafety.SAFE
    return CastSafety.UNSAFE
