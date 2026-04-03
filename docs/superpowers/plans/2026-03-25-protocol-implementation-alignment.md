# Protocol-Implementation Alignment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 20 test failures caused by protocol-implementation drift: 16 in `test_protocol_alignment.py` and 4 in `test_ternary_auto_booleanize.py`.

**Architecture:** Protocols are the source of truth. We update protocols to declare all methods that should exist, then fix implementations to match, then implement missing backend methods. Layer by layer: protocols → API builders → enums → backends.

**Tech Stack:** Python 3.12, Polars, Ibis, Narwhals, pytest, hatch

**Spec:** `docs/superpowers/specs/2026-03-25-protocol-implementation-alignment-design.md`

**Test command:** `hatch run test:test-quick` (runs full suite without coverage)

**Baseline:** 1762 passed, 20 failed, 3 skipped, 46 xfailed

---

## File Map

All paths relative to `src/mountainash_expressions/`.

### Protocols to update
| File | Change |
|------|--------|
| `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_arithmetic.py` | Add `modulo`, `rmodulo` |
| `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_boolean.py` | Add `xor_` |
| `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_comparison.py` | Add `eq`, `ne`, `ge`, `le` |
| `core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py` | Add `len`, `length`, `regex_contains`, `regex_match`, `regex_replace`, `slice` |
| `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_arithmetic.py` | Add `rfloor_divide` |
| `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_boolean.py` | Add `always_true`, `always_false` |
| `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_datetime.py` | Add `assume_timezone`, `strftime`, `to_timezone` |
| `core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py` | Add `assume_timezone`, `strftime`, `to_timezone`, `extract`, `extract_boolean`; Remove `between_last`, `newer_than`, `older_than`, `within_last`, `within_next` |

### Implementations to fix
| File | Change |
|------|--------|
| `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py` | Rename `to_upper`→`name_to_upper`, `to_lower`→`name_to_lower` |
| `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_null.py` | Rename param `value`→`replacement` in `fill_null` |
| `core/expression_api/api_builders/substrait/api_bldr_scalar_datetime.py` | Strip to 3 methods, add `local_timestamp` |
| `core/expression_api/boolean.py` | Create composed `DatetimeAPIBuilder`, update `.dt` descriptor |
| `core/expression_system/function_keys/enums.py` | Create `FKEY_MOUNTAINASH_SCALAR_BOOLEAN`, move `XOR_PARITY` |
| `core/expression_system/function_mapping/definitions.py` | Update `XOR_PARITY` enum reference |
| `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_boolean.py` | Update enum import |

### Backends to fix
| File | Change |
|------|--------|
| `backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_null.py` | Add `null_if`, fix `Any` import |
| `backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_null.py` | Add `null_if`, fix `Any` import |
| `backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py` | Add `null_if` |
| `backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_boolean.py` | Fix broken `xor_parity` |
| `backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_boolean.py` | Fix broken `xor_parity` |
| `backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_boolean.py` | Fix broken `xor_parity` |

---

## Task 1: Update Substrait API Builder Protocols

**Files:**
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_arithmetic.py`
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_boolean.py`
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_comparison.py`
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/substrait/prtcl_api_bldr_scalar_string.py`

- [ ] **Step 1: Add `modulo`/`rmodulo` to arithmetic protocol**

Add after `rmodulus` in `prtcl_api_bldr_scalar_arithmetic.py`:

```python
def modulo(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
    """Alias for modulus. Modulo (remainder) operation."""
    ...

def rmodulo(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
    """Alias for rmodulus. Reverse modulo for __rmod__."""
    ...
```

- [ ] **Step 2: Add `xor_` to boolean protocol**

Add after `xor` in `prtcl_api_bldr_scalar_boolean.py`:

```python
def xor_(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """User-facing alias for xor (Python reserved word)."""
    ...
```

- [ ] **Step 3: Add short aliases to comparison protocol**

Add after `gte` in `prtcl_api_bldr_scalar_comparison.py`:

```python
def eq(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Alias for equal."""
    ...

def ne(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Alias for not_equal."""
    ...

def ge(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Alias for gte."""
    ...

def le(self, other: Union[BaseExpressionAPI, ExpressionNode, Any]) -> BaseExpressionAPI:
    """Alias for lte."""
    ...
```

- [ ] **Step 4: Add convenience methods to string protocol**

Add at end of `prtcl_api_bldr_scalar_string.py`:

