"""
Reproduction script for Ibis Polars backend calendar intervals bug.

This script demonstrates that:
1. Native Polars supports calendar intervals via offset_by()
2. Ibis Polars backend fails with months/years
3. Ibis Polars backend works with fixed durations (days, hours, etc.)
4. Other Ibis backends (DuckDB) work correctly with calendar intervals

Run this to verify the bug and test fixes.
"""
import ibis
import polars as pl
from datetime import datetime

print("=" * 70)
print("Ibis Polars Backend - Calendar Interval Test")
print("=" * 70)
print(f"\nVersions:")
print(f"  Ibis: {ibis.__version__}")
print(f"  Polars: {pl.__version__}")
print()

data = {
    "timestamp": [
        datetime(2024, 1, 1, 10, 0, 0),
        datetime(2024, 6, 15, 14, 30, 0),
    ]
}

# Test 1: Native Polars (baseline - this WORKS)
print("1. Native Polars - Adding 3 months:")
print("-" * 70)
try:
    pl_df = pl.DataFrame(data)
    result = pl_df.select(pl.col("timestamp").dt.offset_by("3mo"))
    print(f"✅ SUCCESS: {result['timestamp'].to_list()}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: Ibis Polars - months (this FAILS)
print("\n2. Ibis Polars Backend - Adding 3 months:")
print("-" * 70)
try:
    conn = ibis.polars.connect()
    t = conn.create_table("test", pl.DataFrame(data), overwrite=True)
    result = t.timestamp + ibis.interval(months=3)
    executed = t.select(result.name("result")).execute()
    print(f"✅ SUCCESS: {executed['result'].tolist()}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")

# Test 3: Ibis Polars - years (this FAILS)
print("\n3. Ibis Polars Backend - Adding 1 year:")
print("-" * 70)
try:
    conn = ibis.polars.connect()
    t = conn.create_table("test", pl.DataFrame(data), overwrite=True)
    result = t.timestamp + ibis.interval(years=1)
    executed = t.select(result.name("result")).execute()
    print(f"✅ SUCCESS: {executed['result'].tolist()}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")

# Test 4: Ibis Polars - days (this WORKS)
print("\n4. Ibis Polars Backend - Adding 30 days (fixed duration):")
print("-" * 70)
try:
    conn = ibis.polars.connect()
    t = conn.create_table("test", pl.DataFrame(data), overwrite=True)
    result = t.timestamp + ibis.interval(days=30)
    executed = t.select(result.name("result")).execute()
    print(f"✅ SUCCESS: {executed['result'].tolist()}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")

# Test 5: Ibis DuckDB - months (this WORKS)
print("\n5. Ibis DuckDB Backend - Adding 3 months:")
print("-" * 70)
try:
    conn = ibis.duckdb.connect()
    t = conn.create_table("test", data, overwrite=True)
    result = t.timestamp + ibis.interval(months=3)
    executed = t.select(result.name("result")).execute()
    print(f"✅ SUCCESS: {executed['result'].tolist()}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")

print("\n" + "=" * 70)
print("Summary:")
print("=" * 70)
print("✅ Native Polars supports calendar intervals via offset_by()")
print("✅ Ibis Polars supports fixed durations (days, hours, etc.)")
print("✅ Ibis DuckDB supports calendar intervals (months, years)")
print("❌ Ibis Polars FAILS with calendar intervals (months, years)")
print("\nRoot cause: ibis/backends/polars/compiler.py::_make_duration()")
print("calls pl.duration() which doesn't support months/years parameters")
