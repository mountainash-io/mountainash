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
| Family | Dialect | Cross-backend test suite | Declaration segments | Native information | Public information | Gate refusals | Other policies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| polars | family-wide | n/a | 8 | 0 / 0 / 0 / 0 | 1 / 12 / 3 / 0 | 0 | 0 |
| polars | polars | full suite | 3 | 197 / 0 / 0 / 17 | 3 / 0 / 0 / 32 | 0 | 0 |
| narwhals | family-wide | n/a | 13 | 31 / 4 / 3 / 0 | 1 / 0 / 0 / 0 | 0 | 0 |
| narwhals | narwhals-dask | not in test registry | 4 | 0 / 0 / 0 / 0 | 1 / 0 / 0 / 0 | 14 | materialization error 1 |
| narwhals | narwhals-duckdb | not in test registry | 4 | 5 / 0 / 0 / 0 | 1 / 0 / 0 / 0 | 19 | materialization error 1 |
| narwhals | narwhals-lazy | full suite | 10 | 12 / 0 / 0 / 5 | 0 / 0 / 0 / 0 | 14 | 0 |
| narwhals | narwhals-pandas | full suite | 15 | 273 / 28 / 0 / 33 | 0 / 0 / 0 / 0 | 33 | materialization error 4, result protection 2 |
| narwhals | narwhals-polars | full suite | 12 | 249 / 0 / 0 / 35 | 0 / 0 / 0 / 0 | 14 | immediate error 1, result protection 2 |
| narwhals | narwhals-pyarrow | transfer matrix only | 4 | 5 / 1 / 0 / 0 | 1 / 0 / 0 / 0 | 20 | 0 |
| ibis | family-wide | n/a | 13 | 189 / 16 / 61 / 0 | 7 / 0 / 0 / 0 | 0 | 0 |
| ibis | ibis-duckdb | full suite | 16 | 10 / 0 / 0 / 31 | 0 / 0 / 0 / 0 | 1 | result protection 2 |
| ibis | ibis-exasol | not in test registry | 3 | 0 / 0 / 0 / 0 | 2 / 0 / 0 / 0 | 4 | 0 |
| ibis | ibis-mysql | not in test registry | 2 | 0 / 0 / 0 / 0 | 1 / 0 / 0 / 0 | 3 | 0 |
| ibis | ibis-polars | transfer matrix only | 12 | 29 / 6 / 0 / 1 | 1 / 0 / 0 / 0 | 0 | result protection 2 |
| ibis | ibis-postgres | not in test registry | 3 | 1 / 0 / 0 / 0 | 1 / 0 / 0 / 0 | 3 | 0 |
| ibis | ibis-singlestoredb | not in test registry | 2 | 0 / 0 / 0 / 0 | 1 / 0 / 0 / 0 | 3 | 0 |
| ibis | ibis-sqlite | full suite | 18 | 83 / 0 / 0 / 1 | 0 / 0 / 1 / 0 | 2 | materialization error 1 |
<!-- END GENERATED -->

Family-wide rows apply to every dialect of the family; a dialect row adds to them. A policy whose "Applies when" column names package or engine versions (for example the Ibis, SQLGlot and PostgreSQL versions on two PostgreSQL gates) acts when the running environment matches those versions.

### Implementation discovery

<!-- BEGIN GENERATED: implementation discovery from expression-coverage.json -->
Registered operations: 344

| Family | implemented | implemented via handler | not implemented | unknown |
| --- | --- | --- | --- | --- |
| polars | 341 | 3 | 0 | 0 |
| narwhals | 341 | 3 | 0 | 0 |
| ibis | 341 | 3 | 0 | 0 |
<!-- END GENERATED -->

A dedicated handler dispatches each "Implemented via handler" operation in place of an expression-system method.

### Coverage by operation domain

Each cell counts information records and gate refusals for one domain across all of a family's scopes. Domains follow the operation's key family; "unclassified" collects the key families the report leaves without a domain.

