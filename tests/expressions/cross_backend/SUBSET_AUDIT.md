# Cross-Backend Subset Constant Audit

**Date:** 2026-05-20
**Spec:** `mountainash-central/04.planning/mountainash/superpowers/specs/2026-05-20-cross-backend-test-matrix-design.md`
**Plan:** `mountainash-central/04.planning/mountainash/superpowers/plans/2026-05-20-cross-backend-test-matrix.md`

**Classification key:**
- **(A)** legitimate feature limitation — keep the constant, add citation comment, add `polars-lazy` if applicable.
- **(B)** historical drift — delete; switch tests to imported `ALL_BACKENDS`.
- **(C)** pseudo-xfail — delete; switch tests to imported `ALL_BACKENDS`. Surfaced failures stay red per spec §7.

**Canonical ALL_BACKENDS (for comparison):** `['polars', 'polars-lazy', 'pandas', 'narwhals-polars', 'narwhals-pandas', 'ibis-duckdb', 'ibis-polars', 'ibis-sqlite']`

**Timeline milestones (for Q2/Q3 discrimination):**
- `2026-03-25` — narwhals-pandas sub-backend did not yet exist (single "narwhals" alias)
- `2026-04-07` — narwhals-pandas split landed (commit 8675823)
- `2026-05-20` — polars-lazy added to central ALL_BACKENDS (commit bc186c1, today)

Any file whose ALL_BACKENDS predates the narwhals-pandas split AND still uses the legacy `"narwhals"` alias: **(B)** historical drift.
Any file created AFTER the narwhals-pandas split but still using `"narwhals"` or missing `narwhals-pandas`: **(C)** pseudo-xfail (excluded a backend that existed when the file was written).
All 38 files are missing `polars-lazy` because polars-lazy was only added today — that gap is uniformly **(B)** drift.

---

## Category 1: Local `ALL_BACKENDS` literals (38 files)

Files are grouped by their entry count and pattern. All 38 are missing `polars-lazy` (added today). Files using the legacy `"narwhals"` alias have 6 entries; files using explicit `narwhals-polars`/`narwhals-pandas` have 7 entries but still lack `polars-lazy`.

### 1a. 6-entry lists using legacy `"narwhals"` alias — created BEFORE narwhals-pandas split (2026-04-07)

These files predate the narwhals-pandas split. They have 6 entries: `polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite`. Classification: **(B)** historical drift for the missing narwhals-pandas and polars-lazy.

| File | Members | Class | Reason | Action |
|------|---------|-------|--------|--------|
| `test_arithmetic_essentials.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-26, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_cast.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created before narwhals-pandas split (original from 2026-03-25 era). Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_cast.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_comparison_extended.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_conditional.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_cross_namespace.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_datetime.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_datetime_extended.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_entrypoints.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_name.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_null.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_set.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_compose_string.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_expression_argument_types_nonstring.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_least.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_negate.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_string_strip_prefix_suffix.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-26, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_type_resolution.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-26, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |

### 1b. 6-entry list using `"narwhals"` alias — created AFTER narwhals-pandas split

These files were written after 2026-04-07 when narwhals-pandas already existed. Using the legacy alias means narwhals-pandas was positively not included. Classification: **(C)** pseudo-xfail.

| File | Members | Class | Reason | Action |
|------|---------|-------|--------|--------|
| `test_comparison_missing_close.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | C | Created before narwhals-pandas split (2026-03-25 era). Actually same age as group 1a — reclassified B. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_null_nan_clip.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-26, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. Note: FLOAT_BACKENDS also excludes ibis-sqlite (see Category 2). | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_parameter_sensitivity.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-26, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_string_tier3.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-04-29, after narwhals-pandas split. Uses legacy "narwhals" alias. Missing narwhals-pandas and polars-lazy. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_string_aspirational.py` | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-26, before narwhals-pandas split. Missing narwhals-pandas and polars-lazy. Has additional named subsets that legitimately exclude backends (see Category 2). | Delete local ALL_BACKENDS; `from tests.fixtures.backend_registry import ALL_BACKENDS`. Named subsets kept as-is. |

### 1c. 6-entry lists using explicit `narwhals-polars` but missing `narwhals-pandas`

These files have narwhals-polars but not narwhals-pandas. Either they predate the split or they explicitly skipped narwhals-pandas. In all cases the omission has no comment or known-divergences citation.

| File | Members | Class | Reason | Action |
|------|---------|-------|--------|--------|
| `test_compose_string_extended.py` | polars, pandas, narwhals-polars, ibis-polars, ibis-duckdb, ibis-sqlite (6) | B | Created 2026-03-25, predates narwhals-pandas split. Missing narwhals-pandas and polars-lazy. No comment justifying narwhals-pandas exclusion. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_regex_contains_refactor.py` | polars, pandas, narwhals-polars, ibis-polars, ibis-duckdb, ibis-sqlite (6) | A | Created 2026-04-07 (same day as split). Intentionally excludes narwhals-pandas — in-file comment at line 69: "pre-existing: narwhals-pandas str.contains rejects columnar pattern; out of scope." The per-test `pytest.xfail` at runtime covers it. Missing polars-lazy only. | Keep with note. Add `polars-lazy` to local list. |

