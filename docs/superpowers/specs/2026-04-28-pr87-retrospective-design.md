# PR #87 Retrospective — Between, String Fixes, and Surfaced Issues

> **Context:** PR #87 (`bugfix/between-closed-and-string-parameter-fixes`) was implemented
> without a brainstorming phase. This retrospective validates the decisions made and
> documents two new issues surfaced during post-hoc review.

**Goal:** Fix `between()` closed kwarg crash and eliminate narwhals string no-ops.

**Architecture:** Backend parameter forwarding fixes — no new AST nodes, no new protocols.

---

## Validated Decisions (in PR #87, no changes needed)

### between() closed parameter as option
`closed` is universally literal (no backend accepts a column reference). Stored in
`options`, forwarded as `**kwarg`. Correct per `arguments-vs-options` (ENFORCED).

### Ibis compound comparisons for non-"both" closed
`(x >= low) & (x < high)` etc. Semantically identical to native BETWEEN with bounds.
NULL propagation is correct: SQL `NULL >= 5` → NULL, `NULL & TRUE` → NULL.

### "none"/"neither" synonym acceptance
Public API accepts both `"none"` (Polars convention) and `"neither"` (readable English).
Backends normalize to `"none"`. Ibis validates explicitly and rejects invalid values.

### Narwhals lpad/rpad wired to native pad_start/pad_end
These methods exist since narwhals 2.x. The previous no-op fallbacks were stale code,
not genuine limitations. `KNOWN_EXPR_LIMITATIONS` entries added for literal-only length.

### Narwhals left/right upgraded to native head/tail
Cleaner than the `str.slice()` workaround. Same literal-only limitation, already
registered in `KNOWN_EXPR_LIMITATIONS`.

### Narwhals repeat → BackendCapabilityError
No native `str.repeat()` in narwhals, no clean workaround across sub-backends
(polars, pandas, pyarrow). Raising `BackendCapabilityError` is the correct pattern.

---

## Issue 1: `is_true`/`is_false` ternary shadowing (NEW — not in PR #87)

**Problem:** `MountainAshScalarTernaryAPIBuilder` defines `is_true()` and `is_false()`
that shadow the Substrait `SubstraitScalarComparisonAPIBuilder` versions via
`_FLAT_NAMESPACES` ordering in `boolean.py`. The ternary versions check for sentinel
values (1 / -1); the comparison versions check boolean true/false.

**Why it's a bug:** All other ternary methods use the `t_` prefix convention (`t_col`,
`t_is_in`, `t_is_not_in`). `is_true`/`is_false` break this convention and make the
Substrait comparison versions inaccessible through the fluent API.

**Fix:** Rename ternary versions to `t_is_true()`, `t_is_false()`, and any related
methods (`t_is_unknown()` etc.) following the `t_` prefix convention. The Substrait
`is_true()`/`is_false()` then become accessible without shadowing.

**Scope:** API builder rename + test updates. Backend implementations unchanged (they
dispatch on function key, not method name).

---

## Issue 2: `strip_suffix` needs backend methods (NEW — not in PR #87)

**Problem:** `strip_suffix` is implemented as AST composition at the API builder level
(IfThenNode → ENDS_WITH + CHAR_LENGTH + SUBSTRING). The composed SUBSTRING node
receives an expression-typed `length` argument (computed from `CHAR_LENGTH - literal`).
Narwhals and ibis-polars reject expression-typed substring args, so strip_suffix fails
on these backends with `BackendCapabilityError`.

**Fix:** Add a dedicated `STRIP_SUFFIX` function key and backend methods:
- **Polars:** `x.str.strip_suffix(suffix)` (native method)
- **Ibis:** `x.re_replace(suffix + "$", "")` or equivalent
- **Narwhals:** `x.str.replace(suffix, "")` with ends_with guard, or
  `BackendCapabilityError` if no clean path exists

This follows the established six-step wiring pattern (enum → protocol → API builder →
backends → function mapping → tests).

**Scope:** New function key, protocol method, 3 backend implementations, cross-backend
tests. The API builder's existing `strip_suffix(suffix: str)` method would switch from
AST composition to a simple `ScalarFunctionNode` construction.
