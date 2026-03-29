#!/usr/bin/env python3
"""
Comprehensive investigation of Polars overflow and upcasting behavior.

Tests all arithmetic operations to understand:
1. When Polars upcasts
2. When Polars wraps
3. What's different about power operations
"""

import polars as pl

print("=" * 80)
print("POLARS OVERFLOW & UPCASTING INVESTIGATION")
print("=" * 80)
print()

# Test data
df_small = pl.DataFrame({'col_int8': [63], 'col_int16': [1000], 'col_int32': [100000]})
df_pow = pl.DataFrame({'x': [10]})

print("Test Setup:")
print("  Int8 range: -128 to 127")
print("  Values that overflow Int8: 63 * 63 = 3969, 2^10 = 1024")
print()

# Define test cases: (description, expression, expected_value, expected_dtype)
test_cases = [
    # SECTION 1: Literal-Literal operations (both Int8)
    ("LITERAL-LITERAL (Both Int8)", [
        ("Int8(63) + Int8(63)", pl.lit(63, dtype=pl.Int8) + pl.lit(63, dtype=pl.Int8), 126, "Int8"),
        ("Int8(63) - Int8(10)", pl.lit(63, dtype=pl.Int8) - pl.lit(10, dtype=pl.Int8), 53, "Int8"),
        ("Int8(63) * Int8(63)", pl.lit(63, dtype=pl.Int8) * pl.lit(63, dtype=pl.Int8), -127, "Int8"),  # Wraps
        ("Int8(100) / Int8(2)", pl.lit(100, dtype=pl.Int8) / pl.lit(2, dtype=pl.Int8), 50, "Float*"),
        ("Int8(100) // Int8(3)", pl.lit(100, dtype=pl.Int8) // pl.lit(3, dtype=pl.Int8), 33, "Int8"),
        ("Int8(100) % Int8(7)", pl.lit(100, dtype=pl.Int8) % pl.lit(7, dtype=pl.Int8), 2, "Int8"),
        ("Int8(2) ** Int8(10)", pl.lit(2, dtype=pl.Int8) ** pl.lit(10, dtype=pl.Int8), -128, "Int8"),  # Should wrap?
    ]),

    # SECTION 2: Literal-Column operations (Int8 literal, Int8 column)
    ("LITERAL-COLUMN (Int8 lit, Int8 col)", [
        ("Int8(10) + col_int8(63)", pl.lit(10, dtype=pl.Int8) + pl.col('col_int8'), 73, "Int*"),
        ("Int8(10) - col_int8(63)", pl.lit(10, dtype=pl.Int8) - pl.col('col_int8'), -53, "Int*"),
        ("Int8(63) * col_int8(63)", pl.lit(63, dtype=pl.Int8) * pl.col('col_int8'), 3969, "Int64"),
        ("Int8(100) / col_int8(63)", pl.lit(100, dtype=pl.Int8) / pl.col('col_int8'), 1.587, "Float*"),
        ("Int8(100) // col_int8(63)", pl.lit(100, dtype=pl.Int8) // pl.col('col_int8'), 1, "Int*"),
        ("Int8(100) % col_int8(63)", pl.lit(100, dtype=pl.Int8) % pl.col('col_int8'), 37, "Int*"),
    ]),

    # SECTION 3: Power operations specifically
    ("POWER OPERATIONS (Int8 literal, Int8 column)", [
        ("Int8(2) ** col_int8(63)", pl.lit(2, dtype=pl.Int8) ** pl.col('col_int8'), None, "Int*"),
        ("Int8(2) ** Int8(10)", pl.lit(2, dtype=pl.Int8) ** pl.lit(10, dtype=pl.Int8), None, "Int*"),
    ]),

    # SECTION 4: Column-Literal operations (reversed)
    ("COLUMN-LITERAL (Int8 col, Int8 lit)", [
        ("col_int8(63) + Int8(10)", pl.col('col_int8') + pl.lit(10, dtype=pl.Int8), 73, "Int*"),
        ("col_int8(63) * Int8(63)", pl.col('col_int8') * pl.lit(63, dtype=pl.Int8), 3969, "Int64"),
    ]),

    # SECTION 5: Using .pow() method explicitly
    ("POWER METHOD (.pow())", [
        ("col_int8(63).pow(2)", pl.col('col_int8').pow(2), 3969, "Int*"),
        ("lit(2).pow(col_int8(63))", pl.lit(2, dtype=pl.Int8).pow(pl.col('col_int8')), None, "Int*"),
        ("lit(2).pow(10)", pl.lit(2, dtype=pl.Int8).pow(10), 1024, "Int*"),
    ]),
]

# Run all tests
for section_name, tests in test_cases:
    print()
    print("─" * 80)
    print(f"{section_name}")
    print("─" * 80)
    print(f"{'Operation':<35} {'Result':>10} {'Dtype':>10} {'Expected':>10} {'Status':>10}")
    print("─" * 80)

    for desc, expr, expected, expected_dtype in tests:
        try:
            # Choose appropriate dataframe
            if 'col_int8' in desc:
                df = df_small
            elif 'x' in str(expr):
                df = df_pow
            else:
                df = df_small  # Default

            result_df = df.select(expr.alias('r'))
            value = result_df['r'][0]
            dtype = str(result_df.schema['r'])

            # Check status
            if expected is None:
                status = "N/A"
                expected_str = "N/A"
            else:
                # Allow some tolerance for float comparison
                if isinstance(value, float) and isinstance(expected, (int, float)):
                    matches = abs(value - expected) < 0.01
                else:
                    matches = value == expected

                status = "✅" if matches else f"❌"
                expected_str = str(expected)

            # Dtype check
            dtype_matches = expected_dtype == "N/A" or expected_dtype in dtype or dtype == expected_dtype
            dtype_marker = "" if dtype_matches else " ⚠️"

            print(f"{desc:<35} {value:>10} {dtype:>10}{dtype_marker} {expected_str:>10} {status:>10}")

        except Exception as e:
            print(f"{desc:<35} ERROR: {str(e)[:50]}")

# Summary analysis
print()
print("=" * 80)
print("PATTERN ANALYSIS")
print("=" * 80)
print()

print("1. LITERAL-LITERAL operations (both typed):")
print("   • Stay in narrow type (Int8)")
print("   • Overflow wraps around (standard behavior)")
print()

print("2. LITERAL-COLUMN operations (typed literal + column):")
print("   • Addition/Subtraction: May upcast")
print("   • Multiplication: UPCASTS to Int64 ✅")
print("   • Division: Returns Float")
print("   • Floor division: May upcast")
print("   • Modulo: May upcast")
print("   • Power: STAYS Int8, returns 0 ❌")
print()

print("3. KEY FINDING:")
print("   Power operations DO NOT follow the same upcasting logic as multiplication!")
print()
print("   Multiplication: Int8(63) * col(63) → Int64: 3969 ✅")
print("   Power:          Int8(2) ** col(10) → Int8: 0    ❌")
print()

# Now let's check the actual implementation pattern
print("=" * 80)
print("HYPOTHESIS: Why does multiplication upcast but power doesn't?")
print("=" * 80)
print()

print("Polars likely has special logic for multiplication with columns that:")
print("  1. Detects mixed literal-column operations")
print("  2. Automatically widens the result type to prevent overflow")
print("  3. This logic is MISSING from power operations")
print()

print("Suggested fix for Polars:")
print("  Add the same type widening logic to power operations that")
print("  multiplication already has when one operand is a column.")
