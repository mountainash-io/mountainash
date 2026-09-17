"""Inventory-qualified gap captures supplied by cold verification callers."""

from __future__ import annotations

from dataclasses import dataclass, field

from mountainash.core.capabilities.capture import (
    CapturedAddress,
    VerificationBinding,
    require_immutable,
)
from mountainash.core.capabilities.identity import Scope
from mountainash.core.capabilities.retired import AssertionChange
from mountainash.core.capabilities.schema import (
    CallableRef,
    ExternalEntrypointTarget,
    KnownGap,
    Target,
    _validate_external_target_scope,
    target_order_key,
)


@dataclass(frozen=True)
class InventoryWide:
    """An obligation owned by a verification inventory, not one backend."""


@dataclass(frozen=True)
class GapKey:
    inventory: str
    target: Target
    obligation: str
    coverage_scope: Scope | InventoryWide

    def __post_init__(self) -> None:
        if type(self.inventory) is not str or not self.inventory:
            raise ValueError("gap key requires an inventory")
        target_order_key(self.target)
        if type(self.obligation) is not str or not self.obligation:
            raise ValueError("gap key requires its guard obligation")
        if type(self.coverage_scope) not in (Scope, InventoryWide):
            raise TypeError("gap coverage requires Scope or InventoryWide")
        if type(self.target) is ExternalEntrypointTarget and type(self.coverage_scope) is not Scope:
            raise ValueError("external entrypoint gap requires its exact native dialect scope")
        if type(self.coverage_scope) is Scope:
            _validate_external_target_scope(self.target, self.coverage_scope)


@dataclass(frozen=True)
class InventoryGap:
    key: GapKey
    original_key: tuple[str | CallableRef | None, ...]
    payload: KnownGap
    origins: tuple[CapturedAddress, ...]
    reference_context: tuple[CapturedAddress, ...] = ()

    def __post_init__(self) -> None:
        if type(self.key) is not GapKey or type(self.payload) is not KnownGap:
            raise TypeError("inventory gap requires a qualified key and KnownGap payload")
        if (
            type(self.original_key) is not tuple
            or not self.original_key
            or any(type(part) not in (str, CallableRef, type(None)) for part in self.original_key)
        ):
            raise TypeError("original inventory key requires immutable text/protocol-reference slots")
        if (
            type(self.origins) is not tuple
            or not self.origins
            or any(type(origin) is not CapturedAddress for origin in self.origins)
        ):
            raise TypeError("inventory gap requires captured source origins")
        if type(self.reference_context) is not tuple or any(
            type(reference) is not CapturedAddress for reference in self.reference_context
        ):
            raise TypeError("inventory gap reference context requires captured addresses")
        require_immutable(self)


def gap_order_key(record: InventoryGap) -> tuple:
    scope = record.key.coverage_scope
    scope_key = (
        ("scope", scope.backend.value, type(scope.applicability).__name__, scope.dialect or "")
        if type(scope) is Scope
        else ("inventory",)
    )
    return (
        record.key.inventory,
        target_order_key(record.key.target),
        record.key.obligation,
        scope_key,
    )


@dataclass(frozen=True)
class GapInventory:
    name: str
    owner: CapturedAddress
    gaps: tuple[InventoryGap, ...]
    changes: tuple[AssertionChange, ...] = ()

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name or type(self.owner) is not CapturedAddress:
            raise TypeError("inventory requires its name and captured owner")
        if type(self.gaps) is not tuple or any(type(gap) is not InventoryGap for gap in self.gaps):
            raise TypeError("inventory gaps require an immutable qualified tuple")
        if any(gap.key.inventory != self.name for gap in self.gaps):
            raise ValueError("gap belongs to another inventory")
        if len({gap.key for gap in self.gaps}) != len(self.gaps):
            raise ValueError("duplicate inventory-qualified gap key")
        if len({gap.original_key for gap in self.gaps}) != len(self.gaps):
            raise ValueError("duplicate original inventory key")
        if type(self.changes) is not tuple or any(type(change) is not AssertionChange for change in self.changes):
            raise TypeError("inventory changes require AssertionChange records")
        for change in self.changes:
            if (
                change.prior.family != "gap"
                or type(change.prior.key) is not GapKey
                or change.prior.key.inventory != self.name
            ):
                raise ValueError("gap change predecessor belongs to another inventory")
        require_immutable(self)


@dataclass(frozen=True)
class VerificationSnapshot:
    inventories: tuple[GapInventory, ...]
    bindings: tuple[VerificationBinding, ...] | None = None
    gaps: tuple[InventoryGap, ...] = field(init=False)
    changes: tuple[AssertionChange, ...] = field(init=False)

    def __post_init__(self) -> None:
        if type(self.inventories) is not tuple or any(
            type(inventory) is not GapInventory for inventory in self.inventories
        ):
            raise TypeError("verification snapshot requires immutable inventories")
        if len({inventory.name for inventory in self.inventories}) != len(self.inventories):
            raise ValueError("duplicate verification inventory")
        gaps = tuple(
            sorted(
                (gap for inventory in self.inventories for gap in inventory.gaps),
                key=gap_order_key,
            )
        )
        changes = tuple(change for inventory in self.inventories for change in inventory.changes)
        if len({change.change_ref for change in changes}) != len(changes):
            raise ValueError("duplicate gap change address")
        if self.bindings is not None:
            if type(self.bindings) is not tuple or any(
                type(binding) is not VerificationBinding for binding in self.bindings
            ):
                raise TypeError("verification bindings require an immutable typed tuple")
            identities: list[tuple[object, object, object, object]] = []
            for binding in self.bindings:
                identity = (
                    binding.captured_claim,
                    binding.scenario,
                    binding.role,
                    binding.observer,
                )
                if identity in identities:
                    raise ValueError("duplicate verification binding identity")
                identities.append(identity)
        object.__setattr__(self, "gaps", gaps)
        object.__setattr__(self, "changes", changes)
        require_immutable(self)
