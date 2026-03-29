# Mountainash-Expressions Principles Repository — Design Spec

## Overview

Create a principles repository for mountainash-expressions at:
```
/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/
```

The repository captures durable design decisions, architectural philosophy, and development practices for the mountainash-expressions package. It serves both human developers (returning after time away) and AI agents (Claude Code sessions needing architectural context).

Structure follows the pattern established in `fairgo-central/02.principles/`.

## Status Markers

| Status | Meaning |
|--------|---------|
| `ENFORCED` | In code and verified by tests |
| `ADOPTED` | In code, not fully tested or partially implemented |
| `PROPOSED` | Documented in ADR, not yet in code |
| `EXPLORATORY` | Thinking only, not committed to |

## Directory Structure

```
mountainash-expresions/
├── PRINCIPLES.md                          # Governance doc
├── README.md                              # Index with tables
├── a.architecture/
│   ├── substrait-first-design.md
│   ├── minimal-ast.md
│   ├── three-layer-separation.md
│   └── unified-visitor.md
├── b.type-system/
│   ├── function-key-enums.md
│   ├── protocol-as-contract.md
│   └── node-type-design.md
├── c.api-design/
│   ├── build-then-compile.md
│   ├── fluent-builder-pattern.md
│   ├── operator-overloading.md
│   └── short-aliases.md
├── d.ternary-logic/
│   ├── three-valued-semantics.md
│   ├── booleanization.md
│   ├── sentinel-values.md
│   └── bidirectional-coercion.md
├── e.cross-backend/
│   ├── backend-detection.md
│   ├── consistency-guarantees.md
│   └── known-divergences.md
├── f.extension-model/
│   ├── substrait-vs-mountainash.md
│   ├── adding-operations.md
│   └── backend-composition.md
└── g.development-practices/
    ├── naming-conventions.md
    ├── testing-philosophy.md
    └── file-organisation.md
```

**Total: 24 documents** (22 principles + PRINCIPLES.md + README.md)

## Document Template

Every principle document follows this structure:

```markdown
# [Title]

> **Status:** ENFORCED | ADOPTED | PROPOSED | EXPLORATORY

## The Principle

[One to three crisp sentences stating the principle declaratively.]

## Rationale

[Why this decision was made. What problem it solves.]

## Examples

[Concrete code examples, tables, or scenarios.]

## Anti-Patterns

[What NOT to do. Common mistakes this principle prevents.]

## Technical Reference

[Specific files, classes, methods, or imports.]

## Future Considerations

[Known gaps, planned extensions, or open questions.]
```

## Governance Document (PRINCIPLES.md)

Covers:
- Why the directory exists (scattered decisions across ADRs, CLAUDE.md, and code comments)
- How categories were chosen (map to concerns, not code directories)
- Status marker definitions
- How to add new principles
- Relationship to other documentation (ADRs in docs/adr/, CLAUDE.md, code comments)
- Conflict documentation pattern (CONFLICTS.md per category when tensions exist)

## Index Document (README.md)

One table per category with columns: Document | Status | Summary. Links to governance doc at top. Same format as fairgo README.md.

## Document Inventory

### a. Architecture

| Document | Status | Summary |
|----------|--------|---------|
| `substrait-first-design.md` | ENFORCED | All operations align with Substrait specification where possible; custom ops live in a separate extension namespace |
| `minimal-ast.md` | ENFORCED | Only 7 node types; ScalarFunctionNode handles 90% of operations via function key ENUMs |
| `three-layer-separation.md` | ENFORCED | Protocol → API Builder → Backend. Each layer has a single responsibility and can change independently |
| `unified-visitor.md` | ADOPTED | Single visitor dispatches all node types via function registry lookup, replacing 12+ category-specific visitors |

### b. Type System

