# Expression Argument Consistency Phase 2 — All Remaining Operations

> **Date:** 2026-04-07
> **Status:** Draft
> **Prerequisite:** Phase 1 (string operations) complete — see `2026-04-06-expression-argument-consistency-design.md`
> **Principle alignment:** `e.cross-backend/arguments-vs-options.md` (ENFORCED)

## Problem

Phase 1 removed all `_extract_literal_value` calls from string operations across all three backends. 65 calls remain in non-string operations: datetime (48), name (9), rounding (3), logarithmic (2), null (3), and window (1).

Beyond the Phase 1 issues (silent extraction, no error context), a deeper problem emerges: **some parameters that are universally literal on all backends are incorrectly modelled as `arguments`** in the AST. The `arguments-vs-options.md` principle is clear — `options` are always raw Python values, `arguments` are visited expressions. Parameters that can never be column references should be `options`, not `arguments` that get wrapped in `LiteralNode` only to be unwrapped again in every backend.

## Empirical Backend Capabilities (Tested 2026-04-07)

### Rounding — `round(decimals)`

| Backend | Expr decimals | Notes |
|---------|:-----:|-------|
| Polars | **NO** (TypeError) | Requires literal int |
| Ibis (DuckDB) | **NO** (BinderException) | Requires literal int |
| Narwhals | **NO** (TypeError) | Requires literal int |

**Universal literal** — should be an option, not an argument.

### Logarithmic — `log(base)`

| Backend | Expr base |
|---------|:-----:|
| Polars | **YES** |
| Ibis (DuckDB) | **YES** |

Narwhals has no logarithmic implementation. Since some backends accept Expr, this correctly belongs as an argument.

### Datetime — Offset Operations (`add_years`, `add_months`, `add_days`, etc.)

| Backend | Expr duration amount | Notes |
|---------|:-----:|-------|
| Polars | **YES** via `pl.duration(days=Expr)` | Native expression support |
| Ibis | **NO** via `ibis.interval(days=Expr)` | Requires literal int |
| Narwhals | **NO** | Requires raw Python values |

Since Polars accepts Expr, these correctly belong as arguments. Ibis/Narwhals limitations get registry entries + xfails.

### Datetime — Unit/Timezone/Format Parameters

Already correctly in `options` at the API builder level. The `_extract_literal_value` calls in backends are no-ops (extracting a raw string to... a raw string). These just need the call removed.

### Name Operations (`alias`, `prefix`, `suffix`)

Currently in `arguments` as `LiteralNode(value=name)`. Column names are never data — these should be `options`.

### Null Operations (Narwhals only)

| Method | Expr argument |
|--------|:-----:|
| `fill_null(replacement)` | **YES** |
| `coalesce(condition, replacement)` | **YES** |

These correctly belong as arguments. Remove `_extract_literal_value` and pass through.

### Window — `window_offset` (Polars only)

Literal integer. Should be an option.

## Design

### Three Categories of Change

**Category A: Move from `arguments` to `options` (universal literals)**

Parameters that no backend accepts as expressions. The fix is at the API builder level — stop wrapping in `LiteralNode`, pass through `options` dict instead. Backends then receive raw Python values directly and need no extraction.

| Parameter | Current | Target | API Builder File |
|-----------|---------|--------|-----------------|
| `round(decimals)` | `arguments` | `options={"s": decimals}` | `api_bldr_scalar_rounding.py` |
| `name.alias(name)` | `arguments` via `LiteralNode` | `options={"name": name}` | `api_bldr_ext_ma_name.py` |
| `name.prefix(prefix)` | `arguments` via `LiteralNode` | `options={"prefix": prefix}` | `api_bldr_ext_ma_name.py` |
| `name.suffix(suffix)` | `arguments` via `LiteralNode` | `options={"suffix": suffix}` | `api_bldr_ext_ma_name.py` |
| `window_offset` | `arguments` | `options={"window_offset": offset}` | window API builder |

After this change:
- API builders pass these via `options={...}` on `ScalarFunctionNode`
- The visitor delivers them as `**kwargs` to backend methods (raw Python values)
- Backends receive raw values — no extraction needed
- Remove the `_extract_literal_value` calls from backend methods
- Update backend method signatures to reflect they receive raw values (e.g., `s: int` not `s: PolarsExpr`)

**Category B: Pass-through migration (some backends accept Expr)**

Parameters that at least one backend accepts as expressions. Apply Phase 1 pattern:
- Remove `_extract_literal_value`
- For Narwhals: use `_extract_literal_if_possible`
- Wrap with `_call_with_expr_support`
- Add `KNOWN_EXPR_LIMITATIONS` for backends that can't handle Expr

