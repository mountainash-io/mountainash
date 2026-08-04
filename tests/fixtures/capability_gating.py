"""Spine-derived test expectations — the single surface a test uses to ask
"what does the capability spine say about (op, family, dialect)?".
Nothing here is hand-maintained; see spec 2026-08-01-spine-derived-test-expectations.
"""
from __future__ import annotations

from mountainash.core.capabilities.identity import KNOWN_DIALECTS, BackendIdentity
from mountainash.core.capabilities.registry import CapabilityRegistry
from mountainash.core.capabilities.schema import (
    Boundary,
    CapabilityFact,
    CapabilityLevel,
    Enforcement,
    WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND

_DIALECT_TO_FAMILY: dict[str, CONST_BACKEND] = {}
for _family, _dialects in KNOWN_DIALECTS.items():
    for _dialect in _dialects:
        if _dialect in _DIALECT_TO_FAMILY:  # pragma: no cover
            raise ValueError(f"dialect {_dialect!r} owned by two families")
        _DIALECT_TO_FAMILY[_dialect] = _family

_FAMILY_PREFIXES = (
    ("narwhals", CONST_BACKEND.NARWHALS),
    ("ibis", CONST_BACKEND.IBIS),
    ("pandas", CONST_BACKEND.PANDAS),
    ("pyarrow", CONST_BACKEND.PYARROW),
    ("polars", CONST_BACKEND.POLARS),
)


def identity_for(backend_name: str) -> BackendIdentity:
    """Name-string path (parametrized tests only). Prefer resolve_identity() with the real object."""
    fam = _DIALECT_TO_FAMILY.get(backend_name)
    if fam is not None:
        return BackendIdentity(family=fam, dialect=backend_name)
    for prefix, f in _FAMILY_PREFIXES:
        if backend_name == prefix or backend_name.startswith(prefix + "-"):
            return BackendIdentity(family=f, dialect=None)
    raise ValueError(f"cannot resolve backend family for {backend_name!r}")


def resolve_identity(backend_or_name) -> BackendIdentity:
    """Identity from the REAL backend object via production detection (rev-2 new-I2); the name-string
    map is a fallback only for a bare str. Objects are authoritative — the test factory routes e.g.
    pandas THROUGH Narwhals, so the fixture name alone resolves the wrong family."""
    if isinstance(backend_or_name, str):
        return identity_for(backend_or_name)
    from mountainash.core.backend_detection import identify_backend_identity

    return identify_backend_identity(backend_or_name)


def gate_family(backend_or_name) -> CONST_BACKEND:
    return resolve_identity(backend_or_name).family


def gate_dialect(backend_or_name) -> str | None:
    return resolve_identity(backend_or_name).dialect


_GATING = {
    (Enforcement.GATE, Boundary.BUILD),
    (Enforcement.MATERIALIZE_RESIDUE, Boundary.MATERIALIZE),
}


def capability_gate(operation_key, family, *, dialect=None,
                    param=WILDCARD_PARAM, option_value=None) -> CapabilityFact | None:
    fact = CapabilityRegistry.capability_for(
        operation_key, param, family, dialect=dialect, option_value=option_value
    )
    if fact is None or fact.level is not CapabilityLevel.UNSUPPORTED:
        return None
    if (fact.enforcement, fact.boundary) not in _GATING:
        return None
    return fact
