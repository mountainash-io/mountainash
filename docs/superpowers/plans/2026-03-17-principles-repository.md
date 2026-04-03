# Principles Repository Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a 22-document principles repository for mountainash-expressions at `mountainash-central/01.principles/mountainash-expresions/`

**Architecture:** Documentation-only — no code changes except a CLAUDE.md pointer. Each principle document follows a 6-section template (Principle, Rationale, Examples, Anti-Patterns, Technical Reference, Future Considerations). Content extracted from CLAUDE.md, ADRs, and source code.

**Tech Stack:** Markdown files. No build tooling.

**Spec:** `docs/superpowers/specs/2026-03-17-principles-repository-design.md`

**Base path:** `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions`

**Source project:** `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions`

---

## Chunk 1: Scaffolding and Governance

### Task 1: Create directory structure and governance docs

**Files:**
- Create: `PRINCIPLES.md`
- Create: `README.md`
- Create: 7 category directories (empty initially)

- [ ] **Step 1: Create all category directories**

```bash
BASE="/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions"
mkdir -p "$BASE/a.architecture"
mkdir -p "$BASE/b.type-system"
mkdir -p "$BASE/c.api-design"
mkdir -p "$BASE/d.ternary-logic"
mkdir -p "$BASE/e.cross-backend"
mkdir -p "$BASE/f.extension-model"
mkdir -p "$BASE/g.development-practices"
```

- [ ] **Step 2: Write PRINCIPLES.md**

Write the governance document covering:
- Why this directory exists — design decisions were scattered across ADRs (`docs/adr/`), `CLAUDE.md`, code comments, and lived experience. No single source of truth for architectural philosophy.
- How categories were chosen — map to concerns that guide decisions, not code directories. Lettered a–g by dependency (foundations first, practices last).
- Status markers table: ENFORCED, ADOPTED, PROPOSED, EXPLORATORY (definitions from spec lines 16-21)
- How to add new principles (place in category, follow template, mark status, update README.md)
- Relationship to other docs: ADRs document individual decisions with alternatives; CLAUDE.md is the operational guide; principles explain the *why*
- Conflict documentation pattern: CONFLICTS.md per category when principles tension against each other
- Category precedence rule: lower-lettered categories take precedence when conflicts arise
- The document template (6 sections)

Reference the fairgo governance doc at `/home/nathanielramm/git/fairgo/fairgo-central/02.principles/PRINCIPLES.md` for tone and structure.

- [ ] **Step 3: Write README.md**

Write the index document with:
- Link to PRINCIPLES.md at top: `> See [PRINCIPLES.md](PRINCIPLES.md) for governance.`
- One table per category (a through g) with columns: Document | Status | Summary
- Tables are the literal content from the spec's Document Inventory section (spec lines 114-171)
- All links should be relative paths to the principle documents

Reference the fairgo README at `/home/nathanielramm/git/fairgo/fairgo-central/02.principles/README.md` for format.

