"""Scope-owned capability declarations; import-safe data only."""

from __future__ import annotations

from mountainash.core.capabilities.applicability import unbounded
from mountainash.core.capabilities.declarations import (
    CapabilityInformation,
    CapabilityKey,
    CapabilitySegment,
    Domain,
    Selector,
)
from mountainash.core.capabilities.schema import CapabilityLevel, Clause, ClauseOp, InformationLayer, Predicate
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL

SEGMENT = CapabilitySegment(
    domain=Domain.GEOSPATIAL,
    information=(
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                subject="format",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="format", op=ClauseOp.EQ, operand="array"),
                            Clause(path="source_representation", op=ClauseOp.EQ, operand="native"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                subject="format",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="format", op=ClauseOp.EQ, operand="object"),
                            Clause(path="source_representation", op=ClauseOp.EQ, operand="native"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
        CapabilityInformation(
            key=CapabilityKey(
                operation=FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL.PARSE_GEOPOINT,
                subject="format",
                selector=Selector(
                    kind="predicate",
                    value=Predicate(
                        clauses=(
                            Clause(path="failure_behavior", op=ClauseOp.EQ, operand="throw"),
                            Clause(path="format", op=ClauseOp.EQ, operand="default"),
                            Clause(path="source_representation", op=ClauseOp.EQ, operand="lexical"),
                        )
                    ),
                ),
            ),
            level=CapabilityLevel.UNSUPPORTED,
            message="This backend cannot execute the requested geospatial operation cell",
            layer=InformationLayer.NATIVE,
            applicability=unbounded,
        ),
    ),
)
