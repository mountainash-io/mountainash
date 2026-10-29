---
title: Type System and Schema
description: Shared TableSchema and FieldDefinition declarations, schema extraction, Frictionless interchange, and protocol-owned native representations.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 9: Type System and Schema

## Summary

Shared declarations, recursive field composition, contextual naming, FieldConstraints, UniversalType, native type/schema adapters, Frictionless interchange, extraction, conformance and validation.

---

## Introduction

Mountainash uses one backend- and format-neutral declaration model across schemas, conformance and data contracts. Frictionless Table Schema is a supported interchange format, not the owner of the Python layout. Native adapters translate representations; existing expression/relation execution converts data, and validation checks requirements.

<!-- concept:150 -->
## UniversalType Enum

The `UniversalType` enum defines the universal data types that mountainash recognizes. Based on the Frictionless Table Schema specification, these types provide a common vocabulary that maps to every supported backend's native type system.

```python
class UniversalType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"      # Broad numeric meaning; dtype may refine it to Decimal
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DURATION = "duration"
    YEAR = "year"
    YEARMONTH = "yearmonth"
    LIST = "list"          # Lexical delimited collection
    ARRAY = "array"
    OBJECT = "object"
    GEOPOINT = "geopoint"
    GEOJSON = "geojson"
    ANY = "any"
```

Unlike `MountainashDtype` (which uses Substrait-aligned names like `i64` and `fp32` for expression-level type casting), `UniversalType` uses the Frictionless naming convention for schema-level type metadata. The type bridge (described below) converts between these two systems.

| UniversalType | Frictionless Equivalent | Polars Type | Pandas Dtype |
|---------------|------------------------|-------------|--------------|
| STRING | string | Utf8 | object/string |
| INTEGER | integer | Int64 | int64 |
| NUMBER | number | Float64 | float64 |
| BOOLEAN | boolean | Boolean | bool |
| DATE | date | Date | datetime64[ns] |
| DATETIME | datetime | Datetime | datetime64[ns] |

<!-- concept:148 -->
## FieldDefinition

A `FieldDefinition` is an unnamed, immutable declaration of type, constraints, conversion instructions and metadata. Local names belong to table/record mappings or data-contract members. Reuse a definition unchanged, or make a copy with `.variant(...)`.

```python
from mountainash import FieldDefinition, TableSchema
from mountainash.typespec import UniversalType

quantity = FieldDefinition(type=UniversalType.INTEGER, minimum=0)
schema = TableSchema(fields={
    "quantity": quantity,
    "shipped": quantity.variant(rename_from="raw_shipped", null_fill=0),
    "lines": FieldDefinition(element=FieldDefinition(fields={"quantity": quantity})),
}, fields_match="open")
```

`rename_from` selects an original source column; the containing mapping key selects
the output name. Swaps and fan-out read unchanged source values. Record `fields`,
collection `element` and optional fixed-array `dimensions` compose complete
definitions. A bare dtype remains useful without a field declaration.

- **type / dtype**: Broad logical meaning and optional precise representation.
- **constraints**: Shared requirements interpreted by validation.
- **missing_values / null_fill**: Conversion instructions; failed casts do not become original missing values.
- **rename_from / severity**: Local-use settings carried by an immutable copy.

<!-- concept:149 -->
## FieldConstraints

`FieldConstraints` is shared by schema and contract authoring. It includes required,
unique, inclusive/exclusive bounds, length, pattern, enum and JSON Schema checks,
plus equality/exclusion and string requirements. Definitions may use concise
constraint keywords, as `minimum=0` does above, without creating a contract-only
requirement store. A constraint does not invent a dtype, and conform does not
execute validation checks.

Constraints are checked during schema validation (described later in this chapter). They can express rules like "this column must not be null" (required=True), "values must be unique" (unique=True), or "values must match this regex" (pattern).

<!-- concept:147 -->
## TableSchema

`TableSchema` owns a mutable, insertion-ordered name-to-FieldDefinition mapping, plus table-level keys and metadata. Construction copies the supplied mapping; deferred operations capture snapshots so later author edits do not change an already-built plan.

```python
# Creating a TableSchema from a simple dictionary
import mountainash as ma

spec = ma.table_schema({
    "id": "integer",
    "name": "string",
    "email": "string",
    "created_at": "datetime",
})
```

TableSchema supports direct mappings, simple type dictionaries, Frictionless descriptors and extraction from dataframes, dataclasses and Pydantic models. None requires adopting a data-contract base class.

