#!/usr/bin/env python3
"""Verify the exact behavior of Polars ** operator vs .pow() method."""

import polars as pl

df = pl.DataFrame({'x': [10]})

print("Polars: Detailed ** Operator vs .pow() Method Test")
print("=" * 60)
print()

tests = [
    ("pl.lit(2).pow(pl.col('x'))",
     lambda: df.select(pl.lit(2).pow(pl.col('x')).alias('r'))['r'][0]),

    ("pl.lit(2) ** pl.col('x')",
     lambda: df.select((pl.lit(2) ** pl.col('x')).alias('r'))['r'][0]),

    ("pl.lit(2, dtype=Int8).pow(pl.col('x'))",
     lambda: df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('x')).alias('r'))['r'][0]),

    ("pl.lit(2, dtype=Int8) ** pl.col('x')",
     lambda: df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))['r'][0]),

    ("pl.lit(2, dtype=Int16).pow(pl.col('x'))",
     lambda: df.select(pl.lit(2, dtype=pl.Int16).pow(pl.col('x')).alias('r'))['r'][0]),

    ("pl.lit(2, dtype=Int16) ** pl.col('x')",
     lambda: df.select((pl.lit(2, dtype=pl.Int16) ** pl.col('x')).alias('r'))['r'][0]),
]

print(f"{'Expression':<45} {'Result':>8} {'Status':>10}")
print("-" * 60)

for desc, test_func in tests:
    result = test_func()
    status = "✅" if result == 1024 else f"❌ ({result})"
    print(f"{desc:<45} {result:>8} {status:>10}")

print()
print("=" * 60)
print("KEY FINDING:")

# Test if both methods produce the same result for Int8
pow_result = df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('x')).alias('r'))['r'][0]
op_result = df.select((pl.lit(2, dtype=pl.Int8) ** pl.col('x')).alias('r'))['r'][0]

if pow_result == op_result:
    print(f"  Both .pow() and ** operator return {pow_result} with Int8 dtype")
    print(f"  → This is a Polars bug in BOTH implementations")
else:
    print(f"  .pow() returns {pow_result}, ** returns {op_result}")
    print(f"  → Inconsistent behavior between the two")
