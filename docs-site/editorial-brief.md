# Editorial brief: mountainash

Status: confirmed on 2026-10-30. The user confirmed the complete brief as recorded below: scope and exclusions, all seven facets as reading paths, the early ecosystem-context section, inline limits plus a generated support matrix, no reuse, FAQ and glossary, Mermaid first, and the package licence.
Source revision: `0a625ad1d1cc8b436b9fc66b027ac80fdff466ae` (develop). The working tree is clean. The profile source revision is `1d32ab4a`, and `src/` is identical between the two.
Profile basis: `docs-site/profile/manifest.json` (38 modules profiled, 2 version files ignored, validated with `ibook profile validate`, PR #439). The facets are `users`, `maintainers`, `contributors`, `backend-architecture`, `extension-authors`, `executives-marketing` and `broader-hype`. Coverage is reported in `docs-site/profile/coverage.md`.
Operation: replacement rebuild from scratch on `docs/textbook-rebuild` (from develop `0a625ad`). The existing 15-chapter book (baseline `00e99834`) remains the accepted book until the replacement is accepted.

## Purpose and reader outcomes

This is package documentation for `mountainash`. Readers write data logic once with a Polars-style expression and relation API, and it compiles to native Polars, to Narwhals-reached libraries (pandas, PyArrow, Dask, DuckDB and others) and to Ibis SQL engines. Schemas are Frictionless-aligned (`TableSchema`, `DataPackage`). Conformance, data contracts and a backend-agnostic validation engine sit on the same AST. A capability registry records what each backend and dialect can do.

Readers should be able to:

- install mountainash with the right extras and understand the lazy-import top-level namespace (`import mountainash as ma`);
- build expressions (`col`, `lit`, `when`, the namespaces and ternary logic with `t_col`) and relations (filter, join, group, window, set operations), then collect them on any supported backend through terminals and egress formats;
- pick an execution target and understand cross-backend operand transfer and cross-type joins;
- declare schemas with `TableSchema`, `FieldDefinition` and the canonical dtypes, read and write Frictionless descriptors, and extract schemas from dataframes, dataclasses and Pydantic models;
- conform data to a schema under a `ConformContract`, and report drift;
- declare data contracts, run validation and read the result and failure-case model, including foreign-key checks;
- orchestrate multi-table work with `RelationDAG` (dependency vs constraint edges, DataPackage round trip) and with pipelines (units, runner, checkpoints, resume);
- move data between Python objects and relations (ingress and egress);
- interpret capability errors and backend limits, and use `capability_policy` to adjust protection;
- extend or maintain the package. This covers:
  - the three-layer architecture (protocol, API builder, backend);
  - function keys and registries;
  - the expression and relation visitors;
  - the capability spine (segments, bootstrap, registry, gates);
  - the six-step workflow for adding an operation;
  - relation node and visit-handler registration;
  - dtype and schema adapters;
  - custom rules, ingress handlers and pipeline units.

## Audience coverage

All seven facets are served. They become reading paths through shared explanations, not one chapter per facet.

- **users** (core path). Covers the top-level namespace, expressions, relations, schemas and dtypes, conform, data contracts and validation, RelationDAG, pipelines, pydata ingress and egress, errors and capability policy.
- **maintainers, contributors, backend-architecture, extension-authors.** These are served by the internals depth of the same chapters plus an architecture and extension part, with no separate track. That part covers:
  - protocols as contracts;
  - dispatch through function keys and the operation registries;
  - the visitors;
  - backend composition by mixins;
  - the capability spine and per-dialect declarations;
  - execution planning and transfer;
  - the type system;
  - the graph kernel;
  - extension points;
  - conventions (naming prefixes, the typed error hierarchy, cross-backend testing with per-backend xfail).

  Internal-only modules (`relations.core`, `expressions.membership`, the capability declaration packages) are explained there, not on user pages.
- **executives-marketing and broader-hype.** These feed the home page and About page only. Every claim is backed by a runnable example or a test. Neither gets a chapter.

**Ecosystem context.** One short section early in the book places mountainash among its direct dependencies and extras, using only what `pyproject.toml` declares:
- `mountainash-transport` for remote resource I/O;
- `mountainash-files` and `mountainash-data` via the `ibis`, `files` and cloud extras;
- the `dbos` extra.

Later pages link to it at each boundary. Claims about sibling packages are limited to their public declarations.

## Scope and exclusions

**In scope:**
- Every public capability in the profile.
- The backend families and dialects the capability declarations name: Polars; Narwhals over pandas, PyArrow, Dask, DuckDB, Polars and lazy frames; Ibis over DuckDB, SQLite, PostgreSQL, MySQL, Polars, SingleStoreDB and Exasol. Each is stated with the support level the registry records.
- Optional extras and the base install.
- Documented behavioural limits where they affect correct use.
- The evolving status of pipelines and of the semi-public validation surface, stated plainly.

**Excluded:**
- Unimplemented roadmap work (for example Substrait plan import/export, semantic-layer interchange). A clearly labelled status note may mention it.
- Performance claims without a benchmark in the repository.
- Internal backlog IDs and private repository links.
- Storage-transport internals (owned by `mountainash-transport`).
- Upstream library tutorials (Polars, Ibis, Narwhals). Link to their official documentation instead.

**Prerequisites:** Python 3.12+, dataframe basics (columns, rows, joins, group-by) and basic typing. Lazy evaluation, ASTs, Substrait and three-valued logic are introduced where first needed.

## Depth and reading paths

Concepts, then package use, then internals. Chapter and section organisation is proposed fresh in the chapter plan. Users can stop after the use sections. Architecture, maintainer, contributor and extension readers continue into the internals sections and the architecture and extension part. Shared explanations are written once and linked, not repeated: build-then-compile, the three-layer model, ternary logic, capability gating and execution locations. Each page states its assumed starting point.

## Register

Package documentation: self-describing pages with no course preamble, learning objectives, "Key Takeaways" or recap sections. Licence statements follow the package licence (`Apache-2.0 AND MIT`, see `LICENSE`/`NOTICE`), not the old book's CC BY-NC-SA.

## Reuse

None. This is a rebuild from scratch. Old chapters, the course description, MicroSims, FAQ and learning graph are not reused as structure or prose. Facts come from the current source, profile, tests and principle documents. The old reader pages (`course-description.md`, the learning-graph pages and `sims/`) leave with the old book on acceptance. The canonical graph stays internal under `docs-site/learning-graph/`.

## Limitations and capability coverage

- An admonition appears at the point of use in each relevant section.
- One "Backend support and known limits" reference page is built from the generated capability coverage report (`core.capabilities` coverage/`render_markdown`). The generation command and source revision are stated on the page.
- No internal backlog IDs appear.

## Appendices

- **FAQ:** included (confirmed 2026-10-30).
- **Glossary:** included (confirmed 2026-10-30).

Both link to the relevant chapter or section explanations.

## Visual policy

Mermaid first. Planned diagrams:
- the three-layer architecture;
- the build → compile → collect flow;
- visitor dispatch;
- the capability spine (segments → bootstrap → registry → gates);
- execution locations and transfer;
- DAG dependency vs constraint edges;
- the pipeline plan/execute phases;
- the support matrix as a table.

MicroSims only when interaction adds explanatory value. A ternary truth-table explorer is the one candidate, to be decided in the chapter plan. No quizzes in the Mountainash workflow.

## Decisions recorded 2026-10-30 (user answers)

- **Rebuild.** The user approved a full replacement rebuild after the textbook-refresh check. The old baseline was `00e99834`, 1208 commits behind. Thirteen new modules have no chapter coverage. Chapter 12 teaches the removed pipelines API.
- **Facets.** As recommended: users get the core path; the four technical facets get internals depth plus an architecture and extension part; the two positioning facets feed the home and About pages only.
- **Reuse.** None.
- **Limitations.** Inline admonitions plus a generated support-matrix page.
- **Branch.** `docs/textbook-rebuild` from develop `0a625ad`, reviewed via PR into develop.

## Approval and open questions

- **Confirmed 2026-10-30:** the complete brief as drafted.
- **Open, deferred to the chapter plan:** whether the ternary truth-table MicroSim is included.
