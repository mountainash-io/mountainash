# Chapter plan: mountainash

Status: approved on 2026-10-30 by the user: the 23-chapter, three-part plan as written. This includes the generated support-matrix page (chapter 16), the FAQ, the glossary, API reference and Mermaid visuals. No MicroSims: the ternary truth-table candidate is declined. Chapters 12 and 13 stay separate.

Post-approval editorial change (2026-10-30): every graph node received a `chapter` field set to its primary chapter slug from this plan. This is a deliberate mapping on a new graph, not mechanical reconciliation.
Implements: `docs-site/editorial-brief.md` (confirmed 2026-10-30).
Source: `0a625ad` (develop). Profile: `docs-site/profile` (src `1d32ab4a`, unchanged in `src/`). Graph: `docs-site/learning-graph/learning-graph.json` (213 concepts, IDs 301–554, validated). Book-wide `cis_max` = 1373 (Dataframe Libraries and Engines).

Replacement book with a fresh structure. Nothing is reused from the old 15-chapter book (brief: no reuse).

## Shape

Three parts follow the depth progression concepts → use → internals:
- **Concepts** (chapter 1) gives the shared vocabulary: backend-agnostic logic, build-then-compile, the AST and Substrait, and three-valued logic.
- **Using the package** (chapters 2–16) is the user path, ending with the generated support-matrix reference page that the brief requires. Chapters on mechanisms with user-visible consequences (execution targets, capabilities, conform, validation) carry short "how it works" sections that link forward to Part III rather than repeating it.
- **Internals** (chapters 17–23) is for maintainers, contributors, backend architects and extension authors.

Every chapter states its assumed starting point and links to the primary explanation of each prerequisite instead of repeating it.

Graph corrections made while planning: concept 513 (Families and Dialects) now depends only on 514 (Backend Identity), and concept 512 (Capability Segments and Scopes) depends on 513. Dialects are a user-level identity concept that declarations are scoped to, not the reverse. The graph was revalidated.

## Audience coverage

- **users:** chapters 1–16 are the core path. Error handling is chapter 2. Capability errors and `capability_policy` are chapter 9. The support matrix is chapter 16.
- **maintainers:** invariants and failure modes appear in the internals sections of chapters 9, 11 and 13, plus chapters 17–20 and 23. Shared infrastructure (backend detection, lazy imports, errors) is chapter 2; the graph kernel is chapter 14.
- **contributors:** chapters 17–19 show where code lives. Chapter 22 has the six-step operation walkthrough and chapter 23 the conventions and testing. Naming prefixes are explained once, in chapter 23, and linked from 17.
- **backend-architecture:** chapters 9, 16 and 17–21 cover protocols, dispatch, backend composition, capability declarations per dialect, and execution and transfer.
- **extension-authors:** chapter 22 indexes every extension surface and links to the chapter that explains each mechanism. Those chapters are 3 (dtype adapters), 10 (schema adapters, custom types), 12 (rules), 15 (units, sinks, checkpoints), 19 (visit handlers) and 20 (capability segments).
- **executives-marketing and broader-hype:** no chapter, per the brief. These facets feed the home and About pages only, drawing on chapters 1, 4, 7, 10, 11 and 16. Every claim is backed by a runnable example or test.
- **Ecosystem context:** one section in chapter 2 ("Where mountainash sits"), linked from chapter 10 (remote resources via transport) and chapter 21 (Ibis extra).

## Chapters

### Part I — Concepts

#### 01-what-mountainash-does — What mountainash does

- **Audiences:** all
- **Why a chapter:** Shared vocabulary every later page uses: backend-agnostic logic, build-then-compile, the AST and Substrait alignment, three-valued logic.
- **Prerequisite chapters:** none
- **Sources:** `README.md`; `src/mountainash/__init__.py`; `principles: substrait-first-design, build-then-compile, polars-api-substrait-ast`
- **Visual:** Mermaid: build -> compile -> collect across Polars / Narwhals / Ibis.
- **Sections:**
  - One logic, many engines: 301 Dataframe Libraries and Engines, 303 Backend-Agnostic Data Logic, 307 Polars-Style Public API
  - Lazy plans and the AST: 302 Lazy Evaluation, 304 Abstract Syntax Trees, 305 Build Then Compile, 306 Substrait Alignment
  - Three-valued logic: 309 Three-Valued Logic

