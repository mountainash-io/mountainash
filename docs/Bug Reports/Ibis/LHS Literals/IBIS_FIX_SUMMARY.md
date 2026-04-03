# Ibis Reverse Operator Fix - Quick Reference

## The Problem

```python
import ibis

lit = ibis.literal(5)
col = ibis._['value']

col + lit  # ✅ Works
lit + col  # ❌ InputTypeError
```

## The Root Cause

The `_binop` function doesn't catch `InputTypeError`, so it raises instead of returning `NotImplemented`, preventing Python from trying the reverse operator.

## The Fix (ONE LINE)

**File:** `ibis/expr/types/core.py`  
**Function:** `_binop`

```python
def _binop(op_class, left, right):
    try:
        node = op_class(left, right)
    except (ValidationError, NotImplementedError, InputTypeError):  # ← Add InputTypeError
        return NotImplemented
    else:
        return node.to_expr()
```

## Why It's Safe

`InputTypeError` is **ONLY** raised for unbound references (Deferred, UnboundTable), **NOT** for type mismatches:

✅ **Type mismatches still raise errors:**
- `literal("hi") + literal(5)` → `SignatureValidationError` 
- `literal(True) + literal(5)` → `IbisTypeError`
- `literal(None) + literal(5)` → `TypeError`

✅ **Unbound references return NotImplemented:**
- `literal(5) + ibis._['x']` → `NotImplemented` (enables reverse operator)
- `literal(5) + ibis.table({"a": "int"})` → `NotImplemented` (already works)

## What This Fixes

Before:
```python
literal(5) + ibis._['x']
# → InputTypeError (Python never tries reverse operator)
```

After:
```python
literal(5) + ibis._['x']
# → NotImplemented → Python tries ibis._['x'].__radd__(5) → ✅ Works!
```

## Evidence

See: `docs/IBIS_INPUTTYPEERROR_SAFETY_ANALYSIS.md` for complete analysis proving this is safe.

## Verification

Test script: `docs/ibis_reverse_operator_repro_final.py`

Expected after fix:
```
1. Column + Literal: ✅ Success: [15, 25, 35]
2. Literal + Column: ✅ Success: [15, 25, 35]
```