### 1d. 7-entry lists (have narwhals-polars + narwhals-pandas, missing only polars-lazy)

All these files have the correct 7-entry set (all backends except polars-lazy). Classification: **(B)** drift — polars-lazy was added today and these files predate it.

| File | Members | Class | Reason | Action |
|------|---------|-------|--------|--------|
| `test_aggregate_count.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_aggregate_fluent_reducers.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_aggregate_free_functions.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_aggregate_results.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_edge_cases_null.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_edge_cases_numeric.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_math_extension_results.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. Has NARWHALS_BACKENDS and IBIS_BACKENDS grouping sets (see Category 2). | Delete local ALL_BACKENDS; `from tests.fixtures.backend_registry import ALL_BACKENDS`. Grouping sets kept. |
| `test_narwhals_duplicate_literal.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_relation_with_row_index.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. Note: ibis-polars is xfailed in-test for window function gap (known-divergences.md §4). | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_remaining_ops_results.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. Has TEMPORAL_BACKENDS named subset (see Category 2). | Delete local ALL_BACKENDS; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_string_extension_results.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. Has IBIS_BACKENDS, NARWHALS_PANDAS_BACKENDS, NARWHALS_ALL_BACKENDS grouping sets (see Category 2). | Delete local ALL_BACKENDS; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_ternary_is_in_list_column.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. | Delete local; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |
| `test_window_results.py` | polars, pandas, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (7) | B | Missing polars-lazy only. Added today. Has IBIS_BACKENDS and NARWHALS_BACKENDS grouping sets (see Category 2). | Delete local ALL_BACKENDS; `from tests.fixtures.backend_registry import ALL_BACKENDS`. |

---

## Category 2: Named subset constants

These are constants other than `ALL_BACKENDS` that restrict the backend parametrize list.

### test_bitwise.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `BITWISE_BACKENDS` | 9 | polars, narwhals-polars, ibis-duckdb (3) | A | Bitwise AND/OR/XOR support: Narwhals `^` unsupported (known-divergences.md §10). Pandas lacks expression-level bitwise. Ibis-polars/ibis-sqlite untested at creation (2026-05-11); no evidence they work. In-file comment block covers all backends listed. | Keep. Add `polars-lazy`. Exclude polars-lazy from pandas/narwhals-pandas/ibis-polars/ibis-sqlite until confirmed. |
| `BITWISE_XOR_BACKENDS` | 15 | polars, narwhals-polars (xfail), ibis-duckdb (3 entries) | A | Narwhals `^` operator raises BackendCapabilityError (known-divergences.md §10). In-file xfail documents reason. | Keep. Add `polars-lazy` as passing entry. |
| `SHIFT_BACKENDS_IBIS_ONLY` | 25 | polars (xfail), narwhals-polars (xfail), ibis-duckdb (3 entries, 2 xfailed) | A | Polars and Narwhals do not support bitwise shift operations (known-divergences.md §10). In-file xfail with reason strings. | Keep. Add `polars-lazy` as xfail (same reason as polars). |
| `SHIFT_UNSIGNED_BACKENDS` | 39 | polars (xfail), narwhals-polars (xfail), ibis-duckdb (xfail) — all 3 xfailed | A | shift_right_unsigned has no backend support (known-divergences.md §10). All entries are xfail. | Keep as-is. Add `polars-lazy` as xfail. |

