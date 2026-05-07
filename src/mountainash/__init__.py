from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from mountainash.datacontracts.contract import BaseDataContract

# Re-export the full expressions public API at the top level
# so that `import mountainash as ma; ma.col("x")` works
from mountainash.expressions import (
    BaseExpressionAPI,
    BooleanExpressionAPI,
    col,
    lit,
    duration,
    native,
    coalesce,
    greatest,
    least,
    min_horizontal,
    max_horizontal,
    all_horizontal,
    any_horizontal,
    len,
    sum_horizontal,
    count_records,
    corr,
    median,
    quantile,
    when,
    t_col,
    always_true,
    always_false,
    always_unknown,
    CONST_VISITOR_BACKENDS,
    CONST_LOGIC_TYPES,
    CONST_EXPRESSION_NODE_TYPES,
)  # noqa: F401

from mountainash.__version__ import __version__  # noqa: F401

# Relations - Substrait-aligned relational AST
from mountainash.relations import relation, concat  # noqa: F401

# TypeSpec - backend-agnostic type specification
from mountainash.typespec.spec import TypeSpec  # noqa: F401

# DataPackage / DataResource / TableDialect — Frictionless Data Package support
from mountainash.typespec.datapackage import (  # noqa: F401
    DataPackage,
    DataResource,
    TableDialect,
)

# RelationDAG — orchestrator for named, interconnected Relations
from mountainash.relations.dag import RelationDAG, ResourceRef  # noqa: F401

# Conform - compile type specifications to relation operations
from mountainash.conform.builder import ConformBuilder  # noqa: F401


def typespec(columns: dict[str, str], **metadata) -> TypeSpec:
    """Create a TypeSpec from a simple {name: type_string} dict."""
    return TypeSpec.from_simple_dict(columns, **metadata)


def conform(source: dict | TypeSpec) -> ConformBuilder:
    """Create a ConformBuilder from a dict or TypeSpec."""
    return ConformBuilder(source)


def datacontract(source: "dict | TypeSpec | type | str | Path") -> "type[BaseDataContract]":
    """Create a DataContract from various schema sources.

    Accepts:
        - TypeSpec object
        - BaseDataContract subclass (returned as-is)
        - pandera DataFrameModel subclass (wrapped with BaseDataContract methods)
        - Pydantic BaseModel subclass (extracted to TypeSpec, then compiled)
        - str or Path to a Frictionless JSON schema file
        - dict with "fields" key (Frictionless descriptor)
        - dict without "fields" key (simple {name: type_string} mapping)
    """
    from pathlib import Path as _Path
    from mountainash.datacontracts.compiler import compile_datacontract
    from mountainash.datacontracts.contract import BaseDataContract as _BaseDataContract

    import pandera.polars as pa

    if isinstance(source, type) and issubclass(source, _BaseDataContract):
        return source

    if isinstance(source, type) and issubclass(source, pa.DataFrameModel):
        return type(
            f"{source.__name__}_DataContract",
            (_BaseDataContract, source),
            {},
        )

    if isinstance(source, TypeSpec):
        return compile_datacontract(source)

    try:
        from pydantic import BaseModel as _PydanticBaseModel
    except ImportError:
        _PydanticBaseModel = None

    if _PydanticBaseModel is not None and isinstance(source, type) and issubclass(source, _PydanticBaseModel):
        from mountainash.typespec.extraction import extract_from_pydantic
        _spec = extract_from_pydantic(source)
        return compile_datacontract(_spec)

    if isinstance(source, (str, _Path)):
        from mountainash.typespec.frictionless import typespec_from_frictionless
        _spec = typespec_from_frictionless(source)
        return compile_datacontract(_spec)

    if isinstance(source, dict):
        if "fields" in source:
            from mountainash.typespec.frictionless import typespec_from_frictionless
            _spec = typespec_from_frictionless(source)
            return compile_datacontract(_spec)
        _spec = TypeSpec.from_simple_dict(source)
        return compile_datacontract(_spec)

    raise TypeError(
        f"Cannot create datacontract from {type(source).__name__}. "
        "Expected TypeSpec, dict, BaseModel subclass, DataFrameModel subclass, "
        "or path to a Frictionless JSON file."
    )


"""Mountainash - Unified cross-backend DataFrame expression system."""
