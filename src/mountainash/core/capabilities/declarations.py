"""Governing protocol for capability declaration modules (spec rev 3, §1).

A declaration module is import-safe pure data: it exposes
``DECLARATIONS: tuple[CapabilityDeclaration, ...]`` and NEVER registers
anything itself — bootstrap discovers modules under the two capability
package roots and performs registration.

Declaration identity is (backend, source, domain, probe wave). A module may
emit several declarations for the same (backend, source, domain), one per
``ProbeEvidence`` wave.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from mountainash.core.capabilities.schema import CapabilityFact, _validate_since

if TYPE_CHECKING:
    from mountainash.core.constants import CONST_BACKEND


class FactSource(Enum):
    SUBSTRAIT = "substrait"
    MOUNTAINASH = "mountainash"


class Domain(Enum):
    STRING = "string"
    ARITHMETIC = "arithmetic"
    DATETIME = "datetime"
    LIST = "list"
    SET = "set"
    TERNARY = "ternary"
    RELATION = "relation"


# Enum-class-name suffix -> Domain. Extended only when a new FKEY/RKEY
# category gains declaration facts; classify_domain raises on unknowns so
# the extension is forced, not forgotten.
_DOMAIN_SUFFIXES: dict[str, Domain] = {
    "STRING": Domain.STRING,
    "ARITHMETIC": Domain.ARITHMETIC,
    "DATETIME": Domain.DATETIME,
    "LIST": Domain.LIST,
    "SET": Domain.SET,
    "TERNARY": Domain.TERNARY,
}


def classify_source(operation_key: Any) -> FactSource:
    name = type(operation_key).__name__
    if name.startswith("RKEY_"):
        return FactSource.MOUNTAINASH
    if name.startswith(("FKEY_SUBSTRAIT", "SUBSTRAIT")):
        return FactSource.SUBSTRAIT
    if name.startswith("FKEY_MOUNTAINASH"):
        return FactSource.MOUNTAINASH
    raise ValueError(f"cannot classify source of operation-key enum {name!r}")


def classify_domain(operation_key: Any) -> Domain:
    name = type(operation_key).__name__
    if name.startswith("RKEY_"):
        return Domain.RELATION
    for suffix, domain in _DOMAIN_SUFFIXES.items():
        if name.endswith(f"_{suffix}") or name.endswith(f"SCALAR_{suffix}"):
            return domain
    raise ValueError(
        f"cannot classify domain of operation-key enum {name!r}; extend "
        "Domain/_DOMAIN_SUFFIXES in core/capabilities/declarations.py"
    )


@dataclass(frozen=True)
class ProbeEvidence:
    """Structured empirical basis for ONE probe wave."""

    probe_date: str
    library_versions: tuple[tuple[str, str], ...]
    fixtures: tuple[str, ...]

    def __post_init__(self) -> None:
        try:
            _validate_since(self.probe_date, "ProbeEvidence")
        except ValueError:
            raise ValueError(
                f"ProbeEvidence: probe_date must be YYYY-MM-DD, got "
                f"{self.probe_date!r}"
            ) from None


@dataclass(frozen=True)
class CapabilityDeclaration:
    """One backend's facts, from one source, one domain, one probe wave."""

    backend: "CONST_BACKEND"
    domain: Domain
    source: FactSource
    facts: tuple[CapabilityFact, ...]
    evidence: ProbeEvidence | None = None

    def __post_init__(self) -> None:
        for fact in self.facts:
            if fact.backend is not self.backend:
                raise ValueError(
                    f"CapabilityDeclaration({self.backend}, {self.domain}): "
                    f"fact ({fact.operation_key}, {fact.param}) has backend "
                    f"{fact.backend}"
                )
            actual_source = classify_source(fact.operation_key)
            if actual_source is not self.source:
                raise ValueError(
                    f"CapabilityDeclaration({self.backend}, {self.domain}): "
                    f"fact ({fact.operation_key}, {fact.param}) classifies to "
                    f"source {actual_source}, declaration says {self.source}"
                )
            actual_domain = classify_domain(fact.operation_key)
            if actual_domain is not self.domain:
                raise ValueError(
                    f"CapabilityDeclaration({self.backend}, {self.domain}): "
                    f"fact ({fact.operation_key}, {fact.param}) classifies to "
                    f"domain {actual_domain}, declaration says {self.domain}"
                )
        if self.evidence is None and any(
            f.probe_exempt is None for f in self.facts
        ):
            raise ValueError(
                f"CapabilityDeclaration({self.backend}, {self.domain}): "
                "evidence may be None only when every fact is probe_exempt"
            )


@runtime_checkable
class CapabilityDeclarationModule(Protocol):
    """Shape of a declaration module (checked by the protocol guard)."""

    DECLARATIONS: tuple[CapabilityDeclaration, ...]
