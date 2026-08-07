"""Capability declarations for expression backends (spec 2026-08-07).

PROTOCOL (machine-enforced by tests/core/test_capability_protocol_guard.py):
- Every non-exempt module here exposes
  ``DECLARATIONS: tuple[CapabilityDeclaration, ...]`` and registers NOTHING
  itself — bootstrap discovers this package and registers.
- Exempt from the DECLARATIONS requirement: ``__init__.py`` files and
  ``_``-prefixed helper modules (package-local data builders only).
- Import-safe: no module here imports ibis or narwhals (polars is a core
  dependency of the parent chain and exempt).
- One declaration per (backend x domain x source x probe wave); evidence is
  None only for fully probe_exempt waves.
- Placement (spec §3 decision table): domain modules (string, arithmetic,
  datetime/*, polymorphic) hold cross-backend facts about one operation
  domain; backend modules (polars, narwhals, ibis) hold that backend's
  inherent expr-argument facts (LITERAL_ONLY etc.).
- Family/dialect discipline: ibis declares family-default (dialect=None)
  AND concrete-dialect facts (except family-supported ops with dialect-only
  gaps, per the strptime precedent); narwhals declares per-dialect only.
- Retirement: a fixed limitation MOVES to core/capabilities/retired.py.
"""
from __future__ import annotations