<!-- BEGIN GENERATED: domain coverage from expression-coverage.json -->
| Domain | Registered operations | polars: information / gate refusals | narwhals: information / gate refusals | ibis: information / gate refusals |
| --- | --- | --- | --- | --- |
| aggregate | 17 | 0 / 0 | 1 / 0 | 1 / 0 |
| arithmetic | 34 | 152 / 0 | 304 / 0 | 162 / 0 |
| boolean | 7 | 0 / 0 | 0 / 0 | 1 / 0 |
| cast | 1 | 0 / 0 | 1 / 0 | 0 / 0 |
| categorical | 1 | 0 / 0 | 3 / 0 | 1 / 0 |
| comparison | 23 | 0 / 0 | 0 / 0 | 0 / 0 |
| conditional | 1 | 0 / 0 | 0 / 0 | 0 / 0 |
| datetime | 67 | 7 / 0 | 55 / 0 | 115 / 0 |
| geospatial | 3 | 0 / 0 | 5 / 0 | 8 / 0 |
| list | 44 | 0 / 0 | 27 / 0 | 17 / 0 |
| null | 3 | 0 / 0 | 0 / 0 | 0 / 0 |
| relation | 30 | 1 / 0 | 4 / 1 | 4 / 9 |
| rounding | 3 | 0 / 0 | 0 / 0 | 0 / 0 |
| set | 3 | 2 / 0 | 2 / 0 | 2 / 0 |
| string | 46 | 102 / 0 | 228 / 2 | 121 / 2 |
| struct | 2 | 0 / 0 | 5 / 0 | 4 / 0 |
| ternary | 24 | 1 / 0 | 1 / 0 | 1 / 0 |
| unclassified | 10 | 0 / 0 | 0 / 0 | 0 / 0 |
| value | 4 | 0 / 0 | 8 / 5 | 5 / 5 |
| window | 21 | 0 / 0 | 44 / 106 | 0 / 0 |
<!-- END GENERATED -->

### Policies by dialect

Every executable policy, grouped by dialect. A condition of "always" applies to every call of the operation; any other condition applies to the calls whose arguments match it. Each operation appears as the function key that a `BackendCapabilityError` reports.

<!-- BEGIN GENERATED: policies by dialect from expression-coverage.json -->
??? note "narwhals-dask (gate refusals: 14; other policies: 1)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `RKEY_SUBSTRAIT_REL.FETCH` | gate / block | `has_offset` eq `True` and `offset` is set | any version | Positive-offset slicing on Narwhals/Dask is unsupported because native offset construction can evaluate source rows before a terminal. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `RKEY_MOUNTAINASH_REL.IMPORT_INTO` | materialization error / enrich | always | any version | a lazy-only Narwhals implementation cannot import an eager Arrow table |

??? note "narwhals-duckdb (gate refusals: 19; other policies: 1)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | narwhals==2.27.1, duckdb==1.5.6 | Mountainash has no Narwhals DuckDB Decimal conversion implementation; rounding and non-strict cast limitations are tracked by narwhals#3698 and #3702. |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals duckdb cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `FKEY_MOUNTAINASH_WINDOW.RANK_MAX` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals duckdb cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals duckdb cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.RANK` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals duckdb cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals duckdb cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `RKEY_MOUNTAINASH_REL.IMPORT_INTO` | materialization error / enrich | always | any version | a lazy-only Narwhals implementation cannot import an eager Arrow table |

??? note "narwhals-lazy (gate refusals: 14; other policies: 0)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | any version | Narwhals cannot express decimal casts natively: no round mode (narwhals#3698) and no non-strict cast (narwhals#3702). |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |

??? note "narwhals-pandas (gate refusals: 33; other policies: 6)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS` | gate / block | always | narwhals==2.27.1, pandas==3.0.6 | Narwhals pandas regex matching requires a literal pattern; per-row patterns are unsupported. |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | any version | Narwhals cannot express decimal casts natively: no round mode (narwhals#3698) and no non-strict cast (narwhals#3702). |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pandas cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `FKEY_MOUNTAINASH_WINDOW.RANK_MAX` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pandas cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pandas cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.multi_key` eq `True` | narwhals==2.27.1, pandas==3.0.6; narwhals==2.27.1, pandas==3.1.0 | Narwhals pandas-like orders multi-key windows by the last key only. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.RANK` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pandas cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pandas cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION` | result protection / detect non null to null | always | any version | Invalid XSD duration lexicals silently become null during native parsing. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE` | result protection / detect non null to null | always | any version | Invalid XSD partial-date lexicals silently become null during native parsing. |
    | `FKEY_MOUNTAINASH_SCALAR_LIST.CONTAINS` | materialization error / enrich | always | any version | Narwhals pandas list membership requires Arrow-backed list storage. |
    | `FKEY_MOUNTAINASH_SCALAR_LIST.PARSE` | materialization error / enrich | always | any version | Narwhals list parsing requires Arrow-backed pandas string storage. |
    | `FKEY_MOUNTAINASH_SCALAR_LIST.T_CONTAINS` | materialization error / enrich | always | any version | Narwhals pandas ternary list membership requires Arrow-backed list storage. |
    | `FKEY_SUBSTRAIT_SCALAR_STRING.SPLIT` | materialization error / enrich | always | any version | Narwhals string splitting requires Arrow-backed pandas string storage. |

