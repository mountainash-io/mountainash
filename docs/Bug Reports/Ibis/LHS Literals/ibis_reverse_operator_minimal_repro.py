"""
Minimal reproduction for Ibis reverse arithmetic operator bug.

This script demonstrates that arithmetic operations fail when a literal
is on the LEFT side and a Deferred column reference is on the RIGHT side.

Issue: literal + deferred fails, but deferred + literal works
"""

import ibis
import polars as pl
import pandas as pd


def test_reverse_operators():
    """Test reverse operators across multiple backends."""

    # Setup backends
    polars_backend = ibis.polars.connect()
    duckdb_backend = ibis.duckdb.connect()
    sqlite_backend = ibis.sqlite.connect()

    # Create test data
    pl_df = pl.DataFrame({'value': [10, 20, 30]})

    # Create tables
    df_polars = polars_backend.create_table('test', pl_df, overwrite=True)
    df_duckdb = duckdb_backend.create_table('test', pl_df, overwrite=True)
    df_sqlite = sqlite_backend.create_table('test', pl_df, overwrite=True)

    # Define expressions using Deferred syntax
    lit = ibis.literal(5)
    col = ibis._['value']  # Deferred column reference

    # Test each backend
    results = []

    for backend_name, table in [
        ('polars', df_polars),
        ('duckdb', df_duckdb),
        ('sqlite', df_sqlite),
    ]:
        result = {
            'backend': backend_name,
            'col+lit': '✓',
            'lit+col': '✗',
        }

        # Test: col + lit (should always work)
        try:
            expr = col + lit
            table.select(expr.name('result')).execute()
            result['col+lit'] = '✓'
        except Exception as e:
            result['col+lit'] = f'✗ {type(e).__name__}'

        # Test: lit + col (fails with InputTypeError for Deferred)
        try:
            expr = lit + col
            table.select(expr.name('result')).execute()
            result['lit+col'] = '✓'
        except Exception as e:
            result['lit+col'] = f'✗ {type(e).__name__}'

        results.append(result)

    # Display results
    df_results = pd.DataFrame(results)
    print("\nReverse Operator Test Results:")
    print("=" * 70)
    print(df_results.to_markdown(index=False))
    print("\n✓ = Success, ✗ = Failure\n")

    # Show detailed error
    print("Detailed Error (using Deferred syntax):")
    print("-" * 70)
    try:
        expr = lit + col
        df_polars.select(expr.name('result')).execute()
    except Exception as e:
        print(f"{type(e).__name__}: {e}")

    print("\nNote: The issue occurs specifically with ibis._['column'] (Deferred)")
    print("      but NOT with table.column (BoundColumn)")


if __name__ == '__main__':
    test_reverse_operators()