### Part II — Using the package

#### 02-installation-and-package-surface — Installation and the package surface

- **Audiences:** users, maintainers, contributors
- **Why a chapter:** Install, extras and the top-level namespace are prerequisites for every usage page; includes the brief's ecosystem-context section.
- **Prerequisite chapters:** 01-what-mountainash-does
- **Sources:** `pyproject.toml`; `src/mountainash/__init__.py`; `src/mountainash/exceptions.py`; `src/mountainash/core/backend_detection.py`; `src/mountainash/core/value_classification.py`
- **Visual:** Mermaid: dependency map (mountainash -> transport; extras -> files, data, dbos).
- **Sections:**
  - Where mountainash sits: 308 Mountainash Ecosystem Dependencies
  - Base install and extras: 310 Installation and Extras
  - The top-level namespace: 311 Top-Level Namespace, 312 Lazy Top-Level Imports
  - Backend detection: 313 Backend Detection
  - Errors: 314 MountainashError Hierarchy, 315 Exceptions Facade
  - Value classification: 316 Value Classification

#### 03-dtypes — Data types

- **Audiences:** users, backend-architecture, extension-authors
- **Why a chapter:** The canonical dtype system is a prerequisite for schemas, casting and conformance.
- **Prerequisite chapters:** 01-what-mountainash-does, 02-installation-and-package-surface
- **Sources:** `src/mountainash/core/dtypes/`
- **Visual:** Table: canonical dtypes vs native types per target.
- **Sections:**
  - Canonical dtypes: 395 Canonical Dtypes, 396 Parameterized Dtypes
  - Parsing dtypes: 397 Dtype Parsing
  - Native type targets: 399 Native Type Targets

#### 04-building-expressions — Building expressions

- **Audiences:** users, contributors
- **Why a chapter:** The expression API is the entry point for all data logic (highest-CIS user concepts).
- **Prerequisite chapters:** 01-what-mountainash-does, 02-installation-and-package-surface, 03-dtypes
- **Sources:** `src/mountainash/expressions/core/expression_api/`; `src/mountainash/expressions/__init__.py`; `src/mountainash/expressions/introspect.py`
- **Sections:**
  - Expression objects: 320 Expression Builder Objects
  - Columns, literals and conditions: 321 col, 322 lit, 323 when-then-otherwise, 334 today and now
  - Operators: 324 Operator Overloading, 343 Arithmetic and Comparison Operations, 344 Boolean Operations, 347 Rounding and Logarithmic Operations
  - Casting, cast safety and nulls: 345 Casting, 398 Cast Safety, 346 Null Handling Operations
  - Combining columns: 327 coalesce greatest and least
  - Escaping to native expressions: 326 native Passthrough
  - Compiling an expression: 325 Expression Compile
  - Output names: 331 Expression Output Names
  - Inspecting an expression: 332 AST Introspection

#### 05-namespaces-aggregates-and-windows — Namespaces, aggregates and windows

- **Audiences:** users
- **Why a chapter:** Domain namespaces and aggregate/window semantics are a separate layer of the API with their own rules.
- **Prerequisite chapters:** 04-building-expressions
- **Sources:** `src/mountainash/expressions/core/expression_api/`; `src/mountainash/expressions/membership/`
- **Sections:**
  - Namespaces: 335 Expression Namespaces
  - Strings and dates: 336 String Namespace, 337 Datetime Namespace
  - Names, structs and lists: 338 Name Namespace, 339 Struct Namespace, 340 List Namespace and element
  - Categoricals and geometry: 341 Categorical Namespace, 342 Geospatial Namespace
  - Membership: 333 Membership with is_in
  - Horizontal functions: 328 Horizontal Functions
  - Aggregates: 329 Aggregate Expressions
  - Windows with over: 330 Window Expressions with over

