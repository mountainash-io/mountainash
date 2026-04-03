# Protocol-Implementation Alignment Design

**Date:** 2026-03-25
**Status:** Draft
**Branch:** feature/substrait_alignment

## Problem

The protocol alignment tests catch 20 failures total: 16 in `test_protocol_alignment.py` (protocol-implementation drift) and 4 in `test_ternary_auto_booleanize.py` (missing `xor_parity` backend implementation). The Substrait refactor introduced drift between protocols (source of truth) and their implementations at three layers: API builders, backend expression systems, and function key enums.

Additionally, `test_namespace_infrastructure.py` had stale imports referencing removed modules (`api_namespaces`). These have already been fixed in this session by updating imports to the current `api_builders` paths and enum names.

## Principles

1. **Protocols are the source of truth.** Implementations conform to protocols, not the other way around.
2. **All public methods get protocol coverage.** Methods on implementations that aren't in any protocol are legacy spikes that must be formally declared in the appropriate protocol.
3. **Substrait/extension split is internal.** Users see a unified API surface (e.g., `.dt` exposes both Substrait and extension methods seamlessly).
4. **Reverse operators get protocol coverage.** Python interop plumbing (`rfloor_divide`, `rmodulo`, etc.) is tracked and aligned like any other function.

## Design

### Layer 1: Protocol Updates (source of truth — update first)

#### Substrait API Builder Protocols

**`SubstraitScalarArithmeticAPIBuilderProtocol`** — add:
- `modulo(other)` — alias for `modulus`
- `rmodulo(other)` — alias for `rmodulus`

**`SubstraitScalarBooleanAPIBuilderProtocol`** — add:
- `xor_(other)` — user-facing alias for `xor` (Python reserved word)

**`SubstraitScalarComparisonAPIBuilderProtocol`** — add:
- `eq(other)` — alias for `equal`
- `ne(other)` — alias for `not_equal`
- `ge(other)` — alias for `gte`
- `le(other)` — alias for `lte`

**`SubstraitScalarStringAPIBuilderProtocol`** — add:
- `len()` — alias for `char_length`
- `length()` — alias for `char_length`
- `regex_contains(pattern)` — alias for `regexp_match_substring` (returns bool)
- `regex_match(pattern)` — alias for `regexp_match_substring`
- `regex_replace(pattern, replacement)` — alias for `regexp_replace`
- `slice(offset, length)` — alias for `substring`

#### Mountainash API Builder Protocols

**`MountainAshScalarArithmeticAPIBuilderProtocol`** — add:
- `rfloor_divide(other)` — reverse floor division for `__rfloordiv__`

**`MountainAshScalarBooleanAPIBuilderProtocol`** — add:
- `always_true()` — boolean constant TRUE
- `always_false()` — boolean constant FALSE
- `xor_parity(*others)` — TRUE when odd number of inputs are TRUE

**`MountainAshScalarDatetimeAPIBuilderProtocol`** — add:
- `assume_timezone(timezone)` — assume local timestamp is in given timezone
- `strftime(format)` — format datetime as string
- `to_timezone(timezone)` — convert to specified timezone

#### Mountainash Backend ExpressionSystem Protocols

**`MountainAshScalarDatetimeExpressionSystemProtocol`**:
- **Add:** `assume_timezone`, `strftime`, `to_timezone`, `extract`, `extract_boolean`
- **Remove:** `between_last`, `newer_than`, `older_than`, `within_last`, `within_next`

Rationale: The natural-language temporal filters (`within_last`, etc.) compute thresholds at API build time and delegate to `.gt()`/`.lt()`. They are API-layer sugar, not backend operations. The timezone/formatting and extract helpers are real backend operations that need protocol coverage.

### Layer 2: Implementation Fixes

#### API Builder Fixes

**`MountainAshNameAPIBuilder`** — rename methods to match protocol:
- `to_upper` → `name_to_upper`
- `to_lower` → `name_to_lower`

**`MountainAshNullAPIBuilder`** — fix parameter name to match protocol:
- `fill_null(value)` → `fill_null(replacement)`

#### Substrait Datetime Builder Deduplication

The `SubstraitScalarDatetimeAPIBuilder` is a full copy of `MountainAshScalarDatetimeAPIBuilder` — 45 identical methods, all using `FKEY_MOUNTAINASH_SCALAR_DATETIME` keys. The Substrait protocol only declares 3 methods.

**Fix:**
1. Strip all non-Substrait methods from `SubstraitScalarDatetimeAPIBuilder`. Add `local_timestamp` (declared in protocol but never implemented — `to_timezone` exists as the extension equivalent but `local_timestamp` is the Substrait-named method). Keep `assume_timezone` and `strftime`. Final builder has exactly the 3 protocol methods: `local_timestamp`, `assume_timezone`, `strftime`
2. Create a composed `DatetimeAPIBuilder` that inherits from both builders:
   ```python
   class DatetimeAPIBuilder(
       MountainAshScalarDatetimeAPIBuilder,   # 45+ extension methods
       SubstraitScalarDatetimeAPIBuilder,      # 3 Substrait methods
   ):
       pass
   ```
