# Generic Protocol Types — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make expression system protocols generic over `ExpressionT` so backends bind concrete types and Pyright verifies the full protocol-to-implementation chain.

**Architecture:** Update `core/types.py` with Ibis domain-specific aliases, make ~25 protocols generic over `ExpressionT`, update ~78 backend mixin files to bind concrete types in their protocol inheritance, and adjust the `ExpressionSystem` base class. Each backend is updated independently and tested separately.

**Tech Stack:** Python typing (TypeVar, Protocol, Generic), Pyright, hatch

---

## File Structure

| Layer | Files | Change |
|-------|-------|--------|
| Types | `src/mountainash/core/types.py` | Add 10 Ibis domain-specific type aliases |
| Protocols (substrait) | 18 files in `expression_protocols/expression_systems/substrait/` | Add `[ExpressionT]` to class, replace `SupportedExpressions` with `ExpressionT` |
| Protocols (extensions) | 7 files in `expression_protocols/expression_systems/extensions_mountainash/` | Same |
| Polars backend | 26 files in `backends/expression_systems/polars/` | Bind `pl.Expr` in protocol inheritance |
| Ibis backend | 25 files in `backends/expression_systems/ibis/` | Bind domain-specific Ibis type in protocol inheritance |
| Narwhals backend | 25 files in `backends/expression_systems/narwhals/` | Bind `nw.Expr` in protocol inheritance |
| Base class | `src/mountainash/expressions/core/expression_system/expsys_base.py` | Leave protocols unbound |

---

### Task 1: Add Ibis domain-specific type aliases

**Files:**
- Modify: `src/mountainash/core/types.py`

- [ ] **Step 1: Read the current type aliases**

Read `src/mountainash/core/types.py` and locate the existing `IbisExpr`, `PolarsExpr`, `NarwhalsExpr`, `SupportedExpressions`, and `ExpressionT` definitions.

- [ ] **Step 2: Add Ibis domain-specific aliases**

After the existing `ExpressionT` definition, add:

```python
# ============================================================================
# Ibis Domain-Specific Type Aliases
# ============================================================================
# Used by Ibis backend mixin files to bind ExpressionT to the correct
# Ibis expression subclass per protocol domain. See spec:
# docs/superpowers/specs/2026-03-31-generic-protocol-types-design.md

if TYPE_CHECKING:
    IbisNumericExpr: TypeAlias = ir.NumericValue
    IbisBooleanExpr: TypeAlias = ir.BooleanValue
    IbisStringExpr: TypeAlias = ir.StringValue
    IbisTemporalExpr: TypeAlias = Union[ir.TimestampValue, ir.DateValue, ir.TimeValue]
    IbisColumnExpr: TypeAlias = ir.Column
    IbisNumericColumnExpr: TypeAlias = ir.NumericColumn
    IbisBooleanColumnExpr: TypeAlias = ir.BooleanColumn
    IbisStringColumnExpr: TypeAlias = ir.StringColumn
    IbisValueExpr: TypeAlias = ir.Value
    IbisScalarExpr: TypeAlias = ir.Scalar
```

Note: These must be under `TYPE_CHECKING` because the existing `ir` import is already conditional. Check how `ir` is imported in the file and follow the same pattern.

- [ ] **Step 3: Verify no import errors**

```bash
python -c "from mountainash.core.types import ExpressionT; print('OK')"
```

Expected: `OK` (runtime import works — the new aliases are TYPE_CHECKING only)

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/core/types.py
git commit -m "feat: add Ibis domain-specific type aliases to core/types.py

IbisNumericExpr, IbisBooleanExpr, IbisStringExpr, etc. for
binding ExpressionT in Ibis backend protocol implementations.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Make Substrait protocols generic over ExpressionT

**Files:**
- Modify: 18 files in `src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/`

The files are:
- `prtcl_expsys_aggregate_arithmetic.py`
- `prtcl_expsys_aggregate_boolean.py`
- `prtcl_expsys_aggregate_generic.py`
- `prtcl_expsys_aggregate_string.py`
- `prtcl_expsys_cast.py`
- `prtcl_expsys_conditional.py`
- `prtcl_expsys_field_reference.py`
- `prtcl_expsys_literal.py`
- `prtcl_expsys_scalar_arithmetic.py`
- `prtcl_expsys_scalar_boolean.py`
- `prtcl_expsys_scalar_comparison.py`
- `prtcl_expsys_scalar_datetime.py`
- `prtcl_expsys_scalar_geometry.py`
- `prtcl_expsys_scalar_logarithmic.py`
- `prtcl_expsys_scalar_rounding.py`
- `prtcl_expsys_scalar_set.py`
- `prtcl_expsys_scalar_string.py`
- `prtcl_expsys_window_arithmetic.py`

