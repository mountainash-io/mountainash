#!/usr/bin/env python3
"""Minimal reproduction of Polars pow bug."""

import polars as pl

print("Polars .pow() Bug - Minimal Reproduction")
print("=" * 60)
print()

df = pl.DataFrame({'x': [10]})

tests = [
    ("pl.lit(2, dtype=Int8).pow(col)", pl.lit(2, dtype=pl.Int8).pow(pl.col('x')), 1024),
    ("pl.lit(2, dtype=Int16).pow(col)", pl.lit(2, dtype=pl.Int16).pow(pl.col('x')), 1024),
    ("pl.lit(2, dtype=Int32).pow(col)", pl.lit(2, dtype=pl.Int32).pow(pl.col('x')), 1024),
    ("pl.lit(2, dtype=Int64).pow(col)", pl.lit(2, dtype=pl.Int64).pow(pl.col('x')), 1024),
    ("pl.lit(128, dtype=Int16).pow(col)", pl.lit(128, dtype=pl.Int16).pow(pl.col('x')), 1024),
    ("", None, None),  # Spacer
    ("pl.lit(2).pow(col) [no dtype]", pl.lit(2).pow(pl.col('x')), 1024),
    ("pl.lit(2) ** col [operator]", pl.lit(2) ** pl.col('x'), 1024),
    ("pl.lit(2, Int8).cast(Int16).pow(col)", pl.lit(2, dtype=pl.Int8).cast(pl.Int16).pow(pl.col('x')), 1024),
]

print("Testing 2^10 (expected: 1024):")
print("-" * 60)

for name, expr, expected in tests:
    if expr is None:
        print()
        continue

    result = df.select(expr.alias('r'))['r'][0]
    status = "✅" if result == expected else f"❌ (got {result})"
    print(f"{name:45} = {result:4} {status}")

print()
print("=" * 60)
print("CONCLUSION:")
print("• pl.lit(value, dtype=X).pow(col) returns wrong results")
print("• pl.lit(value).pow(col) works correctly")
print("• pl.lit(value, dtype=X).cast(Y).pow(col) works correctly")
print("• pl.lit(value) ** col works correctly")
print()
print("This appears to be a Polars bug, not an Ibis issue.")
