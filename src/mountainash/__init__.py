from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from mountainash.datacontracts.contract import BaseDataContract

# Re-export the full expressions public API at the top level
# so that `import mountainash as ma; ma.col("x")` works
from mountainash.__version__ import __version__  # noqa: F401

# MountainashDtype — canonical type vocabulary (accepted by cast/schema APIs)
from mountainash.core.dtypes import MountainashDtype  # noqa: F401

# MountainashError — root of the typed error hierarchy.
# NOTE: import ONLY the root here. Do NOT import mountainash.exceptions (the
# façade), whose transitive imports would run at package-init time and re-expose
# circular-import risk. The façade is imported only on explicit `import
# mountainash.exceptions`.
from mountainash.core.errors import MountainashError  # noqa: F401

# RelationDAG — orchestrator for named, interconnected Relations
from mountainash.core.resource_ref import ResourceRef  # noqa: F401
from mountainash.core.types import DataFrameT
from mountainash.expressions import (
    CONST_EXPRESSION_NODE_TYPES,
    CONST_LOGIC_TYPES,
    BaseExpressionAPI,
    BooleanExpressionAPI,
    all_horizontal,
    always_false,
    always_true,
    always_unknown,
    any_horizontal,
    coalesce,
    col,
    corr,
    count_records,
    duration,
    greatest,
    least,
    len,
    lit,
    max_horizontal,
    median,
    min_horizontal,
    native,
    now,
    quantile,
    sum_horizontal,
    t_col,
    today,
    when,
)  # noqa: F401
from mountainash.pydata.ingress import PydataIngress

# Relations - Substrait-aligned relational AST
from mountainash.relations import concat, relation  # noqa: F401
from mountainash.relations.dag import RelationDAG  # noqa: F401

# DataPackage / DataResource / TableDialect — Frictionless Data Package support
from mountainash.typespec.datapackage import (  # noqa: F401
    DataPackage,
    DataResource,
    TableDialect,
)

# TypeSpec - backend-agnostic type specification
from mountainash.typespec.spec import TypeSpec  # noqa: F401


def typespec(columns: dict[str, str], **metadata) -> TypeSpec:
    """Create a TypeSpec from a simple {name: type_string} dict."""
    return TypeSpec.from_simple_dict(columns, **metadata)


def datacontract(source: "dict | TypeSpec | type | str | Path") -> "type[BaseDataContract]":
    """Create a DataContract from various schema sources.

    Accepts:
        - TypeSpec object
        - BaseDataContract subclass (returned as-is)
        - Pydantic BaseModel subclass (extracted to TypeSpec, then compiled)
        - str or Path to a Frictionless JSON schema file
        - dict with "fields" key (Frictionless descriptor)
        - dict without "fields" key (simple {name: type_string} mapping)
    """
    from pathlib import Path as _Path
    from mountainash.datacontracts.compiler import contract_from_typespec
    from mountainash.datacontracts.contract import BaseDataContract as _BaseDataContract

    if isinstance(source, type) and issubclass(source, _BaseDataContract):
        return source

    if isinstance(source, TypeSpec):
        return contract_from_typespec(source)

    try:
        from pydantic import BaseModel as _PydanticBaseModel
    except ImportError:
        _PydanticBaseModel = None

    if _PydanticBaseModel is not None and isinstance(source, type) and issubclass(source, _PydanticBaseModel):
        from mountainash.typespec.extraction import extract_from_pydantic

        _spec = extract_from_pydantic(source)
        return contract_from_typespec(_spec)

    if isinstance(source, (str, _Path)):
        from mountainash.typespec.frictionless import typespec_from_frictionless

        _spec = typespec_from_frictionless(source)
        return contract_from_typespec(_spec)

    if isinstance(source, dict):
        if "fields" in source:
            from mountainash.typespec.frictionless import typespec_from_frictionless

            _spec = typespec_from_frictionless(source)
            return contract_from_typespec(_spec)
        _spec = TypeSpec.from_simple_dict(source)
        return contract_from_typespec(_spec)

    raise TypeError(
        f"Cannot create datacontract from {type(source).__name__}. "
        "Expected TypeSpec, dict, BaseModel subclass, "
        "or path to a Frictionless JSON file."
    )


"""Mountainash - Unified cross-backend DataFrame expression system."""