```python
# Convenience aliases

def len(self) -> BaseExpressionAPI:
    """Alias for char_length. String length in characters."""
    ...

def length(self) -> BaseExpressionAPI:
    """Alias for char_length. String length in characters."""
    ...

def regex_contains(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], *, case_sensitive: bool = True) -> BaseExpressionAPI:
    """Alias for regexp_match_substring (returns bool). Test if pattern matches."""
    ...

def regex_match(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], *, case_sensitive: bool = True) -> BaseExpressionAPI:
    """Alias for regexp_match_substring."""
    ...

def regex_replace(self, pattern: Union[BaseExpressionAPI, ExpressionNode, Any], replacement: Union[BaseExpressionAPI, ExpressionNode, Any], case_sensitive: bool = True) -> BaseExpressionAPI:
    """Alias for regexp_replace."""
    ...

def slice(self, start: Union[BaseExpressionAPI, ExpressionNode, Any, int], length: Optional[Union[BaseExpressionAPI, ExpressionNode, Any, int]] = None) -> BaseExpressionAPI:
    """Alias for substring."""
    ...
```

- [ ] **Step 5: Run protocol alignment tests to verify progress**

Run: `hatch run test:test-quick tests/unit/test_protocol_alignment.py::TestSubstraitAPIBuilderAlignment -v --tb=short`

Expected: The 5 Substrait API builder failures should now pass (arithmetic, boolean, comparison, datetime, string). Datetime may still fail due to the 42 extra methods — that gets fixed in Task 5.

- [ ] **Step 6: Commit**

```
git add src/mountainash_expressions/core/expression_protocols/api_builders/substrait/
git commit -m "feat: add missing method declarations to Substrait API builder protocols"
```

---

## Task 2: Update Mountainash API Builder Protocols

**Files:**
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_arithmetic.py`
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_boolean.py`
- Modify: `src/mountainash_expressions/core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_scalar_datetime.py`

- [ ] **Step 1: Add `rfloor_divide` to arithmetic protocol**

Add after `floor_divide` in `prtcl_api_bldr_ext_ma_scalar_arithmetic.py`:

```python
def rfloor_divide(self, other: Union[BaseExpressionAPI, ExpressionNode, Any], /) -> BaseExpressionAPI:
    """Reverse floor division for __rfloordiv__."""
    ...
```

- [ ] **Step 2: Add `always_true`/`always_false` to boolean protocol**

Add to `prtcl_api_bldr_ext_ma_scalar_boolean.py` (which currently only has `xor_parity`):

```python
def always_true(self) -> BaseExpressionAPI:
    """Boolean constant TRUE."""
    ...

def always_false(self) -> BaseExpressionAPI:
    """Boolean constant FALSE."""
    ...
```

- [ ] **Step 3: Add timezone/formatting methods to datetime protocol**

Add at end of `prtcl_api_bldr_ext_ma_scalar_datetime.py`:

```python
# Timezone Operations

def to_timezone(self, timezone: str) -> BaseExpressionAPI:
    """Convert to specified timezone."""
    ...

def assume_timezone(self, timezone: str) -> BaseExpressionAPI:
    """Assume the timestamp is in the specified timezone."""
    ...

# Formatting

def strftime(self, format: str) -> BaseExpressionAPI:
    """Format datetime as string using strftime format codes."""
    ...
```

- [ ] **Step 4: Run Mountainash API builder alignment tests**

Run: `hatch run test:test-quick tests/unit/test_protocol_alignment.py::TestMountainashAPIBuilderAlignment -v --tb=short`

Expected: arithmetic, boolean, and datetime Mountainash builder tests should pass. Name and null may still fail (fixed in Task 3).

- [ ] **Step 5: Commit**

```
git add src/mountainash_expressions/core/expression_protocols/api_builders/extensions_mountainash/
git commit -m "feat: add missing method declarations to Mountainash API builder protocols"
```

---

## Task 3: Fix API Builder Implementation Mismatches