- [ ] **Step 4: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central
git add 01.principles/mountainash-expresions/
git commit -m "feat: scaffold principles repository structure"
```

---

## Chunk 2: Architecture Principles (a.architecture/)

### Task 2: Write a.architecture/substrait-first-design.md

**Files:**
- Create: `a.architecture/substrait-first-design.md`

**Content sources:**
- `CLAUDE.md` "Current Architecture Status" section
- `docs/adr/ADR-008-substrait-extension-alignment.md`
- `src/mountainash_expressions/core/expression_system/function_keys/enums.py` (SubstraitExtension URIs, FKEY_SUBSTRAIT_* vs FKEY_MOUNTAINASH_* naming)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Operations align with the Substrait specification where possible. Custom operations live in a physically separate extension namespace (`extensions_mountainash/`). The Substrait spec is the default — deviations require justification.

Key content to cover:
- Substrait as open standard for data compute operations
- 13 Substrait categories implemented (comparison, boolean, arithmetic, string, datetime, etc.)
- Physical directory separation: `substrait/` vs `extensions_mountainash/` at every layer
- ENUM naming separation: `FKEY_SUBSTRAIT_*` vs `FKEY_MOUNTAINASH_*`
- SubstraitExtension URIs for serialization references
- Anti-patterns: inventing custom operations when a Substrait equivalent exists; mixing extension and standard operations in the same directory
- Technical references: `src/mountainash_expressions/core/expression_system/function_keys/enums.py` (SubstraitExtension class, MountainashExtension class), directory structure at each layer
- Future: Substrait serialization (to/from protobuf), window functions

- [ ] **Step 2: Commit**

```bash
git add 01.principles/mountainash-expresions/a.architecture/substrait-first-design.md
git commit -m "docs: add substrait-first-design principle"
```

### Task 3: Write a.architecture/minimal-ast.md

**Files:**
- Create: `a.architecture/minimal-ast.md`

**Content sources:**
- `CLAUDE.md` "The Minimal AST (7 Node Types)" section
- `src/mountainash_expressions/core/expression_nodes/substrait/` (all exn_*.py files)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: The expression tree uses only 7 node types. `ScalarFunctionNode` handles ~90% of operations via a function key ENUM, rather than category-specific node types.

Key content to cover:
- The 7 node types: ExpressionNode (base), FieldReferenceNode, LiteralNode, ScalarFunctionNode, IfThenNode, CastNode, SingularOrListNode
- Why minimal: fewer node types = simpler visitor, easier serialization, less surface area for bugs
- ScalarFunctionNode as the workhorse — function_key ENUM + arguments list + options dict
- Anti-patterns: creating new node types for new operations (use ScalarFunctionNode instead); putting business logic in nodes (nodes are data, visitor has logic)
- Technical references: each `exn_*.py` file path
- Example: `col("age").gt(30)` creates `ScalarFunctionNode(function_key=FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT, arguments=[FieldReferenceNode("age"), LiteralNode(30)])`

- [ ] **Step 2: Commit**

```bash
git add 01.principles/mountainash-expresions/a.architecture/minimal-ast.md
git commit -m "docs: add minimal-ast principle"
```

### Task 4: Write a.architecture/three-layer-separation.md

**Files:**
- Create: `a.architecture/three-layer-separation.md`

**Content sources:**
- `CLAUDE.md` "Core Architecture: Substrait-Aligned Design" and "The Architecture Flow" sections
- `src/mountainash_expressions/core/expression_protocols/` (protocol layer)
- `src/mountainash_expressions/core/expression_api/api_builders/` (API builder layer)
- `src/mountainash_expressions/backends/expression_systems/` (backend layer)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: The architecture has three layers — Protocol, API Builder, Backend — each with a single responsibility. Protocols define contracts. API Builders construct AST nodes. Backends compile nodes to native expressions.

Key content to cover:
- Layer 1: Protocols (`expression_protocols/`) — typing.Protocol classes defining method signatures. Source of truth for what backends must implement.
- Layer 2: API Builders (`expression_api/api_builders/`) — construct ScalarFunctionNode trees. No backend awareness.
- Layer 3: Backends (`backends/expression_systems/`) — implement protocol methods with backend-native code (Polars, Ibis, Narwhals).
- The flow: User → API Builder → AST Node → Visitor → Backend Method → Native Expression
- Anti-patterns: putting backend logic in API builders; having protocols import backend types; skipping the AST and going straight to backend expressions
- Each layer mirrors the same directory structure (substrait/ + extensions_mountainash/)

- [ ] **Step 2: Commit**

```bash
git add 01.principles/mountainash-expresions/a.architecture/three-layer-separation.md
git commit -m "docs: add three-layer-separation principle"
```

### Task 5: Write a.architecture/unified-visitor.md

**Files:**
- Create: `a.architecture/unified-visitor.md`

**Content sources:**
- `src/mountainash_expressions/core/unified_visitor/visitor.py`
- `src/mountainash_expressions/core/expression_system/function_mapping/registry.py`
- `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py`

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: A single `UnifiedExpressionVisitor` dispatches all node types by looking up the function key in a central registry, then calling the corresponding backend method by name. This replaced 12+ category-specific visitors.

Key content to cover:
- How dispatch works: node.accept(visitor) → visitor.visit_scalar_function(node) → registry.get(node.function_key) → getattr(backend, method_name)(*args, **options)
- The function registry: `ExpressionFunctionRegistry` maps FKEY enums to `ExpressionFunctionDef` (protocol_method, substrait_uri, etc.)
- Special handling: LIST function extracts raw values; is_in/is_not_in extract raw haystack values; options passed as **kwargs
- Anti-patterns: creating per-category visitors; hardcoding dispatch logic instead of using registry; putting compilation logic in nodes
- Future: the registry also enables future Substrait serialization

- [ ] **Step 2: Commit**

```bash
git add 01.principles/mountainash-expresions/a.architecture/unified-visitor.md
git commit -m "docs: add unified-visitor principle"
```

---

## Chunk 3: Type System and API Design Principles (b + c)

### Task 6: Write b.type-system/function-key-enums.md

**Files:**
- Create: `b.type-system/function-key-enums.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_system/function_keys/enums.py`

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Every operation has an ENUM key with the `FKEY_` prefix. Substrait operations use `FKEY_SUBSTRAIT_<CATEGORY>` classes; Mountainash extensions use `FKEY_MOUNTAINASH_<CATEGORY>` classes. The ENUM is the canonical identifier for an operation throughout the system.

Key content:
- 13 Substrait FKEY enums + 7 Mountainash FKEY enums listed
- FKEY_ prefix is mandatory — old-style names (KEY_*, MOUNTAINASH_*) were removed during alignment
- Helper frozensets: MOUNTAINASH_TERNARY_TERMINAL, MOUNTAINASH_TERNARY_NON_TERMINAL, MOUNTAINASH_TERNARY_ALL
- Union types: SubstraitFunction, MountainashFunction, FunctionEnum
- Anti-patterns: using string literals instead of enums; creating enum members without registering in definitions.py; using old-style names without FKEY_ prefix
- Example: `FKEY_SUBSTRAIT_SCALAR_COMPARISON.GT` not `"gt"` or `KEY_SCALAR_COMPARISON.GT`

- [ ] **Step 2: Commit**

### Task 7: Write b.type-system/protocol-as-contract.md

**Files:**
- Create: `b.type-system/protocol-as-contract.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_protocols/expression_systems/` (both substrait/ and extensions_mountainash/)
- `tests/unit/test_protocol_alignment.py`

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Protocol classes are the source of truth for what a backend must implement. If a method is in the protocol, every backend must have it. If it's not in the protocol, backends should not invent it.

Key content:
- Protocol classes use `typing.Protocol` — structural subtyping, no explicit inheritance required
- Naming: `Substrait<Category>ExpressionSystemProtocol` / `MountainAsh<Category>ExpressionSystemProtocol`
- Method signatures use positional-only parameters (`/`) and `SupportedExpressions` type
- `test_protocol_alignment.py` verifies that every protocol method exists on every backend implementation
- Anti-patterns: adding backend methods without adding to protocol; having protocols with methods no backend implements; changing protocol signatures without updating all backends

- [ ] **Step 2: Commit**

### Task 8: Write b.type-system/node-type-design.md

**Files:**
- Create: `b.type-system/node-type-design.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_nodes/substrait/` (all exn_*.py)
- `src/mountainash_expressions/core/expression_nodes/substrait/exn_base.py`

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: Expression nodes are Pydantic models (immutable data). They carry metadata (unknown_values, options) but no logic beyond `accept()` for visitor dispatch.

Key content:
- Pydantic BaseModel with `model_config = ConfigDict(arbitrary_types_allowed=True)`
- `function_key` field on all nodes — the central dispatch key
- `FieldReferenceNode.unknown_values: Optional[Set[Any]]` — carries sentinel values for ternary logic
- `ScalarFunctionNode.options: Dict[str, Any]` — carries operation-specific parameters (left_unknown, right_unknown, case_sensitivity, etc.)
- `is_ternary_non_terminal` / `is_ternary` properties on ScalarFunctionNode for auto-booleanization
- Anti-patterns: putting compilation logic in nodes; mutating nodes after creation; storing backend-specific types in nodes

- [ ] **Step 2: Commit**

### Task 9: Write c.api-design/build-then-compile.md

**Files:**
- Create: `c.api-design/build-then-compile.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_api/api_base.py` (compile method)
- `CLAUDE.md` "Public API" and "The Architecture Flow" sections

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Expression building and compilation are separate phases. Building creates a backend-agnostic AST. Compilation detects the backend from the DataFrame and produces a native expression. The user never needs to specify which backend they're using.

Key content:
- `ma.col("age").gt(30)` builds AST — no backend needed
- `.compile(df)` detects backend, creates visitor, visits AST
- `_maybe_booleanize()` auto-wraps ternary expressions before compilation
- Booleanizer parameter: `compile(df, booleanizer="is_true")` / `booleanizer=None` for raw values
- Anti-patterns: requiring users to specify backend; building backend-specific expressions in API builders; compiling at build time
- Example showing the full flow from `ma.col("age").gt(30)` through AST to `pl.col("age").gt(30)`

- [ ] **Step 2: Commit**

### Task 10: Write c.api-design/fluent-builder-pattern.md

**Files:**
- Create: `c.api-design/fluent-builder-pattern.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_api/boolean.py`
- `src/mountainash_expressions/core/expression_api/api_base.py` (`__getattr__`)
- `src/mountainash_expressions/core/expression_api/descriptor.py`

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: `BooleanExpressionAPI` composes methods from multiple API Builders via `__getattr__` dispatch over `_FLAT_NAMESPACES`. Explicit namespaces (`.str`, `.dt`, `.name`) use `NamespaceDescriptor`.

Key content:
- `_FLAT_NAMESPACES` tuple — searched in order, first match wins
- Extension builders listed before Substrait builders (ternary takes priority for is_true etc.)
- NamespaceDescriptor pattern for explicit namespaces
- Each builder inherits from `BaseExpressionAPIBuilder` and a protocol
- `_build(node)` returns a new `BooleanExpressionAPI` wrapping the new node — enables chaining
- Anti-patterns: adding methods directly to BooleanExpressionAPI; putting multiple responsibilities in one builder; having builders depend on each other

- [ ] **Step 2: Commit**

### Task 11: Write c.api-design/operator-overloading.md

**Files:**
- Create: `c.api-design/operator-overloading.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_api/boolean.py` (dunder methods)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Python operators map to named methods on `BooleanExpressionAPI`. Every operator has a corresponding named method. Reversed operators (`__radd__`, `__rsub__`) are supported for `other + col()` patterns.

Key content:
- Full operator table: `>` → `gt()`, `&` → `and_()`, `+` → `add()`, `//` → `floor_divide()`, `-col` → `negate()`
- Reversed operators: `__radd__` calls `add(other)`, `__rsub__` calls `rsubtract(other)`, etc.
- Anti-patterns: implementing operator logic in the dunder method (should delegate to named method); forgetting reversed operators
- Note: `__eq__` and `__ne__` return `BooleanExpressionAPI`, not `bool` — this means expression objects are not hashable

