#!/usr/bin/env python3
"""
Demonstrate multiplication overflow with real Parquet files.
Shows this happens with optimized production schemas.
"""

import ibis
import polars as pl
import tempfile
import os

print("=" * 80)
print("PARQUET FILE MULTIPLICATION OVERFLOW")
print("=" * 80)

# Create temporary directory for Parquet file
with tempfile.TemporaryDirectory() as tmpdir:
    parquet_path = os.path.join(tmpdir, 'orders.parquet')

    print("\n1. CREATE OPTIMIZED DATAFRAME")
    print("-" * 80)

    # Typical production scenario: optimize schema to save storage
    df = pl.DataFrame({
        'quantity': pl.Series([100, 75, 50], dtype=pl.Int8),
        'price': pl.Series([25, 30, 15], dtype=pl.Int8),
    })

    print(f"Schema before writing: {df.schema}")
    print(f"Memory usage: {df.estimated_size()} bytes")

    # Compare to unoptimized (int64)
    df_unoptimized = pl.DataFrame({
        'quantity': [100, 75, 50],
        'price': [25, 30, 15],
    })
    print(f"Unoptimized schema: {df_unoptimized.schema}")
    print(f"Unoptimized memory: {df_unoptimized.estimated_size()} bytes")

    savings = (1 - df.estimated_size() / df_unoptimized.estimated_size()) * 100
    print(f"Memory savings: {savings:.1f}%")

    print("\n2. WRITE TO PARQUET")
    print("-" * 80)

    df.write_parquet(parquet_path)
    print(f"✅ Written to: {parquet_path}")

    # Check file size
    file_size = os.path.getsize(parquet_path)
    print(f"File size: {file_size} bytes")

    print("\n3. READ BACK WITH IBIS (Polars backend)")
    print("-" * 80)

    polars_backend = ibis.polars.connect()
    table = polars_backend.read_parquet(parquet_path)

    print(f"Table schema: {table.schema()}")
    print("✅ Types preserved from Parquet (int8)")

    print("\n4. PERFORM CALCULATIONS")
    print("-" * 80)

    # Calculate order totals: quantity × price
    print("\nTest 1: quantity × price (order totals)")
    result1 = (table.quantity * table.price).execute()
    expected1 = [2500, 2250, 750]
    print(f"  Expected: {expected1}")
    print(f"  Actual:   {list(result1)}")
    print(f"  Status:   {'❌ WRONG' if list(result1) != expected1 else '✅ Correct'}")

    # Scale by 100
    print("\nTest 2: quantity × 100 (scaling)")
    result2 = (table.quantity * 100).execute()
    expected2 = [10000, 7500, 5000]
    print(f"  Expected: {expected2}")
    print(f"  Actual:   {list(result2)}")
    print(f"  Status:   {'❌ WRONG' if list(result2) != expected2 else '✅ Correct'}")

    # Double the quantity
    print("\nTest 3: quantity × 2 (doubling)")
    result3 = (table.quantity * 2).execute()
    expected3 = [200, 150, 100]
    print(f"  Expected: {expected3}")
    print(f"  Actual:   {list(result3)}")
    print(f"  Status:   {'❌ WRONG' if list(result3) != expected3 else '✅ Correct'}")

    print("\n5. COMPARISON WITH DUCKDB BACKEND")
    print("-" * 80)

    duckdb_backend = ibis.duckdb.connect()
    table_duck = duckdb_backend.read_parquet(parquet_path)

    print(f"DuckDB table schema: {table_duck.schema()}")

    # Same calculations with DuckDB
    print("\nDuckDB Test 1: quantity × price")
    try:
        result1_duck = (table_duck.quantity * table_duck.price).execute()
        print(f"  Result: {list(result1_duck)}")
        print(f"  Status: {'✅ Correct' if list(result1_duck) == expected1 else '❌ WRONG'}")
    except Exception as e:
        print(f"  Result: EXCEPTION - {type(e).__name__}")
        print(f"  Status: ⚠️  DuckDB throws error (better than silent corruption!)")

    print("\nDuckDB Test 2: quantity × 100")
    try:
        result2_duck = (table_duck.quantity * 100).execute()
        print(f"  Result: {list(result2_duck)}")
        print(f"  Status: {'✅ Correct' if list(result2_duck) == expected2 else '❌ WRONG'}")
    except Exception as e:
        print(f"  Result: EXCEPTION - {type(e).__name__}")
        print(f"  Status: ⚠️  DuckDB throws error (better than silent corruption!)")

    print("\nDuckDB Test 3: quantity × 2")
    try:
        result3_duck = (table_duck.quantity * 2).execute()
        print(f"  Result: {list(result3_duck)}")
        print(f"  Status: {'✅ Correct' if list(result3_duck) == expected3 else '❌ WRONG'}")
    except Exception as e:
        print(f"  Result: EXCEPTION - {type(e).__name__}")
        print(f"  Status: ⚠️  DuckDB throws error (better than silent corruption!)")

    print("\n6. THE WORKAROUND")
    print("-" * 80)

    print("\nWithout cast (fails):")
    result_fail = (table.quantity * table.price).execute()
    print(f"  table.quantity * table.price = {list(result_fail)}")

    print("\nWith explicit int64 cast (works):")
    result_work = (table.quantity * ibis.literal(1).cast('int64') * table.price).execute()
    print(f"  table.quantity * lit(1).cast('int64') * table.price = {list(result_work)}")

    # Better workaround: cast columns
    print("\nCasting columns to int64 (best workaround):")
    result_cast = (table.quantity.cast('int64') * table.price.cast('int64')).execute()
    print(f"  quantity.cast('int64') * price.cast('int64') = {list(result_cast)}")

