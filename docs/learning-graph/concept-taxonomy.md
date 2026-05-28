# Concept Taxonomy

This taxonomy organizes the 200 mountainash concepts into 13 categories aligned with the package's architecture layers.

## Categories

### FOUND — Foundation Concepts

Prerequisites and external knowledge: Python type system, DataFrame libraries, SQL, design patterns (visitor, DAG, method chaining). These are concepts a developer brings to mountainash, not concepts mountainash teaches.

### CORE — Core Infrastructure

Shared infrastructure that all other modules depend on: backend/dtype/operation enums, type guards, factory base classes, lazy imports, and the constants module.

### EXAPI — Expression API

The user-facing fluent expression API: col/lit/when factory functions, namespace operations (.str, .dt, .struct, .list, .name), operator overloading, aggregation, window functions, and null handling.

### EXAST — Expression AST & System

Internal expression architecture: the 7 Pydantic-based AST node types, function key enums (FKEY_SUBSTRAIT_*, FKEY_MOUNTAINASH_*), function registry, unified visitor, and protocol contracts.

### EXBKD — Expression Backends

Backend implementations that compile expression AST to native code: PolarsExpressionSystem, NarwhalsExpressionSystem, IbisExpressionSystem, backend composition via multiple inheritance, and cross-backend testing patterns.

### RELAP — Relation API

The user-facing fluent relation API: relation() factory, Relation class with filter/sort/join/group_by/conform/unnest, GroupedRelation, terminal operations (.to_polars, .collect), and build-then-collect pattern.

### REAST — Relation AST & System

Internal relation architecture: 10 Substrait-aligned + 4 extension node types, relation protocols, UnifiedRelationVisitor, RelationVisitRegistry, OptimisationRegistry, and visitor composition with expression visitor.

### RELBK — Relation Backends

Backend implementations for relational operations: PolarsRelationSystem (LazyFrame), NarwhalsRelationSystem, IbisRelationSystem (SQL), cross-type joins, backend divergences, and execution targeting.

### TSPEC — Type System & Schema

Universal type metadata: TypeSpec/FieldSpec/FieldConstraints, UniversalType enum, Frictionless Table Schema alignment, schema extraction from DataFrames/dataclasses/Pydantic, validation, and cross-backend type conversion.

### DAGPK — DAG & DataPackage

Multi-resource orchestration: RelationDAG with two-edge graph model (dependency vs constraint edges), topological collection, ref_resolver, Frictionless DataPackage/DataResource/TableDialect, and FK integrity checking.

### PIPE — Pipeline Framework

Declarative pipeline orchestration: PipelineBuilder fluent API, step/source decorators, PipelineSpec, ParamSpec typed parameter binding, ParamsRelNode/PipelineStepRelNode AST integration, fold_params, and pipeline runners.

### RELBK — Relation Backends

(See above — covers Polars LazyFrame, Narwhals, and Ibis SQL relation compilation.)

### TSPEC — Type System & Schema

(See above — covers TypeSpec, FieldSpec, UniversalType, Frictionless, extraction, validation, conversion.)

## Taxonomy Summary Table

| TaxonomyID | Category Name | Concept Range | Count |
|------------|---------------|---------------|-------|
| FOUND | Foundation Concepts | 1–12 | 12 |
| CORE | Core Infrastructure | 13–24 | 12 |
| EXAPI | Expression API | 25–54 | 30 |
| EXAST | Expression AST & System | 55–78 | 24 |
| EXBKD | Expression Backends | 79–94 | 16 |
| RELAP | Relation API | 95–114 | 20 |
| REAST | Relation AST & System | 115–134 | 20 |
| RELBK | Relation Backends | 135–146 | 12 |
| TSPEC | Type System & Schema | 147–168 | 22 |
| DAGPK | DAG & DataPackage | 169–186 | 18 |
| PIPE | Pipeline Framework | 187–200 | 14 |
