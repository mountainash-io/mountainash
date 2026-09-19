"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.declarations import Domain
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL
from mountainash.core.capabilities.declarations import CapabilityKey
from mountainash.core.capabilities.schema import CapabilityLevel, InformationLayer


from mountainash.core.capabilities.declarations import CapabilityInformation
from mountainash.core.capabilities.schema import ClauseOp
from mountainash.core.capabilities.schema import Clause
from mountainash.core.capabilities.schema import Predicate
from mountainash.core.capabilities.declarations import Selector
from mountainash.core.capabilities.declarations import CapabilitySegment

SEGMENT = CapabilitySegment(
    domain=Domain.GEOSPATIAL,
    information=(
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOJSON, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.PUBLIC,
        ),
        CapabilityInformation(
            key=CapabilityKey(operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.SERIALIZE_GEOJSON, subject="*"),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.PUBLIC,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                subject="format",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="format", op=ClauseOp.EQ, operand="array"),
                            Clause(path="source_representation", op=ClauseOp.EQ, operand="lexical"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                subject="format",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="format", op=ClauseOp.EQ, operand="array"),
                            Clause(path="source_representation", op=ClauseOp.EQ, operand="native"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.NATIVE,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                subject="format",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="null"),
                            Clause(path="format", op=ClauseOp.EQ, operand="object"),
                            Clause(path="source_representation", op=ClauseOp.EQ, operand="native"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            since="2026-08-21",
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.NATIVE,
        ),
    ),
)
