from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from mountainash.datacontracts.contract import BaseDataContract

# Lightweight eager exports: no dataframe backend is imported at package init.
from mountainash.__version__ import __version__
from mountainash.core.dtypes import DecimalDtype, MountainashDtype
from mountainash.core.errors import MountainashError
from mountainash.core.resource_ref import ResourceRef
from mountainash.core.types import DataFrameT
from mountainash.core.value_classification import (
    ValueKind,
    boolean_value,
    text_value,
    value_kind,
)
from mountainash.typespec.datapackage import DataPackage, DataResource, TableDialect
from mountainash.typespec.frictionless_codec import DescriptorWriteMode
from mountainash.typespec.spec import FieldDefinition, TableSchema

import lazy_loader


__getattr__, _lazy_dir, _LAZY_EXPORTS = lazy_loader.attach(
    __name__,
    submod_attrs={
        "core.capabilities": [
            "CapabilityIssueClass",
            "CapabilityPolicy",
            "ProtectionMechanism",
            "capability_policy",
        ],
        "expressions": [
            "CONST_EXPRESSION_NODE_TYPES",
            "CONST_LOGIC_TYPES",
            "BaseExpressionAPI",
            "BooleanExpressionAPI",
            "all_horizontal",
            "always_false",
            "always_true",
            "always_unknown",
            "any_horizontal",
            "coalesce",
            "col",
            "corr",
            "count_records",
            "duration",
            "greatest",
            "least",
            "len",
            "lit",
            "max_horizontal",
            "median",
            "min_horizontal",
            "native",
            "now",
            "quantile",
            "sum_horizontal",
            "t_col",
            "today",
            "when",
            "element",
        ],
        "expressions.core.expression_protocols.api_builders.substrait.prtcl_api_bldr_cast": [
            "CaseFailureBehaviour",
        ],
        "pydata.ingress": ["PydataIngress"],
        "relations": ["concat", "relation", "from_arrow"],
        "relations.dag": ["RelationDAG"],
        "relations.core.relation_api.materialization_scope": ["materialization_scope", "CheckpointPolicy"],
    },
)


def table_schema(columns: dict[str, str], **metadata) -> TableSchema:
    """Create a TableSchema from a simple {name: type_string} dict."""
    return TableSchema.from_simple_dict(columns, **metadata)


def datacontract(source: "dict | TableSchema | type | str | Path") -> "type[BaseDataContract]":
    """Create a DataContract from various schema sources.

    Accepts:
        - TableSchema object
        - BaseDataContract subclass (returned as-is)
        - Pydantic BaseModel subclass (extracted to TableSchema, then compiled)
        - str or Path to a Frictionless JSON schema file
        - dict with "fields" key (Frictionless descriptor)
        - dict without "fields" key (simple {name: type_string} mapping)
    """
    from pathlib import Path as _Path
    from mountainash.datacontracts.compiler import contract_from_table_schema
    from mountainash.datacontracts.contract import BaseDataContract as _BaseDataContract

    if isinstance(source, type) and issubclass(source, _BaseDataContract):
        return source

    if isinstance(source, TableSchema):
        return contract_from_table_schema(source)

    try:
        from pydantic import BaseModel as _PydanticBaseModel
    except ImportError:
        _PydanticBaseModel = None

    if _PydanticBaseModel is not None and isinstance(source, type) and issubclass(source, _PydanticBaseModel):
        from mountainash.typespec.extraction import extract_from_pydantic

        _schema = extract_from_pydantic(source)
        return contract_from_table_schema(_schema)

    if isinstance(source, (str, _Path)):
        import json

        from mountainash.typespec.datapackage import DataPackage

        path = _Path(source)
        if isinstance(source, _Path) or path.is_file():
            schema_source: object = path.name
            base_uri: _Path | None = path.parent
        else:
            schema_source = json.loads(source)
            base_uri = None
        package = DataPackage.from_descriptor(
            {
                "resources": [
                    {
                        "name": path.stem if path.stem else "schema",
                        "data": [],
                        "schema": schema_source,
                    }
                ]
            },
            base_uri=base_uri,
        )
        _schema = package.resources[0].to_table_schema()
        if _schema is None:
            raise TypeError("Frictionless schema input did not produce a schema mapping")
        return contract_from_table_schema(_schema)

    if isinstance(source, dict):
        if "fields" in source:
            from mountainash.typespec.frictionless import table_schema_from_frictionless

            _schema = table_schema_from_frictionless(source)
            return contract_from_table_schema(_schema)
        _schema = TableSchema.from_simple_dict(source)
        return contract_from_table_schema(_schema)

    raise TypeError(
        f"Cannot create datacontract from {type(source).__name__}. "
        "Expected TableSchema, dict, BaseModel subclass, "
        "or path to a Frictionless JSON file."
    )


"""Mountainash - Unified cross-backend DataFrame expression system."""

__all__ = [
    "__version__",
    "DecimalDtype",
    "MountainashDtype",
    "MountainashError",
    "ResourceRef",
    "DataFrameT",
    "ValueKind",
    "value_kind",
    "boolean_value",
    "text_value",
    "DataPackage",
    "DataResource",
    "TableDialect",
    "DescriptorWriteMode",
    "TableSchema",
    "FieldDefinition",
    "table_schema",
    "datacontract",
    "CapabilityIssueClass",
    "CapabilityPolicy",
    "ProtectionMechanism",
    "capability_policy",
    "CONST_EXPRESSION_NODE_TYPES",
    "CONST_LOGIC_TYPES",
    "BaseExpressionAPI",
    "BooleanExpressionAPI",
    "all_horizontal",
    "always_false",
    "always_true",
    "always_unknown",
    "any_horizontal",
    "coalesce",
    "col",
    "corr",
    "count_records",
    "duration",
    "greatest",
    "least",
    "len",
    "lit",
    "max_horizontal",
    "median",
    "min_horizontal",
    "native",
    "now",
    "quantile",
    "sum_horizontal",
    "t_col",
    "today",
    "when",
    "element",
    "CaseFailureBehaviour",
    "PydataIngress",
    "concat",
    "relation",
    "from_arrow",
    "RelationDAG",
    "materialization_scope",
    "CheckpointPolicy",
]


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