- [ ] **Step 1: For each protocol file, apply the mechanical transformation**

For every file listed above:

1. Add the `ExpressionT` import:
```python
from mountainash.core.types import ExpressionT
```

2. Change the class definition from:
```python
class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol):
```
to:
```python
class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol[ExpressionT]):
```

3. Replace every occurrence of `SupportedExpressions` in method parameter and return type annotations with `ExpressionT`.

4. Remove the `SupportedExpressions` import if it is no longer used in the file.

**Example — `prtcl_expsys_scalar_arithmetic.py` before:**
```python
if TYPE_CHECKING:
    from mountainash.expressions.types import SupportedExpressions

class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol):
    def add(self, x: SupportedExpressions, y: SupportedExpressions, /, overflow: Any = None) -> SupportedExpressions: ...
```

**After:**
```python
from mountainash.core.types import ExpressionT

class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol[ExpressionT]):
    def add(self, x: ExpressionT, y: ExpressionT, /, overflow: Any = None) -> ExpressionT: ...
```

- [ ] **Step 2: Verify no import errors**

```bash
python -c "
from mountainash.expressions.core.expression_protocols.expression_systems.substrait.prtcl_expsys_scalar_arithmetic import SubstraitScalarArithmeticExpressionSystemProtocol
print('OK')
"
```

Expected: `OK`

- [ ] **Step 3: Run tests**

```bash
hatch run test:test-quick -- -x -q 2>&1 | tail -10
```

Expected: All tests pass. This is a types-only change — no runtime behavior change.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/core/expression_protocols/expression_systems/substrait/
git commit -m "feat: make 18 Substrait protocols generic over ExpressionT

Replace SupportedExpressions with ExpressionT in all method
signatures. Protocols now accept Protocol[ExpressionT] so
backends can bind concrete types.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Make MountainAsh extension protocols generic over ExpressionT

**Files:**
- Modify: 7 files in `src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/`

The files are:
- `prtcl_expsys_ext_ma_name.py`
- `prtcl_expsys_ext_ma_null.py`
- `prtcl_expsys_ext_ma_scalar_arithmetic.py`
- `prtcl_expsys_ext_ma_scalar_boolean.py`
- `prtcl_expsys_ext_ma_scalar_datetime.py`
- `prtcl_expsys_ext_ma_scalar_set.py`
- `prtcl_expsys_ext_ma_scalar_ternary.py`

- [ ] **Step 1: Apply the same mechanical transformation as Task 2**

For every file: add `ExpressionT` import, add `[ExpressionT]` to class, replace `SupportedExpressions` with `ExpressionT`, remove unused `SupportedExpressions` import.

- [ ] **Step 2: Run tests**

