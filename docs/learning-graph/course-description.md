---
title: Mountainash Package Description
description: A detailed description of the mountainash cross-backend data expression and relational pipeline library
quality_score: 90
---

# Mountainash Package Description

## Title

Mountainash: Cross-Backend Data Expression and Relational Pipeline Library

## Target Audience

Python developers building data pipelines, analytics workflows, and data quality systems who need backend-portable expressions and relational operations across Polars, pandas (via Narwhals), and SQL databases (via Ibis).

## Prerequisites

- Intermediate Python programming (classes, decorators, type hints, protocols)
- Familiarity with at least one DataFrame library (Polars, pandas, or similar)
- Basic understanding of SQL concepts (SELECT, JOIN, GROUP BY, WHERE)
- Understanding of directed acyclic graphs (DAGs) and topological ordering

## Topics Covered

1. **Core Infrastructure** — Backend detection, type guards, enums, factory patterns, lazy imports
2. **Expression System** — Fluent expression API, AST nodes, function key registry, visitor pattern compilation
3. **Expression Backends** — Polars, Narwhals, and Ibis expression compilation with cross-backend consistency
4. **Relation System** — Relational AST with Substrait-aligned node types, fluent relation builder, unified visitor
5. **Relation Backends** — Polars LazyFrame, Narwhals, and Ibis SQL relation compilation
6. **Type System (TypeSpec)** — Universal type metadata, Frictionless Table Schema alignment, schema extraction and validation
7. **Data Conformance** — TypeSpec-driven column transformation via Relation.conform()
8. **Ternary Logic** — Three-valued semantics (TRUE/FALSE/UNKNOWN) with sentinel integers and auto-booleanization
9. **DAG & DataPackage** — RelationDAG orchestrator, Frictionless DataPackage integration, two-edge graph model
10. **Pipeline Framework** — Declarative multi-step pipelines with typed parameter binding and caching

## Topics Excluded

- Low-level Polars/Ibis/Narwhals internals (upstream library implementation details)
- Database administration or SQL optimization
- Machine learning model training or serving
- Web framework integration
- Deployment and infrastructure concerns

## Learning Outcomes

After studying this package, developers will be able to:

### Remember

- List the seven expression AST node types and their Substrait alignment
- Identify the ten relational node types and their roles
- Name the three supported backends (Polars, Narwhals, Ibis)
- Recall the function key enum naming convention (FKEY_SUBSTRAIT_*, FKEY_MOUNTAINASH_*)
- List the three-layer architecture: Protocol → API Builder → Backend

### Understand

- Explain the build-then-compile pattern for expressions and build-then-collect for relations
- Describe how the unified visitor dispatches AST nodes via the function registry
- Explain the difference between dependency edges and constraint edges in RelationDAG
- Describe how ternary logic differs from SQL NULL propagation
- Explain the protocol-as-contract principle and how backends implement obligations

### Apply

- Build fluent expression chains using col(), lit(), when(), and namespace operations
- Construct relational pipelines with filter, sort, join, group_by, and terminal operations
- Define TypeSpec schemas and use Relation.conform() for cross-backend conformance
- Create RelationDAG workflows from Frictionless DataPackage descriptors
- Write cross-backend parametrized tests with appropriate xfail markers

### Analyze

- Analyze backend detection and automatic coercion in cross-type join scenarios
- Compare expression compilation strategies across Polars, Narwhals, and Ibis backends
- Evaluate known divergences and their impact on cross-backend consistency
- Analyze the pipeline parameter binding flow from ParamSpec through fold_params

### Evaluate

- Assess whether a new operation belongs in the Substrait or Mountainash extension namespace
- Evaluate the six-step process for adding new operations across all architecture layers
- Judge appropriate use of arguments vs options for expression parameters
- Evaluate TypeSpec schema designs for Frictionless structural fidelity

### Create

- Implement new expression operations following the six-step wiring process
- Build custom pipeline steps with ParamSpec parameter declarations
- Create DataPackage-backed multi-resource DAG workflows
- Design custom type converters for the CustomTypeRegistry
- Build extension relation node types using RelationVisitRegistry

## Context

Mountainash positions itself as a backend-portable abstraction layer for data expressions and relational operations. Unlike Ibis (SQL-focused) or Narwhals (DataFrame-agnostic thin layer), mountainash provides a full Substrait-aligned AST with three-valued ternary logic, schema-first data quality via TypeSpec, and declarative pipeline orchestration — enabling "abstract data products" that run identically across Polars, pandas, and SQL backends.