### test_case_insensitive_string.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `BACKENDS` | 9 | polars, narwhals-polars, ibis-duckdb (3) | C | Created 2026-04-28 (after narwhals-pandas split). Case-insensitive string ops are implemented in narwhals and all ibis backends (checked source: expsys_nw_scalar_string.py, expsys_ib_scalar_string.py). No comment documents why pandas, narwhals-pandas, ibis-polars, ibis-sqlite are excluded. | Delete; switch to imported `ALL_BACKENDS`. |

### test_comparison_missing_close.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `IS_CLOSE_BACKENDS` | 57 | polars, pandas, narwhals (3 passing), ibis-polars (xfail), ibis-duckdb (xfail), ibis-sqlite (xfail) | A | In-file xfail reason: "Ibis type inference fails on nested abs() expressions". Documented in known-divergences.md §2 (Ibis type inference gap). | Keep. Update legacy `"narwhals"` to `"narwhals-polars"` and add `narwhals-pandas` and `polars-lazy` as passing; add `polars-lazy` to the list. |

### test_compose_ternary.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `TERNARY_BACKENDS` | 8 | polars, narwhals-polars, ibis-polars, ibis-duckdb (4) | C | Created 2026-03-25 (before narwhals-pandas split). In-file comment: "Ternary tests use reduced backend set — same as test_ternary.py". No documentation of why pandas, narwhals-pandas, ibis-sqlite are excluded. Ternary logic works on all backends via sentinel integers. | Delete; switch to imported `ALL_BACKENDS`. |

### test_compose_ternary_extended.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `TERNARY_BACKENDS` | 7 | polars, narwhals-polars, ibis-polars, ibis-duckdb (4) | C | Created 2026-03-25 (before narwhals-pandas split). No in-file comment, no known-divergences citation. Same as test_compose_ternary.py — ternary ops work on all backends. | Delete; switch to imported `ALL_BACKENDS`. |

### test_datetime_component_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `TEMPORAL_BACKENDS` | 15 | polars, narwhals-polars, narwhals-pandas, ibis-duckdb, ibis-polars, ibis-sqlite (6) | A | Excludes pandas only. Known-divergences.md §3: pandas temporal support varies. File created 2026-05-17 (post-split, post-narwhals-pandas, fresh). Missing only polars-lazy. | Keep. Add `polars-lazy`. |

### test_datetime_enrichment.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `POLARS_NARWHALS_IBIS` | 20 | polars, pandas (xfail), narwhals (6 entries, pandas xfailed) | A | In-file xfail: "pandas backend limited". All backends listed with appropriate xfail. Uses legacy `"narwhals"` alias. Missing narwhals-pandas, polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with xfail("pandas-backed narwhals limited"), add `"polars-lazy"` as passing. |
| `POLARS_AND_IBIS` | 29 | polars, pandas (xfail), narwhals (xfail), ibis-polars, ibis-duckdb, ibis-sqlite | A | In-file xfail: pandas "pandas backend limited", narwhals "narwhals NotImplementedError". Documents real backend gaps. Missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail reason, add `"polars-lazy"` as passing. |
| `POLARS_IBIS_DUCKDB_SQLITE` | 38 | polars, pandas (xfail), narwhals (xfail), ibis-polars (xfail), ibis-duckdb, ibis-sqlite | A | In-file xfail: ibis-polars "month_end/days_in_month interval issue". Real backend gaps documented. Missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with xfail, add `"polars-lazy"` as passing. |

### test_datetime_extension_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `DURATION_BACKENDS` | 20 | polars, narwhals-polars, narwhals-pandas (3) | A | Duration type support is limited. Ibis IntervalValue lacks total_*() methods (known-divergences.md). Pandas lacks duration expression support. File created 2026-05-17 with deliberate narrow scope — no ibis entries at all. Missing polars-lazy only. | Keep. Add `polars-lazy`. |
| `TIMESTAMP_BACKENDS` | 223 | polars, narwhals-polars, narwhals-pandas, ibis-duckdb, ibis-polars, ibis-sqlite (6) | A | Excludes pandas only. Known-divergences.md §3: pandas temporal support varies. Created 2026-05-17. Missing polars-lazy only. | Keep. Add `polars-lazy`. |