??? note "narwhals-polars (gate refusals: 14; other policies: 3)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | any version | Narwhals cannot express decimal casts natively: no round mode (narwhals#3698) and no non-strict cast (narwhals#3702). |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION` | result protection / detect non null to null | always | any version | Invalid XSD duration lexicals silently become null during native parsing. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE` | result protection / detect non null to null | always | any version | Invalid XSD partial-date lexicals silently become null during native parsing. |
    | `FKEY_MOUNTAINASH_SCALAR_LIST.GET` | immediate error / enrich | always | any version | Narwhals list.get() and list.last() do not support negative indices. |

??? note "narwhals-pyarrow (gate refusals: 20; other policies: 0)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS` | gate / block | always | narwhals==2.27.1, pyarrow==26.0.0 | Narwhals PyArrow regex matching requires a literal pattern; per-row patterns are unsupported. |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | narwhals==2.27.1, pyarrow==26.0.0 | Mountainash has no Narwhals PyArrow Decimal conversion implementation; rounding and non-strict cast limitations are tracked by narwhals#3698 and #3702. |
    | `FKEY_MOUNTAINASH_WINDOW.BACKWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_COUNT` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MAX` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_MIN` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_PROD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.CUM_SUM` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.DIFF` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.FORWARD_FILL` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `FKEY_MOUNTAINASH_WINDOW.RANK_AVERAGE` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pyarrow cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `FKEY_MOUNTAINASH_WINDOW.RANK_MAX` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pyarrow cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.DENSE_RANK` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pyarrow cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.FIRST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAG` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LAST_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.LEAD` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.NTH_VALUE` | gate / block | `__window__.any_descending` eq `True` | any version | Narwhals .over(order_by=...) has no sort direction; descending window order is unsupported. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.RANK` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pyarrow cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |
    | `SUBSTRAIT_ARITHMETIC_WINDOW.ROW_NUMBER` | gate / block | `__window__.multi_key` eq `True` | any version | Narwhals pyarrow cannot rank by several sort keys: .over(partition) accepts only elementary expressions. |

??? note "ibis-duckdb (gate refusals: 1; other policies: 2)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `RKEY_MOUNTAINASH_REL.SAMPLE` | gate / block | `n` is set and `seed` is set | any version | Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION` | result protection / detect non null to null | always | any version | Detect invalid XSD duration lexical values that the native parser converts from non-null input to null. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE` | result protection / detect non null to null | always | any version | Detect invalid XSD partial-date lexical values that the native parser converts from non-null input to null. |

??? note "ibis-exasol (gate refusals: 4; other policies: 0)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS` | gate / block | always | ibis-framework==12.0.0 | Ibis 12.0.0 Exasol lacks RegexSearch translation for literal and dynamic regex patterns. |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | ibis-framework==12.0.0 | Ibis 12.0.0 Exasol lacks RegexReplace translation required by Decimal text normalization. |
    | `RKEY_MOUNTAINASH_REL.IMPORT_INTO` | gate / block | always | any version | owned temporary-table adoption is unsupported on this SQL dialect |
    | `RKEY_MOUNTAINASH_REL.SAMPLE` | gate / block | `n` is set and `seed` is set | any version | Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported. |

??? note "ibis-mysql (gate refusals: 3; other policies: 0)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | ibis-framework==12.0.0 | Ibis 12.0.0 MySQL lacks RegexReplace translation required by Decimal text normalization. |
    | `RKEY_MOUNTAINASH_REL.IMPORT_INTO` | gate / block | always | any version | owned temporary-table adoption is unsupported on this SQL dialect |
    | `RKEY_MOUNTAINASH_REL.SAMPLE` | gate / block | `n` is set and `seed` is set | any version | Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported. |