**Files:**
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_null.py`

- [ ] **Step 1: Rename methods in name builder**

In `api_bldr_ext_ma_name.py`, rename:
- `def to_upper(self)` → `def name_to_upper(self)`
- `def to_lower(self)` → `def name_to_lower(self)`

Also update any internal references to the FKEY enum if needed. The FKEY enum already has `NAME_TO_UPPER` and `NAME_TO_LOWER`.

- [ ] **Step 2: Update tests that call the old method names**

`tests/cross_backend/test_name.py` calls `.name.to_upper()` (lines 291, 308, 322) and `.name.to_lower()` (lines 353, 370, 384). Update all references:
- `to_upper` → `name_to_upper`
- `to_lower` → `name_to_lower`

Also search for any other references: `grep -r "\.to_upper\|\.to_lower" tests/`

- [ ] **Step 3: Fix parameter name in null builder**

In `api_bldr_ext_ma_null.py`, rename the `fill_null` parameter:
- `def fill_null(self, value: ...)` → `def fill_null(self, replacement: ...)`

Update any usage of `value` inside the method body to `replacement`.

- [ ] **Step 3: Run alignment tests for name and null**

Run: `hatch run test:test-quick tests/unit/test_protocol_alignment.py::TestMountainashAPIBuilderAlignment -v --tb=short`

Expected: Name and null alignment tests should pass.

- [ ] **Step 4: Run full test suite to check for regressions from renames**

Run: `hatch run test:test-quick --tb=short`

The `name_to_upper`/`name_to_lower` rename changes the public API on the `.name` namespace. Check if any existing tests call `.name.to_upper()` or `.name.to_lower()` — these would need updating.

- [ ] **Step 5: Commit**

```
git add src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_name.py
git add src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_null.py
git commit -m "fix: rename name builder methods and null builder param to match protocols"
```

---

## Task 4: Create FKEY_MOUNTAINASH_SCALAR_BOOLEAN Enum and Move XOR_PARITY

**Files:**
- Modify: `src/mountainash_expressions/core/expression_system/function_keys/enums.py`
- Modify: `src/mountainash_expressions/core/expression_system/function_mapping/definitions.py`
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_boolean.py`

- [ ] **Step 1: Create new enum and move XOR_PARITY**

In `enums.py`, add a new enum class after `FKEY_MOUNTAINASH_SCALAR_COMPARISON`:

```python
class FKEY_MOUNTAINASH_SCALAR_BOOLEAN(Enum):
    """Mountainash boolean extensions not in Substrait."""

    XOR_PARITY = "xor_parity"
```

Remove `XOR_PARITY` from `FKEY_MOUNTAINASH_SCALAR_COMPARISON` (leaving only `IS_CLOSE`).

- [ ] **Step 2: Update function mapping definitions**

In `definitions.py`, find the `ExpressionFunctionDef` that references `FKEY_MOUNTAINASH_SCALAR_COMPARISON.XOR_PARITY` and change to `FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY`. Update the import to include the new enum class.

- [ ] **Step 3: Update API builder enum reference**

In `api_bldr_ext_ma_scalar_boolean.py`, change the import and usage from `FKEY_MOUNTAINASH_SCALAR_COMPARISON.XOR_PARITY` to `FKEY_MOUNTAINASH_SCALAR_BOOLEAN.XOR_PARITY`.

- [ ] **Step 4: Search for any other references to the old enum path**

Run: `grep -r "FKEY_MOUNTAINASH_SCALAR_COMPARISON.XOR_PARITY" src/ tests/`

Fix any remaining references.

- [ ] **Step 5: Run tests to verify no breakage**

Run: `hatch run test:test-quick --tb=short`

Expected: Same pass/fail count — this is a refactor, not a fix.

- [ ] **Step 6: Commit**

```
git add src/mountainash_expressions/core/expression_system/function_keys/enums.py
git add src/mountainash_expressions/core/expression_system/function_mapping/definitions.py
git add src/mountainash_expressions/core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_scalar_boolean.py
git commit -m "refactor: create FKEY_MOUNTAINASH_SCALAR_BOOLEAN enum, move XOR_PARITY"
```

---

## Task 5: Substrait Datetime Builder Deduplication

**Files:**
- Modify: `src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_datetime.py`
- Modify: `src/mountainash_expressions/core/expression_api/boolean.py`

- [ ] **Step 1: Strip SubstraitScalarDatetimeAPIBuilder to 3 methods**

Replace the entire body of `SubstraitScalarDatetimeAPIBuilder` in `api_bldr_scalar_datetime.py` with only:

```python
class SubstraitScalarDatetimeAPIBuilder(BaseExpressionAPIBuilder, SubstraitScalarDatetimeAPIBuilderProtocol):
    """Substrait datetime operations (timezone and formatting only).

    Substrait defines: local_timestamp, assume_timezone, strftime.
    All other datetime operations are in MountainAshScalarDatetimeAPIBuilder.
    """

    def local_timestamp(self, timezone: str) -> BaseExpressionAPI:
        """Get current timestamp in the specified timezone.

        Substrait: local_timestamp

        Args:
            timezone: IANA timezone name (e.g., "America/New_York", "UTC").

        Returns:
            New ExpressionAPI with local_timestamp node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_SUBSTRAIT_SCALAR_DATETIME.LOCAL_TIMESTAMP,
            arguments=[self._node],
            options={"timezone": timezone},
        )
        return self._build(node)

    def assume_timezone(self, timezone: str) -> BaseExpressionAPI:
        """Assume the timestamp is in the specified timezone.

        Substrait: assume_timezone

        Args:
            timezone: IANA timezone name.

        Returns:
            New ExpressionAPI with assume_timezone node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.ASSUME_TIMEZONE,
            arguments=[self._node],
            options={"timezone": timezone},
        )
        return self._build(node)

    def strftime(self, format: str) -> BaseExpressionAPI:
        """Format datetime as string.

        Substrait: strftime

        Args:
            format: Format string (e.g., "%Y-%m-%d %H:%M:%S").

        Returns:
            New ExpressionAPI with strftime node.
        """
        node = ScalarFunctionNode(
            function_key=FKEY_MOUNTAINASH_SCALAR_DATETIME.STRFTIME,
            arguments=[self._node],
            options={"format": format},
        )
        return self._build(node)
```

**Important:** `FKEY_SUBSTRAIT_SCALAR_DATETIME` currently only has `EXTRACT` and `EXTRACT_BOOLEAN` — there is no `LOCAL_TIMESTAMP` member. You must add it as a prerequisite:

In `core/expression_system/function_keys/enums.py`, add to `FKEY_SUBSTRAIT_SCALAR_DATETIME`:
```python
class FKEY_SUBSTRAIT_SCALAR_DATETIME(Enum):
    EXTRACT = auto()
    EXTRACT_BOOLEAN = auto()
    LOCAL_TIMESTAMP = auto()  # ADD THIS
```

Keep `FKEY_MOUNTAINASH_SCALAR_DATETIME` imported for `assume_timezone`/`strftime` which use extension keys.

- [ ] **Step 2: Create composed DatetimeAPIBuilder in boolean.py**

In `boolean.py`, add after the existing imports:

```python
from .api_builders.extensions_mountainash import MountainAshScalarDatetimeAPIBuilder

class DatetimeAPIBuilder(
    MountainAshScalarDatetimeAPIBuilder,   # 45+ extension methods
    SubstraitScalarDatetimeAPIBuilder,      # 3 Substrait methods
):
    """Composed datetime builder exposing both Substrait and extension methods."""
    pass
```

Then update the `.dt` descriptor:

```python
# Change from:
dt = NamespaceDescriptor(SubstraitScalarDatetimeAPIBuilder)
# To:
dt = NamespaceDescriptor(DatetimeAPIBuilder)
```

- [ ] **Step 3: Run Substrait datetime alignment test**

Run: `hatch run test:test-quick "tests/unit/test_protocol_alignment.py::TestSubstraitAPIBuilderAlignment::test_substrait_api_builder_alignment[SubstraitScalarDatetimeAPIBuilderProtocol-scalar_datetime]" -v --tb=long`

Expected: PASS — the Substrait datetime builder now has exactly 3 methods matching its protocol.

- [ ] **Step 4: Run full test suite to verify .dt namespace still works**

Run: `hatch run test:test-quick --tb=short`

Expected: All datetime-related cross-backend tests still pass (they use `.dt.year()`, `.dt.add_days()`, etc. which now route through `DatetimeAPIBuilder` → `MountainAshScalarDatetimeAPIBuilder`).

- [ ] **Step 5: Commit**

```
git add src/mountainash_expressions/core/expression_api/api_builders/substrait/api_bldr_scalar_datetime.py
git add src/mountainash_expressions/core/expression_api/boolean.py
git commit -m "refactor: strip Substrait datetime builder to 3 methods, compose with extension"
```

---

## Task 6: Update Backend ExpressionSystem Datetime Protocol

**Files:**
- Modify: `src/mountainash_expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py`

- [ ] **Step 1: Remove API-layer methods from backend protocol**

