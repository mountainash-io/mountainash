"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
from mountainash.core.capabilities.schema import ValueClass
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel


from mountainash.core.capabilities.declarations import CapabilityAssertion
from mountainash.core.capabilities.schema import Boundary
from mountainash.core.capabilities.schema import Enforcement
from mountainash.core.capabilities.schema import ResidueSignal
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.DATETIME,
    capabilities=(
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.TO_TIMEZONE,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-07-29",
            message="to_timezone is correct only at the materialization boundary -- the target zone lives in the ibis output dtype, not in the engine (SQL is a bare CAST AS TIMESTAMPTZ), so any expression composed on the result raises UnsupportedOperationError (verified 2026-07-29, ibis 12.0.0/duckdb)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.IS_DST,
                subject="timezone",
                selector=Selector(kind="value_class", value=ValueClass.IANA_TIMEZONE),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="is_dst is not supported on ibis -- ibis has no DST/timezone-offset primitive to build on (verified 2026-08-16, ibis 12.0.0/duckdb)",
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="invalid XSD lexical values are converted to null by the residue policy",
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            signal=ResidueSignal.NON_NULL_TO_NULL,
        ),
        CapabilityAssertion(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="invalid XSD lexical values are converted to null by the residue policy",
            boundary=Boundary.MATERIALIZE,
            enforcement=Enforcement.MATERIALIZE_RESIDUE,
            signal=ResidueSignal.NON_NULL_TO_NULL,
        ),
    ),
)