??? note "ibis-polars (gate refusals: 0; other policies: 2)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_DURATION` | result protection / detect non null to null | always | any version | Detect invalid XSD duration lexical values that the native parser converts from non-null input to null. |
    | `FKEY_MOUNTAINASH_SCALAR_DATETIME.PARSE_XSD_PARTIAL_DATE` | result protection / detect non null to null | always | any version | Detect invalid XSD partial-date lexical values that the native parser converts from non-null input to null. |

??? note "ibis-postgres (gate refusals: 3; other policies: 0)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_STRING.REGEX_CONTAINS` | gate / block | `case_sensitivity` eq `CASE_INSENSITIVE` and `pattern` is dynamic | ibis-framework==12.0.0, sqlglot==29.0.1, postgres==16.15 | Ibis 12.0.0 with SQLGlot 29.0.1 on PostgreSQL 16.15 loses pattern-concatenation grouping for dynamic case-insensitive regex matching. |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | `failure_behavior` eq `null` | ibis-framework==12.0.0, sqlglot==29.0.1, postgres==16.15 | Ibis 12.0.0 with SQLGlot 29.0.1 on PostgreSQL 16.15 lowers TryCast to a strict cast; Decimal failure_behavior='null' cannot return null for invalid text. This mode is refused even for valid inputs; use failure_behavior='throw' for strict conversion. |
    | `RKEY_MOUNTAINASH_REL.SAMPLE` | gate / block | `n` is set and `seed` is set | any version | Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported. |

??? note "ibis-singlestoredb (gate refusals: 3; other policies: 0)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | ibis-framework==12.0.0 | Ibis 12.0.0 SingleStoreDB lacks RegexReplace translation required by Decimal text normalization. |
    | `RKEY_MOUNTAINASH_REL.IMPORT_INTO` | gate / block | always | any version | owned temporary-table adoption is unsupported on this SQL dialect |
    | `RKEY_MOUNTAINASH_REL.SAMPLE` | gate / block | `n` is set and `seed` is set | any version | Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported. |

??? note "ibis-sqlite (gate refusals: 2; other policies: 1)"

    | Operation | Consumer / action | Condition | Applies when | Message |
    | --- | --- | --- | --- | --- |
    | `FKEY_MOUNTAINASH_SCALAR_VALUE.DECIMAL_CAST` | gate / block | always | any version | SQLite has no fixed-precision decimal type; Ibis lowers decimal to REAL. |
    | `RKEY_MOUNTAINASH_REL.SAMPLE` | gate / block | `n` is set and `seed` is set | any version | Ibis exact-count sampling with a seed is unsupported; omit seed or use fractional sampling where supported. |
    | `RKEY_MOUNTAINASH_REL.IMPORT_INTO` | materialization error / enrich | always | any version | SQLite cannot store IEEE NaN (stored as NULL), bind non-null Decimal values, or hold nested types; an owned table copy also cannot hold a decimal column |
<!-- END GENERATED -->

The full report also lists every information record with its selector, message and source module. At this revision `expression-coverage.md` is 2086 lines, `expression-coverage-scoped.md` 1562 lines and `expression-coverage.json` 172878 lines; the command above regenerates it.

## Known divergences

<!-- concept:524 -->
A known divergence is a recorded case where the same expression or relation fails or gives a different result on some backend. The package's consistency rule is that one plan produces the same logical result on every backend that supports it. Where an engine departs from that, mountainash declares the difference, and where the declaration is a gate, the gate refuses the call before it runs. The divergences catalogue joins authored illustrations to the matching catalogue declarations. The catalogue describes its illustrations as render-only examples: they are neither executable tests nor newly verified observations, and they establish no version range.

Most catalogued divergences are refusals or errors. A smaller number silently return different values, and these need the most care. Examples from the catalogue include "sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges", "str.replace_slice() returns input unchanged." on Narwhals over pandas and Polars, and "Cyclic calculations and hash bucketing with negative dividends diverge" on Ibis DuckDB and SQLite, where the remainder takes the sign of the dividend.

