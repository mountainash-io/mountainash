# Generic Protocol Types

**Date:** 2026-03-31
**Status:** Approved
**Goal:** Make expression system protocols generic over `ExpressionT` so that each backend binds concrete types and Pyright can verify the full chain from protocol through to backend implementation.

## Problem

Expression system protocols define their method signatures using `SupportedExpressions` — a union of `PolarsExpr | IbisExpr | NarwhalsExpr`. Concrete backends implement these methods with backend-specific types (e.g., `pl.Expr`, `ir.NumericValue`). Pyright correctly flags this as incompatible overrides — the implementation narrows the type relative to the protocol contract.

This produces ~151 `reportIncompatibleMethodOverride` errors and contributes to ~173 `reportArgumentType` errors. The existing `ExpressionT = TypeVar("ExpressionT", bound=SupportedExpressions)` in `core/types.py` was designed to solve this but was never wired into the protocols.

## Solution

Make every hand-maintained protocol generic over `ExpressionT`. Each backend mixin binds the concrete type when inheriting from the protocol.

## 1. Protocol Changes

Every protocol in `expression_protocols/expression_systems/substrait/` and `expression_protocols/expression_systems/extensions_mountainash/` (~25 files) becomes generic:

**Before:**
```python
class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol):
    def add(self, x: SupportedExpressions, y: SupportedExpressions, /) -> SupportedExpressions: ...
```

**After:**
```python
from mountainash.core.types import ExpressionT

class SubstraitScalarArithmeticExpressionSystemProtocol(Protocol[ExpressionT]):
    def add(self, x: ExpressionT, y: ExpressionT, /) -> ExpressionT: ...
```

The change is mechanical: replace `SupportedExpressions` with `ExpressionT` in all parameter and return type annotations, and add `[ExpressionT]` to the class definition.

## 2. Backend Type Bindings

Each backend mixin binds `ExpressionT` to its concrete type when inheriting from the protocol.

### Polars — `pl.Expr` everywhere

```python
class SubstraitPolarsScalarArithmeticExpressionSystem(
    PolarsBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol[pl.Expr]
): ...
```

Polars has a single expression type. All ~25 Polars mixin files bind `pl.Expr`.

### Narwhals — `nw.Expr` everywhere

```python
class SubstraitNarwhalsScalarArithmeticExpressionSystem(
    NarwhalsBaseExpressionSystem,
    SubstraitScalarArithmeticExpressionSystemProtocol[nw.Expr]
): ...
```

Same pattern as Polars. All ~25 Narwhals mixin files bind `nw.Expr`.

### Ibis — domain-specific types

Ibis has a rich type hierarchy where operators and methods are defined on specific subclasses. Each Ibis mixin binds the most specific correct type:

| Protocol domain | Ibis binding | Reason |
|---|---|---|
| Scalar arithmetic | `ir.NumericValue` | `+`, `-`, `*`, `/`, `//`, trig functions |
| Scalar boolean | `ir.BooleanValue` | `&`, `\|`, `~` |
| Scalar comparison | `ir.Value` | `==`, `!=`, `.isnull()`, `.between()` — any value |
| Scalar string | `ir.StringValue` | `.upper()`, `.lower()`, `.length()` |
| Scalar datetime | `ir.TimestampValue \| ir.DateValue \| ir.TimeValue` | `.year()`, `.month()`, `.strftime()` |
| Scalar rounding | `ir.NumericValue` | `.round()`, `.ceil()`, `.floor()` |
| Scalar logarithmic | `ir.NumericValue` | `.log()`, `.ln()`, `.exp()` |
| Scalar set | `ir.Value` | `.isin()` — any value |
| Aggregate arithmetic | `ir.NumericColumn` | `.sum()`, `.mean()` — column-shaped |
| Aggregate boolean | `ir.BooleanColumn` | `.all()`, `.any()` |
| Aggregate generic | `ir.Column` | `.count()`, `.first()`, `.last()` |
| Aggregate string | `ir.StringColumn` | `.group_concat()` |
| Window arithmetic | `ir.NumericValue` | `.lag()`, `.lead()` |
| Field reference | `ir.Value` | Column reference — any type |
| Literal | `ir.Scalar` | Literal values |
| Cast | `ir.Value` | `.cast()` — any type |
| Conditional | `ir.Value` | if/then/else — any type |
| Extension: name | `ir.Value` | `.alias()`, `.name` |
| Extension: null | `ir.Value` | `.fillna()`, `.is_null()` |
| Extension: ternary | `ir.Value` | Ternary logic — any type |
| Extension: arithmetic | `ir.NumericValue` | `//`, `%` |
| Extension: boolean | `ir.BooleanValue` | `^` |
| Extension: datetime | `ir.TimestampValue \| ir.DateValue \| ir.TimeValue` | Component extraction |
| Extension: set | `ir.Value` | Set operations |

