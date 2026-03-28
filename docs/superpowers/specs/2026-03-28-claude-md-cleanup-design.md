# CLAUDE.md Cleanup — Design Spec

> **Date:** 2026-03-28
> **Status:** Approved
> **Goal:** Reduce CLAUDE.md from 1,125 lines to ~130 lines by removing content now covered by the principles repository, while retaining operational reference material.

## Context

The mountainash-expressions project maintains a principles repository at:
`/home/nathanielramm/git/mountainash-io/mountainash/mountainash-central/01.principles/mountainash-expresions/`

This repository contains 27 documents across 8 categories (a–h) covering architecture, type system, API design, ternary logic, cross-backend concerns, the extension model, and development practices. These were distilled from the ADRs and the CLAUDE.md itself, making much of the CLAUDE.md redundant.

The PRINCIPLES.md governance document defines the relationship: "Principles explain the *why* behind the patterns. CLAUDE.md executes on those outcomes." Currently, CLAUDE.md duplicates ~900 lines of *why* content.

## Approach: "Map + Commands"

The new CLAUDE.md exposes the *structure and contents* of the principles repo (as a table of contents) with a mandatory consultation instruction, plus purely operational content that can't be derived from principles or code.

## New CLAUDE.md Structure

### Section 1: Principles (Mandatory Consultation) — ~55 lines

**Hard instruction:**
A clear directive that Claude MUST read the relevant principle documents before making architectural decisions, adding operations, modifying protocols, or changing backend implementations. Not advisory — mandatory.

**Principles index table:**
The full table from the principles repo README, showing all categories (a–h), every document filename, its status (ENFORCED/ADOPTED), and its one-line summary. This gives Claude a complete map of what exists and where to look, without duplicating the content.

**Path:**
The absolute path to the principles repo directory.

**What this replaces (removed from CLAUDE.md):**
- Project Overview / Current Architecture Status (~100 lines)
- Core Architecture: Substrait-Aligned Design (~150 lines)
- Naming Conventions (~30 lines)
- Implemented Categories tables (~40 lines)
- Ternary Logic System (~120 lines)
- Public API / BooleanExpressionAPI full method listing (~200 lines)
- "Adding a New Substrait Operation" / "Adding an Alias" guides (~100 lines)
- Backend Support / Known Issues & Inconsistencies (~50 lines)
- Common Patterns / Debugging Expression Compilation (~50 lines)
- Architecture Summary table (~15 lines)
- Future Work (~10 lines)
- References section (~5 lines)

### Section 2: Operational Reference — ~75 lines

Content that is purely operational and not covered by the principles repo:

1. **Code Intelligence (~12 lines)** — LSP preferences (goToDefinition, findReferences, etc.). Kept as-is.

2. **Package Structure (~25 lines)** — Condensed file tree showing `src/mountainash/` top-level layout (core, expressions, dataframes, schema, pydata, backwards-compat shim). Omits the deep nesting already documented in `g.development-practices/file-organisation.md`.

3. **Development Commands (~15 lines)** — `hatch run test:test`, `hatch run ruff:check`, `hatch build`, etc. Kept as-is.

4. **Dependencies (~5 lines)** — Critical note about the local Ibis fork at `/home/nathanielramm/git/ibis` and why it's needed (Polars calendar interval fix). Easy to miss, causes real confusion.

5. **Quick Reference: Import Paths (~15 lines)** — Condensed examples: `import mountainash as ma`, backwards-compat shim (`import mountainash_expressions as ma`), key internal paths. Reduced from ~40 lines.

6. **GitHub Operations (~5 lines)** — Pointer to hiivmind-pulse-gh plugin and config location. Kept as-is.

## What Is NOT Changed

- The principles repo itself — no modifications.
- The `docs/adr/` directory — untouched.
- The backwards-compat shim at `src/mountainash_expressions/` — untouched.

## Maintenance

When the principles README is updated (new documents added, statuses changed), the CLAUDE.md principles index table should be updated to match. This is a manual sync — the table is a snapshot, not a live reference.

## Success Criteria

- CLAUDE.md is ~130 lines (down from 1,125)
- All architectural/design content is removed (no duplication with principles)
- The principles index table matches the current principles README
- Mandatory consultation instruction is present
- All operational content (commands, paths, dependencies) is preserved
- A new Claude Code session can orient itself quickly and knows exactly which principle docs to consult for any task