| Document | Status | Summary |
|----------|--------|---------|
| `function-key-enums.md` | ENFORCED | Every operation has an ENUM key (FKEY_* prefix); enables type-safe dispatch, IDE autocomplete, and registry lookup |
| `protocol-as-contract.md` | ENFORCED | Protocol classes are the source of truth for what a backend must implement; method signatures are the contract |
| `node-type-design.md` | ADOPTED | Pydantic-based nodes; FieldReferenceNode carries optional unknown_values; ScalarFunctionNode carries options dict |

### c. API Design

| Document | Status | Summary |
|----------|--------|---------|
| `build-then-compile.md` | ENFORCED | Expressions build a backend-agnostic AST; `.compile(df)` detects the backend and produces native expressions |
| `fluent-builder-pattern.md` | ENFORCED | Method chaining via `__getattr__` dispatch to flat namespace builders; explicit namespaces (.str, .dt, .name) via descriptors |
| `operator-overloading.md` | ENFORCED | Python operators (`>`, `&`, `+`, `//`) map to named methods; reversed operators (`__radd__`) supported |
| `short-aliases.md` | ADOPTED | Public API uses short names (eq, ge, modulo); builders may use Substrait names internally (equal, gte, modulus) with aliases |

### d. Ternary Logic

| Document | Status | Summary |
|----------|--------|---------|
| `three-valued-semantics.md` | ENFORCED | TRUE=1, UNKNOWN=0, FALSE=-1; sentinel integer values, not NULL propagation |
| `booleanization.md` | ENFORCED | Ternary expressions auto-booleanize at compile time; six built-in booleanizers (is_true, maybe_true, etc.) |
| `sentinel-values.md` | ADOPTED | `t_col(name, unknown={...})` treats custom values as UNKNOWN; unknown_values flow through node options to backend |
| `bidirectional-coercion.md` | ADOPTED | Boolean→ternary via to_ternary(); ternary→boolean via booleanizer at compile time |

### e. Cross-Backend

| Document | Status | Summary |
|----------|--------|---------|
| `backend-detection.md` | ENFORCED | Automatic backend detection from DataFrame type; registered via `@register_expression_system` decorator |
| `consistency-guarantees.md` | ENFORCED | Same expression must produce same logical result across backends; known divergences are documented and xfailed |
| `known-divergences.md` | ADOPTED | SQLite integer division, modulo sign semantics, Ibis type inference gaps — documented per-backend |

### f. Extension Model

| Document | Status | Summary |
|----------|--------|---------|
| `substrait-vs-mountainash.md` | ENFORCED | Physical directory separation (substrait/ vs extensions_mountainash/); FKEY_SUBSTRAIT_* vs FKEY_MOUNTAINASH_* enums |
| `adding-operations.md` | ADOPTED | Five-step process: enum → protocol → API builder → all backends → tests |
| `backend-composition.md` | ENFORCED | Each backend composes all protocol implementations via multiple inheritance into a single ExpressionSystem class |

### g. Development Practices

| Document | Status | Summary |
|----------|--------|---------|
| `naming-conventions.md` | ENFORCED | File prefixes (exn_, prtcl_, api_bldr_, expsys_), backend prefixes (pl_, ib_, nw_), FKEY_* enum naming |
| `testing-philosophy.md` | ENFORCED | Cross-backend parametrized tests are the primary suite; xfail for known backend quirks; never skip or disable |
| `file-organisation.md` | ADOPTED | Mirror directory structure across layers; every substrait/ has a parallel extensions_mountainash/ |

## Content Guidelines

### Audience
Both human developers and AI agents. Write declaratively — state what IS, not what SHOULD BE. Use code examples from the actual codebase. Include file paths in Technical Reference sections.

### Relationship to Existing Docs
- **ADRs** (`docs/adr/`) document individual decisions with alternatives and rationale. Principles distill the durable outcome.
- **CLAUDE.md** is the operational guide for working in the codebase. Principles explain the *why* behind the patterns CLAUDE.md describes.
- **Code comments** are local. Principles are cross-cutting.

