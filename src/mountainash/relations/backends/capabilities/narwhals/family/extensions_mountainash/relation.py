"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.declarations import CapabilitySegment
from mountainash.core.capabilities.declarations import Domain
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.schema import CapabilityLevel
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import InformationLayer
from mountainash.core.capabilities.schema import Predicate
from mountainash.relations.core.relation_system.relation_keys.enums import RKEY_MOUNTAINASH_REL

SEGMENT = CapabilitySegment(
    domain=Domain.RELATION,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.UNNEST, subject="*"),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-05",
            message="Narwhals does not implement UNNEST and raises NotImplementedError.",
            workaround="Use the Polars backend for unnest.",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=RKEY_MOUNTAINASH_REL.JOIN_ASOF,
                subject="tolerance",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(clauses=(Clause(path="tolerance", op=ClauseOp.IS_SET),)),
                ),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-05",
            message="Narwhals JOIN_ASOF refuses a non-None tolerance; omitting tolerance preserves the native strategy behavior.",
            workaround="Drop tolerance or use the Polars backend.",
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=RKEY_MOUNTAINASH_REL.READ_RESOURCE, subject="resource"),
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-30",
            message="CSV dialect fields outside the native provider contract select Mountainash's portable fallback reader.",
            workaround="No action is needed; Mountainash routes these resources automatically.",
        ),
    ),
)