<!-- BEGIN GENERATED: divergence summary from known-divergences.md -->
Illustrated divergences: 455

| Family | Scope | Illustrations | Distinct descriptions |
| --- | --- | --- | --- |
| polars | family-wide | 5 | 5 |
| polars | polars | 1 | 1 |
| narwhals | family-wide | 23 | 20 |
| narwhals | narwhals-duckdb | 5 | 5 |
| narwhals | narwhals-lazy | 46 | 9 |
| narwhals | narwhals-pandas | 85 | 48 |
| narwhals | narwhals-polars | 84 | 15 |
| narwhals | narwhals-pyarrow | 5 | 5 |
| ibis | family-wide | 6 | 5 |
| ibis | ibis-duckdb | 60 | 16 |
| ibis | ibis-polars | 78 | 15 |
| ibis | ibis-sqlite | 57 | 26 |
<!-- END GENERATED -->

An illustration names one operation; a description can cover several. The descriptions for each scope, with the number of distinct operations each illustrates:

<!-- BEGIN GENERATED: divergence descriptions from known-divergences.md -->
??? note "polars, family-wide (descriptions: 5)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | The multi-column projection raises ShapeError on eager and lazy Polars. | 1 |
    | The null-safe ternary composition raises on the marked provider. | 1 |
    | ma.col(x).cbrt() on negative inputs yields NaN across all backends | 1 |
    | ma.corr() raises on all backends except ibis-polars | 1 |
    | nth_value().over() raises on eager and lazy Polars | 1 |

??? note "polars (descriptions: 1)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | Zero-width-capable regexp split differs from ibis-duckdb on polars. | 1 |

??? note "narwhals, family-wide (descriptions: 20)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | backward_fill() with descending window order is refused on Narwhals | 1 |
    | cum_count() with descending window order is refused on Narwhals | 1 |
    | cum_max() with descending window order is refused on Narwhals | 1 |
    | cum_min() with descending window order is refused on Narwhals | 1 |
    | cum_prod() with descending window order is refused on Narwhals | 1 |
    | cum_sum() with descending window order is refused on Narwhals | 1 |
    | diff() with descending window order is refused on Narwhals | 1 |
    | dt.week_of_year() raises on pandas and all narwhals backends | 1 |
    | first_value() with descending window order is refused on Narwhals | 1 |
    | forward_fill() with descending window order is refused on Narwhals | 1 |
    | lag() with descending window order is refused on Narwhals | 1 |
    | last_value() with descending window order is refused on Narwhals | 1 |
    | lead() with descending window order is refused on Narwhals | 1 |
    | ma.col(x).cbrt() on negative inputs yields NaN across all backends | 1 |
    | ma.col(x).cot() raises on pandas and all narwhals backends | 1 |
    | ma.corr() raises on all backends except ibis-polars | 1 |
    | nth_value() with descending window order is refused on Narwhals | 1 |
    | ntile() is unsupported off Polars | 1 |
    | percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals | 4 |
    | scalar_expr.over(...) raises off Polars | 1 |

??? note "narwhals-duckdb (descriptions: 5)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | dense_rank() with several sort keys is refused on narwhals-duckdb | 1 |
    | rank() with several sort keys is refused on narwhals-duckdb | 1 |
    | rank(method='average') with several sort keys is refused on narwhals-duckdb | 1 |
    | rank(method='max') with several sort keys is refused on narwhals-duckdb | 1 |
    | row_number() with several sort keys is refused on narwhals-duckdb | 1 |

??? note "narwhals-lazy (descriptions: 9)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | Directional trimming over-strips both ends. | 2 |
    | NULL-on-cast-failure cannot materialize on the marked provider. | 1 |
    | Relation.join_asof(tolerance=...) raises BackendCapabilityError on all narwhals-family dialects, including the 'pandas' test backend | 1 |
    | Relation.pivot() raises on all ibis backends and narwhals-lazy; polars and eager narwhals compute it | 1 |
    | Relation.with_row_index() raises on narwhals-lazy; eager narwhals/polars and ibis-duckdb/ibis-sqlite assign a 0..N-1 index | 1 |
    | conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them | 1 |
    | mode() and any_value() raise on narwhals-lazy | 2 |
    | ntile() is unsupported off Polars | 1 |
    | order-dependent window operations raise on narwhals-lazy | 11 |

