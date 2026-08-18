"""Known coverage gaps register (spec 2026-08-07, §4.2).

Mirrors the KNOWN_DIVERGENCES pattern in divergences.py: one module, one
tuple. Ships empty; entries are added when a gap is consciously accepted
rather than fixed. Rendered in docs/reference/expression-coverage.md.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mountainash.core.capabilities.schema import KnownGap

KNOWN_GAPS: tuple[KnownGap, ...] = ()