Remove these method declarations from `prtcl_expsys_ext_ma_scalar_datetime.py`:
- `within_last`
- `older_than`
- `newer_than`
- `within_next`
- `between_last`

These are API-layer sugar that compute thresholds at build time — they never reach the backend.

- [ ] **Step 2: Add real backend operations to protocol**

Add these method declarations:

Signatures verified against all 3 Mountainash extension backends (Polars/Ibis/Narwhals):

```python
def extract(self, x: SupportedExpressions, component: SupportedExpressions, /) -> SupportedExpressions:
    """Extract a datetime component. Dispatches year/month/day/etc."""
    ...

def extract_boolean(self, x: SupportedExpressions, /) -> SupportedExpressions:
    """Extract a boolean datetime property (is_leap_year, is_dst)."""
    ...

def assume_timezone(self, x: SupportedExpressions, *, timezone: str) -> SupportedExpressions:
    """Assume the timestamp is in the specified timezone."""
    ...

def strftime(self, x: SupportedExpressions, *, format: str) -> SupportedExpressions:
    """Format datetime as string."""
    ...

def to_timezone(self, x: SupportedExpressions, *, timezone: str) -> SupportedExpressions:
    """Convert to specified timezone."""
    ...
```

Note: `extract` takes `component` as a positional `SupportedExpressions` arg (not a string). `extract_boolean` takes only `x` (component is determined by the function key). Verify exact signatures against the Polars extension backend at `expsys_pl_ext_ma_scalar_datetime.py` lines 77-128.

- [ ] **Step 3: Run backend datetime alignment tests**

Run: `hatch run test:test-quick tests/unit/test_protocol_alignment.py::TestMountainashExtensionAlignment -v --tb=short -k "scalar_datetime"`

Expected: All 3 backend datetime alignment tests (Polars, Ibis, Narwhals) should pass.

- [ ] **Step 4: Commit**

```
git add src/mountainash_expressions/core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_scalar_datetime.py
git commit -m "fix: align backend datetime protocol with actual backend operations"
```

---

## Task 7: Implement null_if in All Backends

**Files:**
- Modify: `src/mountainash_expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_null.py`
- Modify: `src/mountainash_expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_null.py`
- Modify: `src/mountainash_expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py`

- [ ] **Step 1: Add null_if to Polars backend**

In `expsys_pl_ext_ma_null.py`, add `Any` to imports and add method:

```python
from typing import TYPE_CHECKING, Any

# ... existing code ...

def null_if(
    self,
    input: PolarsExpr,
    condition: Any,
    /,
) -> PolarsExpr:
    """Replace values equal to condition with NULL.

    SQL NULLIF(input, condition) semantics.

    Args:
        input: Expression to check.
        condition: Value to compare against — if equal, returns NULL.

    Returns:
        Expression with matching values replaced by NULL.
    """
    return pl.when(input.eq(condition)).then(None).otherwise(input)
```

- [ ] **Step 2: Add null_if to Ibis backend**

In `expsys_ib_ext_ma_null.py`, add `Any` to imports and add method:

```python
from typing import TYPE_CHECKING, Any

# ... existing code ...

def null_if(
    self,
    input: IbisExpr,
    condition: Any,
    /,
) -> IbisExpr:
    """Replace values equal to condition with NULL.

    Args:
        input: Expression to check.
        condition: Value to compare against.

    Returns:
        Expression with matching values replaced by NULL.
    """
    return input.nullif(condition)
```

- [ ] **Step 3: Add null_if to Narwhals backend**

In `expsys_nw_ext_ma_null.py`, add `Any` to imports (same latent bug as Polars/Ibis) and add method:

```python
def null_if(
    self,
    input: NarwhalsExpr,
    condition: Any,
    /,
) -> NarwhalsExpr:
    """Replace values equal to condition with NULL.

    Args:
        input: Expression to check.
        condition: Value to compare against.

    Returns:
        Expression with matching values replaced by NULL.
    """
    fill_value = self._extract_literal_value(condition)
    return nw.when(input == fill_value).then(None).otherwise(input)
```

- [ ] **Step 4: Run null alignment tests**

Run: `hatch run test:test-quick tests/unit/test_protocol_alignment.py -v --tb=short -k "Null"`

Expected: All 3 backend null alignment tests (Polars, Ibis, Narwhals) should pass.

- [ ] **Step 5: Commit**

