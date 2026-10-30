---
title: Backend support and known limits
---

# Backend support and known limits

mountainash records what each backend family and dialect can do in its capability registry, and the cross-backend divergences it knows of in a generated catalogue. The support matrix and divergence tables below are computed from the coverage report the package generates from that registry and from the catalogue. Check a dialect here before relying on an operation there; the errors and policy controls that act on these declarations are described in [Capability errors and capability_policy](../09-execution-targets-and-capabilities/index.md#capability-errors-and-capability_policy).

Assumes: [Backend capabilities, families and dialects](../09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

Generated from source revision 0a625ad (develop, 0a625ad1d1cc8b436b9fc66b027ac80fdff466ae); `src/`, `scripts/` and `tests/` are identical at this book's branch head. Regenerate the page from the repository root with an output directory outside the repository:

```text
docs-site/scripts/support-matrix/generate.sh OUTDIR
```

The script runs the package's own generators, `python -m mountainash.core.capabilities.render_markdown --output OUTDIR` (the coverage report: `expression-coverage.md`, `expression-coverage-scoped.md` and `expression-coverage.json` under `OUTDIR/docs/reference/`) and `scripts/generate_divergences_catalog.py` (the divergences catalogue). It then computes every table on this page from `expression-coverage.json` and from the catalogue's entry headings, with counts copied as computed, and rewrites this page. The only text changes are formatting for tables: dashes become semicolons and internal tracker references are removed from messages.

## Support matrix

<!-- concept:523 -->
The support matrix crosses the operations mountainash registers with the backend families and dialects named in its capability declarations. Each family implements every registered operation; what differs is what the declarations say about each dialect. The report keeps three kinds of input apart:

- Implementation discovery: whether a family's backend implements an operation at all.
- Information records: descriptive statements, at the native layer (what the engine itself does) or the public layer (what mountainash offers). Each has a level. `unsupported` means the operation, parameter or option value is not available; `literal only` means the argument must be a literal value, not an expression; `polymorphic` means it accepts a literal collection or an expression; `expression-capable` is an explicit dialect-level statement that expressions are accepted. Most native records concern single option values, such as one Substrait overflow or rounding mode, rather than whole operations.
- Policies: executable rules. A gate refusal raises `BackendCapabilityError` before the call runs; the other policies enrich native errors or protect conformed results, as listed in [Backend capabilities, families and dialects](../09-execution-targets-and-capabilities/index.md#backend-capabilities-families-and-dialects).

A missing record means unknown, not supported. The "Cross-backend test suite" column is read from the backend registry in `tests/fixtures/backend_registry.py`, with each test backend mapped to its dialect by mountainash's own detection. "Full suite" dialects run the cross-backend tests; "transfer matrix only" dialects are exercised only as sources and destinations of operand transfer; for the rest, support rests on the declarations alone. Information cells read unsupported / literal only / polymorphic / expression-capable.

<!-- BEGIN GENERATED: dialect summary from expression-coverage.json and tests/fixtures/backend_registry.py -->
{{dialects}}
<!-- END GENERATED -->

Family-wide rows apply to every dialect of the family; a dialect row adds to them. Policies whose "Applies when" column names package or engine versions (for example the Ibis, SQLGlot and PostgreSQL versions on two PostgreSQL gates) act only when the running environment matches.

### Implementation discovery

<!-- BEGIN GENERATED: implementation discovery from expression-coverage.json -->
{{implementation}}
<!-- END GENERATED -->

"Implemented via handler" operations are dispatched by a dedicated handler rather than an expression-system method.

### Coverage by operation domain

Each cell counts information records and gate refusals for one domain across all of a family's scopes. Domains follow the operation's key family; "unclassified" collects key families the report does not assign to a domain.

<!-- BEGIN GENERATED: domain coverage from expression-coverage.json -->
{{domains}}
<!-- END GENERATED -->

### Policies by dialect

Every executable policy, grouped by dialect. A condition of "always" applies to every call of the operation; otherwise the rule applies only to calls whose arguments match. The operation is shown as the function key that a `BackendCapabilityError` reports.

<!-- BEGIN GENERATED: policies by dialect from expression-coverage.json -->
{{policies}}
<!-- END GENERATED -->

The full report also lists every information record with its selector, message and source module. At this revision `expression-coverage.md` is {{full_md_lines}} lines, `expression-coverage-scoped.md` {{full_scoped_lines}} lines and `expression-coverage.json` {{full_json_lines}} lines; regenerate it with the command above for that detail.

## Known divergences

<!-- concept:524 -->
A known divergence is a case where the same expression or relation fails or gives a different result on some backend, recorded instead of hidden. The package's consistency rule is that one plan produces the same logical result on every backend that supports it; where an engine cannot, the difference is declared, and where a declaration makes it a gate the call is refused instead of run. The divergences catalogue joins authored illustrations to the matching catalogue declarations. The catalogue itself states that its illustrations are render-only examples, not executable tests or newly verified observations, and that no version range is established by them.

Most catalogued divergences are refusals or errors. A smaller number change values without an error, and these need the most care. Examples from the catalogue include "sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges", "str.replace_slice() returns input unchanged." on Narwhals over pandas and Polars, and "Cyclic calculations and hash bucketing with negative dividends diverge" on Ibis DuckDB and SQLite, where the remainder takes the sign of the dividend.

<!-- BEGIN GENERATED: divergence summary from known-divergences.md -->
{{divergences_summary}}
<!-- END GENERATED -->

An illustration names one operation; a description can cover several. The descriptions for each scope, with the number of distinct operations each illustrates:

<!-- BEGIN GENERATED: divergence descriptions from known-divergences.md -->
{{divergences_details}}
<!-- END GENERATED -->

The catalogue also lists, for each illustration, its input data, reference and contrasting results, the catalogue descriptions with their workarounds and source modules, and any upstream issue references. At this revision it is {{catalogue_lines}} lines.