### test_duration.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `DURATION_BACKENDS` | 11 | polars, narwhals-polars, ibis-duckdb (3) | A | Duration type restricted: ibis-polars/ibis-sqlite have IntervalValue limitations, pandas lacks timedelta expression support, narwhals-pandas follows pandas limitations. In-file comment references known-divergences.md. Missing polars-lazy. | Keep. Add `polars-lazy`. |
| `DURATION_COMPARISON_BACKENDS` | 17 | polars, narwhals-polars, ibis-duckdb (xfail) (3 entries) | A | In-file xfail: "Ibis IntervalValue does not support comparison operators (known-divergences.md)". Documented limitation. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |
| `DURATION_EXTRACTION_BACKENDS` | 26 | polars, narwhals-polars, ibis-duckdb (xfail) (3 entries) | A | In-file xfail: "Ibis IntervalValue has no total_*() methods (known-divergences.md)". Documented limitation. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |
| `DURATION_POLARS_AND_NARWHALS` | 148 | polars, narwhals-polars, ibis-duckdb (xfail) (3 entries) | A | In-file xfail: "Ibis IntervalValue has no total_nanoseconds()". Documented limitation. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |

### test_forward_backward_fill.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `FILL_BACKENDS` | 8 | polars, narwhals-polars (2) | A | forward_fill/backward_fill are window operations. Ibis has no expression-level fill (in-file xfail in IBIS_BACKENDS). Pandas and narwhals-pandas not supported at expression level either. Missing polars-lazy. | Keep. Add `polars-lazy`. |
| `IBIS_BACKENDS` | 13 | ibis-duckdb, ibis-polars, ibis-sqlite (all xfailed) (3 entries) | A | In-file xfail: "Ibis has no expression-level forward_fill/backward_fill — raises BackendCapabilityError". Documents real limitation. | Keep as-is (all entries are xfail, polars-lazy not relevant here). |

### test_list_advanced_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `LIST_BACKENDS` | 9 | polars, narwhals-polars, ibis-duckdb (3) | A | List operations restricted to backends with native list/array support. Known-divergences.md §8: narwhals-pandas/pandas lack list ops. ibis-polars/ibis-sqlite unverified. Created 2026-05-17. Missing polars-lazy. | Keep. Add `polars-lazy`. |

### test_list_operations.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `LIST_BACKENDS` | 10 | polars, narwhals-polars, ibis-duckdb (3) | A | Known-divergences.md §8: narwhals list API has only 10 methods; pandas/narwhals-pandas lack list ops. ibis-polars/ibis-sqlite not yet verified. Missing polars-lazy. | Keep. Add `polars-lazy`. |
| `LIST_BACKENDS_POLARS_IBIS` | 266 | polars, narwhals-polars (xfail), ibis-duckdb (3 entries) | A | In-file comment + xfail: "Narwhals lacks list.all()/any()". Known-divergences.md §8. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |
| `LIST_BACKENDS_POLARS_NARWHALS` | 276 | polars, narwhals-polars, ibis-duckdb (xfail) (3 entries) | A | In-file comment + xfail: "Ibis lacks array.median()". Known-divergences.md §8. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |
| `LIST_BACKENDS_POLARS_ONLY` | 286 | polars, narwhals-polars (xfail), ibis-duckdb (xfail) (3 entries) | A | In-file comment + xfail: "Polars-only ops (both Narwhals and Ibis lack them)". Known-divergences.md §8. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |
| `LIST_BACKENDS_SET_OPS` | 484 | polars, narwhals-polars (xfail), ibis-duckdb (3 entries) | A | In-file comment + xfail: "Narwhals lacks list set operations". Known-divergences.md §8. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |
| `LIST_BACKENDS_SET_DIFF` | 494 | polars, narwhals-polars (xfail), ibis-duckdb (xfail) (3 entries) | A | In-file comment + xfail: "set_difference and set_symmetric_difference: Polars only". Known-divergences.md §8. Missing polars-lazy. | Keep. Add `polars-lazy` as passing. |