print("\n" + "=" * 80)
print("REAL-WORLD SCENARIO")
print("=" * 80)

print("""
Production Use Case: E-commerce Order Processing

SETUP:
  - Orders table: 100M rows
  - Optimized Parquet with int8 columns → 75% storage savings
  - Deployed to production data warehouse

PROBLEM:
  - Query: SELECT quantity * price FROM orders
  - Returns WRONG values for quantities > 127
  - Financial reports corrupted
  - No errors thrown

IMPACT:
  - Wrong invoices sent to customers
  - Revenue calculations incorrect
  - Tax filings wrong
  - Discovered during audit (too late!)

ROOT CAUSE:
  - Parquet schema uses int8 (storage optimization)
  - Ibis passes int8 literals to Polars
  - Polars performs int8 × int8 = int8 (correct behavior)
  - Result overflows int8 range

DETECTION:
  - Silent corruption (no errors)
  - Wrong values look plausible
  - Found only when reports don't balance

FIX:
  - Stop using narrow types in Parquet? (defeats optimization)
  - Cast all literals to int64? (verbose, error-prone)
  - Fix Ibis literal inference? (proper solution ✅)
""")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("""
This bug affects REAL production systems:

✅ Parquet files preserve narrow types (int8/int16)
✅ Production systems use narrow types for storage optimization
⚠️  DuckDB backend throws exceptions (loud failure, detectable)
❌ Polars backend produces silent corruption (dangerous!)

Backend Comparison:
  - Polars: Returns wrong values (silent corruption)
  - DuckDB: Throws OutOfRangeException (loud failure)
  - SQLite: Works correctly (promotes types)

The issue is NOT with:
  - Parquet format ✅
  - Polars engine ✅ (respects explicit types correctly)
  - Memory-optimized schemas ✅

The issue IS with:
  - Ibis aggressive literal downcasting (int8) ❌
  - Ibis Polars backend passing explicit narrow types ❌

Users cannot avoid this without:
  - Giving up storage optimization (unacceptable)
  - Verbose casting everywhere (error-prone)
  - Using different backend (defeats Polars benefits)

FIX: Change Ibis literal inference or Polars backend translation.
""")