| Parameter | Polars | Ibis | Narwhals |
|-----------|--------|------|----------|
| `log(base)` | pass-through | pass-through | N/A |
| `add_years(years)` | pass-through | `_extract_literal_if_possible` + registry | `_extract_literal_if_possible` + registry |
| `add_months(months)` | pass-through | same | same |
| `add_days(days)` | pass-through | same | same |
| `add_hours(hours)` | pass-through | same | same |
| `add_minutes(minutes)` | pass-through | same | same |
| `add_seconds(seconds)` | pass-through | same | same |
| `add_milliseconds(ms)` | pass-through | same | same |
| `add_microseconds(us)` | pass-through | same | same |
| `fill_null(replacement)` | N/A | N/A | pass-through (remove extraction) |
| `coalesce(condition)` | N/A | N/A | pass-through |
| `coalesce(replacement)` | N/A | N/A | pass-through |

**Category C: Remove redundant no-op extraction**

Parameters already delivered as raw values via `options`, where `_extract_literal_value` is a no-op:
- Datetime `unit` (all backends) — 15 calls
- Datetime `timezone` (Polars) — 2 calls
- Datetime `format` (Polars) — 1 call
- Datetime `offset` (Polars) — 1 call
- Datetime `rounding` (Polars substrait) — 1 call

Simply remove the `_extract_literal_value` call. No `_call_with_expr_support` needed since the value is already raw.

### Registry Additions

**Ibis** — first entries:
```python
# Datetime offset operations require literal integers for ibis.interval()
_IB_DATETIME_OFFSET_LITERAL_ONLY = KnownLimitation(
    message="Ibis datetime offset operations require literal integer values",
    native_errors=(TypeError,),
    workaround="Use a literal integer for the offset amount",
)

KNOWN_EXPR_LIMITATIONS = {
    (FK_DT.ADD_YEARS, "years"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_MONTHS, "months"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    (FK_DT.ADD_DAYS, "days"): _IB_DATETIME_OFFSET_LITERAL_ONLY,
    # ... all 8 offset operations
}
```

**Narwhals** — add datetime offset entries (same pattern).

### `_extract_literal_value` Removal

After all callers are migrated, remove `_extract_literal_value` from all three base classes entirely. This is the final step.

### Testing Strategy

**New test file:** `tests/cross_backend/test_expression_argument_types_nonstring.py`

| Operation | Raw scalar | Expr literal | Column ref | Expected xfails |
|-----------|:-----:|:-----:|:-----:|------|
| `round(decimals)` | all pass | all pass | N/A (option) | N/A — decimals is an option |
| `log(base)` | Polars+Ibis pass | same | Polars+Ibis pass | Narwhals N/A |
| `add_days(days)` | all pass | all pass | Polars pass | Ibis xfail, Narwhals xfail |
| `fill_null(value)` | all pass | all pass | all pass | — |

Note: Category A parameters (round decimals, names) become options and can no longer accept column references at the API level — the type annotation changes to `int` or `str`, preventing misuse at build time rather than compile time. No xfail tests needed for these.

### Files Changed

**API builder changes (Category A — move to options):**
- `api_bldr_scalar_rounding.py` — `round(decimals)` → options
- `api_bldr_ext_ma_name.py` — `alias/prefix/suffix` → options
- Window API builder — `window_offset` → options

**API builder protocol changes:**
- `prtcl_api_bldr_scalar_rounding.py` — update type annotations
- `prtcl_api_bldr_ext_ma_name.py` — update type annotations

**Backend implementations (Category B — pass-through):**

*Polars:*
- `expsys_pl_ext_ma_scalar_datetime.py` — 8 offset methods: remove extraction, pass through
- `expsys_pl_scalar_logarithmic.py` — remove extraction, pass through

*Ibis:*
- `expsys_ib_ext_ma_scalar_datetime.py` — 8 offset methods: `_extract_literal_if_possible` + registry
- `expsys_ib_scalar_logarithmic.py` — remove extraction, pass through

*Narwhals:*
- `expsys_nw_ext_ma_scalar_datetime.py` — 8 offset methods: `_extract_literal_if_possible` + registry
- `expsys_nw_ext_ma_null.py` — 3 methods: remove extraction, pass through

**Backend implementations (Category A — update signatures after options migration):**

*All backends:*
- `expsys_*_scalar_rounding.py` — update signature, remove extraction
- `expsys_*_ext_ma_name.py` — update signature, remove extraction

**Backend implementations (Category C — remove no-op extraction):**

*All backends:*
- `expsys_*_scalar_datetime.py` — remove no-op extraction of `unit`
- `expsys_*_ext_ma_scalar_datetime.py` — remove no-op extraction of `unit`/`timezone`/`format`/`offset`/`rounding`

**Base classes (remove `_extract_literal_value`):**
- `polars/base.py`
- `ibis/base.py`
- `narwhals/base.py`

**New:**
- `tests/cross_backend/test_expression_argument_types_nonstring.py`