#### 06-ternary-logic — Ternary logic and unknown values

- **Audiences:** users, maintainers
- **Why a chapter:** Ternary semantics differ from null propagation and feed both expressions and validation; worth one focused chapter.
- **Prerequisite chapters:** 01-what-mountainash-does, 04-building-expressions
- **Sources:** `src/mountainash/expressions/core/expression_api/`; `principles: three-valued-semantics, booleanization, sentinel-values, bidirectional-coercion`
- **Visual:** Mermaid or table: TRUE/UNKNOWN/FALSE truth tables. Optional MicroSim candidate (decided below).
- **Sections:**
  - Ternary columns and sentinels: 350 Ternary Columns with t_col, 351 Sentinel Unknown Values, 357 always_true always_false always_unknown
  - Ternary comparisons and logic: 352 Ternary Comparisons, 353 Ternary Logical Operators
  - Booleanization: 354 Booleanization, 355 Booleanizer Choices, 356 Boolean-Ternary Coercion

#### 07-relations — Relations

- **Audiences:** users
- **Why a chapter:** The relation API is the second user entry point; Python data sources live here because they create relations.
- **Prerequisite chapters:** 01-what-mountainash-does, 02-installation-and-package-surface, 04-building-expressions, 05-namespaces-aggregates-and-windows
- **Sources:** `src/mountainash/relations/__init__.py`; `src/mountainash/relations/core/relation_api/`; `src/mountainash/pydata/ingress/`
- **Visual:** Mermaid: chained relation plan tree.
- **Sections:**
  - Relation objects: 360 Relation Objects, 361 relation Factory
  - Relations from Python data: 480 Python Data Ingress, 481 Supported Python Input Formats
  - Relations from Arrow: 374 from_arrow
  - Filtering, selecting and sorting: 362 Filter, 363 Select and with_columns, 364 Sort Head and Tail
  - Joins: 365 Joins, 366 Cross-Type Joins, 367 As-Of Joins
  - Grouping and reshaping: 368 Group By and Aggregate, 370 Pivot and Unpivot
  - Row operations: 369 Unique and Drop Nulls, 371 Explode Unnest and Row Index, 372 Sample and Top-K
  - Combining relations: 373 concat
  - Schema and columns: 375 Relation Schema and Columns

#### 08-collecting-results — Collecting results

- **Audiences:** users
- **Why a chapter:** Terminals are where compilation happens and where every egress format is chosen.
- **Prerequisite chapters:** 01-what-mountainash-does, 05-namespaces-aggregates-and-windows, 07-relations
- **Sources:** `src/mountainash/relations/core/relation_api/`; `src/mountainash/pydata/egress/`
- **Sections:**
  - Collect and terminals: 376 Collect and Terminals, 382 Logical Terminal Requirement
  - Egress formats: 377 Egress Formats, 483 Python Data Egress, 484 Dataclass and Pydantic Egress, 485 Named Tuple and Indexed Egress
  - Scalar terminals: 378 Scalar Terminals
  - Explain, fingerprint and snapshots: 379 explain, 380 Fingerprint, 381 Snapshots

#### 09-execution-targets-and-capabilities — Execution targets and backend capabilities

- **Audiences:** users, backend-architecture
- **Why a chapter:** Choosing where a plan runs and understanding capability errors are user decisions with shared internals.
- **Prerequisite chapters:** 02-installation-and-package-surface, 07-relations, 08-collecting-results
- **Sources:** `src/mountainash/relations/core/execution/`; `src/mountainash/relations/core/materialization.py`; `src/mountainash/core/capabilities/policy.py`; `src/mountainash/relations/schema_resolution.py`
- **Visual:** Mermaid: execution locations and operand transfer.
- **Sections:**
  - Execution targets and locations: 385 Execution Targets, 386 Execution Locations
  - Materialization scopes and checkpoints: 388 Materialization Scopes and Checkpoints
  - Operand transfer and owned copies: 387 Operand Transfer, 389 Owned Copies
  - Compilation reuse: 390 Compilation Reuse
  - Schema inference and resolution: 391 Schema Inference and Resolution
  - Backend capabilities, families and dialects: 509 Backend Capabilities, 514 Backend Identity, 513 Families and Dialects
  - Capability errors and capability_policy: 519 Capability Errors, 520 capability_policy