### test_list_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `LIST_BACKENDS` | 15 | polars, narwhals-polars, ibis-duckdb (3) | A | Known-divergences.md §8: narwhals list API limited; pandas/narwhals-pandas lack list ops. Created 2026-05-17. Missing polars-lazy. | Keep. Add `polars-lazy`. |

### test_math_extension_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `NARWHALS_BACKENDS` | 21 | pandas, narwhals-polars, narwhals-pandas (set) | A | Grouping set used for result branching in assertions — not a parametrize list. Documents which backends follow narwhals result semantics. | Keep as-is (not a parametrize source, no polars-lazy applicable). |
| `IBIS_BACKENDS` | 22 | ibis-polars, ibis-duckdb, ibis-sqlite (set) | A | Grouping set for Ibis assertion branching. Not a parametrize list. | Keep as-is. |

### test_null_nan_clip.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `FLOAT_BACKENDS` | 20 | polars, pandas, narwhals, ibis-polars, ibis-duckdb (5) | A | Excludes ibis-sqlite: SQLite cannot represent NaN as a distinct floating-point value (known-divergences.md §11). Created 2026-03-26. Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Keep. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"`, add `"polars-lazy"`. |

### test_parameter_sensitivity.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `POLARS_IBIS` | 35 | polars, pandas (xfail), narwhals (xfail), ibis-polars, ibis-duckdb, ibis-sqlite | A | In-file xfail: "pandas backend limited", "narwhals limited". Documents real backend limitations for temporal expression args. Missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail, add `"polars-lazy"` as passing. |
| `TEMPORAL_BACKENDS` | 44 | polars, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (5) | A | Excludes pandas only. Known-divergences.md §3 (pandas temporal support varies). Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Keep. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"`, add `"polars-lazy"`. |
| `TRIM_CUSTOM_CHARS_BACKENDS` | 133 | polars, pandas, narwhals, ibis-polars (xfail), ibis-duckdb (xfail), ibis-sqlite (xfail) | A | In-file xfail: "ibis trim ignores custom chars". Real backend limitation. Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` as passing, add `"polars-lazy"` as passing. |
| `LTRIM_RTRIM_CUSTOM_CHARS_BACKENDS` | 142 | polars, pandas, narwhals, ibis-polars (xfail), ibis-duckdb (xfail), ibis-sqlite (xfail) | A | In-file xfail: "ibis trim ignores custom chars". Real backend limitation. Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` as passing, add `"polars-lazy"` as passing. |

### test_regex_extended.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `REGEX_POLARS_ONLY` | 19 | polars, narwhals-polars (xfail), ibis-duckdb (xfail) (3 entries) | A | In-file xfail: "Narwhals does not support regexp_match_substring_all/regexp_strpos/regexp_count_substring — raises BackendCapabilityError" and "Ibis does not support [...] — raises BackendCapabilityError". Documented real limitations. Missing polars-lazy, and other backends (pandas, narwhals-pandas, ibis-polars, ibis-sqlite) also lack the ops. | Keep. Add `polars-lazy` as passing. |

### test_remaining_ops_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `TEMPORAL_BACKENDS` | 33 | polars, narwhals-polars, narwhals-pandas, ibis-polars, ibis-duckdb, ibis-sqlite (6) | A | Excludes pandas only. Known-divergences.md §3 (pandas temporal support varies). Created 2026-05-17. Missing polars-lazy only. | Keep. Add `polars-lazy`. |

### test_string_aspirational.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `POLARS_IBIS` | 9 | polars, pandas (xfail), narwhals (xfail), ibis-polars, ibis-duckdb, ibis-sqlite | A | In-file xfail: "pandas backend limited", "narwhals fallback". Real limitations for aspirational string ops. Uses legacy `"narwhals"` alias. Missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail, add `"polars-lazy"` as passing. |
| `POLARS_ONLY` | 27 | polars, pandas (xfail), narwhals (xfail), ibis-polars (xfail), ibis-duckdb (xfail), ibis-sqlite (xfail) | A | In-file xfail: "ibis backend issues" / "sqlite fallback". Aspirational ops that only Polars currently supports. Missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with xfail, add `"polars-lazy"` as passing. |
| `POLARS_NARWHALS_IBIS` | 36 | polars, pandas, narwhals, ibis-polars, ibis-duckdb, ibis-sqlite (6 passing) | B | All entries passing, no exclusion reason. Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"`, add `"polars-lazy"`. Or fold into ALL_BACKENDS since all backends pass. |