### When to Create CONFLICTS.md
When two principles tension against each other. Example: "short aliases" (c.api-design) vs "protocol-as-contract" (b.type-system) — the protocol defines `equal()` but the public API exposes `eq()`. The conflict doc captures the resolution (aliases bridge the gap) and prevents future confusion.

## Consumption: How Agents and Humans Find These Principles

- **CLAUDE.md** in mountainash-expressions will add a "Principles" section referencing the principles directory path
- **AI agents** will be instructed (via CLAUDE.md) to consult principles when making architectural decisions
- **Humans** browse the README.md index or navigate category folders directly
- The principles repo lives in mountainash-central (the shared governance repo), not inside the code repo — this is intentional, as principles are cross-cutting and may inform multiple repos

## Category Ordering Rationale

Categories are lettered a–g by dependency: foundational decisions first, derived practices last.

- **a–b** (Architecture, Type System): Structural foundations — everything else depends on these
- **c–d** (API Design, Ternary Logic): User-facing semantics built on the architecture
- **e–f** (Cross-Backend, Extension Model): How the architecture scales across backends and grows
- **g** (Development Practices): Conventions that follow from all the above

When principles conflict and no CONFLICTS.md exists, **lower-lettered categories take precedence** (architecture trumps API convenience).

## Definition of Done

Implementation is complete when:
- [ ] All 7 category directories exist
- [ ] All 22 principle documents are written with all 6 template sections populated
- [ ] PRINCIPLES.md governance doc is written
- [ ] README.md index is written with accurate tables
- [ ] Each principle document is 50–150 lines
- [ ] Technical Reference paths use project-root-relative format (e.g., `src/mountainash_expressions/core/...`)
- [ ] CLAUDE.md in mountainash-expressions updated with a Principles section pointing to the repo

No CONFLICTS.md files are expected in the initial implementation — they are added later when tensions are discovered.

## Content Source Map

The implementer should extract principle content from these sources:

| Source | Relevant Principles |
|--------|-------------------|
| `CLAUDE.md` (project) | All categories — the operational descriptions map directly to principles |
| `docs/adr/ADR-008-substrait-extension-alignment.md` | a.architecture, f.extension-model |
| `docs/adr/ADR-009-substrait-backend-implementation-alignment.md` | e.cross-backend, f.extension-model |
| `docs/adr/ADR-010-api-builder-protocol-alignment.md` | b.type-system, c.api-design |
| `src/mountainash_expressions/core/expression_nodes/substrait/` | a.architecture (minimal-ast), b.type-system (node-type-design) |
| `src/mountainash_expressions/core/expression_system/function_keys/enums.py` | b.type-system (function-key-enums) |
| `src/mountainash_expressions/core/expression_protocols/` | b.type-system (protocol-as-contract) |
| `src/mountainash_expressions/core/expression_api/` | c.api-design (all documents) |
| `src/mountainash_expressions/backends/expression_systems/` | e.cross-backend, f.extension-model (backend-composition) |
| `tests/cross_backend/` | g.development-practices (testing-philosophy), e.cross-backend (known-divergences) |
| `pyproject.toml` naming + file prefixes | g.development-practices (naming-conventions, file-organisation) |
| This session's work (enum standardisation, sentinel wiring) | Lived experience of the architecture in action |

## Implementation Notes

- Target directory already exists (empty): `mountainash-central/01.principles/mountainash-expresions/`
  - **Note:** The directory name `mountainash-expresions` (single 's') matches the pre-existing directory. This is the user's chosen spelling.
- No code changes to mountainash-expressions package itself (only CLAUDE.md update)
- Each principle document should be 50–150 lines — enough to be useful, short enough to scan
- Technical Reference sections use project-root-relative paths (e.g., `src/mountainash_expressions/core/...`), not absolute filesystem paths
- README.md tables are generated from the Document Inventory section of this spec — they are the literal content