#### Diagram: TableSchema Construction Sources
<iframe src="../../sims/typespec-construction/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>TableSchema Construction Sources</summary>
Type: workflow
**sim-id:** typespec-construction<br/>
**Library:** vis-network<br/>
**Status:** Specified

The diagram connects supported authoring and extraction routes to TableSchema. Each route supplies only its available evidence: dataframe metadata does not invent business constraints, and the typed codec does not own file resolution.
</details>

<!-- concept:151 -->
## Type Bridge

The broad `UniversalType` vocabulary maps to canonical `MountainashDtype` values
and portable parameterized descriptors. Shared resolution combines authored
requirements with available source evidence without rewriting the declaration.
For example, INTEGER normally resolves to I64, while a precise dtype can select
I32. Native overrides remain target-specific and authoritative. UNKNOWN evidence
and an explicitly unconstrained declaration are different states.

<!-- concept:152 -->
## Backend Type Mapping

Native type adapters own construction, parsing, reverse mapping and equivalence
for their representation family. Native schema adapters own complete schemas and
source evidence. The existing dtype/schema registries select implementations
lazily; shared consumers do not contain backend constructor ladders.

The extension boundaries are `NativeTypeAdapter`, `NativeSchemaAdapter`,
`NativeArrowTransportAdapter` and `SchemaCodec`. Adding a representation requires
its adapter and registration, protocol-alignment checks and behavioral fidelity
checks. Adding an execution backend or SQL dialect also uses the existing
expression/relation systems; registering a schema adapter alone does not supply
an execution engine.

<!-- concept:153 -->
## Foreign Keys

Foreign keys define referential integrity relationships between tables. A foreign key declaration says "the values in these columns of this table must exist in the specified columns of another table."

```python
@dataclass
class ForeignKey:
    fields: list[str]         # Columns in this table
    reference: ForeignKeyReference  # Target table and columns
```

Foreign keys are stored on TableSchema and used by RelationDAG for constraint metadata and integrity validation. Constraint edges never become dependency edges or trigger upstream execution.

<!-- concept:154 -->
## ForeignKeyReference

`ForeignKeyReference` specifies the target of a foreign key relationship. It identifies the referenced table (resource) name and the field(s) within that table.

```python
@dataclass
class ForeignKeyReference:
    resource: str | None  # None means a self-reference
    fields: list[str]   # Column(s) in the referenced table
```

`resource=None` represents a self-reference. The typed writer omits that property; the reader also accepts the official legacy empty-string shorthand.

<!-- concept:155 -->
## Custom Type Registry

The custom type registry enables extending the type system with domain-specific types beyond the standard UniversalType values. This is useful for types that have specialized validation or conversion logic not covered by the base Frictionless types.

`CustomTypeRegistry` owns the existing Python-only and Narwhals-vectorized conversion tiers at Python I/O boundaries. It is distinct from native representation adapters and does not create another conform execution engine.

<!-- concept:156 -->
## Type Converters

Public converter helpers delegate to the selected native adapters. Native schema
projection describes representable types; it does not execute constraints.
Extraction preserves available parameters and qualifiers, including Arrow field
metadata and wrapped native precision, without inventing authored requirements.

<!-- concept:157 -->
## Frictionless Standard

The Frictionless Data standard is an open specification for describing tabular data. Mountainash aligns with its Table Schema and Data Package specifications to enable interoperability with the broader data ecosystem.

Key Frictionless concepts that mountainash adopts include:

- **Table Schema**: JSON structure describing column names, types, and constraints
- **Data Resource**: Wrapper around a table schema with path and format metadata
- **Data Package**: Collection of data resources with package-level metadata
- **Field descriptors**: JSON objects with name, type, format, and constraints
- **Missing values**: Configurable string representations of null

This alignment means mountainash can read and write standard Frictionless descriptor files, enabling schema sharing with tools outside the mountainash ecosystem.

<!-- concept:158 -->
## Table Schema

A Table Schema is the Frictionless standard's way of describing the structure of a tabular dataset. It consists of an array of field descriptors (each specifying a column name and type) plus optional primary key and foreign key declarations.

```json
{
  "fields": [
    {"name": "id", "type": "integer", "constraints": {"required": true}},
    {"name": "name", "type": "string"},
    {"name": "email", "type": "string", "constraints": {"pattern": ".*@.*"}}
  ],
  "primaryKey": ["id"],
  "foreignKeys": []
}
```