#### 10-table-schemas-and-datapackage — Table schemas and DataPackage

- **Audiences:** users, maintainers, extension-authors
- **Why a chapter:** Schemas and Frictionless descriptors are the contract layer used by conform, validation and the DAG.
- **Prerequisite chapters:** 02-installation-and-package-surface, 03-dtypes, 07-relations
- **Sources:** `src/mountainash/typespec/`; `principles: typespec-metadata-standard, frictionless-structural-fidelity, lossless-frictionless-storage`
- **Sections:**
  - TableSchema and fields: 400 TableSchema, 401 FieldDefinition and FieldConstraints, 402 table_schema Shortcut
  - Missing values and temporals: 413 Missing Values and Labeled Values, 415 Temporal Parsing
  - Frictionless descriptors: 403 Frictionless Table Schema, 404 Universal Types Boundary
  - DataPackage, resources and dialects: 405 DataPackage and DataResource, 406 TableDialect, 407 Descriptor Read and Write, 408 Descriptor Reference Resolution
  - Foreign keys: 414 Foreign Keys in Schemas
  - Extracting and converting schemas: 409 Schema Extraction, 410 Native Schema Conversion, 411 Schema Comparison
  - Custom semantic types: 412 Custom Semantic Types
  - Typed Python data ingress: 482 Source Schema vs Target Schema

#### 11-conforming-data — Conforming data to a schema

- **Audiences:** users, maintainers
- **Why a chapter:** Conformance is a distinct operation with its own contract model and drift dual.
- **Prerequisite chapters:** 02-installation-and-package-surface, 05-namespaces-aggregates-and-windows, 07-relations, 08-collecting-results, 10-table-schemas-and-datapackage
- **Sources:** `src/mountainash/conform/`; `principles: build-then-conform, conform-contract`
- **Visual:** Mermaid: conform transform stages.
- **Sections:**
  - Relation conform: 420 Relation conform
  - ConformContract dimensions and presets: 421 ConformContract Dimensions, 422 fields_match Presets
  - Transform stages: 423 Conform Transform Stages, 427 Structured Field Transport
  - Conform errors: 424 Conform Errors
  - Drift reporting: 425 Drift Reporting, 426 collect_with_drift

#### 12-data-contracts — Data contracts

- **Audiences:** users, extension-authors
- **Why a chapter:** Contract declaration and rule composition are a user-facing layer over the validation engine.
- **Prerequisite chapters:** 02-installation-and-package-surface, 06-ternary-logic, 10-table-schemas-and-datapackage, 11-conforming-data
- **Sources:** `src/mountainash/datacontracts/`
- **Sections:**
  - Declaring a contract: 430 Data Contracts, 431 BaseDataContract, 432 datacontract Factory
  - Rules and guarded rules: 433 Rules and RuleRegistry, 434 Guarded Rules
  - Validator and validation plans: 435 Validator, 436 ValidationPlan

#### 13-validation — Validation

- **Audiences:** users, maintainers, backend-architecture
- **Why a chapter:** The validation engine (check IR, runner, results) is large and used directly by DAG validation.
- **Prerequisite chapters:** 06-ternary-logic, 08-collecting-results, 10-table-schemas-and-datapackage
- **Sources:** `src/mountainash/validation/`
- **Visual:** Mermaid: check IR -> runner -> result.
- **Sections:**
  - Check IR and rule kinds: 437 Validation Check IR, 438 Value Row Scalar and Relation Rules, 445 Distribution Rules, 446 JSON Schema and GeoJSON Checks
  - Running checks: 439 ValidationRunner, 443 Severities
  - Results, row identity and failure cases: 440 ValidationResult and CheckSummary, 441 Row Identity, 442 Failure Cases
  - Foreign keys: 444 Foreign Key Validation
  - Table schema semantic validation: 447 Table Schema Semantic Validation

