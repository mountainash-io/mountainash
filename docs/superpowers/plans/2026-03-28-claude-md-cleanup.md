# CLAUDE.md Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 1,125-line CLAUDE.md with a ~130-line version that maps the principles repo and retains only operational content.

**Architecture:** Single file rewrite. The new CLAUDE.md has two sections: (1) principles index with mandatory consultation instruction, (2) operational reference (commands, paths, dependencies).

**Tech Stack:** Markdown only. No code changes.

---

### Task 1: Replace CLAUDE.md with new content

**Files:**
- Modify: `CLAUDE.md` (full rewrite)
- Reference (read-only): `/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/README.md`

- [ ] **Step 1: Read the current principles README to confirm the index table is up to date**

Run:
```bash
cat /home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/README.md
```

Verify the table has categories a–h with all documents listed. The new CLAUDE.md will embed this table.

- [ ] **Step 2: Replace CLAUDE.md with the new content**

Overwrite the entire file with this content:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

### Code Intelligence

Prefer LSP over Grep/Glob/Read for code navigation:
- `goToDefinition` / `goToImplementation` to jump to source
- `findReferences` to see all usages across the codebase
- `workspaceSymbol` to find where something is defined
- `documentSymbol` to list all symbols in a file
- `hover` for type info without reading the file
- `incomingCalls` / `outgoingCalls` for call hierarchy

Before renaming or changing a function signature, use
`findReferences` to find all call sites first.

Use Grep/Glob only for text/pattern searches (comments,
strings, config values) where LSP doesn't help.

After writing or editing code, check LSP diagnostics before
moving on. Fix any type errors or missing imports immediately.


## Design Principles (MANDATORY)

**You MUST read the relevant principle documents before:**
- Making any architectural decision
- Adding or modifying operations, protocols, or function keys
- Changing backend implementations
- Modifying the extension model or naming conventions
- Resolving design tensions or trade-offs

This is not advisory. Do not rely on summaries, memory, or assumptions — read the actual principle document.

**Principles location:**
`/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/`

See [PRINCIPLES.md](../mountainash-central/01.principles/mountainash-expresions/PRINCIPLES.md) for governance: statuses, category precedence, how to add new principles.

### a. Architecture

| Document | Status | Summary |
|----------|--------|---------|
| substrait-first-design.md | ENFORCED | All operations align with Substrait specification; custom ops in separate extension namespace |
| minimal-ast.md | ENFORCED | Only 7 node types; ScalarFunctionNode handles 90% of operations via function key ENUMs |
| three-layer-separation.md | ENFORCED | Protocol → API Builder → Backend; each layer has a single responsibility |
| unified-visitor.md | ADOPTED | Single visitor dispatches all node types via function registry lookup |
| wiring-matrix.md | ADOPTED | Every operation must be wired through all six architecture layers |
| unified-package-roadmap.md | ADOPTED | Prioritized roadmap: wiring → shared infra → operations → alignment → release |

### b. Type System

| Document | Status | Summary |
|----------|--------|---------|
| function-key-enums.md | ENFORCED | Every operation has an ENUM key (FKEY_* prefix); type-safe dispatch and registry lookup |
| protocol-as-contract.md | ENFORCED | Protocol classes are the source of truth for what a backend must implement |
| node-type-design.md | ADOPTED | Pydantic-based nodes carry metadata but no logic beyond accept() |

### c. API Design

| Document | Status | Summary |
|----------|--------|---------|
| build-then-compile.md | ENFORCED | Expressions build a backend-agnostic AST; .compile(df) detects backend and produces native expressions |
| fluent-builder-pattern.md | ENFORCED | Method chaining via __getattr__ dispatch; explicit namespaces via descriptors |
| operator-overloading.md | ENFORCED | Python operators map to named methods; reversed operators supported |
| short-aliases.md | ENFORCED | All aliases live in extension builders; Substrait builders contain only canonical names |

### d. Ternary Logic

| Document | Status | Summary |
|----------|--------|---------|
| three-valued-semantics.md | ENFORCED | TRUE=1, UNKNOWN=0, FALSE=-1; sentinel integer values, not NULL propagation |
| booleanization.md | ENFORCED | Ternary expressions auto-booleanize at compile time; six built-in booleanizers |
| sentinel-values.md | ADOPTED | t_col(name, unknown={...}) treats custom values as UNKNOWN |
| bidirectional-coercion.md | ADOPTED | Boolean↔ternary coercion happens automatically at the API builder level |

### e. Cross-Backend

| Document | Status | Summary |
|----------|--------|---------|
| backend-detection.md | ENFORCED | Automatic backend detection from DataFrame type; registered via decorator |
| consistency-guarantees.md | ENFORCED | Same expression must produce same logical result across all backends |
| known-divergences.md | ADOPTED | SQLite integer division, modulo sign semantics, Ibis type inference gaps |
| arguments-vs-options.md | ENFORCED | Arguments are visited expressions; options are raw literals |

