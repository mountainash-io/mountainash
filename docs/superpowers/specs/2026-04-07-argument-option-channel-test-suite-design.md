# Comprehensive Argument/Option Channel Test Suite

> **Status:** DRAFT
> **Date:** 2026-04-07
> **Related:** `2026-04-06-expression-argument-consistency-design.md`, `2026-04-07-expression-argument-consistency-phase2-design.md`

## Goal

Systematically verify, for every operation in the mountainash-expressions API, that the argument and option channels behave correctly across all backends. This suite is the enforcement mechanism for the `arguments-vs-options.md` principle.

## Motivation

Phase 1 (strings) and Phase 2 (datetime/name/rounding/logarithmic/null/window) migrated the expression system to the `_call_with_expr_support` + `KNOWN_EXPR_LIMITATIONS` pattern. Existing tests cover string operations (114 tests) and a handful of non-string operations (18 tests), but coverage is ad-hoc and has drift risk: nothing prevents a new operation from shipping without argument/option channel tests.

This spec defines a **comprehensive, drift-proof test suite** that:

1. Verifies every expression-typed parameter accepts raw scalars, `ma.lit(...)`, `ma.col(...)`, and complex expressions across Polars, Ibis, and Narwhals.
2. Verifies every option parameter accepts raw Python values and rejects expressions at the API builder level.
3. Tracks known backend limitations via strict xfail (self-healing) AND positively asserts error enrichment (message, workaround, upstream_issue).
4. Detects drift via a coverage guard that introspects protocols and fails when an operation has no test entry.
5. Doubles as a **protocol typing audit** — surfaces parameters that are typed inconsistently with their actual channel.

## Scope

**In scope:**
- All `Substrait*ExpressionSystemProtocol` and `Mountainash*` expression protocols
- Polars, Ibis, Narwhals backends
- Argument channel (expression-typed params)
- Option channel (literal-typed params)
- Error enrichment assertions against `KNOWN_EXPR_LIMITATIONS`

**Out of scope:**
- Relational AST operations (separate future suite)
- `ma.conform` operations
- TypeSpec / schema validation
- Performance / benchmarks

## Architecture

### File Layout

```
tests/cross_backend/argument_types/
├── conftest.py                        # make_df(data, backend) helper
├── _introspection.py                  # Protocol walker, arg/option classifier
├── test_coverage_guard.py             # Meta-test: introspected ops ⊆ tested ops
├── test_arg_types_string.py           # Migrated from existing file
├── test_arg_types_arithmetic.py
├── test_arg_types_comparison.py
├── test_arg_types_boolean.py
├── test_arg_types_datetime.py
├── test_arg_types_name.py
├── test_arg_types_rounding.py
├── test_arg_types_logarithmic.py
├── test_arg_types_null.py
├── test_arg_types_window.py
├── test_arg_types_aggregate.py
├── test_option_channel.py             # All options, uniform pattern
└── test_error_enrichment.py           # Positive assertions on BackendCapabilityError
```

### Key Modules

**`_introspection.py`** — walks protocol classes and classifies parameters.

```python
@dataclass(frozen=True)
class ProtocolParam:
    op_name: str                      # e.g. "contains"
    function_key: Any                 # e.g. FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS
    param_name: str                   # e.g. "substring"
    kind: Literal["argument", "option"]
    category: str                     # e.g. "string", "datetime"

def introspect_protocols() -> list[ProtocolParam]: ...
```

Classification rule:
- Parameter typed as `ExpressionT` → `argument`
- Parameter typed as concrete Python type (`int`, `str`, `bool`, etc.) → `option`
- Parameter typed as `Any` → requires explicit declaration in per-category file (coverage guard flags it)

**`conftest.py`** — shared `make_df(data: dict, backend: str) -> native_df` helper. Each per-category file declares its own raw data dict.

**Per-category files** — hardcode the operation list + minimal data dict, parametrize over `(op, input_type, backend)`. Use `@pytest.mark.xfail(strict=True, raises=BackendCapabilityError)` driven by registry lookups.

Input type matrix (4 types per argument-typed param):
1. **Raw scalar** — `"hello"`, `5`, `10.0`
2. **Literal expression** — `ma.lit("hello")`
3. **Column reference** — `ma.col("pattern")`
4. **Complex expression** — `ma.col("pattern").str.lower()`

