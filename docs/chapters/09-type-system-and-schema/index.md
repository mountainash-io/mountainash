---
title: Type System and Schema
description: Universal type metadata via TypeSpec, FieldSpec, schema extraction from multiple sources, Frictionless Standard alignment, and backend-specific type conversions.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 9: Type System and Schema

## Summary

Universal type metadata via TypeSpec, FieldSpec, FieldConstraints, UniversalType enum, type bridge, backend type mapping, foreign keys, custom type registry, type converters, Frictionless Standard alignment, Table Schema, schema extraction (DataFrame, dataclass, Pydantic), schema validation, schema comparison, and backend-specific schema conversion.

## Concepts Covered

- TypeSpec
- FieldSpec
- FieldConstraints
- UniversalType Enum
- Type Bridge
- Backend Type Mapping
- Foreign Keys
- ForeignKeyReference
- Custom Type Registry
- Type Converters
- Frictionless Standard
- Table Schema
- Schema Extraction
- DataFrame Extraction
- Dataclass Extraction
- Pydantic Extraction
- Schema Validation
- Schema Comparison
- Polars Schema Convert
- Pandas Dtypes Convert
- Arrow Schema Convert

## Prerequisites

- [Chapter 1. Foundation Concepts](../01-foundations/)
- [Chapter 2. Core Infrastructure](../02-core-infrastructure/)

---

## Introduction

Data pipelines frequently need to enforce schemas, convert between type systems, and validate data against constraints. Mountainash provides a backend-agnostic type system built on the Frictionless Table Schema standard. This chapter covers the complete type system, from the `UniversalType` enum through schema extraction, validation, and backend-specific conversion.

## UniversalType Enum

The `UniversalType` enum defines the universal data types that mountainash recognizes. Based on the Frictionless Table Schema specification, these types provide a common vocabulary that maps to every supported backend's native type system.

```python
class UniversalType(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"      # Floating point
    BOOLEAN = "boolean"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    DURATION = "duration"
    YEAR = "year"
    YEARMONTH = "yearmonth"
    ARRAY = "array"
    OBJECT = "object"
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

## FieldSpec

A `FieldSpec` describes a single field (column) in a schema. It extends the Frictionless Table Schema field definition with mountainash-specific features like `rename_from` for column aliasing and `null_fill` for default null replacement.

```python
@dataclass
class FieldSpec:
    name: str
    type: UniversalType = UniversalType.STRING
    format: str = "default"
    title: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[FieldConstraints] = None
    missing_values: Optional[list[str]] = None
    null_fill: Any = None
    rename_from: Optional[str] = None
```

The `source_name` property returns `rename_from` if set, otherwise falls back to `name`. This enables the `conform` operation to map columns from source names to target names transparently.

- **name**: The desired output column name
- **type**: The universal type for this field
- **constraints**: Validation rules (required, unique, min/max, etc.)
- **missing_values**: String representations that should be treated as null
- **null_fill**: Default value to substitute for nulls
- **rename_from**: Source column name if different from target name

## FieldConstraints

`FieldConstraints` specifies validation rules for a single field. These constraints follow the Frictionless Table Schema constraint vocabulary with one mountainash extension (`enum_weights`).

```python
@dataclass
class FieldConstraints:
    required: bool = False
    unique: bool = False
    minimum: Optional[Any] = None
    maximum: Optional[Any] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[list[Any]] = None
    enum_weights: Optional[dict[str, float]] = None  # mountainash extension
```

Constraints are checked during schema validation (described later in this chapter). They can express rules like "this column must not be null" (required=True), "values must be unique" (unique=True), or "values must match this regex" (pattern).

## TypeSpec

`TypeSpec` is the top-level schema object that describes an entire table's structure. It contains a list of `FieldSpec` instances, optional primary key and foreign key declarations, and metadata about the overall schema.

```python
# Creating a TypeSpec from a simple dictionary
import mountainash as ma