```bash
hatch run test:test-quick -- -x -q 2>&1 | tail -10
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/expressions/core/expression_protocols/expression_systems/extensions_mountainash/
git commit -m "feat: make 7 MountainAsh extension protocols generic over ExpressionT

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Update Polars backend — bind `pl.Expr` in all protocol inheritance

**Files:**
- Modify: 26 files in `src/mountainash/expressions/backends/expression_systems/polars/substrait/` and `polars/extensions_mountainash/`

- [ ] **Step 1: For each Polars backend file, update the protocol inheritance**

For every `expsys_pl_*.py` file, change the protocol inheritance from:

```python
class SubstraitPolarsScalarArithmeticExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol
):
```

to:

```python
class SubstraitPolarsScalarArithmeticExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol[pl.Expr]
):
```

Every Polars file binds `pl.Expr` — Polars has one expression type. Ensure `pl` (or `polars`) is imported for the type annotation. It likely already is.

Note: Two Polars extension files (`expsys_pl_ext_ma_scalar_aggregate.py`, `expsys_pl_ext_ma_scalar_comparison.py`) may not inherit from a protocol in the list above. Read them first — if they inherit from a different protocol or none, handle accordingly.

- [ ] **Step 2: Verify Pyright improvement on Polars files**

```bash
python -m pyright src/mountainash/expressions/backends/expression_systems/polars/ --outputjson 2>&1 | python -c "import sys,json; d=json.load(sys.stdin); print(f'Polars errors: {d[\"summary\"][\"errorCount\"]}')"
```

Expected: Error count significantly lower than before.

- [ ] **Step 3: Run Polars tests**

```bash
hatch run test:test-quick -- tests/ -k "polars" -x -q 2>&1 | tail -10
```

Expected: All Polars tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/polars/
git commit -m "feat: bind pl.Expr in all 26 Polars backend protocol inheritance

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Update Ibis backend — bind domain-specific Ibis types in all protocol inheritance

**Files:**
- Modify: 25 files in `src/mountainash/expressions/backends/expression_systems/ibis/substrait/` and `ibis/extensions_mountainash/`

This is the most complex task because each Ibis file binds a different type. Use this mapping:

| Backend file | Protocol to bind | Ibis type |
|---|---|---|
| `expsys_ib_scalar_arithmetic.py` | `SubstraitScalarArithmeticExpressionSystemProtocol` | `IbisNumericExpr` |
| `expsys_ib_scalar_boolean.py` | `SubstraitScalarBooleanExpressionSystemProtocol` | `IbisBooleanExpr` |
| `expsys_ib_scalar_comparison.py` | `SubstraitScalarComparisonExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_scalar_string.py` | `SubstraitScalarStringExpressionSystemProtocol` | `IbisStringExpr` |
| `expsys_ib_scalar_datetime.py` | `SubstraitScalarDatetimeExpressionSystemProtocol` | `IbisTemporalExpr` |
| `expsys_ib_scalar_rounding.py` | `SubstraitScalarRoundingExpressionSystemProtocol` | `IbisNumericExpr` |
| `expsys_ib_scalar_logarithmic.py` | `SubstraitScalarLogarithmicExpressionSystemProtocol` | `IbisNumericExpr` |
| `expsys_ib_scalar_set.py` | `SubstraitScalarSetExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_scalar_geometry.py` | `SubstraitScalarGeometryExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_aggregate_arithmetic.py` | `SubstraitAggregateArithmeticExpressionSystemProtocol` | `IbisNumericColumnExpr` |
| `expsys_ib_aggregate_boolean.py` | `SubstraitAggregateBooleanExpressionSystemProtocol` | `IbisBooleanColumnExpr` |
| `expsys_ib_aggregate_generic.py` | `SubstraitAggregateGenericExpressionSystemProtocol` | `IbisColumnExpr` |
| `expsys_ib_aggregate_string.py` | `SubstraitAggregateStringExpressionSystemProtocol` | `IbisStringColumnExpr` |
| `expsys_ib_window_arithmetic.py` | `SubstraitWindowArithmeticExpressionSystemProtocol` | `IbisNumericExpr` |
| `expsys_ib_field_reference.py` | `SubstraitFieldReferenceExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_literal.py` | `SubstraitLiteralExpressionSystemProtocol` | `IbisScalarExpr` |
| `expsys_ib_cast.py` | `SubstraitCastExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_conditional.py` | `SubstraitConditionalExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_ext_ma_name.py` | `MountainAshNameExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_ext_ma_null.py` | `MountainAshNullExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_ext_ma_scalar_ternary.py` | `MountainAshScalarTernaryExpressionSystemProtocol` | `IbisValueExpr` |
| `expsys_ib_ext_ma_scalar_arithmetic.py` | `MountainAshScalarArithmeticExpressionSystemProtocol` | `IbisNumericExpr` |
| `expsys_ib_ext_ma_scalar_boolean.py` | `MountainAshScalarBooleanExpressionSystemProtocol` | `IbisBooleanExpr` |
| `expsys_ib_ext_ma_scalar_datetime.py` | `MountainAshScalarDatetimeExpressionSystemProtocol` | `IbisTemporalExpr` |
| `expsys_ib_ext_ma_scalar_set.py` | `MountainAshScalarSetExpressionSystemProtocol` | `IbisValueExpr` |

- [ ] **Step 1: For each Ibis backend file, update protocol inheritance and method signatures**

For every file:
1. Change the protocol inheritance to bind the correct Ibis type from the table above
2. Update method parameter and return type annotations from `IbisExpr` to the domain-specific type
3. Add the type alias import from `mountainash.core.types` if not already present

**Example — `expsys_ib_scalar_arithmetic.py` before:**
```python
class SubstraitIbisScalarArithmeticExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol
):
    def add(self, x: IbisExpr, y: IbisExpr, /, overflow: Any = None) -> IbisExpr:
        return x + y
```

**After:**
```python
from mountainash.core.types import IbisNumericExpr

class SubstraitIbisScalarArithmeticExpressionSystem(
    IbisBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol[IbisNumericExpr]
):
    def add(self, x: IbisNumericExpr, y: IbisNumericExpr, /, overflow: Any = None) -> IbisNumericExpr:
        return x + y
