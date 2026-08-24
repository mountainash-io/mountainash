"""Capability declarations for lexical and native list operations."""
from __future__ import annotations

from mountainash.core.capabilities import (
    CapabilityDeclaration, CapabilityFact, CapabilityLevel, Enforcement,
    Boundary, FactSource, Domain, ProbeEvidence, WILDCARD_PARAM,
)
from mountainash.core.constants import CONST_BACKEND
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST
from ._structural_common import unsupported, SINCE
_ITEM_TYPES = ("string", "integer", "boolean", "number", "datetime", "date", "time")
_THROW_SUPPORTED = {
    (CONST_BACKEND.POLARS, None): set(_ITEM_TYPES),
    (CONST_BACKEND.NARWHALS, "narwhals-polars"): {"string", "integer", "number", "boolean", "date"},
    (CONST_BACKEND.NARWHALS, "narwhals-pandas"): {"string", "integer", "number", "boolean", "date"},
    (CONST_BACKEND.NARWHALS, "narwhals-lazy"): {"string", "integer", "number", "boolean", "date"},
    (CONST_BACKEND.IBIS, "ibis-duckdb"): {"string", "integer", "boolean", "number", "date", "time"},
    (CONST_BACKEND.IBIS, "ibis-polars"): {"string"},
    (CONST_BACKEND.IBIS, "ibis-sqlite"): set(),
}
_NULL_SUPPORTED = {
    (CONST_BACKEND.POLARS, None): set(_ITEM_TYPES),
    (CONST_BACKEND.NARWHALS, "narwhals-polars"): {"string"},
    (CONST_BACKEND.NARWHALS, "narwhals-pandas"): {"string"},
    (CONST_BACKEND.NARWHALS, "narwhals-lazy"): {"string"},
    (CONST_BACKEND.IBIS, "ibis-duckdb"): {"string"},
    (CONST_BACKEND.IBIS, "ibis-polars"): {"string"},
    (CONST_BACKEND.IBIS, "ibis-sqlite"): set(),
}

_MSG_PARSE = "This backend cannot execute LIST.PARSE for the requested item type and failure behavior"
_MSG_CAST = "This backend cannot execute LIST.CAST_ITEMS for the requested failure behavior"
def _parse_facts() -> tuple:
    out = []
    for (backend, dialect), throw_supported in _THROW_SUPPORTED.items():
        if backend is CONST_BACKEND.IBIS and dialect == "ibis-sqlite":
            out.append(
                unsupported(
                    FK_LIST.PARSE, backend, dialect, message=_MSG_PARSE,
                )
            )
            continue
        for item_type in _ITEM_TYPES:
            if item_type not in throw_supported:
                out.append(
                    unsupported(
                        FK_LIST.PARSE, backend, dialect, message=_MSG_PARSE,
                        option="item_type", value=item_type,
                    )
                )
    for (backend, dialect), null_supported in _NULL_SUPPORTED.items():
        if backend is CONST_BACKEND.IBIS and dialect == "ibis-sqlite":
            continue
        throw_supported = _THROW_SUPPORTED[(backend, dialect)]
        for item_type in _ITEM_TYPES:
            if item_type in throw_supported and item_type not in null_supported:
                out.append(
                    unsupported(
                        FK_LIST.PARSE, backend, dialect, message=_MSG_PARSE,
                        option="failure_behavior", item_type=item_type,
                        failure_behavior="null",
                    )
                )
    return tuple(out)


def _cast_facts() -> tuple:
    out = []
    throw_support = {
        (CONST_BACKEND.POLARS, None): True,
        (CONST_BACKEND.NARWHALS, "narwhals-polars"): True,
        (CONST_BACKEND.NARWHALS, "narwhals-pandas"): False,
        (CONST_BACKEND.NARWHALS, "narwhals-lazy"): False,
        (CONST_BACKEND.IBIS, "ibis-duckdb"): True,
        (CONST_BACKEND.IBIS, "ibis-polars"): True,
        (CONST_BACKEND.IBIS, "ibis-sqlite"): False,
    }
    null_support = {
        (CONST_BACKEND.POLARS, None): True,
        (CONST_BACKEND.NARWHALS, "narwhals-polars"): False,
        (CONST_BACKEND.NARWHALS, "narwhals-pandas"): False,
        (CONST_BACKEND.NARWHALS, "narwhals-lazy"): False,
        (CONST_BACKEND.IBIS, "ibis-duckdb"): False,
        (CONST_BACKEND.IBIS, "ibis-polars"): False,
        (CONST_BACKEND.IBIS, "ibis-sqlite"): False,
    }
    for (backend, dialect), supported in throw_support.items():
        if not supported:
            out.append(unsupported(FK_LIST.CAST_ITEMS, backend, dialect, message=_MSG_CAST, option="failure_behavior", value="throw"))
    for (backend, dialect), supported in null_support.items():
        if not supported:
            out.append(unsupported(FK_LIST.CAST_ITEMS, backend, dialect, message=_MSG_CAST, option="failure_behavior", value="null"))
    return tuple(out)

FACTS = _parse_facts() + _cast_facts() + (
    CapabilityFact(
        operation_key=FK_LIST.PARSE,
        param=WILDCARD_PARAM,
        level=CapabilityLevel.UNSUPPORTED,
        backend=CONST_BACKEND.NARWHALS,
        dialect="narwhals-pandas",
        message="Narwhals pandas list parsing may raise a TypeError during materialization",
        since=SINCE,
        boundary=Boundary.MATERIALIZE,
        enforcement=Enforcement.MATERIALIZE_RESIDUE,
        native_errors=(TypeError,),
    ),
)
_EVIDENCE = ProbeEvidence(probe_date=SINCE, library_versions=(), fixtures=("lexical-list-seven-item-types", "recursive-array-struct"))

DECLARATIONS = tuple(
    CapabilityDeclaration(backend=backend, domain=Domain.LIST, source=FactSource.MOUNTAINASH, facts=tuple(f for f in FACTS if f.backend is backend), evidence=_EVIDENCE)
    for backend in (CONST_BACKEND.POLARS, CONST_BACKEND.NARWHALS, CONST_BACKEND.IBIS)
)
