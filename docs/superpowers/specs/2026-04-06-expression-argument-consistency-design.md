# Expression Argument Consistency Design

> **Date:** 2026-04-06
> **Status:** Draft
> **Principle alignment:** `e.cross-backend/arguments-vs-options.md` (ENFORCED), `e.cross-backend/consistency-guarantees.md` (ENFORCED), `e.cross-backend/known-divergences.md` (ADOPTED), `g.development-practices/testing-philosophy.md` (ENFORCED)

## Problem

Backend string methods handle expression-typed arguments inconsistently:

1. **Silent extraction:** Many methods call `_extract_literal_value()` on arguments that the visitor already resolved as backend expressions. When the argument is a column reference, extraction silently fails and returns the expression unchanged — which then hits native APIs that may or may not accept it, producing unpredictable results.

2. **Cross-method inconsistency:** In the Polars backend, `starts_with` passes expressions through but `contains` extracts the literal. Both have the same API shape and Polars supports expressions for both.

3. **Cross-backend inconsistency:** Polars `starts_with` passes expressions through; Ibis `starts_with` extracts the literal — even though Ibis natively supports expressions for `startswith`.

4. **No error context:** When a backend genuinely can't handle an expression argument (e.g., Narwhals `str.starts_with` requires a literal string), the user gets a raw `TypeError` from Pandas internals with no guidance.

### Empirical Backend Capabilities (Tested 2026-04-06)

**Polars — expression argument support:**

| Method | Expr pattern/substring | Expr replacement | Expr numeric |
|--------|:-----:|:-----:|:-----:|
| starts_with / ends_with | YES | — | — |
| contains (literal=True and False) | YES | — | — |
| find | YES | — | — |
| count_matches | YES | — | — |
| replace / replace_all | NO (dynamic pattern) | YES (literal pattern only) | — |
| pad_start / pad_end | — | — | NO (TypeError) |
| strip_chars | YES | — | — |
| slice | — | — | YES |
| split | YES | — | — |
| extract / extract_all | YES | — | — |
| strip_prefix / strip_suffix | YES | — | — |
| head / tail | — | — | YES |

**Ibis (DuckDB) — expression argument support:**

All tested string methods accept expression arguments. SQL natively supports column references in all positions.

**Narwhals (Pandas backend) — expression argument support:**

No string method accepts expression arguments. All pattern/substring parameters require literal values. Unary methods (to_lowercase, len_chars, etc.) are unaffected.

## Design

### Approach: Pass-Through with Registry-Based Error Enrichment

Three components:

1. **Remove `_extract_literal_value` from all string methods** — let expressions pass through to the native backend API unchanged.
2. **Explicit error catching** — each backend method wraps native calls with `_call_with_expr_support()`, which catches known native error types.
3. **Known limitation registry** — when a native error is caught, the registry provides a curated error message with upstream issue links and workarounds. Unknown errors propagate unchanged.

This design is **self-healing**: when a backend adds expression support, the native error stops being raised, the registry entry goes dormant, and the corresponding strict xfail test breaks to alert us.

### Component 1: `KnownLimitation` Dataclass

**Location:** `src/mountainash/core/types.py` (shared core, all backends import it)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class KnownLimitation:
    """Documents a known backend limitation for expression-typed arguments.
    
    Consulted only when the backend raises a native error — never gates
    execution. When the upstream library adds support, the error stops
    being raised and this entry becomes dormant.
    """
    message: str
    native_errors: tuple[type[Exception], ...]
    upstream_issue: str | None = None
    workaround: str | None = None
```

### Component 2: `BackendCapabilityError`

**Location:** `src/mountainash/core/types.py`

```python
class BackendCapabilityError(Exception):
    """Raised when a backend cannot handle an expression-typed argument.
    
    Wraps native backend errors with curated context from the known
    limitation registry.
    """
    def __init__(
        self,
        message: str,
        *,
        backend: str,
        function_key: str,
        limitation: KnownLimitation | None = None,
    ):
        parts = [f"[{backend}] {message}"]
        if limitation:
            if limitation.workaround:
                parts.append(f"Workaround: {limitation.workaround}")
            if limitation.upstream_issue:
                parts.append(f"Upstream: {limitation.upstream_issue}")
        super().__init__("\n".join(parts))
        self.backend = backend
        self.function_key = function_key
        self.limitation = limitation
