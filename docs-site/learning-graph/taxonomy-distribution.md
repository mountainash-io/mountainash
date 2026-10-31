# Taxonomy Distribution Report

## Overview

- **Total Concepts**: 213
- **Number of Taxonomies**: 16
- **Average Concepts per Taxonomy**: 13.3

## Distribution Summary

| Category | TaxonomyID | Count | Percentage | Status |
|----------|-----------|-------|------------|--------|
| Relation API | REL | 23 | 10.8% | ✅ |
| Types, Schemas and DataPackage | TYPE | 21 | 9.9% | ✅ |
| RelationDAG and Pipelines | ORCH | 21 | 9.9% | ✅ |
| Data Contracts and Validation | QUAL | 18 | 8.5% | ✅ |
| Architecture: Protocols, Registries and Visitors | ARCH | 18 | 8.5% | ✅ |
| Capabilities and Backend Support | CAP | 16 | 7.5% | ✅ |
| Expression API | EXPR | 15 | 7.0% | ✅ |
| Extending and Maintaining | EXT | 15 | 7.0% | ✅ |
| Expression Operations and Namespaces | XOPS | 13 | 6.1% | ✅ |
| Foundations and Ecosystem | FOUND | 9 | 4.2% | ✅ |
| Ternary Logic and Booleanization | TERN | 8 | 3.8% | ✅ |
| Schema Conformance | CONF | 8 | 3.8% | ✅ |
| Backends | BACK | 8 | 3.8% | ✅ |
| Package Surface and Install | SURF | 7 | 3.3% | ✅ |
| Execution Targets and Materialization | EXEC | 7 | 3.3% | ✅ |
| Python Data Ingress and Egress | PYD | 6 | 2.8% | ℹ️ Under |

## Visual Distribution

```
Relation API              █████  23 ( 10.8%)
Types, Schemas and DataPa ████  21 (  9.9%)
RelationDAG and Pipelines ████  21 (  9.9%)
Data Contracts and Valida ████  18 (  8.5%)
Architecture: Protocols,  ████  18 (  8.5%)
Capabilities and Backend  ███  16 (  7.5%)
Expression API            ███  15 (  7.0%)
Extending and Maintaining ███  15 (  7.0%)
Expression Operations and ███  13 (  6.1%)
Foundations and Ecosystem ██   9 (  4.2%)
Ternary Logic and Boolean █   8 (  3.8%)
Schema Conformance        █   8 (  3.8%)
Backends                  █   8 (  3.8%)
Package Surface and Insta █   7 (  3.3%)
Execution Targets and Mat █   7 (  3.3%)
Python Data Ingress and E █   6 (  2.8%)
```

## Balance Analysis

### ✅ No Over-Represented Categories

All categories are under the 30% threshold. Good balance!

### ℹ️ Under-Represented Categories (<3%)

- **Python Data Ingress and Egress** (PYD): 6 concepts (2.8%)
  - *Note*: Small categories are acceptable for specialized topics

## Category Details

### Relation API (REL)

**Count**: 23 concepts (10.8%)

**Concepts**:

- 360. Relation Objects
- 361. relation Factory
- 362. Filter
- 363. Select and with_columns
- 364. Sort Head and Tail
- 365. Joins
- 366. Cross-Type Joins
- 367. As-Of Joins
- 368. Group By and Aggregate
- 369. Unique and Drop Nulls
- 370. Pivot and Unpivot
- 371. Explode Unnest and Row Index
- 372. Sample and Top-K
- 373. concat
- 374. from_arrow
- *...and 8 more*

### Types, Schemas and DataPackage (TYPE)

**Count**: 21 concepts (9.9%)

**Concepts**:

- 395. Canonical Dtypes
- 396. Parameterized Dtypes
- 397. Dtype Parsing
- 398. Cast Safety
- 399. Native Type Targets
- 400. TableSchema
- 401. FieldDefinition and FieldConstraints
- 402. table_schema Shortcut
- 403. Frictionless Table Schema
- 404. Universal Types Boundary
- 405. DataPackage and DataResource
- 406. TableDialect
- 407. Descriptor Read and Write
- 408. Descriptor Reference Resolution
- 409. Schema Extraction
- *...and 6 more*

### RelationDAG and Pipelines (ORCH)

**Count**: 21 concepts (9.9%)

**Concepts**:

- 450. Graph Kernel
- 451. Dependency and Constraint Edges
- 452. RelationDAG
- 453. DAG References
- 454. DAG Collect
- 455. DAG Materialization Session
- 456. DataPackage to DAG
- 457. DAG Validation
- 458. Cross-Family DAG Collection
- 459. ResourceRef
- 460. Resource Reads
- 465. Pipelines
- 466. Units
- 467. Source and Sink Units
- 468. DAG and Python Units
- *...and 6 more*

### Data Contracts and Validation (QUAL)

**Count**: 18 concepts (8.5%)

**Concepts**:

- 430. Data Contracts
- 431. BaseDataContract
- 432. datacontract Factory
- 433. Rules and RuleRegistry
- 434. Guarded Rules
- 435. Validator
- 436. ValidationPlan
- 437. Validation Check IR
- 438. Value Row Scalar and Relation Rules
- 439. ValidationRunner
- 440. ValidationResult and CheckSummary
- 441. Row Identity
- 442. Failure Cases
- 443. Severities
- 444. Foreign Key Validation
- *...and 3 more*

### Architecture: Protocols, Registries and Visitors (ARCH)

**Count**: 18 concepts (8.5%)

**Concepts**:

- 490. Three-Layer Separation
- 491. Protocols as Contracts
- 492. API Builders
- 493. Expression Systems
- 494. Function Keys
- 495. Substrait vs Mountainash Extensions
- 496. Function Registry
- 497. Expression AST Nodes
- 498. Arguments vs Options
- 499. Unified Expression Visitor
- 500. Operand Type Resolution
- 501. Gate Then Lower
- 502. Relation AST Nodes
- 503. Relation Operation Keys and Registry
- 504. Relation Systems
- *...and 3 more*

### Capabilities and Backend Support (CAP)

**Count**: 16 concepts (7.5%)

**Concepts**:

- 509. Backend Capabilities
- 510. Capability Spine
- 511. Capability Information vs Policy
- 512. Capability Segments and Scopes
- 513. Families and Dialects
- 514. Backend Identity
- 515. Capability Bootstrap
- 516. CapabilityRegistry
- 517. Bound Calls
- 518. Capability Gates
- 519. Capability Errors
- 520. capability_policy
- 521. Value Classes and Predicates
- 522. Capability Preflight
- 523. Backend Support Matrix
- *...and 1 more*

### Expression API (EXPR)

**Count**: 15 concepts (7.0%)

**Concepts**:

- 320. Expression Builder Objects
- 321. col
- 322. lit
- 323. when-then-otherwise
- 324. Operator Overloading
- 325. Expression Compile
- 326. native Passthrough
- 327. coalesce greatest and least
- 328. Horizontal Functions
- 329. Aggregate Expressions
- 330. Window Expressions with over
- 331. Expression Output Names
- 332. AST Introspection
- 333. Membership with is_in
- 334. today and now

### Extending and Maintaining (EXT)

**Count**: 15 concepts (7.0%)

**Concepts**:

- 540. Adding an Expression Operation
- 541. Adding a Relation Operation
- 542. Custom Relation Nodes and Visit Handlers
- 543. Declaring Capability Segments
- 544. Native Type Adapters
- 545. Schema Adapters and Codecs
- 546. Custom Ingress Handlers
- 547. Custom Units Sinks and Checkpoints
- 548. Custom Rules and Value Validators
- 549. Naming Conventions
- 550. Import Conventions
- 551. Cross-Backend Testing
- 552. Per-Backend xfail for Known Divergences
- 553. Protocol Alignment Tests
- 554. Typed Error Conventions

### Expression Operations and Namespaces (XOPS)

**Count**: 13 concepts (6.1%)

**Concepts**:

- 335. Expression Namespaces
- 336. String Namespace
- 337. Datetime Namespace
- 338. Name Namespace
- 339. Struct Namespace
- 340. List Namespace and element
- 341. Categorical Namespace
- 342. Geospatial Namespace
- 343. Arithmetic and Comparison Operations
- 344. Boolean Operations
- 345. Casting
- 346. Null Handling Operations
- 347. Rounding and Logarithmic Operations

### Foundations and Ecosystem (FOUND)

**Count**: 9 concepts (4.2%)

**Concepts**:

- 301. Dataframe Libraries and Engines
- 302. Lazy Evaluation
- 303. Backend-Agnostic Data Logic
- 304. Abstract Syntax Trees
- 305. Build Then Compile
- 306. Substrait Alignment
- 307. Polars-Style Public API
- 308. Mountainash Ecosystem Dependencies
- 309. Three-Valued Logic

### Ternary Logic and Booleanization (TERN)

**Count**: 8 concepts (3.8%)

**Concepts**:

- 350. Ternary Columns with t_col
- 351. Sentinel Unknown Values
- 352. Ternary Comparisons
- 353. Ternary Logical Operators
- 354. Booleanization
- 355. Booleanizer Choices
- 356. Boolean-Ternary Coercion
- 357. always_true always_false always_unknown

### Schema Conformance (CONF)

**Count**: 8 concepts (3.8%)

**Concepts**:

- 420. Relation conform
- 421. ConformContract Dimensions
- 422. fields_match Presets
- 423. Conform Transform Stages
- 424. Conform Errors
- 425. Drift Reporting
- 426. collect_with_drift
- 427. Structured Field Transport

### Backends (BACK)

**Count**: 8 concepts (3.8%)

**Concepts**:

- 530. Backend Composition by Mixins
- 531. Backend Registration
- 532. Polars Backend
- 533. Narwhals Backend
- 534. Ibis Backend
- 535. Narwhals Providers
- 536. Ibis SQL Dialects
- 537. Arrow Import and Export

### Package Surface and Install (SURF)

**Count**: 7 concepts (3.3%)

**Concepts**:

- 310. Installation and Extras
- 311. Top-Level Namespace
- 312. Lazy Top-Level Imports
- 313. Backend Detection
- 314. MountainashError Hierarchy
- 315. Exceptions Facade
- 316. Value Classification

### Execution Targets and Materialization (EXEC)

**Count**: 7 concepts (3.3%)

**Concepts**:

- 385. Execution Targets
- 386. Execution Locations
- 387. Operand Transfer
- 388. Materialization Scopes and Checkpoints
- 389. Owned Copies
- 390. Compilation Reuse
- 391. Schema Inference and Resolution

### Python Data Ingress and Egress (PYD)

**Count**: 6 concepts (2.8%)

**Concepts**:

- 480. Python Data Ingress
- 481. Supported Python Input Formats
- 482. Source Schema vs Target Schema
- 483. Python Data Egress
- 484. Dataclass and Pydantic Egress
- 485. Named Tuple and Indexed Egress

## Recommendations

- ✅ **Excellent balance**: Categories are evenly distributed (spread: 8.0%)
- ✅ **MISC category minimal**: Good categorization specificity

### Educational Use Recommendations

- Use taxonomy categories for color-coding in graph visualizations
- Design curriculum modules based on taxonomy groupings
- Create filtered views for focused learning paths
- Use categories for assessment organization
- Enable navigation by topic area in interactive tools

---

*Report generated by ibook graph taxonomy-report*