spec = ma.typespec({
    "id": "integer",
    "name": "string",
    "email": "string",
    "created_at": "datetime",
})
```

TypeSpec supports construction from multiple sources: simple dictionaries, Frictionless Table Schema descriptors, DataFrame introspection, dataclass definitions, and Pydantic models. This flexibility means you can define your schema in whatever format is most natural for your project.

#### Diagram: TypeSpec Construction Sources
<iframe src="../../sims/typespec-construction/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>TypeSpec Construction Sources</summary>
Type: workflow
**sim-id:** typespec-construction<br/>
**Library:** vis-network<br/>
**Status:** Specified

A hub-and-spoke diagram with TypeSpec at the center. Five spokes connect to construction sources: Simple Dict, Frictionless JSON, Polars DataFrame, Python Dataclass, and Pydantic Model. Each source node shows a code snippet on hover. Clicking a source shows the extraction path and any information lost during conversion. Arrows point inward toward TypeSpec. Colors: MediumPurple for type system elements. Learning objective: Identify the multiple paths for constructing TypeSpec objects and understand what metadata each source provides (Bloom: Understand).
</details>

## Type Bridge

The type bridge converts between `UniversalType` (Frictionless-level types) and `MountainashDtype` (Substrait-level types). This conversion is necessary because the schema system uses Frictionless types while the expression system uses Substrait-aligned types.

For example, Frictionless `INTEGER` maps to MountainashDtype `I64` (the default integer width). Frictionless `NUMBER` maps to MountainashDtype `FP64`. The bridge handles these conversions bidirectionally.

The type bridge is also responsible for mapping between UniversalType and the `MountainashDtype` used in cast operations. When the `conform` operation needs to cast a column to match its TypeSpec, it uses the type bridge to determine the target MountainashDtype from the UniversalType in the FieldSpec.

## Backend Type Mapping

Backend type mapping translates `UniversalType` values to the concrete type objects used by each backend library. Each backend has its own type representation (Polars uses `pl.DataType` subclasses, pandas uses numpy dtypes, Arrow uses `pa.DataType`).

```python
# Universal -> Polars mapping (simplified)
{
    UniversalType.STRING: pl.Utf8,
    UniversalType.INTEGER: pl.Int64,
    UniversalType.NUMBER: pl.Float64,
    UniversalType.BOOLEAN: pl.Boolean,
    UniversalType.DATE: pl.Date,
    UniversalType.DATETIME: pl.Datetime,
}
```

These mappings are defined as lazy functions to avoid importing backend libraries until needed. Each mapping function (`_get_universal_to_polars`, `_get_universal_to_pandas`, etc.) imports its backend on first call and caches the result.

## Foreign Keys

Foreign keys define referential integrity relationships between tables. A foreign key declaration says "the values in these columns of this table must exist in the specified columns of another table."

```python
@dataclass
class ForeignKey:
    fields: list[str]         # Columns in this table
    reference: ForeignKeyReference  # Target table and columns
```

Foreign keys are stored at the TypeSpec level and used by the `RelationDAG` for constraint edges and integrity validation. They represent a different kind of dependency than data flow: they say "this table's data depends on that table's data for validity."

## ForeignKeyReference

`ForeignKeyReference` specifies the target of a foreign key relationship. It identifies the referenced table (resource) name and the field(s) within that table.

```python
@dataclass
class ForeignKeyReference:
    resource: str       # Name of the referenced table
    fields: list[str]   # Column(s) in the referenced table
```

An empty `resource` string indicates a self-referencing foreign key (the referenced table is the same table containing the key). This is used for hierarchical data where a column references another row in the same table (like a parent_id column).

## Custom Type Registry

The custom type registry enables extending the type system with domain-specific types beyond the standard UniversalType values. This is useful for types that have specialized validation or conversion logic not covered by the base Frictionless types.

The registry uses lazy evaluation so that custom type definitions are loaded only when encountered during schema processing. New types can be registered with their conversion functions for each backend.

## Type Converters

Type converters translate between the universal type system and backend-specific type representations. Each converter handles one direction of the mapping (universal-to-backend or backend-to-universal) for one backend library.

The converter system is used during schema extraction (backend-to-universal) and during schema application (universal-to-backend). Converters handle edge cases like Polars' distinction between `Datetime` with and without timezone, pandas' nullable integer types, and Arrow's parameterized types.

## Frictionless Standard

The Frictionless Data standard is an open specification for describing tabular data. Mountainash aligns with its Table Schema and Data Package specifications to enable interoperability with the broader data ecosystem.

Key Frictionless concepts that mountainash adopts include:

- **Table Schema**: JSON structure describing column names, types, and constraints
- **Data Resource**: Wrapper around a table schema with path and format metadata
- **Data Package**: Collection of data resources with package-level metadata
- **Field descriptors**: JSON objects with name, type, format, and constraints
- **Missing values**: Configurable string representations of null

This alignment means mountainash can read and write standard Frictionless descriptor files, enabling schema sharing with tools outside the mountainash ecosystem.

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

Mountainash's TypeSpec can be constructed from a Table Schema descriptor via `typespec_from_frictionless()` and exported back via `typespec_to_frictionless()`. This round-trip capability ensures no information is lost when moving between mountainash's internal representation and the standard JSON format.

## Schema Extraction

Schema extraction is the process of inferring a TypeSpec from an existing data source. Mountainash supports extraction from three source types: DataFrames, Python dataclasses, and Pydantic models.

The extraction system uses the factory pattern to dispatch to the appropriate extractor based on the source type. Each extractor inspects the source's structure and produces a TypeSpec with the appropriate UniversalType mappings.

## DataFrame Extraction

DataFrame extraction inspects a backend-specific DataFrame's schema (column names and types) and converts each column type to the corresponding UniversalType. This is the reverse of backend type mapping.

```python
import polars as pl
from mountainash.typespec.extraction import extract_from_dataframe

