"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_DATETIME
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="MONDAY_WEEK"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="PICOSECOND"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="SUNDAY_WEEK"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="TIMEZONE_OFFSET"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="US_WEEK"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT,
                subject="component",
                selector=Selector(kind="exact", value="US_YEAR"),
            ),
            layer=InformationLayer.NATIVE,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="the native backend has no primitive for this extract component (verified by semantic probe; see capabilities/datetime/extract.py)",
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_SUBSTRAIT_SCALAR_DATETIME.EXTRACT_BOOLEAN,
                subject="component",
                selector=Selector(kind="exact", value="IS_DST"),
            ),
            layer=InformationLayer.PUBLIC,
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-15",
            message="extract_boolean(IS_DST) is a placeholder (constant False) on all backends; deferred to backlog item 65 (is-dst-placeholder-implementation)",
        ),
    ),
)
