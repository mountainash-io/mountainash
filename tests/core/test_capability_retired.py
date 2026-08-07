"""Retirement catalog (spec rev 3, §4)."""
from __future__ import annotations

import pytest

from mountainash.core.capabilities import (
    CapabilityFact,
    CapabilityLevel,
    CapabilityRegistry,
    ValueClass,
)
from mountainash.core.capabilities.retired import (
    RETIRED_FACTS,
    RetiredFact,
    assert_no_active_retired_overlap,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STR,
)


def _retired(**kw):
    base = dict(
        operation_key=FK_STR.CENTER, param="length",
        backend=CONST_BACKEND.IBIS, dialect=None,
        option_value=None, value_class=None,
        level=CapabilityLevel.LITERAL_ONLY,
        since="2026-07-05", retired_on="2026-08-07",
        fixed_in_versions=(("ibis", "13.0.0"),),
        upstream_ref=None, note="probe honored dynamic length",
    )
    base.update(kw)
    return RetiredFact(**base)


def test_catalog_starts_empty():
    assert RETIRED_FACTS == ()


def test_retired_fact_validates_dates():
    with pytest.raises(ValueError):
        _retired(retired_on="08-07-2026")
    with pytest.raises(ValueError):
        _retired(since="bad")


def test_overlap_guard_detects_active_option_fact(monkeypatch):
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
            CapabilityFact(
                operation_key=FK_STR.CENTER, param="length",
                level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.IBIS,
                message="t", since="2026-07-05", probe_exempt="test",
            )
        ])
        monkeypatch.setattr(
            "mountainash.core.capabilities.retired.RETIRED_FACTS", (_retired(),)
        )
        with pytest.raises(AssertionError, match="simultaneously active and retired"):
            assert_no_active_retired_overlap(CapabilityRegistry)
    finally:
        CapabilityRegistry.restore(snap)


def test_overlap_guard_detects_active_value_class_fact(monkeypatch):
    """Spec §4 disjointness over BOTH active keyspaces (G1, round 2).

    The option-value branch was already covered by
    ``test_overlap_guard_detects_active_option_fact``. This test pins the
    value-class branch: an active fact carrying a `value_class` (lands in
    ``_value_class_facts``) collides with a RetiredFact that carries the same
    `value_class` over the same key — the guard's `if r.value_class is not
    None` branch must fire.
    """
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        CapabilityRegistry.register_backend(CONST_BACKEND.IBIS, [
            CapabilityFact(
                operation_key=FK_STR.CENTER, param="length",
                level=CapabilityLevel.LITERAL_ONLY, backend=CONST_BACKEND.IBIS,
                value_class=ValueClass.DURATION_MULTIPLIER,
                message="t", since="2026-07-05", probe_exempt="test",
            )
        ])
        # Construct a RetiredFact with the same value_class key. The guard's
        # value-class branch (r.value_class is not None) must fire here, NOT
        # the option-value branch — option_value is None and value_class is
        # set, so the active fact is in _value_class_facts, not _facts.
        monkeypatch.setattr(
            "mountainash.core.capabilities.retired.RETIRED_FACTS",
            (_retired(
                option_value=None,
                value_class=ValueClass.DURATION_MULTIPLIER,
                level=CapabilityLevel.LITERAL_ONLY,
            ),)
        )
        with pytest.raises(AssertionError, match="simultaneously active and retired"):
            assert_no_active_retired_overlap(CapabilityRegistry)
    finally:
        CapabilityRegistry.restore(snap)


def test_overlap_guard_passes_when_disjoint(monkeypatch):
    monkeypatch.setattr(
        "mountainash.core.capabilities.retired.RETIRED_FACTS", (_retired(),)
    )
    snap = CapabilityRegistry.snapshot()
    try:
        CapabilityRegistry.reset()
        assert_no_active_retired_overlap(CapabilityRegistry)
    finally:
        CapabilityRegistry.restore(snap)