```

### Component 3: Per-Backend Limitation Registry

Each backend base class defines a class-level registry mapping `(function_key, param_name)` to `KnownLimitation`. The registry is populated from the empirical testing above.

**Polars example** (`expsys_pl_scalar_string.py` or Polars base):

```python
from mountainash.core.types import KnownLimitation
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_SUBSTRAIT_SCALAR_STRING as FK,
)

KNOWN_EXPR_LIMITATIONS: dict[tuple[str, str], KnownLimitation] = {
    (FK.REPLACE, "pattern"): KnownLimitation(
        message="Polars does not support dynamic column patterns in str.replace",
        native_errors=(pl.exceptions.ComputeError,),
        upstream_issue=None,  # to be filed
        workaround="Use a literal string pattern; replacement can be a column reference",
    ),
    (FK.REPLACE_ALL, "pattern"): KnownLimitation(
        message="Polars does not support dynamic column patterns in str.replace_all",
        native_errors=(pl.exceptions.ComputeError,),
        upstream_issue=None,
        workaround="Use a literal string pattern; replacement can be a column reference",
    ),
    (FK.LPAD, "length"): KnownLimitation(
        message="Polars str.pad_start requires a literal integer length",
        native_errors=(TypeError,),
        upstream_issue=None,
        workaround="Use a literal integer for the padding length",
    ),
    (FK.RPAD, "length"): KnownLimitation(
        message="Polars str.pad_end requires a literal integer length",
        native_errors=(TypeError,),
        upstream_issue=None,
        workaround="Use a literal integer for the padding length",
    ),
}
```

**Narwhals example** — broader, since almost all parameterised string methods are literal-only:

```python
# All parameterised string methods require literals in Narwhals
_NW_STRING_LITERAL_ONLY = KnownLimitation(
    message="Narwhals string methods require literal values, not column references",
    native_errors=(TypeError,),
    upstream_issue=None,
    workaround="Use a literal string value instead of a column reference",
)

KNOWN_EXPR_LIMITATIONS: dict[tuple[str, str], KnownLimitation] = {
    (fk, param): _NW_STRING_LITERAL_ONLY
    for fk, param in [
        (FK.STARTS_WITH, "substring"),
        (FK.ENDS_WITH, "substring"),
        (FK.CONTAINS, "substring"),
        (FK.REPLACE, "substring"),
        (FK.REPLACE, "replacement"),
        (FK.LIKE, "match"),
        (FK.REGEXP_REPLACE, "pattern"),
        (FK.REGEXP_REPLACE, "replacement"),
        (FK.SUBSTRING, "start"),
        (FK.SUBSTRING, "length"),
        (FK.LEFT, "count"),
        (FK.RIGHT, "count"),
        (FK.TRIM, "characters"),
        (FK.LTRIM, "characters"),
        (FK.RTRIM, "characters"),
    ]
}
```

**Ibis** — empty registry (all methods support expressions).

### Component 4: `_extract_literal_if_possible` Base Method

Some backends (Narwhals/Pandas) require raw Python values for string method parameters — they reject even `nw.lit("hello")`. The visitor resolves `LiteralNode(value="hello")` into `nw.lit("hello")` (an `nw.Expr`), so these backends need to unwrap literal expressions back to raw values while still allowing column references and complex expressions to pass through.

Each backend base class gets this method to replace `_extract_literal_value`:

```python
def _extract_literal_if_possible(self, expr: ExpressionT) -> ExpressionT | Any:
    """Extract the raw Python value from a literal expression, if possible.
    
    Unlike _extract_literal_value, this method is explicit about its purpose:
    some native APIs require raw Python values, not expression objects, even
    for literal values. Column references and complex expressions pass through
    unchanged — the caller (via _call_with_expr_support) handles the case
    where the native API rejects them.
    
    Returns:
        Raw Python value if the expression is a simple literal, otherwise
        the expression unchanged.
    """
    # Subclasses implement backend-specific literal detection
    raise NotImplementedError
