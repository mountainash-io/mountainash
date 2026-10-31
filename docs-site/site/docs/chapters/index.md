# Chapters


## Concepts

1. [What mountainash does](01-what-mountainash-does/index.md): What mountainash is for: data logic written once with a Polars-style API and compiled to Polars, Narwhals-reached libraries and Ibis SQL engines.

## Using the package

2. [Installation and the package surface](02-installation-and-package-surface/index.md): Installing mountainash and its extras, the top-level namespace, backend detection, and the errors you can catch.
3. [Data types](03-dtypes/index.md): The canonical data types, how to write them as strings, which casts are safe, and how they map to each backend.
4. [Building expressions](04-building-expressions/index.md): Writing expressions with col, lit and when, using operators and casts, and compiling an expression for a dataframe.
5. [Namespaces, aggregates and windows](05-namespaces-aggregates-and-windows/index.md): String, date, name, struct, list, categorical and geometry namespaces, membership tests, aggregates and window expressions.
6. [Ternary logic and unknown values](06-ternary-logic/index.md): Working with TRUE, FALSE and UNKNOWN: ternary columns, sentinel values, and turning ternary results into booleans.
7. [Relations](07-relations/index.md): Creating relations from dataframes, Python data and Arrow, then filtering, joining, grouping, reshaping and combining them.
8. [Collecting results](08-collecting-results/index.md): Running a relation and getting results back as dataframes, Python objects or single values, and inspecting a plan.
9. [Execution targets and backend capabilities](09-execution-targets-and-capabilities/index.md): Choosing where a relation runs, how data moves between backends, and what to do when a backend cannot run an operation.
10. [Table schemas and DataPackage](10-table-schemas-and-datapackage/index.md): Declaring table schemas, reading and writing Frictionless descriptors and DataPackages, and extracting or converting schemas.
11. [Conforming data to a schema](11-conforming-data/index.md): Making a relation match a table schema, choosing how strict to be, and reporting how the data drifted.
12. [Data contracts](12-data-contracts/index.md): Declaring data contracts with fields and rules, and running them with a Validator.
13. [Validation](13-validation/index.md): The validation engine: check kinds, running checks, reading results and failure cases, and foreign-key checks.
14. [RelationDAG](14-relationdag/index.md): Building a graph of named relations, collecting it, and round-tripping it through a DataPackage.
15. [Pipelines](15-pipelines/index.md): Composing units into pipelines and running them with checkpoints, resume and retry.
16. [Backend support and known limits](16-backend-support-and-limits/index.md): Which operations each backend and SQL dialect supports, and the known differences between them.

## Internals

17. [Architecture](17-architecture/index.md): How mountainash separates protocols, API builders and backends, and why.
18. [How expressions compile](18-expression-compilation/index.md): How an expression becomes a backend-native expression: function keys, the registry, AST nodes and the visitor.
19. [How relations compile](19-relation-compilation/index.md): How a relation plan compiles: relation nodes, operation keys, relation systems and the relation visitor.
20. [The capability spine](20-capability-spine/index.md): How backend capabilities are declared, loaded and enforced when a plan is built and run.
21. [Backends](21-backends/index.md): How the Polars, Narwhals and Ibis backends are assembled, and where each one differs.
22. [Extending mountainash](22-extending-mountainash/index.md): Adding operations, relation nodes, capability declarations, type adapters, ingress handlers, pipeline units and rules.
23. [Contributing and testing](23-contributing-and-testing/index.md): Naming and import conventions, error conventions, and how cross-backend tests and known divergences work.