#### 14-relationdag — RelationDAG

- **Audiences:** users, backend-architecture
- **Why a chapter:** Multi-table orchestration with a two-edge graph model and DataPackage round trip.
- **Prerequisite chapters:** 07-relations, 08-collecting-results, 09-execution-targets-and-capabilities, 10-table-schemas-and-datapackage, 13-validation
- **Sources:** `src/mountainash/graph/`; `src/mountainash/relations/dag/`; `principles: relation-dag-orchestrator, two-edge-graph-model`
- **Visual:** Mermaid: dependency vs constraint edges.
- **Sections:**
  - The graph kernel: 450 Graph Kernel, 451 Dependency and Constraint Edges
  - Building a DAG: 452 RelationDAG, 453 DAG References
  - Collecting a DAG: 454 DAG Collect, 455 DAG Materialization Session, 458 Cross-Family DAG Collection
  - Resources and DataPackage: 459 ResourceRef, 460 Resource Reads, 456 DataPackage to DAG
  - Validating a DAG: 457 DAG Validation

#### 15-pipelines — Pipelines

- **Audiences:** users, extension-authors
- **Why a chapter:** Macro-orchestration of units with checkpoints and resume; evolving API stated plainly.
- **Prerequisite chapters:** 02-installation-and-package-surface, 14-relationdag
- **Sources:** `src/mountainash/pipelines/`
- **Visual:** Mermaid: plan/execute phases.
- **Sections:**
  - Pipelines and units: 465 Pipelines, 466 Units, 467 Source and Sink Units, 468 DAG and Python Units, 473 Parameter Axes
  - Running a pipeline: 469 Runner Plan and Execute, 472 Retry and Empty Policies
  - Values, identity and checkpoints: 470 Values Identity and Coverage, 471 Pipeline Checkpoints and Resume
  - Pipeline errors: 474 Pipeline Errors

#### 16-backend-support-and-limits — Backend support and known limits

- **Audiences:** users, backend-architecture
- **Why a chapter:** Reference page required by the brief, built from the generated capability coverage report.
- **Prerequisite chapters:** 09-execution-targets-and-capabilities
- **Sources:** `src/mountainash/core/capabilities/coverage.py`; `src/mountainash/core/capabilities/render_markdown.py`
- **Visual:** Generated table.
- **Sections:**
  - Support matrix: 523 Backend Support Matrix
  - Known divergences: 524 Known Divergences

### Part III — Internals

#### 17-architecture — Architecture

- **Audiences:** maintainers, contributors, backend-architecture, extension-authors
- **Why a chapter:** Three-layer separation is the shared frame for every internals chapter.
- **Prerequisite chapters:** 01-what-mountainash-does, 04-building-expressions
- **Sources:** `principles: three-layer-separation, protocol-as-contract, wiring-matrix`; `src/mountainash/expressions/core/expression_protocols/`
- **Visual:** Mermaid: protocol -> API builder -> backend layering.
- **Sections:**
  - Three-layer separation: 490 Three-Layer Separation
  - Protocols as contracts: 491 Protocols as Contracts
  - API builders and expression systems: 492 API Builders, 493 Expression Systems

#### 18-expression-compilation — How expressions compile

- **Audiences:** maintainers, contributors, backend-architecture
- **Why a chapter:** Function keys, registry, nodes and the visitor form one dispatch path.
- **Prerequisite chapters:** 01-what-mountainash-does, 17-architecture
- **Sources:** `src/mountainash/expressions/core/expression_system/`; `src/mountainash/expressions/core/expression_nodes/`; `src/mountainash/expressions/core/unified_visitor/`
- **Visual:** Mermaid: visitor dispatch.
- **Sections:**
  - Function keys: 494 Function Keys, 495 Substrait vs Mountainash Extensions
  - The function registry: 496 Function Registry, 506 Keyed Registries
  - Expression AST nodes: 497 Expression AST Nodes, 498 Arguments vs Options
  - The unified expression visitor: 499 Unified Expression Visitor, 500 Operand Type Resolution, 501 Gate Then Lower