### f. Extension Model

| Document | Status | Summary |
|----------|--------|---------|
| substrait-vs-mountainash.md | ENFORCED | Physical directory separation at every layer; FKEY_SUBSTRAIT_* vs FKEY_MOUNTAINASH_* enums |
| adding-operations.md | ADOPTED | Six-step process: enum → protocol → API builder → all backends → function mapping → tests |
| backend-composition.md | ENFORCED | Each backend composes all protocol implementations via multiple inheritance |

### g. Development Practices

| Document | Status | Summary |
|----------|--------|---------|
| naming-conventions.md | ENFORCED | File prefixes (exn_, prtcl_, api_bldr_, expsys_), backend prefixes (pl_, ib_, nw_) |
| testing-philosophy.md | ENFORCED | Cross-backend parametrized tests; xfail for known quirks; never skip or disable |
| file-organisation.md | ADOPTED | Mirror directory structure across layers; every substrait/ has a parallel extensions_mountainash/ |

### h. Backlog

| Document | Summary |
|----------|---------|
| polars-alignment-deferred.md | Deferred work from Polars API alignment batches 1–7 |


## Package Structure

```
src/mountainash/
├── __init__.py                  # Top-level re-exports (col, lit, when, etc.)
├── core/                        # Shared infrastructure (constants, types)
├── expressions/                 # Expression module (mature)
│   ├── core/                   # Nodes, protocols, API builders, function keys
│   └── backends/               # Polars, Ibis, Narwhals implementations
├── dataframes/                  # DataFrame-level operations (planned)
├── schema/                      # Schema definitions (planned)
└── pydata/                      # PyData integrations (planned)

src/mountainash_expressions/     # Backwards-compat shim (import hook → mountainash.expressions)
```

For detailed file organisation see principle: `g.development-practices/file-organisation.md`


## Dependencies

**IMPORTANT:** Using **local Ibis fork** with Polars calendar interval fix:

```toml
ibis-framework = { path = "/home/nathanielramm/git/ibis", extras = ["pandas", "sqlite", "duckdb"] }
```

All other dependencies are in `pyproject.toml`.


## Development Commands

```bash
# Testing
hatch run test:test                  # Full suite with coverage
hatch run test:test-quick            # Fast iteration (no coverage)
hatch run test:test-target <path>    # Specific file or test
hatch run test:test-target-quick <path>  # Specific, no coverage

# Linting & type checking
hatch run ruff:check                 # Check for issues
hatch run ruff:fix                   # Auto-fix issues
hatch run mypy:check                 # Type safety validation

# Building
hatch build
```


## Import Paths

```python
# Public API (both work identically)
import mountainash as ma                    # Canonical
import mountainash_expressions as ma        # Deprecated, works via shim
from mountainash import col, lit, coalesce, greatest, least, when, native, t_col

# Constants (shared core)
from mountainash.core.constants import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

# Function key enums
from mountainash.expressions.core.expression_system.function_keys.enums import (
    KEY_SCALAR_COMPARISON, KEY_SCALAR_BOOLEAN, MOUNTAINASH_TERNARY,
)

# Nodes
from mountainash.expressions.core.expression_nodes.substrait import (
    ScalarFunctionNode, FieldReferenceNode, LiteralNode,
)
```


## GitHub Operations

This project uses [hiivmind-pulse-gh](https://github.com/hiivmind/hiivmind-pulse-gh) for GitHub automation.

**Configuration Location**: `/home/nathanielramm/git/mountainash-io/mountainash/.hiivmind/github`

Use the hiivmind-pulse-gh plugin for all GitHub operations (issues, PRs, milestones, project status) to benefit from automatic context enrichment.
```

- [ ] **Step 3: Verify the line count**

Run:
```bash
wc -l CLAUDE.md
```

Expected: approximately 130 lines (± 10).

- [ ] **Step 4: Verify no architectural/design content was accidentally retained**

Scan for keywords that should no longer appear as section content (they may appear in the principles index table summaries, which is fine):

```bash
grep -n "^## .*Architecture\|^## .*Ternary\|^## .*Naming\|^## .*Backend Support\|^## .*Known Issues\|^## .*Common Development\|^## .*Public API\|^## .*Future Work\|^## .*References\|^## .*Test Structure\|^## .*Core Architecture" CLAUDE.md
```

Expected: no matches. The removed sections should not exist as headings.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: slim CLAUDE.md from 1125 to ~130 lines

Replace duplicated architecture/design content with a principles
index table and mandatory consultation instruction. Retain only
operational content (commands, paths, dependencies, imports)."
```