3. Update `BooleanExpressionAPI` to point `.dt` descriptor at `DatetimeAPIBuilder`

This keeps the internal Substrait/extension separation clean while presenting a unified `.dt` namespace to users. MRO handles overlaps (extension has `assume_timezone`/`strftime` too — same FKEY, either resolution is correct).

#### Enum Fix

Move `XOR_PARITY` from `FKEY_MOUNTAINASH_SCALAR_COMPARISON` to `FKEY_MOUNTAINASH_SCALAR_BOOLEAN`.

Note: `FKEY_MOUNTAINASH_SCALAR_BOOLEAN` does not currently exist as an enum class — it needs to be created in `enums.py` to house `XOR_PARITY` (and potentially `ALWAYS_TRUE`/`ALWAYS_FALSE` if they become enum-backed). After the move, `FKEY_MOUNTAINASH_SCALAR_COMPARISON` will contain only `IS_CLOSE` — this is acceptable as a single-member enum for now.

Update all references:
- API builder (`MountainAshScalarBooleanAPIBuilder`)
- Function mapping registry in `core/expression_system/function_mapping/definitions.py` (contains the `FKEY_MOUNTAINASH_SCALAR_COMPARISON.XOR_PARITY` reference that drives visitor dispatch)
- Any tests referencing the enum

### Layer 3: Backend Implementations

#### null_if — all 3 backends

Implement `null_if(input, condition)` on:
- `MountainAshPolarsNullExpressionSystem`
- `MountainAshIbisNullExpressionSystem`
- `MountainAshNarwhalsNullExpressionSystem`

Semantics: SQL `NULLIF(input, condition)` — returns NULL when input equals condition, otherwise returns input.

**Polars:** `pl.when(input.eq(condition)).then(None).otherwise(input)`
**Ibis:** `input.nullif(condition)` (native support)
**Narwhals:** `nw.when(input.eq(condition)).then(None).otherwise(input)`

#### xor_parity — all 3 backends

Implement `xor_parity(*args)` on:
- `MountainAshPolarsScalarBooleanExpressionSystem` (or equivalent extension)
- `MountainAshIbisScalarBooleanExpressionSystem`
- `MountainAshNarwhalsScalarBooleanExpressionSystem`

Semantics: Returns TRUE when an odd number of inputs are TRUE. For ternary logic (-1/0/1), if any input is UNKNOWN (0), result is UNKNOWN; otherwise count TRUE values and check parity.

### Layer 4: Test Fixes (already completed)

`test_namespace_infrastructure.py` — import paths updated in this session:
- `BaseExpressionNamespace` → `BaseExpressionAPIBuilder`
- `api_namespaces` → `api_builders`
- `KEY_SCALAR_*` → `FKEY_SUBSTRAIT_SCALAR_*`
- `MOUNTAINASH_*` → `FKEY_MOUNTAINASH_*`
- Namespace class references updated to builder class names

## Files Changed

### Protocols (update)
- `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_arithmetic.py`
- `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_boolean.py`
- `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_comparison.py`
- `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py`
- `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_arithmetic.py`
- `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_boolean.py`
- `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_datetime.py`
- `core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py`

### API Builders (fix)
- `core/expression_api/api_builders/substrait/api_bldr_scalar_datetime.py` — strip to 3 methods
- `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py` — rename methods
- `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_null.py` — fix param name
- `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_boolean.py` — update enum ref
- `core/expression_api/boolean.py` — create composed DatetimeAPIBuilder, update .dt descriptor

### Enums (fix)
- `core/expression_system/function_keys/enums.py` — move XOR_PARITY

### Backends (implement)
- `backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_null.py`
- `backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_null.py`
- `backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py`
- `backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_boolean.py`
- `backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_boolean.py`
- `backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_boolean.py`

### Function Registry (update)
- `core/expression_system/function_mapping/definitions.py` — update XOR_PARITY enum reference

### Already Fixed
- `tests/unit/test_namespace_infrastructure.py` — import paths
- `src/mountainash_expressions/core/expression_api/api_base.py` — stale TYPE_CHECKING import

## Success Criteria

- All 16 currently-failing `test_protocol_alignment.py` tests pass
- All 4 `test_ternary_xor_parity_boolean_coercion` tests pass
- All `test_namespace_infrastructure.py` tests pass (already fixed)
- No regressions in the 1762 currently-passing tests
- Full test suite: 0 failures