```
git add src/mountainash_expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_null.py
git add src/mountainash_expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_null.py
git add src/mountainash_expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_null.py
git commit -m "feat: implement null_if in all 3 backends"
```

---

## Task 8: Fix xor_parity in All Backends

**Files:**
- Modify: `src/mountainash_expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_boolean.py`
- Modify: `src/mountainash_expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_boolean.py`
- Modify: `src/mountainash_expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_boolean.py`

All 3 backends have broken `xor_parity` implementations. The Polars version references undefined `a`/`b` variables (uses `*args` in signature but `a ^ b` in body). Ibis and Narwhals take `(a, b)` positional args.

**Dispatch pattern:** The visitor (`unified_visitor/visitor.py:372`) calls `method(*args)` where args are the resolved `ScalarFunctionNode.arguments`. The API builder chains binary pairs: `ScalarFunctionNode(XOR_PARITY, [left, right])`, so the backend always receives **exactly 2 positional arguments**. Use `(self, a, b)` signature to match.

Note: These files are currently named as Substrait boolean expression systems (`SubstraitPolars...`) but contain the Mountainash `xor_parity` method. The implementation lives wherever the visitor dispatches to — check `getattr(self.backend, method_name)` resolution through the composed class MRO.

- [ ] **Step 1: Fix Polars xor_parity**

In `expsys_pl_ext_ma_scalar_boolean.py`, fix the implementation:

```python
def xor_parity(self, a: PolarsExpr, b: PolarsExpr, /) -> PolarsExpr:
    """XOR parity check (odd number of TRUE values).

    Returns TRUE if an odd number of operands are TRUE.
    Returns null if either input is null.

    The API builder chains binary pairs for >2 operands.
    """
    return a ^ b
```

- [ ] **Step 2: Fix Ibis xor_parity**

In `expsys_ib_ext_ma_scalar_boolean.py` — the existing `(a, b)` signature is correct but verify the body:

```python
def xor_parity(self, a: IbisExpr, b: IbisExpr, /) -> IbisExpr:
    """XOR parity check (odd number of TRUE values)."""
    return a ^ b
```

- [ ] **Step 3: Fix Narwhals xor_parity**

In `expsys_nw_ext_ma_scalar_boolean.py`:

```python
def xor_parity(self, a: NarwhalsExpr, b: NarwhalsExpr, /) -> NarwhalsExpr:
    """XOR parity check (odd number of TRUE values).

    Narwhals may not support ^ directly. Use logical equivalence:
    XOR(a, b) = (a | b) & ~(a & b)
    """
    return (a | b) & ~(a & b)
```

- [ ] **Step 4: Run xor_parity tests**

Run: `hatch run test:test-quick tests/cross_backend/test_ternary_auto_booleanize.py::TestTernaryToBooleanCoercionExtended::test_ternary_xor_parity_boolean_coercion -v --tb=long`

Expected: All 4 xor_parity tests pass (polars, narwhals, ibis-polars, ibis-duckdb).

**Important:** If these still fail, the issue may be in how the visitor dispatches `*args` to the method. Check `unified_visitor/visitor.py` to see how `ScalarFunctionNode` arguments are unpacked for variadic functions vs positional functions.

- [ ] **Step 5: Commit**

```
git add src/mountainash_expressions/backends/expression_systems/polars/extensions_mountainash/expsys_pl_ext_ma_scalar_boolean.py
git add src/mountainash_expressions/backends/expression_systems/ibis/extensions_mountainash/expsys_ib_ext_ma_scalar_boolean.py
git add src/mountainash_expressions/backends/expression_systems/narwhals/extensions_mountainash/expsys_nw_ext_ma_scalar_boolean.py
git commit -m "fix: implement xor_parity correctly in all 3 backends"
```

---

## Task 9: Final Verification

- [ ] **Step 1: Run full test suite**

Run: `hatch run test:test-quick`

Expected: 0 failures. All 1791+ tests pass (1762 previously passing + 20 previously failing + any newly collected tests).

- [ ] **Step 2: If any failures remain, diagnose**

Check:
- Are any failures in the 1762 previously-passing tests? (regression)
- Are any of the 20 target failures still failing? (incomplete fix)
- Are there new failures? (side effects from renames or enum moves)

- [ ] **Step 3: Final commit if any fixes needed**

```
git commit -m "fix: resolve remaining protocol alignment issues"
```