`table_schema_from_frictionless()` and `table_schema_to_frictionless()` are the typed codec boundary. They preserve the supported property inventory and recursive declarations through JSON text, but normalize defaults and do not preserve arbitrary unknown properties. Raw DataResource storage owns that separate fidelity contract; `to_table_schema()` resolves and converts lazily without rewriting storage.

<!-- concept:159 -->
## Schema Extraction

Schema extraction produces TableSchema from native dataframe metadata, dataclass
annotations or supported Pydantic field metadata. Native-schema acquisition
selects an adapter centrally; it retains available evidence rather than routing
through a least-common-denominator dataframe conversion.

<!-- concept:160 -->
## DataFrame Extraction

Dataframe extraction reads native schema metadata and produces contextual field definitions. Precise dtype parameters remain available alongside broad UniversalType metadata.

```python
import polars as pl
from mountainash.typespec.extraction import extract_from_dataframe

df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
spec = extract_from_dataframe(df)
# spec.fields["id"].type == UniversalType.INTEGER
# spec.fields["name"].type == UniversalType.STRING
```

DataFrame extraction captures type information but cannot infer constraints (required, unique, min/max) because those are semantic properties not visible from the data alone.

<!-- concept:161 -->
## Dataclass Extraction

Dataclass extraction reads Python type annotations from a `@dataclass` class definition and maps them to UniversalType values. This enables defining schemas as Python code with full IDE support.

```python
from dataclasses import dataclass
from datetime import datetime
from mountainash.typespec.extraction import extract_from_dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime

schema = extract_from_dataclass(User)
```

Python type annotations map naturally to universal types: `int` becomes INTEGER, `str` becomes STRING, `float` becomes NUMBER, `bool` becomes BOOLEAN, and datetime types map to their temporal equivalents.

<!-- concept:162 -->
## Pydantic Extraction

Pydantic extraction reads supported field annotations and constraint metadata from a BaseModel. It does not translate arbitrary Python validator code into portable checks.

```python
from pydantic import BaseModel, Field
from mountainash.typespec.extraction import extract_from_pydantic

class User(BaseModel):
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1)
    email: str

schema = extract_from_pydantic(User)
```

<!-- concept:163 -->
## Schema Validation

`validate_match(frame, schema)` checks structural/type compatibility; it is not the
value-constraint engine. `schema.to_contract().validate_datacontract(frame)` uses
the existing validation machinery for shared requirements. Conform converts;
contract checking reports failures and configured severity.

<!-- concept:165 -->
## Schema Comparison

`compare_specs(actual, expected)` compares declared field names and types. Use
contract validation for value requirements and the conform reconciliation policy
for structural drift; these operations have separate responsibilities.

#### Diagram: Schema Comparison Workflow
<iframe src="../../sims/schema-comparison/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Schema Comparison Workflow</summary>
Type: microsim
**sim-id:** schema-comparison<br/>
**Library:** p5.js<br/>
**Status:** Specified

The comparison diagram illustrates source and target TableSchema field names/types. It is not evidence that constraints ran or that every backend can represent a requested dtype.
</details>

<!-- concept:166 -->
## Polars Schema Convert

Polars schema projection produces a name-to-native-dtype mapping through its registered adapters. Reverse acquisition preserves available native parameters; data values are not queried to invent a schema.

<!-- concept:167 -->
## Pandas Dtypes Convert

Pandas adapters handle its NumPy, nullable and Arrow-backed dtype representations. Target intent, source evidence and representation limits remain distinct.

<!-- concept:168 -->
## Arrow Schema Convert

Arrow adapters retain supported parameterized types and field qualifiers. Native-to-Arrow transport is a companion of the existing dtype registry, not a second backend-selection ladder.

## Key Takeaways

- FieldDefinition carries immutable shared meaning; names and order belong to mappings or contract members.
- TableSchema owns its mapping, while deferred operations retain stable snapshots.
- Recursive composition has one authority: `fields` or `element` with optional `dimensions`, or a bare dtype.
- Native type/schema adapters own representation; the codec owns typed interchange; resource context owns I/O.
- Conform and inference share resolved output projection. Existing execution and validation remain separate owners.
- Protocol alignment, registration reachability and public behavioral fidelity require distinct evidence.
- Existing backend limitations remain explicit; a schema adapter does not imply universal execution support.