**`test_coverage_guard.py`** — single meta-test that:
1. Calls `introspect_protocols()` to collect all argument-channel `(function_key, param_name)` pairs.
2. Collects all `(function_key, param_name)` pairs declared in per-category files via a module-level `TESTED_PARAMS` list.
3. Asserts: introspected set == tested set. Fails loudly with the diff.

**`test_option_channel.py`** — for every option parameter, asserts:
- Accepts raw Python value of the declared type
- Raises `TypeError` (or similar) when passed `ma.col(...)` or `ma.lit(...)` at the API builder level

**`test_error_enrichment.py`** — for each entry in each backend's `KNOWN_EXPR_LIMITATIONS`:
- Triggers the limitation (passes a column reference to the known-limited parameter)
- Catches `BackendCapabilityError`
- Asserts error contains `limitation.message`, `limitation.workaround`, and `limitation.upstream_issue` if set

## Phases

### Phase 0 — Protocol Typing Audit

Build `_introspection.py` first. Run it and review the classified table. Fix any mistyped protocol parameters before writing tests:
- `ExpressionT` on universally-literal params → should be concrete type
- Concrete type on params that should accept expressions → should be `ExpressionT`

Each fix is its own commit. Outcome: protocols become the trustworthy source of truth.

### Phase 1 — Infrastructure

- Create `conftest.py` with `make_df` helper
- Create `test_coverage_guard.py` skeleton (initially fails — no files registered)
- Create `test_error_enrichment.py` iterating all three backend registries

### Phase 2 — Per-Category Argument Tests

One file per category, one commit each, in dependency order:

1. Migrate existing `test_expression_argument_types.py` → `test_arg_types_string.py`
2. Migrate existing `test_expression_argument_types_nonstring.py` → split across relevant category files
3. `test_arg_types_arithmetic.py`
4. `test_arg_types_comparison.py`
5. `test_arg_types_boolean.py`
6. `test_arg_types_null.py`
7. `test_arg_types_rounding.py`
8. `test_arg_types_logarithmic.py`
9. `test_arg_types_datetime.py`
10. `test_arg_types_name.py`
11. `test_arg_types_window.py`
12. `test_arg_types_aggregate.py`

Coverage guard test turns green incrementally as each category is filled.

### Phase 3 — Option Channel

Write `test_option_channel.py` covering every option parameter surfaced by the introspector.

### Phase 4 — CI Integration & Docs

- Confirm suite runs in `hatch run test:test`
- Update `arguments-vs-options.md` principle with a "Testing" section
- Update `known-divergences.md` if Phase 0 surfaces new divergences

## Success Criteria

- Every expression-typed parameter in every protocol has at least one test per backend per input type (4 × 3 = 12 assertions minimum)
- Every option parameter is verified to reject expressions
- Every `KNOWN_EXPR_LIMITATIONS` entry has both a strict xfail and an error-enrichment assertion
- `test_coverage_guard.py` passes — no drift
- Protocol typing audit surfaces zero anomalies after Phase 0

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Introspection misclassifies `Any`-typed params | Treat `Any` as explicit-declaration-required; coverage guard flags unclassified params |
| Aggregate/window ops have structural requirements (`.over()`, group_by context) | Per-category files define their own execution wrapper |
| Protocol typing fixes in Phase 0 break existing tests | Each fix is its own commit; run full suite after each |
| Registry lookups in xfail marks are fragile | Centralize the xfail helper in `conftest.py`; accepts `(backend, function_key, param_name)` |

## Open Questions

None — all design decisions are locked.

## Anti-Patterns to Avoid

- **Hardcoding expected limitations in test files** instead of driving from the registry — defeats self-healing
- **Skipping the coverage guard** because "we'll remember to add the test" — we won't
- **One giant parametrized file** instead of per-category — makes failures harder to locate
- **Testing backend quirks instead of the abstraction** — if Polars' `str.contains` behaves differently, that's a registry entry, not a test adjustment

## References

- `mountainash-central/01.principles/mountainash-expressions/e.cross-backend/arguments-vs-options.md`
- `mountainash-central/01.principles/mountainash-expressions/e.cross-backend/known-divergences.md`
- `docs/superpowers/specs/2026-04-06-expression-argument-consistency-design.md`
- `docs/superpowers/specs/2026-04-07-expression-argument-consistency-phase2-design.md`
- Existing tests: `tests/cross_backend/test_expression_argument_types.py`, `tests/cross_backend/test_expression_argument_types_nonstring.py`
