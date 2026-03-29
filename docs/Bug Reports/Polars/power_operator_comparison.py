#!/usr/bin/env python3
"""
Comprehensive side-by-side comparison of power operator behavior.

Compares:
- Ibis vs Polars
- Literals vs Raw values
- Left operand vs Right operand
- Different type casts
"""

import sys
sys.path.insert(0, '/home/nathanielramm/git/ibis')

import ibis
import polars as pl


def run_comparison():
    """Run comprehensive power operator comparison."""
    # Setup
    df = pl.DataFrame({'x': [10]})
    conn = ibis.polars.connect()
    table = conn.create_table('test', df, overwrite=True)

    print("=" * 100)
    print("POWER OPERATOR COMPARISON: IBIS vs POLARS")
    print("=" * 100)
    print(f"Test data: x = 10")
    print(f"Computing: 2 ** 10 = 1024 (expected)")
    print()

    # Define test cases
    test_cases = [
        # Section 1: Basic operations
        ("BASIC OPERATIONS", [
            ("col ** lit",
             lambda: (ibis._['x'] ** ibis.literal(2), df.select((pl.col('x') ** pl.lit(2)).alias('r'))['r'][0]),
             100, "10 ** 2"),

            ("lit ** col",
             lambda: (ibis.literal(2) ** ibis._['x'], df.select((pl.lit(2) ** pl.col('x')).alias('r'))['r'][0]),
             1024, "2 ** 10"),

            ("raw ** col",
             lambda: (2 ** ibis._['x'], df.select((2 ** pl.col('x')).alias('r'))['r'][0]),
             1024, "2 ** 10"),

            ("col ** raw",
             lambda: (ibis._['x'] ** 2, df.select((pl.col('x') ** 2).alias('r'))['r'][0]),
             100, "10 ** 2"),
        ]),

        # Section 2: Literal types (left side)
        ("LITERAL AS BASE (lit ** col, computing 2 ** 10)", [
            ("literal(2) [int8]",
             lambda: (ibis.literal(2) ** ibis._['x'], df.select((pl.lit(2) ** pl.col('x')).alias('r'))['r'][0]),
             1024, None),

            ("literal(128) [int16]",
             lambda: (ibis.literal(128) ** ibis._['x'], df.select((pl.lit(128) ** pl.col('x')).alias('r'))['r'][0]),
             None, "Note: 128^10 would overflow"),

            ("literal(2).cast(int16)",
             lambda: (ibis.literal(2).cast('int16') ** ibis._['x'],
                     df.select((pl.lit(2).cast(pl.Int16) ** pl.col('x')).alias('r'))['r'][0]),
             1024, None),

            ("literal(2).cast(int32)",
             lambda: (ibis.literal(2).cast('int32') ** ibis._['x'],
                     df.select((pl.lit(2).cast(pl.Int32) ** pl.col('x')).alias('r'))['r'][0]),
             1024, None),

            ("literal(2).cast(int64)",
             lambda: (ibis.literal(2).cast('int64') ** ibis._['x'],
                     df.select((pl.lit(2).cast(pl.Int64) ** pl.col('x')).alias('r'))['r'][0]),
             1024, None),
        ]),

        # Section 3: Literal types (right side)
        ("LITERAL AS EXPONENT (col ** lit, computing 10 ** 2)", [
            ("col ** literal(2) [int8]",
             lambda: (ibis._['x'] ** ibis.literal(2), df.select((pl.col('x') ** pl.lit(2)).alias('r'))['r'][0]),
             100, None),

            ("col ** literal(2).cast(int16)",
             lambda: (ibis._['x'] ** ibis.literal(2).cast('int16'),
                     df.select((pl.col('x') ** pl.lit(2).cast(pl.Int16)).alias('r'))['r'][0]),
             100, None),

            ("col ** literal(2).cast(int32)",
             lambda: (ibis._['x'] ** ibis.literal(2).cast('int32'),
                     df.select((pl.col('x') ** pl.lit(2).cast(pl.Int32)).alias('r'))['r'][0]),
             100, None),

            ("col ** literal(2).cast(int64)",
             lambda: (ibis._['x'] ** ibis.literal(2).cast('int64'),
                     df.select((pl.col('x') ** pl.lit(2).cast(pl.Int64)).alias('r'))['r'][0]),
             100, None),
        ]),

        # Section 4: Using .pow() method directly
        ("POLARS .pow() METHOD (with explicit dtypes)", [
            ("pl.lit(2, dtype=Int8).pow(col)",
             lambda: (None, df.select(pl.lit(2, dtype=pl.Int8).pow(pl.col('x')).alias('r'))['r'][0]),
             1024, "Polars only"),

            ("pl.lit(2, dtype=Int16).pow(col)",
             lambda: (None, df.select(pl.lit(2, dtype=pl.Int16).pow(pl.col('x')).alias('r'))['r'][0]),
             1024, "Polars only"),

            ("pl.lit(2, dtype=Int32).pow(col)",
             lambda: (None, df.select(pl.lit(2, dtype=pl.Int32).pow(pl.col('x')).alias('r'))['r'][0]),
             1024, "Polars only"),

            ("pl.lit(2, dtype=Int64).pow(col)",
             lambda: (None, df.select(pl.lit(2, dtype=pl.Int64).pow(pl.col('x')).alias('r'))['r'][0]),
             1024, "Polars only"),
        ]),
    ]

    # Run tests
    for section_name, tests in test_cases:
        print()
        print("─" * 100)
        print(f"{section_name}")
        print("─" * 100)
        print(f"{'Expression':<40} {'Ibis Result':>12} {'Polars Result':>14} {'Expected':>10} {'Status':>10}")
        print("─" * 100)

        for test_name, test_func, expected, note in tests:
            try:
                result = test_func()
                ibis_expr, polars_result = result

                # Execute Ibis expression if available
                if ibis_expr is not None:
                    try:
                        ibis_result = table.select(ibis_expr.name('r'))['r'].execute().tolist()[0]
                    except Exception as e:
                        ibis_result = f"ERROR: {type(e).__name__}"
                else:
                    ibis_result = "N/A"

                # Format results
                ibis_str = str(ibis_result) if isinstance(ibis_result, (int, float)) else ibis_result
                polars_str = str(polars_result)
                expected_str = str(expected) if expected is not None else "N/A"

                # Determine status
                if expected is None:
                    status = "N/A"
                elif isinstance(polars_result, str) and "ERROR" in polars_result:
                    status = "ERROR"
                elif isinstance(ibis_result, str) and "ERROR" in ibis_result and ibis_result != "N/A":
                    status = "ERROR"
                else:
                    # Handle Polars-only tests
                    if ibis_result == "N/A":
                        polars_ok = polars_result == expected
                        status = "✅ P" if polars_ok else "❌ P"
                    else:
                        ibis_ok = ibis_result == expected
                        polars_ok = polars_result == expected

                        if ibis_ok and polars_ok:
                            status = "✅ Both"
                        elif ibis_ok and not polars_ok:
                            status = "❌ P"
                        elif not ibis_ok and polars_ok:
                            status = "❌ I"
                        else:
                            status = "❌ Both"

                print(f"{test_name:<40} {ibis_str:>12} {polars_str:>14} {expected_str:>10} {status:>10}")
                if note:
                    print(f"{'':>40} {note}")

            except Exception as e:
                print(f"{test_name:<40} ERROR: {e}")

        print()

    # Legend
    print()
    print("=" * 100)
    print("LEGEND")
    print("=" * 100)
    print("✅ Both  - Both Ibis and Polars return correct result")
    print("✅ P     - Polars returns correct result (Polars-only test)")
    print("❌ I     - Ibis returns incorrect result, Polars correct")
    print("❌ P     - Polars returns incorrect result (or Ibis N/A)")
    print("❌ Both  - Both return incorrect results")
    print()
    print("KEY FINDINGS:")
    print("  • Ibis literal(2) [int8] ** col fails due to Int8 overflow (result doesn't fit)")
    print("  • Casting to wider types (int16+) fixes the issue")
    print("  • Polars with explicit Int8 dtype also fails")
    print("  • Polars ** operator (without explicit dtype) works correctly")
    print()


if __name__ == '__main__':
    run_comparison()