#### 19-relation-compilation — How relations compile

- **Audiences:** maintainers, contributors, backend-architecture
- **Why a chapter:** The relation analog of chapter 17, composing with the expression visitor.
- **Prerequisite chapters:** 01-what-mountainash-does, 17-architecture, 18-expression-compilation
- **Sources:** `src/mountainash/relations/core/relation_nodes/`; `src/mountainash/relations/core/relation_system/`; `src/mountainash/relations/core/relation_protocols/`; `src/mountainash/relations/core/unified_visitor/`
- **Sections:**
  - Relation AST nodes: 502 Relation AST Nodes
  - Relation operation keys and registry: 503 Relation Operation Keys and Registry
  - Relation systems: 504 Relation Systems
  - The unified relation visitor: 505 Unified Relation Visitor
  - Optimisation passes: 507 Optimisation Passes

#### 20-capability-spine — The capability spine

- **Audiences:** maintainers, backend-architecture, extension-authors
- **Why a chapter:** Capability declarations, bootstrap, registry and gates are a subsystem of their own.
- **Prerequisite chapters:** 02-installation-and-package-surface, 09-execution-targets-and-capabilities, 18-expression-compilation, 19-relation-compilation
- **Sources:** `src/mountainash/core/capabilities/`; `src/mountainash/expressions/backends/capabilities/`; `src/mountainash/relations/backends/capabilities/`; `principles: capability-as-call-property, explicit-enforcement-role, gate-then-lower`
- **Visual:** Mermaid: segments -> bootstrap -> registry -> gates.
- **Sections:**
  - Information and policy: 510 Capability Spine, 511 Capability Information vs Policy
  - Segments and scopes: 512 Capability Segments and Scopes
  - Bootstrap and the registry: 515 Capability Bootstrap, 516 CapabilityRegistry
  - Bound calls and value classes: 517 Bound Calls, 521 Value Classes and Predicates
  - Gates and preflight: 518 Capability Gates, 522 Capability Preflight

#### 21-backends — Backends

- **Audiences:** maintainers, backend-architecture, contributors
- **Why a chapter:** Backend composition and per-backend specifics (providers, dialects, Arrow boundary).
- **Prerequisite chapters:** 09-execution-targets-and-capabilities, 17-architecture, 18-expression-compilation, 19-relation-compilation
- **Sources:** `src/mountainash/expressions/backends/expression_systems/`; `src/mountainash/relations/backends/relation_systems/`
- **Visual:** Mermaid: backend composition by mixins.
- **Sections:**
  - Composition and registration: 530 Backend Composition by Mixins, 531 Backend Registration
  - Polars: 532 Polars Backend
  - Narwhals and its providers: 533 Narwhals Backend, 535 Narwhals Providers
  - Ibis and SQL dialects: 534 Ibis Backend, 536 Ibis SQL Dialects
  - Arrow import and export: 537 Arrow Import and Export

#### 22-extending-mountainash — Extending mountainash

- **Audiences:** contributors, extension-authors
- **Why a chapter:** Every extension surface in one place, linking back to the chapter that explains the mechanism.
- **Prerequisite chapters:** 03-dtypes, 07-relations, 10-table-schemas-and-datapackage, 12-data-contracts, 13-validation, 15-pipelines, 16-backend-support-and-limits, 17-architecture, 18-expression-compilation, 19-relation-compilation, 20-capability-spine, 21-backends
- **Sources:** `principles: adding-operations, backend-composition`; `src/mountainash/relations/core/unified_visitor/`; `src/mountainash/core/dtypes/protocols.py`
- **Sections:**
  - Adding an expression operation: 540 Adding an Expression Operation
  - Adding a relation operation: 541 Adding a Relation Operation
  - Custom relation nodes: 542 Custom Relation Nodes and Visit Handlers
  - Declaring capability segments: 543 Declaring Capability Segments
  - Type and schema adapters: 544 Native Type Adapters, 545 Schema Adapters and Codecs
  - Ingress handlers, units and rules: 546 Custom Ingress Handlers, 547 Custom Units Sinks and Checkpoints, 548 Custom Rules and Value Validators