```

- [ ] **Step 2: Verify Pyright improvement on Ibis files**

```bash
python -m pyright src/mountainash/expressions/backends/expression_systems/ibis/ --outputjson 2>&1 | python -c "import sys,json; d=json.load(sys.stdin); print(f'Ibis errors: {d[\"summary\"][\"errorCount\"]}')"
```

Expected: Significant reduction in errors, especially `reportAttributeAccessIssue` and `reportOperatorIssue`.

- [ ] **Step 3: Run Ibis tests**

```bash
hatch run test:test-quick -- tests/ -k "ibis" -x -q 2>&1 | tail -10
```

Expected: All Ibis tests pass. This is a types-only change — method implementations are unchanged.

- [ ] **Step 4: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/ibis/
git commit -m "feat: bind domain-specific Ibis types in all 25 Ibis backend protocol inheritance

ir.NumericValue for arithmetic, ir.StringValue for strings,
ir.BooleanValue for boolean, ir.Value for comparison/generic, etc.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Update Narwhals backend — bind `nw.Expr` in all protocol inheritance

**Files:**
- Modify: 25 files in `src/mountainash/expressions/backends/expression_systems/narwhals/substrait/` and `narwhals/extensions_mountainash/`

- [ ] **Step 1: For each Narwhals backend file, update the protocol inheritance**

Same mechanical transformation as Task 4 (Polars), but binding `nw.Expr` instead of `pl.Expr`:

```python
class SubstraitNarwhalsScalarArithmeticExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol[nw.Expr]
):
```

Every Narwhals file binds `nw.Expr`. Ensure `nw` (or `narwhals`) is imported.

- [ ] **Step 2: Run Narwhals tests**

```bash
hatch run test:test-quick -- tests/ -k "narwhals" -x -q 2>&1 | tail -10
```

Expected: All Narwhals tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/mountainash/expressions/backends/expression_systems/narwhals/
git commit -m "feat: bind nw.Expr in all 25 Narwhals backend protocol inheritance

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Update ExpressionSystem base class

**Files:**
- Modify: `src/mountainash/expressions/core/expression_system/expsys_base.py`

- [ ] **Step 1: Read the current ExpressionSystem class**

Read `src/mountainash/expressions/core/expression_system/expsys_base.py` and note how it inherits from the protocols.

- [ ] **Step 2: Leave protocols unbound in base class**

The base `ExpressionSystem` class should inherit from the protocols **without** binding `ExpressionT`. Since the protocols are now `Protocol[ExpressionT]`, inheriting without a type argument leaves `ExpressionT` as a free variable. This is correct — the base class is abstract.

No change should be needed if the base class already inherits from the protocol classes without type arguments. Verify this is the case. If the class explicitly referenced `SupportedExpressions`, update those references.

- [ ] **Step 3: Run full test suite**

```bash
hatch run test:test-quick -- -x -q 2>&1 | tail -10
```

Expected: All tests pass.

- [ ] **Step 4: Commit (only if changes were made)**

```bash
git add src/mountainash/expressions/core/expression_system/expsys_base.py
git commit -m "chore: update ExpressionSystem base class for generic protocols

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Final verification and Pyright error count

- [ ] **Step 1: Run full Pyright check**

```bash
python -m pyright src/mountainash/ --outputjson 2>&1 | python -c "
import sys, json
from collections import Counter
d = json.load(sys.stdin)
s = d['summary']
print(f'Errors: {s[\"errorCount\"]}  Warnings: {s[\"warningCount\"]}  Files: {s[\"filesAnalyzed\"]}')
rules = Counter()
for diag in d.get('generalDiagnostics', []):
    rule = diag.get('rule', 'unknown')
    rules[rule] += 1
print()
for rule, count in rules.most_common(20):
    print(f'  {count:4d}  {rule}')
"
```

Expected: Significant reduction from the 227 baseline. Specifically:
- `reportIncompatibleMethodOverride` should be near zero (was 151 at standard mode)
- `reportArgumentType` should be significantly reduced (was 173 at standard mode)

- [ ] **Step 2: Run full test suite**

```bash
hatch run test:test-quick -- -x -q 2>&1 | tail -10
```

Expected: All tests pass.

- [ ] **Step 3: Report results**

Report the before/after Pyright error counts by rule. Identify any new errors introduced by the type changes (e.g., Ibis methods that don't actually match the bound type). These are real findings — they may reveal places where the Ibis backend is using a method not available on the declared type.