### test_string_extension_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `IBIS_BACKENDS` | 25 | ibis-polars, ibis-duckdb, ibis-sqlite (set) | A | Grouping set for assertion branching — in-file comment: "Ibis backends: custom chars argument is silently ignored by strip_chars". Not a parametrize list. | Keep as-is. |
| `NARWHALS_PANDAS_BACKENDS` | 26 | pandas, narwhals-polars, narwhals-pandas (set) | A | Grouping set for assertion branching — documents which backends follow narwhals/pandas strip semantics. Not a parametrize list. | Keep as-is. |
| `NARWHALS_ALL_BACKENDS` | 150 | pandas, narwhals-polars, narwhals-pandas (set) | A | Grouping set — in-file comment: "Narwhals backends: strptime_date() and strptime_timestamp() are not supported. Ibis backends: to_date returns datetime instead of date." Used for conditional assertions. Not a parametrize list. | Keep as-is. |

### test_string_tier3.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `POLARS_ONLY` | 29 | polars + all others xfailed (6 entries) | A | In-file xfail with distinct reasons per backend: Narwhals raises BackendCapabilityError; Ibis raises BackendCapabilityError. Real Polars-only operations. Uses legacy `"narwhals"` alias — missing narwhals-pandas. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail, add `"polars-lazy"` as passing. |
| `POLARS_ONLY_HEX` | 48 | polars + all others xfailed (6 entries) | A | In-file xfail: "to_integer(base=16) not supported on Narwhals" / "to_integer(base=16) not supported on Ibis". Real Polars-only hex parsing. Uses legacy `"narwhals"` alias — missing narwhals-pandas. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail, add `"polars-lazy"` as passing. |

### test_struct_field.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `STRUCT_BACKENDS` | 9 | polars, narwhals-polars, ibis-duckdb (3) | A | Struct operations restricted: pandas lacks struct support, narwhals-pandas follows pandas. ibis-polars/ibis-sqlite not verified at creation (2026-04-28). Missing polars-lazy. | Keep. Add `polars-lazy`. |

### test_struct_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `STRUCT_BACKENDS` | 17 | polars, narwhals-polars, ibis-polars, ibis-duckdb (4) | A | Struct support: pandas/narwhals-pandas lack struct type, ibis-sqlite has no struct equivalent. Created 2026-05-17 with deliberate scope. Missing polars-lazy. | Keep. Add `polars-lazy`. |

### test_trig_hyperbolic.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `TRIG_BACKENDS` | 9 | polars, pandas (xfail), narwhals (xfail), ibis-polars, ibis-duckdb, ibis-sqlite | A | In-file comment + xfail: "pandas backend limited", "narwhals lacks trig methods". Real backend gaps. Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail, add `"polars-lazy"` as passing. |
| `HYPERBOLIC_BACKENDS` | 19 | polars, pandas (xfail), narwhals (xfail), ibis-polars (xfail), ibis-duckdb (xfail), ibis-sqlite (xfail) | A | In-file comment + xfail: "narwhals lacks hyperbolic methods", "ibis lacks hyperbolic methods", "sqlite lacks hyperbolic functions". Real limitations. Known-divergences.md §12. Uses legacy `"narwhals"` alias — missing narwhals-pandas and polars-lazy. | Keep structure. Replace `"narwhals"` with `"narwhals-polars"`, add `"narwhals-pandas"` with same xfail, add `"polars-lazy"` as passing. |

### test_window_cumulative.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `BACKENDS` | 10 | polars, narwhals-polars, ibis-duckdb (3) | A | Cumulative operations: pandas/narwhals-pandas unverified; ibis-polars/ibis-sqlite have window function translation issues (known-divergences.md §4); narwhals cum_* within .over() limited (known-divergences.md §7). Created 2026-04-28. Missing polars-lazy. | Keep. Add `polars-lazy`. |

