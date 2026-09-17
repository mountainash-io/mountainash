"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME
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
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1y"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1mo"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="year"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.ROUND,
                subject="unit",
                selector=Selector(kind="exact", value="month"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1y"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1mo"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="1q"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="year"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="quarter"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
        ),
        CapabilityAssertion(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_DATETIME.CEIL,
                subject="unit",
                selector=Selector(kind="exact", value="month"),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-16",
            message="ibis's polars sub-backend translates interval addition via polars.duration(), which has no months/years kwarg -- round/ceil cannot compute the next calendar boundary (truncate/floor, which only need FLOOR, are unaffected); verified 2026-08-16, ibis 12.0.0",
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
