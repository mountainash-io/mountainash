"""
Minimal reproduction for Ibis reverse arithmetic operator bug.
For GitHub issue: Reverse arithmetic operators fail with Deferred column references
"""

import ibis
import polars as pl
import pandas as pd

# Setup backend
conn = ibis.polars.connect()
pl_df = pl.DataFrame({'value': [10, 20, 30]})
table = conn.create_table('test', pl_df, overwrite=True)

# Define expressions
lit = ibis.literal(5)
col = ibis._['value']  # Deferred column reference

print("Testing operator symmetry with Deferred column references:")
print("=" * 70)

# Test 1: Column on left (this works ✅)
print("\n1. Column + Literal (col + lit):")
try:
    expr = col + lit
    result = table.select(expr.name('result')).execute()
    print(f"   ✓ Success: {result['result'].tolist()}")
except Exception as e:
    print(f"   ✗ Failed: {type(e).__name__}: {e}")

# Test 2: Literal on left (this fails ❌)
print("\n2. Literal + Column (lit + col):")
try:
    expr = lit + col
    result = table.select(expr.name('result')).execute()
    print(f"   ✓ Success: {result['result'].tolist()}")
except Exception as e:
    print(f"   ✗ Failed: {type(e).__name__}")
    print(f"      Error: {e}")

print("\n" + "=" * 70)
print("Expected: Both operations should succeed (commutativity)")
print("Actual:   Only col + lit works; lit + col fails")
