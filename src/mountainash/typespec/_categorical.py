"""Shared categorical value extraction (item 54, gap 3).

The value-extraction logic for Frictionless ``categories`` (simple
``["a", "b"]`` form vs object ``[{"value":.., "label":..}]`` form) was
copy-paste-identical between conform's stage-5b expression builder and the
typespec converters. This module is the single home for it — both call sites
import from here so they can never diverge.
"""
from __future__ import annotations

from typing import Any


def categorical_values(categories: list[Any]) -> list[Any]:
    """Extract raw values from a categories list (simple values, LabeledValue
    objects, or {value,label} dicts). Returns a NEW list — never aliases the
    input."""
    from mountainash.typespec.spec import LabeledValue

    return [
        c.value
        if isinstance(c, LabeledValue)
        else (c["value"] if isinstance(c, dict) else c)
        for c in categories
    ]


__all__ = ["categorical_values"]