```

**Polars implementation:** Check if `pl.select(expr).item()` succeeds (existing pattern, but only for actual literals — column refs raise and pass through).

**Ibis implementation:** Returns expression unchanged (Ibis accepts expressions everywhere).

**Narwhals implementation:** Attempts `nw.to_native(expr)` or inspects the expression graph for literal extraction. Falls back to returning the expression unchanged.

The critical difference from `_extract_literal_value`: this method is only used in backends where the native API genuinely requires raw values (Narwhals), and it's combined with `_call_with_expr_support` to catch the case where a non-literal expression reaches a literal-only API.

### Component 5: `_call_with_expr_support` Base Method

Each backend base class gets this method. Individual backend string methods call it explicitly.

```python
def _call_with_expr_support(
    self,
    fn: Callable[..., ExpressionT],
    *,
    function_key: str,
    **named_args: Any,
) -> ExpressionT:
    """Call a native backend function, enriching errors for known expression limitations.
    
    Args:
        fn: The native backend call (e.g., lambda: input.str.contains(pattern)).
        function_key: The FKEY_* enum value for registry lookup.
        **named_args: Parameter names mapped to their values, used to identify
            which parameter caused the error in registry lookup.
    """
    try:
        return fn()
    except Exception as exc:
        # Look up known limitations for this function
        for param_name in named_args:
            key = (function_key, param_name)
            limitation = self.KNOWN_EXPR_LIMITATIONS.get(key)
            if limitation and isinstance(exc, limitation.native_errors):
                raise BackendCapabilityError(
                    limitation.message,
                    backend=self.BACKEND_NAME,
                    function_key=function_key,
                    limitation=limitation,
                ) from exc
        # Not a known limitation — propagate unchanged
        raise
```

### Component 6: Backend Method Migration

Each backend string method is updated to:
1. Remove `_extract_literal_value` calls
2. For backends that accept expressions (Polars, Ibis): pass through directly
3. For backends requiring raw values (Narwhals): use `_extract_literal_if_possible` to unwrap literals, but let non-literal expressions pass through
4. Wrap the native call in `_call_with_expr_support`

**Before (Polars `contains`):**

```python
def contains(self, input, /, substring, case_sensitivity=None):
    pattern = self._extract_literal_value(substring)  # ← REMOVES EXPR CAPABILITY
    return input.str.contains(pattern, literal=True)
```

**After (Polars — accepts expressions natively):**

```python
def contains(self, input, /, substring, case_sensitivity=None):
    return self._call_with_expr_support(
        lambda: input.str.contains(substring, literal=True),
        function_key=FK.CONTAINS,
        substring=substring,
    )
```

**Before (Narwhals `starts_with`):**

```python
def starts_with(self, input, /, substring):
    prefix = self._extract_literal_value(substring)
    return input.str.starts_with(prefix)
```

**After (Narwhals — needs raw values for literals, catches column refs):**

```python
def starts_with(self, input, /, substring):
    prefix = self._extract_literal_if_possible(substring)
    return self._call_with_expr_support(
        lambda: input.str.starts_with(prefix),
        function_key=FK.STARTS_WITH,
        substring=substring,
    )
```

When `substring` is `nw.lit("hello")`, `_extract_literal_if_possible` unwraps it to `"hello"` and the native API works. When `substring` is a column reference, unwrapping fails (returns the Expr unchanged), the native API raises `TypeError`, and `_call_with_expr_support` enriches it via the registry.

For Polars and Ibis, `starts_with` accepts expressions natively — no extraction needed, no error, no registry lookup.

### Component 7: `_extract_literal_value` Deprecation

After string methods are migrated:
1. Mark `_extract_literal_value` as deprecated with a comment pointing to this spec
2. Non-string callers (datetime, rounding, logarithmic, name) continue using it until their own migration pass
3. Once all callers are migrated, remove the method entirely

`_extract_literal_if_possible` replaces it for the Narwhals use case — same literal unwrapping, but with an explicit name that documents why it exists and combined with `_call_with_expr_support` for the non-literal case.

### Component 8: Testing Strategy

**New test file:** `tests/cross_backend/test_expression_argument_types.py`

**Four argument type fixtures:**

```python
class ArgType(Enum):
    RAW_SCALAR = "raw_scalar"           # "world" — raw Python value
    EXPRESSION_LITERAL = "expr_literal"  # ma.lit("world") — LiteralNode
    COLUMN_REFERENCE = "col_ref"         # ma.col("pattern") — FieldReferenceNode
    COMPLEX_EXPRESSION = "complex_expr"  # ma.col("a").str.lower() — computed