- [ ] **Step 2: Commit**

### Task 12: Write c.api-design/short-aliases.md

**Files:**
- Create: `c.api-design/short-aliases.md`

**Content sources:**
- This session's work on adding aliases (eq/equal, ge/gte, modulo/modulus)
- `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_comparison.py` (alias declarations)
- `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_arithmetic.py` (alias declarations)

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: The public API uses short, familiar names (eq, ge, modulo). API Builders may implement the Substrait name (equal, gte, modulus) and provide short aliases as class attributes. Both names are valid.

Key content:
- Alias table: eq=equal, ne=not_equal, ge=gte, le=lte, modulo=modulus, rmodulo=rmodulus, xor_=xor, length=char_length
- Implementation: `eq = equal` (class attribute alias) — simple, no code duplication
- Why both names: Substrait names for spec alignment, short names for user convenience
- Anti-patterns: implementing the same logic twice under different names; only having one name without the alias
- Future: protocol alignment tests should validate that both names exist

- [ ] **Step 2: Commit all c.api-design**

```bash
git add 01.principles/mountainash-expresions/b.type-system/ 01.principles/mountainash-expresions/c.api-design/
git commit -m "docs: add type-system and api-design principles"
```

---

## Chunk 4: Ternary Logic and Cross-Backend Principles (d + e)

