"""Shared base for backend relation systems: backend identity + dialect.

Relation limitations are declared as CapabilityFacts on each backend's
``CAPABILITIES`` tuple and enforced through the capability spine — the
compile-time gate (``_gate_capabilities``) for BUILD facts and
``enrich_materialization`` (registry residue) for MATERIALIZE facts. The
legacy ``KNOWN_REL_LIMITATIONS`` class dict was retired in the spine's
Phase 1.
"""
from __future__ import annotations


class BaseRelationSystem:
    """Mixin carrying backend identity for all relation systems."""

    BACKEND_NAME: str = "unknown"

    def __init__(self, dialect: str | None = None) -> None:
        self.dialect = dialect
