#!/usr/bin/env python3
"""
Investigate Polars source to understand where upcasting happens.

Try to find the difference between how multiplication and power are implemented.
"""

import polars as pl
import inspect

print("Polars Expression Source Investigation")
print("=" * 70)
print()

# Create an expression to examine
expr_mult = pl.lit(63, dtype=pl.Int8) * pl.col('x')
expr_pow = pl.lit(2, dtype=pl.Int8) ** pl.col('x')

print("1. Expression Objects:")
print(f"   Multiplication: {type(expr_mult)}")
print(f"   Power:          {type(expr_pow)}")
print()

# Check if there are different internal representations
print("2. Expression String Representations:")
print(f"   Multiplication: {expr_mult}")
print(f"   Power:          {expr_pow}")
print()

# Try to inspect the methods
print("3. Available Methods on Expr:")
methods = [m for m in dir(pl.Expr) if not m.startswith('_')]
print(f"   Total methods: {len(methods)}")

# Check for pow-specific methods
pow_methods = [m for m in methods if 'pow' in m.lower()]
print(f"   Power-related methods: {pow_methods}")
print()

# Check operator methods
print("4. Operator Methods:")
operator_methods = ['__add__', '__sub__', '__mul__', '__truediv__',
                   '__floordiv__', '__mod__', '__pow__', '__rpow__']

for method in operator_methods:
    if hasattr(pl.Expr, method):
        func = getattr(pl.Expr, method)
        try:
            # Try to get source or signature
            sig = inspect.signature(func)
            print(f"   {method}: {sig}")
        except:
            print(f"   {method}: (signature not available)")
print()

# Look for type promotion/supertype logic
print("5. Type-related Functions:")
type_funcs = [f for f in dir(pl) if 'type' in f.lower() or 'super' in f.lower()]
print(f"   Found: {type_funcs[:10]}")
print()

# Check datatypes
print("6. Data Type Hierarchy:")
print(f"   Int8:  {pl.Int8}")
print(f"   Int16: {pl.Int16}")
print(f"   Int32: {pl.Int32}")
print(f"   Int64: {pl.Int64}")
print()

# Try to examine what happens during expression construction
print("7. Expression Construction Analysis:")
print()

# Multiplication creates expression that upcasts
df = pl.DataFrame({'x': [63]})
mult_result = df.select((pl.lit(63, dtype=pl.Int8) * pl.col('x')).alias('r'))
print(f"   Multiplication result schema: {mult_result.schema}")
print(f"   Multiplication result:        {mult_result['r'][0]}")
print()

# Power creates expression that doesn't upcast
pow_result = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))
print(f"   Power result schema:          {pow_result.schema}")
print(f"   Power result:                 {pow_result['r'][0]}")
print()

print("=" * 70)
print("CONCLUSION:")
print("=" * 70)
print()
print("The difference is in how the expressions are compiled:")
print()
print("  Multiplication:")
print("    • Expr.__mul__ likely calls internal type promotion logic")
print("    • When seeing literal * column, promotes result to Int64")
print()
print("  Power:")
print("    • Expr.__pow__ does NOT call the same promotion logic")
print("    • Result stays in Int8, causing overflow to 0")
print()
print("This is a bug in Polars' power operation implementation.")
print("Power should use the same type promotion as other arithmetic ops.")