### Task 13: Write d.ternary-logic/three-valued-semantics.md

**Files:**
- Create: `d.ternary-logic/three-valued-semantics.md`

**Content sources:**
- `CLAUDE.md` "Ternary Logic System" section
- `src/mountainash_expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_ternary.py`

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Ternary logic uses integer sentinel values: TRUE=1, UNKNOWN=0, FALSE=-1. This is not SQL NULL propagation — UNKNOWN is an explicit value that participates in logic operations with defined semantics.

Key content:
- Why integers not NULL: NULL propagates silently; sentinel integers are explicit and inspectable
- Truth tables: T AND U = U (min), T OR U = T (max), NOT U = U (sign flip)
- Comparison: boolean `True AND NULL = NULL` (ambiguous) vs ternary `TRUE AND UNKNOWN = UNKNOWN` (explicit)
- t_* prefix convention: t_eq, t_gt, t_and, t_or, t_not — all return -1/0/1
- Anti-patterns: using NULL for UNKNOWN; treating 0 as FALSE (it's UNKNOWN); mixing boolean and ternary operations without coercion

- [ ] **Step 2: Commit**

### Task 14: Write d.ternary-logic/booleanization.md

**Files:**
- Create: `d.ternary-logic/booleanization.md`

**Content sources:**
- `CLAUDE.md` "Auto-Booleanization" section
- `src/mountainash_expressions/core/expression_api/api_base.py` (`_maybe_booleanize` method)
- `src/mountainash_expressions/core/expression_system/function_keys/enums.py` (MOUNTAINASH_TERNARY_TERMINAL/NON_TERMINAL frozensets)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Ternary expressions are automatically converted to boolean at compile time. The default booleanizer is `is_true` (only TRUE passes). Users can choose other strategies (`maybe_true`, `is_false`, etc.) or disable booleanization entirely.

Key content:
- Six built-in booleanizers table (from CLAUDE.md)
- Terminal vs non-terminal: terminal functions (is_true, maybe_true, etc.) already return boolean; non-terminal functions (t_eq, t_and, etc.) need booleanization
- `MOUNTAINASH_TERNARY_TERMINAL` / `MOUNTAINASH_TERNARY_NON_TERMINAL` frozensets as the single source of truth
- `compile(df, booleanizer=None)` returns raw -1/0/1 values
- Anti-patterns: manually wrapping ternary expressions with is_true(); forgetting to add new terminal functions to the frozenset

- [ ] **Step 2: Commit**

### Task 15: Write d.ternary-logic/sentinel-values.md

**Files:**
- Create: `d.ternary-logic/sentinel-values.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_api/entrypoints.py` (t_col function)
- `src/mountainash_expressions/core/expression_nodes/substrait/exn_field_reference.py` (unknown_values field)
- `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py` (_extract_unknown_options)
- `src/mountainash_expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_ternary.py` (_check_unknown)

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: `t_col(name, unknown={...})` creates a column reference that treats specified values as UNKNOWN in ternary comparisons. Sentinel values flow from `FieldReferenceNode.unknown_values` through the API builder (stored in `ScalarFunctionNode.options` as `left_unknown`/`right_unknown`) to backend methods that conditionally map sentinels to UNKNOWN(0).

Key content:
- The data flow: t_col() → FieldReferenceNode(unknown_values=) → ternary builder extracts via _extract_unknown_options() → stored in node.options → visitor passes as **kwargs → backend _check_unknown() processes
- Use cases: legacy systems with -99999 sentinels, empty strings as missing, "N/A" markers
- Backend implementation: `_check_unknown()` builds `when(is_sentinel_or_null).then(0).otherwise(comparison)` chains
- Anti-patterns: checking sentinels in the visitor instead of the backend; losing unknown_values during AST construction

- [ ] **Step 2: Commit**

### Task 16: Write d.ternary-logic/bidirectional-coercion.md

**Files:**
- Create: `d.ternary-logic/bidirectional-coercion.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_ternary.py` (_coerce_if_needed)
- `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_boolean.py` (_coerce_if_needed)

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: Boolean and ternary expressions coerce automatically in both directions. Boolean→ternary wraps with `to_ternary()`. Ternary→boolean wraps with `is_true()`. Coercion happens at the API builder level, not at compile time.

Key content:
- Boolean builder: `_coerce_if_needed()` checks `is_ternary_non_terminal` and wraps with `is_true()`
- Ternary builder: `_coerce_if_needed()` checks `not is_ternary` and wraps with `to_ternary()`
- Example: `col("active").eq(True).t_and(col("score").t_gt(70))` — the boolean eq() result is automatically wrapped with to_ternary()
- Anti-patterns: requiring explicit coercion from users; coercing at compile time (too late, AST is already built)

- [ ] **Step 2: Commit**

### Task 17: Write e.cross-backend/backend-detection.md

**Files:**
- Create: `e.cross-backend/backend-detection.md`

**Content sources:**
- `src/mountainash_expressions/core/expression_system/expsys_base.py` (register_expression_system decorator)
- `src/mountainash_expressions/core/expression_api/api_base.py` (compile method — backend detection)
- `src/mountainash_expressions/backends/expression_systems/*/` (__init__.py files with @register_expression_system)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Backends register with `@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)`. At compile time, the DataFrame type is inspected to select the correct backend. Users never specify which backend to use.

Key content:
- Registration decorator pattern
- Detection logic: Polars → PolarsExpressionSystem, Narwhals → NarwhalsExpressionSystem, Ibis → IbisExpressionSystem
- Narwhals auto-rejects Narwhals-wrapped Ibis (incompatible)
- Ibis supports multiple sub-backends (Polars, DuckDB, SQLite)
- Anti-patterns: requiring backend specification in API calls; hardcoding backend checks in business logic

- [ ] **Step 2: Commit**

### Task 18: Write e.cross-backend/consistency-guarantees.md

**Files:**
- Create: `e.cross-backend/consistency-guarantees.md`

**Content sources:**
- `tests/cross_backend/` (parametrized test pattern)
- `CLAUDE.md` "Backend Support" section

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: The same expression must produce the same logical result across all backends. Cross-backend parametrized tests are the enforcement mechanism. Known divergences are documented with `pytest.xfail`, never silently tolerated.

Key content:
- `ALL_BACKENDS` list in conftest.py: polars, pandas, narwhals, ibis-duckdb, ibis-polars, ibis-sqlite
- Test pattern: `@pytest.mark.parametrize("backend_name", ALL_BACKENDS)` — every test runs on every backend
- When backends legitimately differ: use `pytest.xfail(reason="...")` with specific explanation, never `skip`
- Anti-patterns: writing backend-specific tests; silently skipping backends; accepting different results without documentation

- [ ] **Step 2: Commit**

### Task 19: Write e.cross-backend/known-divergences.md

**Files:**
- Create: `e.cross-backend/known-divergences.md`

**Content sources:**
- `CLAUDE.md` "Known Issues & Backend Inconsistencies" section
- xfail markers in `tests/cross_backend/` test files

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: Backend divergences are documented explicitly with root cause and impact. Each divergence has a clear explanation of why it occurs and which tests account for it.

Key content:
- SQLite integer division: `20 / 3 = 6` not `6.666...`
- Modulo sign semantics: Python/Polars use modulo (sign of divisor), SQLite/DuckDB use remainder (sign of dividend) — `-7 % 3 = 2` vs `-7 % 3 = -1`
- Ibis type inference: Issue #11742 — some type inference fails
- Ibis LIKE pattern: unsupported on some backends
- Temporal limitations: SQLite very limited datetime filtering
- Anti-patterns: silently accepting divergent results; adding workarounds in production code to handle backend quirks

- [ ] **Step 2: Commit all d + e**

```bash
git add 01.principles/mountainash-expresions/d.ternary-logic/ 01.principles/mountainash-expresions/e.cross-backend/
git commit -m "docs: add ternary-logic and cross-backend principles"
```

---

## Chunk 5: Extension Model, Development Practices, and Final Wiring (f + g + CLAUDE.md)

### Task 20: Write f.extension-model/substrait-vs-mountainash.md

**Files:**
- Create: `f.extension-model/substrait-vs-mountainash.md`

**Content sources:**
- `docs/adr/ADR-008-substrait-extension-alignment.md`
- `CLAUDE.md` "Naming Conventions" tables

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Substrait-standard and Mountainash-custom operations are physically separated at every layer. Directory names, file prefixes, ENUM names, and class names all distinguish standard from extension.

Key content:
- Directory separation: `substrait/` vs `extensions_mountainash/` in protocols, api_builders, and backends
- ENUM separation: `FKEY_SUBSTRAIT_*` vs `FKEY_MOUNTAINASH_*`
- Class naming: `Substrait<X>Protocol` vs `MountainAsh<X>Protocol`
- File naming: `expsys_pl_scalar_comparison.py` vs `expsys_pl_ext_ma_null.py`
- URI separation: SubstraitExtension (substrait.io URLs) vs MountainashExtension (file:// URLs)
- Anti-patterns: putting extension operations in substrait directories; using FKEY_SUBSTRAIT_* for custom operations; mixing standard and extension in the same file

- [ ] **Step 2: Commit**

### Task 21: Write f.extension-model/adding-operations.md

**Files:**
- Create: `f.extension-model/adding-operations.md`

**Content sources:**
- `CLAUDE.md` "Adding a New Substrait Operation" and "Adding a Mountainash Extension" sections

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: Adding a new operation follows a five-step process: (1) add ENUM to function_keys, (2) add to protocol, (3) implement in API builder, (4) implement in all backends, (5) add cross-backend tests. The same process applies to both Substrait and Mountainash operations, with different target directories.

Key content:
- Five steps with exact file paths for each (from CLAUDE.md)
- Registration in definitions.py (ExpressionFunctionDef with function_key, substrait_uri, protocol_method)
- The distinction: Substrait ops go in substrait/ directories, extensions go in extensions_mountainash/
- Backend composition: new backend class must be added to the ExpressionSystem __init__.py
- Anti-patterns: implementing in one backend and forgetting others; adding ENUM without registration; skipping protocol step

- [ ] **Step 2: Commit**

### Task 22: Write f.extension-model/backend-composition.md

**Files:**
- Create: `f.extension-model/backend-composition.md`

**Content sources:**
- `src/mountainash_expressions/backends/expression_systems/polars/__init__.py`
- `src/mountainash_expressions/backends/expression_systems/ibis/__init__.py`
- `src/mountainash_expressions/backends/expression_systems/narwhals/__init__.py`

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Each backend composes all protocol implementations into a single `<Backend>ExpressionSystem` class via multiple inheritance. The composition class itself has no methods — it is pure composition with `pass`.

Key content:
- Pattern: `class PolarsExpressionSystem(SubstraitPolarsScalarComparison, ..., MountainAshPolarsTernary): pass`
- `@register_expression_system(CONST_VISITOR_BACKENDS.POLARS)` decorator registers it
- All three backends follow identical structure
- When adding a new protocol implementation: import it and add it to the composition class's base list
- Anti-patterns: putting methods directly on the composition class; having backends with different sets of protocols implemented; forgetting to add new implementations to the composition

- [ ] **Step 2: Commit**

### Task 23: Write g.development-practices/naming-conventions.md

**Files:**
- Create: `g.development-practices/naming-conventions.md`

**Content sources:**
- `CLAUDE.md` "Naming Conventions" section (all three tables)

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: File prefixes, backend prefixes, and class names follow strict conventions that make the codebase navigable without documentation.

Key content:
- File prefix table: exn_ (node), prtcl_ (protocol), api_bldr_ (API builder), expsys_ (backend expression system), ext_ma_ (Mountainash extension)
- Backend prefix table: pl_ (Polars), ib_ (Ibis), nw_ (Narwhals)
- ENUM naming: FKEY_SUBSTRAIT_SCALAR_<CATEGORY> / FKEY_MOUNTAINASH_<CATEGORY> — always FKEY_ prefix
- Class naming table from CLAUDE.md
- Anti-patterns: using old-style enum names (KEY_*, MOUNTAINASH_*); inconsistent prefixes; abbreviating backend names differently

- [ ] **Step 2: Commit**

### Task 24: Write g.development-practices/testing-philosophy.md

**Files:**
- Create: `g.development-practices/testing-philosophy.md`

**Content sources:**
- `tests/conftest.py` (fixture patterns)
- `tests/cross_backend/` (test patterns)
- `CLAUDE.md` "Test Structure" section
- Project CLAUDE.md "Test Integrity" section

- [ ] **Step 1: Write the document**

Status: ENFORCED

The Principle: Cross-backend parametrized tests are the primary test suite. Tests must never be skipped, disabled, or modified to pass without understanding the root cause. When tests fail, present the failure and ask — the test may be correct and the implementation wrong.

Key content:
- ALL_BACKENDS parametrization pattern
- Test structure: `tests/cross_backend/` for functional tests, `tests/unit/` for structural alignment
- `test_protocol_alignment.py` verifies protocol-to-implementation method alignment
- xfail for known backend quirks (with reason), never skip
- Fixture pattern: `backend_factory.create(data, backend_name)` creates DataFrame for any backend
- ~1,800 tests, ~11,000 lines
- Anti-patterns: skipping tests; mocking backends; writing backend-specific tests in cross_backend/; marking tests as expected failures without understanding why

- [ ] **Step 2: Commit**

### Task 25: Write g.development-practices/file-organisation.md

**Files:**
- Create: `g.development-practices/file-organisation.md`

**Content sources:**
- `CLAUDE.md` "Package Structure" section
- Directory listings of protocols, api_builders, and backends

- [ ] **Step 1: Write the document**

Status: ADOPTED

The Principle: Directory structure mirrors across all three layers. Every `substrait/` directory has a parallel `extensions_mountainash/` directory. Every protocol category has a corresponding API builder and backend implementation.

Key content:
- The mirroring: `expression_protocols/expression_systems/substrait/` ↔ `expression_api/api_builders/substrait/` ↔ `backends/expression_systems/polars/substrait/`
- Same for extensions_mountainash/ at each layer
- __init__.py files at each level re-export all classes
- `__all__` lists maintained for explicit exports
- Anti-patterns: creating a protocol without the corresponding builder/backend directories; having asymmetric structures between backends

- [ ] **Step 2: Commit all f + g**

```bash
git add 01.principles/mountainash-expresions/f.extension-model/ 01.principles/mountainash-expresions/g.development-practices/
git commit -m "docs: add extension-model and development-practices principles"
```

### Task 26: Update CLAUDE.md with Principles reference

**Files:**
- Modify: `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions/CLAUDE.md`

- [ ] **Step 1: Add Principles section to CLAUDE.md**

Add near the top of the file (after "Current Architecture Status" section), a new section:

```markdown
## Principles Repository

Design principles for this project are documented at:
`/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/`

Consult the principles when making architectural decisions, adding new operations, or resolving design tensions. The principles explain the *why* behind the patterns described in this file.
```

- [ ] **Step 2: Commit**

```bash
cd /home/nathanielramm/git/mountainash-io/mountainash/mountainash-expressions
git add CLAUDE.md
git commit -m "docs: add principles repository reference to CLAUDE.md"
```

---

## Verification

After all tasks complete, verify the Definition of Done:

```bash
BASE="/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions"

# Check all 7 directories exist
ls -d "$BASE"/a.* "$BASE"/b.* "$BASE"/c.* "$BASE"/d.* "$BASE"/e.* "$BASE"/f.* "$BASE"/g.*

# Check all 24 files exist (22 principles + 2 governance)
find "$BASE" -name "*.md" | wc -l  # Should be 24

# Check no file exceeds 150 lines
find "$BASE" -name "*.md" -exec wc -l {} + | sort -n

# Check no file is under 50 lines (except README which may be shorter)
find "$BASE" -name "*.md" ! -name "README.md" -exec sh -c 'lines=$(wc -l < "$1"); if [ "$lines" -lt 50 ]; then echo "SHORT: $1 ($lines lines)"; fi' _ {} \;

# Check all files use project-root-relative paths (no /home/ paths in Technical Reference)
grep -r "/home/" "$BASE"/*.md "$BASE"/*/*.md || echo "No absolute paths found - GOOD"
```