??? note "narwhals-pandas (descriptions: 48)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | A null input row yields False rather than propagating null. | 3 |
    | Columnar literal contains raises on pandas and ibis-polars. | 1 |
    | Directional trimming over-strips both ends. | 2 |
    | NULL-on-cast-failure cannot materialize on the marked provider. | 1 |
    | Pandas-backed integer casts raise and boolean casts can map None to False. | 1 |
    | Relation greatest()/least() diverge on pandas/narwhals-pandas; polars/narwhals-polars and ibis agree | 2 |
    | Relation.join_asof() with null keys raises on narwhals-pandas and the 'pandas' test backend; polars/narwhals-polars/narwhals-lazy/ibis compute no-match rows | 1 |
    | Relation.join_asof(strategy='nearest') on narwhals-pandas/'pandas' may select a different (but still equally-near) right row than Polars when the right frame has duplicate keys at the winning distance | 1 |
    | Relation.join_asof(tolerance=...) raises BackendCapabilityError on all narwhals-family dialects, including the 'pandas' test backend | 1 |
    | The null-safe ternary composition raises on the marked provider. | 1 |
    | backward_fill() with a multi-key window order is refused on narwhals-pandas | 1 |
    | conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them | 1 |
    | conform() with a dotted struct source path raises on pandas/narwhals-pandas/ibis-sqlite; polars and ibis-duckdb/ibis-polars extract it | 1 |
    | cum_count() with a multi-key window order is refused on narwhals-pandas | 1 |
    | cum_max() with a multi-key window order is refused on narwhals-pandas | 1 |
    | cum_min() with a multi-key window order is refused on narwhals-pandas | 1 |
    | cum_prod() with a multi-key window order is refused on narwhals-pandas | 1 |
    | cum_sum() with a multi-key window order is refused on narwhals-pandas | 1 |
    | datetime enrichment operations raise on pandas/narwhals | 4 |
    | dense_rank() with several sort keys is refused on narwhals-pandas | 1 |
    | diff() with a multi-key window order is refused on narwhals-pandas | 1 |
    | dt.date() raises on narwhals-pandas | 1 |
    | dt.date() raises on pandas and narwhals-pandas | 1 |
    | dt.time() raises on narwhals-polars/narwhals-pandas | 1 |
    | dt.week_of_year() raises on pandas and all narwhals backends | 1 |
    | first_value() with a multi-key window order is refused on narwhals-pandas | 1 |
    | forward_fill() with a multi-key window order is refused on narwhals-pandas | 1 |
    | initcap() differs from Polars on sharp-S and ligature inputs. | 1 |
    | lag() with a multi-key window order is refused on narwhals-pandas | 1 |
    | last_value() with a multi-key window order is refused on narwhals-pandas | 1 |
    | lead() with a multi-key window order is refused on narwhals-pandas | 1 |
    | ma.col(x).cbrt() on negative inputs yields NaN across all backends | 1 |
    | ma.col(x).cot() raises on pandas and all narwhals backends | 1 |
    | ma.corr() raises on all backends except ibis-polars | 1 |
    | nth_value() with a multi-key window order is refused on narwhals-pandas | 1 |
    | ntile() is unsupported off Polars | 1 |
    | percent_rank/cume_dist/nth_value and diff(n>1) raise on pandas/narwhals | 4 |
    | rank() with several sort keys is refused on narwhals-pandas | 1 |
    | rank(method='average') with several sort keys is refused on narwhals-pandas | 1 |
    | rank(method='max') with several sort keys is refused on narwhals-pandas | 1 |
    | row_number() with several sort keys is refused on narwhals-pandas | 1 |
    | scalar_expr.over(...) raises off Polars | 1 |
    | str.center() raises on the marked providers. | 1 |
    | str.repeat() raises on the marked providers. | 1 |
    | str.replace_slice() returns input unchanged. | 1 |
    | title() differs from Polars on sharp-S and ligature inputs. | 1 |
    | trig, angular, and hyperbolic functions raise on pandas/narwhals | 15 |
    | validation outcome-model tests expecting an 'unknown' verdict from a null comparison diverge on pandas/narwhals-pandas | 1 |

