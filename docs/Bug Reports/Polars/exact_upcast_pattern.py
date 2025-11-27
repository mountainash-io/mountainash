#!/usr/bin/env python3
"""
Find the EXACT pattern where multiplication upcasts but power doesn't.

Testing different type combinations to find when get_supertype() is called.
"""

import polars as pl

print("=" * 80)
print("EXACT PATTERN: When does get_supertype() kick in?")
print("=" * 80)

test_cases = [
    # (base_type, exponent_type, base_value, exp_value, description)
    (pl.Int8, pl.Int8, 63, 63, "Int8 * Int8 (both same type)"),
    (pl.Int8, pl.Int64, 63, 63, "Int8 * Int64 (different types)"),
    (pl.Int16, pl.Int8, 50, 50, "Int16 * Int8 (different types)"),
    (pl.Int32, pl.Int8, 100, 100, "Int32 * Int8 (different types)"),
]

print("\n" + "=" * 80)
print("MULTIPLICATION")
print("=" * 80)

for base_type, exp_type, base_val, exp_val, desc in test_cases:
    # Create column with exp_type
    df = pl.DataFrame({'x': [exp_val]}).with_columns(pl.col('x').cast(exp_type))

    # Literal with base_type * Column with exp_type
    result = df.select((pl.lit(base_val, dtype=base_type) * pl.col('x')).alias('r'))

    print(f"\n{desc}")
    print(f"  Expression: {base_type.__name__}({base_val}) * col_{exp_type.__name__}({exp_val})")
    print(f"  Result dtype: {result.schema['r']}")
    print(f"  Result value: {result['r'][0]}")
    print(f"  Expected: {base_val * exp_val}")

print("\n" + "=" * 80)
print("POWER")
print("=" * 80)

power_cases = [
    # (base_type, exponent_type, base_value, exp_value, description)
    (pl.Int8, pl.Int8, 2, 10, "Int8 ** Int8 (both same type)"),
    (pl.Int8, pl.Int64, 2, 10, "Int8 ** Int64 (different types)"),
    (pl.Int16, pl.Int8, 2, 10, "Int16 ** Int8 (different types)"),
    (pl.Int32, pl.Int8, 2, 10, "Int32 ** Int8 (different types)"),
]

for base_type, exp_type, base_val, exp_val, desc in power_cases:
    # Create column with exp_type
    df = pl.DataFrame({'x': [exp_val]}).with_columns(pl.col('x').cast(exp_type))

    # Literal with base_type ** Column with exp_type
    result = df.select((pl.lit(base_val, dtype=base_type) ** pl.col('x')).alias('r'))

    print(f"\n{desc}")
    print(f"  Expression: {base_type.__name__}({base_val}) ** col_{exp_type.__name__}({exp_val})")
    print(f"  Result dtype: {result.schema['r']}")
    print(f"  Result value: {result['r'][0]}")
    print(f"  Expected: {base_val ** exp_val}")

print("\n" + "=" * 80)
print("COMPARISON SUMMARY")
print("=" * 80)
print()
print("| Base Type | Exp Type | Multiplication Result | Power Result | Match? |")
print("|-----------|----------|-----------------------|--------------|--------|")

for (base_type, exp_type, base_val, exp_val, _) in test_cases:
    df = pl.DataFrame({'x': [exp_val]}).with_columns(pl.col('x').cast(exp_type))

    mult_result = df.select((pl.lit(base_val, dtype=base_type) * pl.col('x')).alias('r'))
    mult_dtype = str(mult_result.schema['r'])
    mult_val = mult_result['r'][0]

    # For power, use smaller values
    pow_base = 2
    pow_exp = 10
    df_pow = pl.DataFrame({'x': [pow_exp]}).with_columns(pl.col('x').cast(exp_type))
    pow_result = df_pow.select((pl.lit(pow_base, dtype=base_type) ** pl.col('x')).alias('r'))
    pow_dtype = str(pow_result.schema['r'])
    pow_val = pow_result['r'][0]

    match = "✅" if mult_dtype == pow_dtype else "❌"
    print(f"| {base_type.__name__:9} | {exp_type.__name__:8} | {mult_dtype:21} | {pow_dtype:12} | {match:6} |")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
From the tests above, we can see:

1. Multiplication with DIFFERENT integer types → Upcasts to larger type
   Example: Int8 * Int64 → Int64

2. Power with DIFFERENT integer types → Uses base type (no upcast!)
   Example: Int8 ** Int64 → Int8 (BUG!)

3. When both are the SAME type, both operations stay in that type
   Example: Int8 * Int8 → Int8 (wraps)
           Int8 ** Int8 → Int8 (but returns 0, not wrapped!)

The bug is that power doesn't call get_supertype() when types differ,
so it always uses the base type regardless of the exponent type.
""")
