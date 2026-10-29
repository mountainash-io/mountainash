"""Immutable assertion-change history captures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from mountainash.core.capabilities.capture import (
    CapturedAddress,
    CapturedAssertion,
    Environment,
    EnvironmentCoordinate,
)


class ChangeDisposition(Enum):
    UPSTREAM_FIX = "upstream_fix"
    LOCAL_IMPLEMENTATION_FIX = "local_implementation_fix"
    NARROWED_APPLICABILITY = "narrowed_applicability"
    INCORRECT_DECLARATION = "incorrect_declaration"
    SUPERSESSION = "supersession"




@dataclass(frozen=True)
class HistoricalBoundary:
    """Immutable uncertainty/governance annotation, separate from executable ranges."""

    kind: str
    name: str
    side: str
    owner: str
    evidence_refs: tuple[CapturedAddress, ...]
    next_release: str
    backtesting_obligation: CapturedAddress
    exception_reason: str | None = None
    exception_until: str | None = None

    def __post_init__(self) -> None:
        coordinate = EnvironmentCoordinate(self.kind, self.name, None)
        object.__setattr__(self, "name", coordinate.name)
        if type(self.backtesting_obligation) is not CapturedAddress:
            raise TypeError("historical boundary requires an immutable backtesting obligation")
        if self.side not in {"introduced", "fixed"}:
            raise ValueError("historical boundary side must be introduced or fixed")
        if any(type(value) is not str or not value for value in (self.owner, self.next_release)):
            raise ValueError("historical boundary requires owner and release obligation")
        if type(self.evidence_refs) is not tuple or not self.evidence_refs or any(
            type(ref) is not CapturedAddress for ref in self.evidence_refs
        ):
            raise TypeError("historical boundary requires immutable evidence addresses")
        if (self.exception_reason is None) != (self.exception_until is None):
            raise ValueError("exception reason and deadline must be supplied together")
        if self.exception_reason is not None and any(
            type(value) is not str or not value for value in (self.exception_reason, self.exception_until)
        ):
            raise ValueError("exception reason and deadline must be nonempty")


@dataclass(frozen=True)
class AssertionChange:
    change_ref: CapturedAddress
    prior: CapturedAssertion
    disposition: ChangeDisposition
    recorded_at: str
    reason: str
    successors: tuple[CapturedAssertion, ...] = ()
    evidence_refs: tuple[CapturedAddress, ...] = ()
    fixed_versions: Environment | None = None
    unresolved_boundaries: tuple[HistoricalBoundary, ...] = ()

    def __post_init__(self) -> None:
        if type(self.change_ref) is not CapturedAddress or type(self.prior) is not CapturedAssertion:
            raise TypeError("change requires captured address and complete predecessor")
        if type(self.disposition) is not ChangeDisposition:
            raise TypeError("change requires an explicit disposition")
        if type(self.recorded_at) is not str:
            raise TypeError("recorded_at requires ISO date/time text")
        datetime.fromisoformat(self.recorded_at)
        if type(self.reason) is not str or not self.reason.strip():
            raise ValueError("change requires a reason")
        if type(self.successors) is not tuple or any(
            type(successor) is not CapturedAssertion for successor in self.successors
        ):
            raise TypeError("successors require immutable complete captures")
        if any(successor.family != self.prior.family for successor in self.successors):
            raise ValueError("successor must retain the assertion family")
        if any(successor == self.prior for successor in self.successors):
            raise ValueError("successor cannot be the identical predecessor capture")
        if any(successor.address == self.prior.address for successor in self.successors):
            raise ValueError("successor cannot reuse the immutable predecessor address")
        if len(set(successor.address for successor in self.successors)) != len(self.successors):
            raise ValueError("duplicate successor address")
        if type(self.evidence_refs) is not tuple or any(type(ref) is not CapturedAddress for ref in self.evidence_refs):
            raise TypeError("change evidence requires captured addresses")
        if self.fixed_versions is not None and type(self.fixed_versions) is not Environment:
            raise TypeError("fixed versions require observed coordinates or explicit unknown")
        if type(self.unresolved_boundaries) is not tuple or any(
            type(boundary) is not HistoricalBoundary for boundary in self.unresolved_boundaries
        ):
            raise TypeError("unresolved boundaries require immutable historical annotations")
