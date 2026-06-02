# Concept Graph for Mountainash

This section contains the concept dependency graph for the mountainash package. The graph maps 200 concepts across the library's architecture — from foundation prerequisites through expression and relation systems to pipeline orchestration — as a directed acyclic graph (DAG) where edges represent learning dependencies.

A concept graph serves as a navigable roadmap of the package's knowledge space, useful for onboarding contributors, planning documentation, and understanding architectural dependencies.

At the left of the graph are foundational concepts (Python type hints, DataFrames, SQL databases, etc.) with no prerequisites. At the far right are the most advanced concepts (pipeline fold_params, cross-type joins, FK integrity checks) that require understanding many upstream concepts.

## Source Data

The concept graph was generated from the [mountainash package profile](../../.hiivmind/package-profile/), which contains 25 module profiles and 7 audience facets covering the full package architecture.

## Graph Files

- **[learning-graph.json](./learning-graph.json)** — Complete graph in vis-network.js JSON format (200 nodes, 350 edges, 11 taxonomy groups)
- **[learning-graph.csv](./learning-graph.csv)** — Raw dependency data with taxonomy assignments

## Concept List

The [Concept List](./concept-list.md) enumerates all 200 concepts with short Title Case labels, organized by taxonomy category.

## Analysis & Documentation

### Package Description

The [Package Description](./course-description.md) serves as the source document for concept generation, adapted from the package profile's module and facet data.

### Quality Metrics

The [Quality Metrics Report](./quality-metrics.md) validates the graph structure:

- Valid DAG structure (no cycles)
- 7 foundational entry points, 84 terminal endpoints
- 0 orphaned nodes — all concepts connected
- Maximum dependency chain length: 15
- Average 1.81 dependencies per concept

### Concept Taxonomy

The [Concept Taxonomy](./concept-taxonomy.md) defines 11 categories aligned with mountainash's architecture layers:

| TaxonomyID | Category | Count |
|------------|----------|-------|
| FOUND | Foundation Concepts | 12 |
| CORE | Core Infrastructure | 12 |
| EXAPI | Expression API | 30 |
| EXAST | Expression AST & System | 24 |
| EXBKD | Expression Backends | 16 |
| RELAP | Relation API | 20 |
| REAST | Relation AST & System | 20 |
| RELBK | Relation Backends | 12 |
| TSPEC | Type System & Schema | 22 |
| DAGPK | DAG & DataPackage | 18 |
| PIPE | Pipeline Framework | 14 |

### Taxonomy Distribution

The [Taxonomy Distribution Report](./taxonomy-distribution.md) shows how concepts are distributed across categories, with balance analysis and visual breakdown.