## 3. Type Alias Updates

Add Ibis domain-specific type aliases to `core/types.py`. The existing aliases remain unchanged.

```python
# Existing (unchanged)
PolarsExpr: TypeAlias = pl.Expr
IbisExpr: TypeAlias = Union[ir.Expr, ir.Column, ir.Scalar]
NarwhalsExpr: TypeAlias = nw.Expr
SupportedExpressions: TypeAlias = Union[PolarsExpr, IbisExpr, NarwhalsExpr]
ExpressionT = TypeVar("ExpressionT", bound=SupportedExpressions)

# New — Ibis domain-specific aliases
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

These are centralised in `core/types.py` following the existing pattern.

## 4. ExpressionSystem Base Class

The `ExpressionSystem` base class inherits from all protocols without binding `ExpressionT`. The TypeVar remains free — the class is abstract and never instantiated:

```python
class ExpressionSystem(
    SubstraitCastExpressionSystemProtocol,              # ExpressionT unbound
    SubstraitScalarArithmeticExpressionSystemProtocol,   # ExpressionT unbound
    ...
):
    pass
```

Each concrete `PolarsExpressionSystem`, `IbisExpressionSystem`, `NarwhalsExpressionSystem` resolves the types through its mixins, which each bind the protocol to a concrete type. Pyright checks each mixin independently.

## 5. Scope

### Included

- Making ~25 hand-maintained protocols generic over `ExpressionT`
- Binding concrete types in all three backends (~75 backend mixin files)
- Adding Ibis domain-specific type aliases to `core/types.py`
- Updating the `ExpressionSystem` base class
- Updating method signatures in ~75 backend mixin files to use the bound type

### Not included

- Auto-generated protocol files in `auto_gen/` (unused templates)
- Deprecated protocol files in `deprecated/`
- The `dataframes/` module (deprecated, superseded by `relations/`)
- The `schema_utils.py` import wiring (separate spec)
- Re-enabling deferred Pyright rules (ratchet step after this lands)
- Relation protocols in `relations/` (follow-up if they use the same pattern)

## Expected Impact

After this spec lands:
- ~151 `reportIncompatibleMethodOverride` errors eliminated (protocol/backend signatures now match)
- ~173 `reportArgumentType` errors reduced (concrete types allow Pyright to verify argument compatibility)
- `reportArgumentType` can be re-enabled in `pyrightconfig.json` as a ratchet step
- Ibis `reportAttributeAccessIssue` errors significantly reduced (Pyright can see methods on `ir.NumericValue` that are invisible on `ir.Expr`)

## Files Touched

1. **Modified:** `src/mountainash/core/types.py` (add Ibis domain-specific aliases)
2. **Modified:** ~25 protocol files in `expression_protocols/expression_systems/substrait/` and `extensions_mountainash/`
3. **Modified:** ~75 backend mixin files across `polars/`, `ibis/`, `narwhals/`
4. **Modified:** `src/mountainash/expressions/core/expression_system/expsys_base.py` (ExpressionSystem base)

## Verification

1. `hatch run pyright:check` — error count drops significantly from 227 baseline
2. `hatch run test:test-quick` — all tests pass (this is a types-only change, no runtime behavior change)
3. Re-enable `reportArgumentType` in `pyrightconfig.json` and verify zero new errors from that rule