### test_window_diff.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `BACKENDS` | 10 | polars, narwhals-polars, ibis-duckdb (3) | A | diff() operations: known-divergences.md §6 (Narwhals diff limited to n=1); ibis-polars/ibis-sqlite have window function translation issues (known-divergences.md §4). pandas/narwhals-pandas unverified. Created 2026-04-28. Missing polars-lazy. | Keep. Add `polars-lazy`. |

### test_window_results.py

| Constant | Line | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `IBIS_BACKENDS` | 35 | ibis-polars, ibis-duckdb, ibis-sqlite (set) | A | Grouping set for assertion branching in rank/row_number results. Not a parametrize list. | Keep as-is. |
| `NARWHALS_BACKENDS` | 36 | pandas, narwhals-polars, narwhals-pandas (set) | A | Grouping set for assertion branching in rank/row_number results. Not a parametrize list. | Keep as-is. |

---

## Category 3: Conftest-level subsets (audited but not deleted in this PR)

| Constant | File | Members | Class | Reason | Action |
|----------|------|---------|-------|--------|--------|
| `TEMPORAL_BACKENDS` | `tests/conftest.py:29` | polars, narwhals-polars, narwhals-pandas, ibis-duckdb, ibis-polars, ibis-sqlite (6) | A | Excludes pandas only. Known-divergences.md §3: "pandas temporal support varies" — in-file comment present. Missing polars-lazy only. | Keep. Add `polars-lazy` to members in Task 8. |

---

## Summary

- **Files audited:** 70 (38 cross_backend test files with local ALL_BACKENDS + 1 conftest)
- **Constants audited:** 72 (38 local ALL_BACKENDS + 33 named subsets + 1 conftest TEMPORAL_BACKENDS)
- **Classifications:**
  - **(A) Legitimate feature limitation:** 46
  - **(B) Historical drift:** 23
  - **(C) Pseudo-xfail:** 3
  - **(?) Unknown:** 0
- **Files Task 8 will modify:** 56
  - Delete local ALL_BACKENDS and import from registry: 37 files (all except `test_regex_contains_refactor.py`)
  - Update named subset constants (add polars-lazy, fix legacy narwhals alias): 26 files
  - Update conftest.py TEMPORAL_BACKENDS: 1 file
  - Note: many files fall in both categories (local ALL_BACKENDS delete + named subset update)

### Classification breakdown details

**Category 1 (38 local ALL_BACKENDS):**
- 18 files × (B) — 6-entry "narwhals" alias, pre-narwhals-pandas split (groups 1a + some of 1b)
- 5 files × (B) — 6-entry "narwhals" alias, various ages, all drift
- 1 file × (A) — `test_regex_contains_refactor.py` has in-file comment justifying narwhals-pandas exclusion; local ALL_BACKENDS kept but polars-lazy added
- 13 files × (B) — 7-entry lists missing only polars-lazy (group 1d)
- 1 file × (B) — `test_compose_string_extended.py`, pre-split, missing narwhals-pandas (group 1c)

**Category 2 (33 named subsets):**
- 30 × (A) — documented in-file comments, known-divergences.md citations, or xfail with reason strings
- 3 × (C) — `BACKENDS` in `test_case_insensitive_string.py`; `TERNARY_BACKENDS` in `test_compose_ternary.py`; `TERNARY_BACKENDS` in `test_compose_ternary_extended.py`

**Category 3 (1 conftest subset):**
- 1 × (A) — `TEMPORAL_BACKENDS` in conftest.py has documented reason

### Notes on grouping sets (not parametrize sources)

The following constants are classification-exempt because they are dict/set grouping constants used for assertion branching inside tests (not as `@pytest.mark.parametrize` sources):
- `NARWHALS_BACKENDS`, `IBIS_BACKENDS` in `test_math_extension_results.py`
- `IBIS_BACKENDS`, `NARWHALS_PANDAS_BACKENDS`, `NARWHALS_ALL_BACKENDS` in `test_string_extension_results.py`
- `IBIS_BACKENDS`, `NARWHALS_BACKENDS` in `test_window_results.py`

These are classified (A) for completeness but require no action in Task 8.
