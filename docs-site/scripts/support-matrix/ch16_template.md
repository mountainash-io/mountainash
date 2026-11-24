---
title: Backend support and known limits
---

# Backend support and known limits

mountainash records what each backend family and dialect can do in its capability registry, and records known cross-backend divergences in a generated catalogue. The package generates a coverage report from that registry, and this page computes its support matrix and divergence tables from that report and from the catalogue. Check a dialect here before you rely on an operation there; the errors and policy controls that act on these declarations are explained in [Capability errors and capability_policy](../09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy).

Assumes: [Backend capabilities, families and dialects](../09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

Generated from source revision 0a625ad (develop, 0a625ad1d1cc8b436b9fc66b027ac80fdff466ae); `src/`, `scripts/` and `tests/` are identical at this book's branch head. Regenerate the page from the repository root with an output directory outside the repository:

```text
docs-site/scripts/support-matrix/generate.sh OUTDIR
```

The script runs the package's own generators, `python -m mountainash.core.capabilities.render_markdown --output OUTDIR` (the coverage report: `expression-coverage.md`, `expression-coverage-scoped.md` and `expression-coverage.json` under `OUTDIR/docs/reference/`) and `scripts/generate_divergences_catalog.py` (the divergences catalogue). It then computes every table on this page from `expression-coverage.json` and from the catalogue's entry headings, copies the counts as computed, and rewrites this page. The script edits message text in two ways only, to fit tables: it turns dashes into semicolons and strips internal tracker references.

## Support matrix

<!-- concept:523 -->
The support matrix crosses the operations mountainash registers with the backend families and dialects named in its capability declarations. Each family implements every registered operation, and the declarations then describe each dialect. The report keeps three kinds of input apart:

- Implementation discovery: which operations a family's backend implements.
- Information records: descriptive statements, at the native layer (what the engine itself does) or the public layer (what mountainash offers). Each has a level. `unsupported` marks an operation, parameter or option value the dialect lacks; `literal only` means the argument must be a literal value; `polymorphic` means it accepts a literal collection or an expression; `expression-capable` states explicitly that the dialect accepts expressions. Most native records describe a single option value, such as one Substrait overflow or rounding mode.
- Policies: executable rules. A gate raises `BackendCapabilityError` before the call runs; the other policies enrich native errors or protect conformed results, as listed in [Backend capabilities, families and dialects](../09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

An operation with no record for a dialect has unknown support. The "Cross-backend test suite" column comes from the backend registry in `tests/fixtures/backend_registry.py`, and mountainash's own detection maps each test backend to its dialect. "Full suite" dialects run the cross-backend tests; "transfer matrix only" dialects take part as sources and destinations of operand transfer; for the remaining dialects, the declarations are the evidence of support. Information cells read unsupported / literal only / polymorphic / expression-capable.

<!-- BEGIN GENERATED: dialect summary from expression-coverage.json and tests/fixtures/backend_registry.py -->
{{dialects}}
<!-- END GENERATED -->

Family-wide rows apply to every dialect of the family; a dialect row adds to them. A policy whose "Applies when" column names package or engine versions (for example the Ibis, SQLGlot and PostgreSQL versions on two PostgreSQL gates) acts when the running environment matches those versions.

### Implementation discovery

<!-- BEGIN GENERATED: implementation discovery from expression-coverage.json -->
{{implementation}}
<!-- END GENERATED -->

A dedicated handler dispatches each "Implemented via handler" operation in place of an expression-system method.

### Coverage by operation domain

Each cell counts information records and gate refusals for one domain across all of a family's scopes. Domains follow the operation's key family; "unclassified" collects the key families the report leaves without a domain.

<!-- BEGIN GENERATED: domain coverage from expression-coverage.json -->
{{domains}}
<!-- END GENERATED -->

### Policies by dialect

Every executable policy, grouped by dialect. A condition of "always" applies to every call of the operation; any other condition applies to the calls whose arguments match it. Each operation appears as the function key that a `BackendCapabilityError` reports.

<!-- BEGIN GENERATED: policies by dialect from expression-coverage.json -->
{{policies}}
<!-- END GENERATED -->

The full report also lists every information record with its selector, message and source module. At this revision `expression-coverage.md` is {{full_md_lines}} lines, `expression-coverage-scoped.md` {{full_scoped_lines}} lines and `expression-coverage.json` {{full_json_lines}} lines; the command above regenerates it.

## Known divergences

<!-- concept:524 -->
A known divergence is a recorded case where the same expression or relation fails or gives a different result on some backend. The package's consistency rule is that one plan produces the same logical result on every backend that supports it. Where an engine departs from that, mountainash declares the difference, and where the declaration is a gate, the gate refuses the call before it runs. The divergences catalogue joins authored illustrations to the matching catalogue declarations. The catalogue describes its illustrations as render-only examples: they are neither executable tests nor newly verified observations, and they establish no version range.

Most catalogued divergences are refusals or errors. A smaller number silently return different values, and these need the most care. Examples from the catalogue include "sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges", "str.replace_slice() returns input unchanged." on Narwhals over pandas and Polars, and "Cyclic calculations and hash bucketing with negative dividends diverge" on Ibis DuckDB and SQLite, where the remainder takes the sign of the dividend.

<!-- BEGIN GENERATED: divergence summary from known-divergences.md -->
{{divergences_summary}}
<!-- END GENERATED -->

An illustration names one operation; a description can cover several. The descriptions for each scope, with the number of distinct operations each illustrates:

<!-- BEGIN GENERATED: divergence descriptions from known-divergences.md -->
{{divergences_details}}
<!-- END GENERATED -->

The catalogue also lists, for each illustration, its input data, reference and contrasting results, the catalogue descriptions with their workarounds and source modules, and any upstream issue references. At this revision it is {{catalogue_lines}} lines.