??? note "narwhals-polars (descriptions: 15)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | Directional trimming over-strips both ends. | 2 |
    | NULL-on-cast-failure cannot materialize on the marked provider. | 1 |
    | Relation.join_asof(tolerance=...) raises BackendCapabilityError on all narwhals-family dialects, including the 'pandas' test backend | 1 |
    | Relation.unnest() raises on narwhals backends; polars and ibis compute it | 1 |
    | The listed list operation raises on narwhals-polars. | 21 |
    | an opaque-carrier structured field (no schema evidence, already-native Python container) fails to decode through logical egress when the source is a Narwhals-wrapped Polars frame | 2 |
    | conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them | 1 |
    | datetime enrichment operations raise on pandas/narwhals | 4 |
    | dt.time() raises on narwhals-polars/narwhals-pandas | 1 |
    | list.explode raises on narwhals-polars. | 1 |
    | ntile() is unsupported off Polars | 1 |
    | str.center() raises on the marked providers. | 1 |
    | str.repeat() raises on the marked providers. | 1 |
    | str.replace_slice() returns input unchanged. | 1 |
    | trig, angular, and hyperbolic functions raise on pandas/narwhals | 15 |

??? note "narwhals-pyarrow (descriptions: 5)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | dense_rank() with several sort keys is refused on narwhals-pyarrow | 1 |
    | rank() with several sort keys is refused on narwhals-pyarrow | 1 |
    | rank(method='average') with several sort keys is refused on narwhals-pyarrow | 1 |
    | rank(method='max') with several sort keys is refused on narwhals-pyarrow | 1 |
    | row_number() with several sort keys is refused on narwhals-pyarrow | 1 |

??? note "ibis, family-wide (descriptions: 5)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | cum_prod() raises on all Ibis backends | 1 |
    | ma.col(x).cbrt() on negative inputs yields NaN across all backends | 1 |
    | ntile() is unsupported off Polars | 1 |
    | rank(method='average'\|'max') raises on Ibis | 2 |
    | scalar_expr.over(...) raises off Polars | 1 |

??? note "ibis-duckdb (descriptions: 16)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | Chained boolean parity via xor diverges on ibis-duckdb | 1 |
    | Cyclic calculations and hash bucketing with negative dividends diverge | 1 |
    | Projections whose column is entirely null raise a type resolution error | 1 |
    | Relation.cross_join() raises on ibis-duckdb/ibis-sqlite; polars/narwhals and ibis-polars compute it | 1 |
    | Relation.filter() with certain compound boolean predicates may return rows in a different order than the input on ibis-duckdb; matched VALUES are always correct, only row position differs | 1 |
    | Relation.join_asof(by=...) on ibis-duckdb/ibis-sqlite returns rows grouped by `by` value rather than in left input order when groups interleave; matched values are always correct, only row position differs | 1 |
    | Relation.pivot() raises on all ibis backends and narwhals-lazy; polars and eager narwhals compute it | 1 |
    | Tests expecting truncation-on-cast produce different results on ibis-duckdb. | 1 |
    | The listed list operation raises on ibis-duckdb. | 16 |
    | a full conform multi-transform pipeline raises on ibis-duckdb/ibis-polars/ibis-sqlite; polars/narwhals run it | 1 |
    | dt.nanosecond() returns 0 on Ibis Python-datetime inputs | 1 |
    | hyperbolic functions raise on ibis-polars and ibis-duckdb | 6 |
    | is_nan/fill_nan/NaN comparisons diverge on SQL engines. | 3 |
    | ma.corr() raises on all backends except ibis-polars | 1 |
    | now() differs from the local naive datetime snapshot on non-UTC hosts | 1 |
    | ntile() is unsupported off Polars | 1 |

