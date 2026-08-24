"""Capability declarations for geospatial operation cells."""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityDeclaration,
    CapabilityFact,
    CapabilityLevel,
    Clause,
    ClauseOp,
    Domain,
    FactSource,
    Predicate,
    ProbeEvidence,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_GEOSPATIAL as FK_GEO,
)

SINCE = "2026-08-21"
_MSG = "This backend cannot execute the requested geospatial operation cell"


def _predicate(**values: str) -> Predicate:
    return Predicate(tuple(Clause(name, ClauseOp.EQ, value) for name, value in values.items()))


def _gated(
    key,
    backend: CONST_BACKEND,
    dialect: str | None,
    *,
    predicate: Predicate | None = None,
) -> CapabilityFact:
    return CapabilityFact(
        operation_key=key,
        param="format" if predicate is not None else "*",
        option_value=None,
        predicate=predicate,
        level=CapabilityLevel.UNSUPPORTED,
        backend=backend,
        dialect=dialect,
        message=_MSG,
        since=SINCE,
    )


def _cell_pred(format: str, source_representation: str, failure_behavior: str | None = None) -> Predicate:
    values = {"format": format, "source_representation": source_representation}
    if failure_behavior is not None:
        values["failure_behavior"] = failure_behavior
    return _predicate(**values)

_COMMON_NW = (
    _gated(FK_GEO.PARSE_GEOJSON, CONST_BACKEND.NARWHALS, None),
    _gated(FK_GEO.SERIALIZE_GEOJSON, CONST_BACKEND.NARWHALS, None),
)
_COMMON_IB = (
    _gated(FK_GEO.PARSE_GEOJSON, CONST_BACKEND.IBIS, None),
    _gated(FK_GEO.SERIALIZE_GEOJSON, CONST_BACKEND.IBIS, None),
)

_NW = (
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.NARWHALS, None, predicate=_cell_pred("array", "lexical")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.NARWHALS, None, predicate=_cell_pred("object", "native")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.NARWHALS, None, predicate=_cell_pred("array", "native", "null")),
)
_IB = (
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.IBIS, None, predicate=_cell_pred("array", "lexical")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.IBIS, None, predicate=_cell_pred("array", "native", "null")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.IBIS, None, predicate=_cell_pred("object", "native", "null")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.IBIS, "ibis-sqlite", predicate=_cell_pred("array", "native")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.IBIS, "ibis-sqlite", predicate=_cell_pred("object", "native")),
    _gated(FK_GEO.PARSE_GEOPOINT, CONST_BACKEND.IBIS, "ibis-sqlite", predicate=_cell_pred("default", "lexical", "throw")),
)

_EVIDENCE = ProbeEvidence(
    probe_date=SINCE,
    library_versions=(
        ("narwhals", "2.24.0"),
        ("polars", "1.43.2"),
        ("pandas", "3.0.5"),
        ("pyarrow", "25.0.1"),
        ("ibis", "12.0.0"),
    ),
    fixtures=("geopoint-format-representation", "geojson-object-root", "native-coordinate-validation"),
)

DECLARATIONS = (
    CapabilityDeclaration(
        backend=CONST_BACKEND.POLARS,
        domain=Domain.GEOSPATIAL,
        source=FactSource.MOUNTAINASH,
        facts=(),
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.NARWHALS,
        domain=Domain.GEOSPATIAL,
        source=FactSource.MOUNTAINASH,
        facts=_COMMON_NW + _NW,
        evidence=_EVIDENCE,
    ),
    CapabilityDeclaration(
        backend=CONST_BACKEND.IBIS,
        domain=Domain.GEOSPATIAL,
        source=FactSource.MOUNTAINASH,
        facts=_COMMON_IB + _IB,
        evidence=_EVIDENCE,
    ),
)