#### 23-contributing-and-testing — Contributing and testing

- **Audiences:** contributors, maintainers
- **Why a chapter:** Conventions and the cross-backend testing discipline apply to every change.
- **Prerequisite chapters:** 02-installation-and-package-surface, 16-backend-support-and-limits, 17-architecture, 21-backends
- **Sources:** `principles: naming-conventions, import-conventions, testing-philosophy, cross-backend-test-coverage, typed-error-hierarchy`; `tests/`
- **Sections:**
  - Naming and import conventions: 549 Naming Conventions, 550 Import Conventions
  - Typed error conventions: 554 Typed Error Conventions
  - Cross-backend testing: 551 Cross-Backend Testing, 553 Protocol Alignment Tests
  - Known divergences and per-backend xfail: 552 Per-Backend xfail for Known Divergences

## Appendices and reference

- **FAQ:** included (brief). Each answer links to the primary section.
- **Glossary:** included (brief). Each term links to its primary section.
- **Backend support and known limits:** chapter 16. Generated from the capability coverage report; the generation command and source revision are stated on the page.
- **API reference:** mkdocstrings pages for public modules, linked from chapters.
- **Home and About pages:** draw on the positioning facets and are backed by tests or examples.
- **Old reader pages:** `course-description.md`, the learning-graph pages and `sims/` leave with the old book on acceptance. No graph section is published.

## Visuals

Mermaid diagrams are listed per chapter above. MicroSims: none proposed. The ternary truth tables (chapter 6) are small enough for static tables, so the brief's single candidate is declined unless you want it. No quizzes.

## Elaboration guidance (internal)

Book-wide `cis_max` = 1373. Elaborate concepts at or above 10% of `cis_max` (≥ 137) with a worked example and a diagram where listed. Lower-CIS leaf concepts (individual join kinds, egress formats, error classes) get a concise subsection and a link to the API reference.

| Concept | CIS | Chapter |
|---|---|---|
| 301 Dataframe Libraries and Engines | 1373 | 01-what-mountainash-does |
| 303 Backend-Agnostic Data Logic | 842 | 01-what-mountainash-does |
| 304 Abstract Syntax Trees | 666 | 01-what-mountainash-does |
| 302 Lazy Evaluation | 408 | 01-what-mountainash-does |
| 305 Build Then Compile | 407 | 01-what-mountainash-does |
| 308 Mountainash Ecosystem Dependencies | 256 | 02-installation-and-package-surface |
| 310 Installation and Extras | 255 | 02-installation-and-package-surface |
| 311 Top-Level Namespace | 254 | 02-installation-and-package-surface |
| 490 Three-Layer Separation | 180 | 17-architecture |
| 307 Polars-Style Public API | 178 | 01-what-mountainash-does |
| 491 Protocols as Contracts | 178 | 17-architecture |
| 306 Substrait Alignment | 172 | 01-what-mountainash-does |
| 493 Expression Systems | 139 | 17-architecture |

## Open questions

- Chapter 13 (Validation) and chapter 12 (Data contracts) could merge. They are kept separate because the validation engine is used directly by DAG validation without contracts.
- Chapter 15 (Pipelines) documents an evolving API and states `Runner.plan`/`execute` stability as the source shows it. The missing `docs/guides/pipelines.md` that the module docstring links to is a source-docstring fix outside this book.
- Python data egress has no chapter of its own. It is a section of chapter 8, because egress is reached through `Relation.to_*` terminals.