```

**Test structure:** Parametrized across `(method, arg_type, backend)`. Each test:
1. Builds the expression with the given argument type
2. Compiles against the given backend
3. Asserts the result matches expected output

**xfail markers** applied per `(method, arg_type, backend)` where empirically known to fail:

```python
XFAILS = {
    # Narwhals: all column-ref and complex-expr args fail
    ("starts_with", ArgType.COLUMN_REFERENCE, "narwhals"): "narwhals requires literal",
    ("starts_with", ArgType.COMPLEX_EXPRESSION, "narwhals"): "narwhals requires literal",
    # ... all Narwhals parameterised methods ...
    
    # Polars: replace/replace_all pattern must be literal
    ("replace", ArgType.COLUMN_REFERENCE, "polars"): "polars dynamic pattern not supported",
    ("replace", ArgType.COMPLEX_EXPRESSION, "polars"): "polars dynamic pattern not supported",
    
    # Polars: pad length must be literal int
    ("lpad", ArgType.COLUMN_REFERENCE, "polars"): "polars pad requires literal length",
    ("lpad", ArgType.COMPLEX_EXPRESSION, "polars"): "polars pad requires literal length",
}
```

All xfails use `strict=True` so they break when backends add support.

**Existing tests** remain unchanged — they test literal arguments and will continue to pass.

### Scope

**Phase 1 (this spec):** String operations only — all 37+ methods across Polars, Ibis, Narwhals backends.

**Phase 2 (follow-up):** Extend to datetime, rounding, logarithmic, and name operations. Same pattern: remove `_extract_literal_value`, add `_call_with_expr_support`, populate registry, add tests.

**Phase 3 (follow-up):** Remove `_extract_literal_value` entirely once all callers are migrated.

### Files Changed

**New files:**
- `tests/cross_backend/test_expression_argument_types.py` — parametrized arg-type tests

**Modified files (core):**
- `src/mountainash/core/types.py` — add `KnownLimitation`, `BackendCapabilityError`

**Modified files (Polars backend):**
- `src/mountainash/expressions/backends/expression_systems/polars/base.py` — add `_call_with_expr_support`, `KNOWN_EXPR_LIMITATIONS`, deprecate `_extract_literal_value`
- `src/mountainash/expressions/backends/expression_systems/polars/substrait/expsys_pl_scalar_string.py` — remove `_extract_literal_value` calls, wrap with `_call_with_expr_support`

**Modified files (Ibis backend):**
- `src/mountainash/expressions/backends/expression_systems/ibis/base.py` — add `_call_with_expr_support`, empty `KNOWN_EXPR_LIMITATIONS`
- `src/mountainash/expressions/backends/expression_systems/ibis/substrait/expsys_ib_scalar_string.py` — remove `_extract_literal_value` calls, wrap with `_call_with_expr_support`

**Modified files (Narwhals backend):**
- `src/mountainash/expressions/backends/expression_systems/narwhals/base.py` — add `_call_with_expr_support`, `KNOWN_EXPR_LIMITATIONS`
- `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/expsys_nw_scalar_string.py` — remove `_extract_literal_value` calls, wrap with `_call_with_expr_support`

### Principle Update

The `arguments-vs-options.md` principle already identifies `_extract_literal_value` as problematic and calls for raising/documenting known limitations. After implementation, update the principle to:
- Reference `KnownLimitation` and `BackendCapabilityError` as the concrete mechanism
- Replace the `_extract_literal_value` examples with `_call_with_expr_support` examples
- Remove the "Future Considerations" bullet about auditing backend methods (done)

### Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Removing `_extract_literal_value` breaks existing literal-arg tests | Literal values pass through native APIs unchanged — no behavioural difference |
| Registry entries go stale | Strict xfails break when backends add support; stale entries are dormant (never consulted if no error) |
| `_call_with_expr_support` lambda overhead | Negligible — one lambda per method call, no allocation in the hot path |
| Catching too-broad exceptions | Registry entries specify exact native error types; non-matching errors propagate unchanged |
| Narwhals needs raw values, not `nw.lit()` expressions | Confirmed empirically: Narwhals `str.starts_with(nw.lit("hello"))` raises `TypeError`. The `_extract_literal_if_possible` method handles this — unwraps literal expressions to raw Python values while letting column references pass through to be caught by `_call_with_expr_support` |