??? note "ibis-polars (descriptions: 15)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | Case-insensitive matching raises on ibis-polars. | 3 |
    | Columnar literal contains raises on pandas and ibis-polars. | 1 |
    | Relation.join_asof(strategy='forward'\|'nearest') raises BackendCapabilityError on ibis-polars; backward is native and unaffected | 1 |
    | Relation.pivot() raises on all ibis backends and narwhals-lazy; polars and eager narwhals compute it | 1 |
    | a ScalarRule verdict over an all-null column diverges on ibis-polars/ibis-sqlite; polars/narwhals compute the 'unknown' verdict (ibis-duckdb rejects the all-null table outright; IB-REL-06) | 1 |
    | a full conform multi-transform pipeline raises on ibis-duckdb/ibis-polars/ibis-sqlite; polars/narwhals run it | 1 |
    | all-null sum/mean/std_dev/variance raise on ibis-polars/ibis-sqlite | 4 |
    | calendar interval arithmetic raises TypeError on ibis-polars | 3 |
    | dt.nanosecond() returns 0 on Ibis Python-datetime inputs | 1 |
    | hyperbolic functions raise on ibis-polars and ibis-duckdb | 6 |
    | month_end()/days_in_month() raise on ibis-polars | 2 |
    | ntile() is unsupported off Polars | 1 |
    | str.center() raises on the marked providers. | 1 |
    | time-unit differences raise on ibis-polars and ibis-sqlite | 3 |
    | window operations raise on ibis-polars | 19 |

??? note "ibis-sqlite (descriptions: 26)"

    | Description | Distinct operations illustrated |
    | --- | --- |
    | Cyclic calculations and hash bucketing with negative dividends diverge | 1 |
    | NULL-on-cast-failure cannot materialize on the marked provider. | 1 |
    | Relation.cross_join() raises on ibis-duckdb/ibis-sqlite; polars/narwhals and ibis-polars compute it | 1 |
    | Relation.drop_nans()/unpivot()/melt() raise on ibis-sqlite; other backends compute them | 2 |
    | Relation.join_asof(by=...) on ibis-duckdb/ibis-sqlite returns rows grouped by `by` value rather than in left input order when groups interleave; matched values are always correct, only row position differs | 1 |
    | Relation.join_asof(strategy='nearest') or tolerance=... over a temporal `on` column raises BackendCapabilityError on ibis-sqlite; forward/backward over temporal keys (no distance needed) work fine there | 1 |
    | Relation.pivot() raises on all ibis backends and narwhals-lazy; polars and eager narwhals compute it | 1 |
    | Strict casts do not raise for malformed input on ibis-sqlite. | 1 |
    | a ScalarRule verdict over an all-null column diverges on ibis-polars/ibis-sqlite; polars/narwhals compute the 'unknown' verdict (ibis-duckdb rejects the all-null table outright; IB-REL-06) | 1 |
    | a full conform multi-transform pipeline raises on ibis-duckdb/ibis-polars/ibis-sqlite; polars/narwhals run it | 1 |
    | all-null sum/mean/std_dev/variance raise on ibis-polars/ibis-sqlite | 4 |
    | conform() discard_value/discard_row policies raise on pandas/narwhals and ibis-sqlite; polars and ibis-duckdb/ibis-polars apply them | 1 |
    | conform() with a dotted struct source path raises on pandas/narwhals-pandas/ibis-sqlite; polars and ibis-duckdb/ibis-polars extract it | 1 |
    | conform() with a native OBJECT source raises UnsupportedBackendType on ibis-sqlite; other supported native structured backends execute it | 1 |
    | dt.microsecond() returns the wrong value on ibis-sqlite | 1 |
    | dt.nanosecond() returns 0 on Ibis Python-datetime inputs | 1 |
    | dt.time() yields the wrong type on ibis-sqlite | 1 |
    | is_nan/fill_nan/NaN comparisons diverge on SQL engines. | 3 |
    | ma.col(x).is_finite()/is_infinite() raise on ibis-sqlite; polars, pandas, narwhals, and ibis-polars/ibis-duckdb evaluate them | 2 |
    | ma.corr() raises on all backends except ibis-polars | 1 |
    | now() differs from the local naive datetime snapshot on non-UTC hosts | 1 |
    | ntile() is unsupported off Polars | 1 |
    | sinh/cosh/tanh/asinh/acosh/atanh unavailable on ibis-sqlite | 6 |
    | sub-day temporal arithmetic/comparison on ibis-sqlite silently diverges | 5 |
    | sub-day truncate raises on ibis-sqlite | 1 |
    | time-unit differences raise on ibis-polars and ibis-sqlite | 3 |
<!-- END GENERATED -->

The catalogue also lists, for each illustration, its input data, reference and contrasting results, the catalogue descriptions with their workarounds and source modules, and any upstream issue references. At this revision it is 11089 lines.
