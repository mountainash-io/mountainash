"""Compile a TypeSpec into a pandera DataFrameModel (BaseDataContract subclass)."""
from __future__ import annotations

from typing import Any

import pandera.polars as pa

from mountainash.typespec.spec import TypeSpec, FieldConstraints
from mountainash.typespec.universal_types import UniversalType
from mountainash.datacontracts.contract import BaseDataContract

UNIVERSAL_TYPE_TO_PANDERA: dict[UniversalType, type] = {
    UniversalType.STRING: str,
    UniversalType.INTEGER: int,
    UniversalType.NUMBER: float,
    UniversalType.BOOLEAN: bool,
    UniversalType.DATE: str,
    UniversalType.TIME: str,
    UniversalType.DATETIME: str,
    UniversalType.DURATION: str,
    UniversalType.YEAR: int,
    UniversalType.YEARMONTH: str,
    UniversalType.ANY: object,
}


def _constraints_to_field_kwargs(constraints: FieldConstraints | None) -> dict[str, Any]:
    if constraints is None:
        return {"nullable": True}

    kwargs: dict[str, Any] = {}
    kwargs["nullable"] = not constraints.required
    if constraints.unique:
        kwargs["unique"] = True
    if constraints.minimum is not None:
        kwargs["ge"] = constraints.minimum
    if constraints.maximum is not None:
        kwargs["le"] = constraints.maximum
    if constraints.enum is not None:
        kwargs["isin"] = constraints.enum
    if constraints.pattern is not None:
        kwargs["str_matches"] = constraints.pattern
    if constraints.min_length is not None or constraints.max_length is not None:
        length_kwargs: dict[str, int] = {}
        if constraints.min_length is not None:
            length_kwargs["min_value"] = constraints.min_length
        if constraints.max_length is not None:
            length_kwargs["max_value"] = constraints.max_length
        kwargs["str_length"] = length_kwargs
    return kwargs


def compile_datacontract(
    spec: TypeSpec,
    *,
    name: str | None = None,
) -> type[BaseDataContract]:
    """Generate a BaseDataContract subclass from a TypeSpec."""
    contract_name = name or spec.title or "CompiledDataContract"

    annotations: dict[str, type] = {}
    namespace: dict[str, Any] = {"__annotations__": annotations}

    for field_spec in spec.fields:
        python_type = UNIVERSAL_TYPE_TO_PANDERA.get(field_spec.type, object)
        annotations[field_spec.name] = python_type
        field_kwargs = _constraints_to_field_kwargs(field_spec.constraints)
        if field_kwargs:
            namespace[field_spec.name] = pa.Field(**field_kwargs)

    return type(contract_name, (BaseDataContract,), namespace)