df = pl.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})
spec = extract_from_dataframe(df)
# spec.fields[0].type == UniversalType.INTEGER
# spec.fields[1].type == UniversalType.STRING
```

DataFrame extraction captures type information but cannot infer constraints (required, unique, min/max) because those are semantic properties not visible from the data alone.

## Dataclass Extraction

Dataclass extraction reads Python type annotations from a `@dataclass` class definition and maps them to UniversalType values. This enables defining schemas as Python code with full IDE support.

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime

# Extraction produces TypeSpec with INTEGER, STRING, STRING, DATETIME
```

Python type annotations map naturally to universal types: `int` becomes INTEGER, `str` becomes STRING, `float` becomes NUMBER, `bool` becomes BOOLEAN, and datetime types map to their temporal equivalents.

## Pydantic Extraction

Pydantic extraction reads field definitions from a Pydantic `BaseModel` subclass. In addition to type information, it can capture Pydantic validators as FieldConstraints, providing richer schema metadata than dataclass extraction.

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1)
    email: str

# Extraction captures both types and constraints
```

## Schema Validation

Schema validation checks whether a given dataset conforms to a TypeSpec. It verifies that required columns exist, types are compatible, constraints are satisfied, and foreign key references are valid.

The `validate_match` function is the primary entry point for validation. It compares a DataFrame's actual schema against a TypeSpec and returns a detailed report of matches, mismatches, and missing fields.

## Schema Comparison

Schema comparison computes the differences between two TypeSpec instances. This is useful for detecting schema drift, verifying migration correctness, and generating conformance plans.

The comparison identifies added fields, removed fields, type changes, constraint changes, and renamed fields (via `rename_from` matching). The output is a structured diff that can be used programmatically or displayed as a human-readable report.

#### Diagram: Schema Comparison Workflow
<iframe src="../../sims/schema-comparison/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Schema Comparison Workflow</summary>
Type: microsim
**sim-id:** schema-comparison<br/>
**Library:** p5.js<br/>
**Status:** Specified

An interactive two-panel comparison view. The left panel shows a "Source TypeSpec" with editable fields (name, type pairs). The right panel shows a "Target TypeSpec" with different fields. Between the panels, color-coded indicators show: green for matching fields, yellow for type changes, red for missing fields, blue for added fields. Editing a field name or type in either panel updates the comparison indicators in real time. A summary bar at the bottom counts matches/mismatches. Learning objective: Identify schema differences and predict the conformance operations needed to reconcile two TypeSpec instances (Bloom: Evaluate).
</details>

## Polars Schema Convert

Polars schema conversion translates between TypeSpec and Polars schema objects. The forward direction (TypeSpec -> Polars) produces a dictionary of column names to Polars DataType objects. The reverse direction (Polars -> TypeSpec) extracts column information from a Polars DataFrame or LazyFrame.

## Pandas Dtypes Convert

Pandas dtype conversion handles the mapping between TypeSpec and pandas dtype specifications. Pandas has a more complex type landscape (numpy dtypes, nullable integer types, string vs object dtype), so the converter handles multiple representations for the same logical type.

## Arrow Schema Convert

Arrow schema conversion translates between TypeSpec and PyArrow Schema objects. Arrow's type system is the most detailed of the three backends, supporting parameterized types (e.g., `timestamp[ns, tz=UTC]`), so the converter must handle precision and metadata that other backends abstract away.

## Key Takeaways

- `UniversalType` provides a Frictionless-aligned type vocabulary that maps to every backend's native type system through bidirectional conversion functions.
- `FieldSpec` describes individual columns with type, constraints, rename mapping, null fill values, and Frictionless-compatible metadata.
- `TypeSpec` is the top-level schema object supporting construction from dictionaries, Frictionless JSON, DataFrames, dataclasses, and Pydantic models.
- The type bridge converts between Frictionless-level types (UniversalType) and expression-level types (MountainashDtype) for schema-to-expression integration.
- Foreign keys and ForeignKeyReference define referential integrity relationships used by RelationDAG for constraint edges and validation.
- Schema extraction automatically infers TypeSpec from existing data sources, with the depth of metadata depending on the source type.
- Schema validation and comparison provide runtime checking and drift detection between expected and actual data structures.
- Backend-specific converters (Polars, pandas, Arrow) handle the edge cases and type system differences unique to each library.
