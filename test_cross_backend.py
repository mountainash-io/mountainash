#!/usr/bin/env python3
"""Test cross-backend compatibility of ExpressionSystem pattern."""

import sys
sys.path.insert(0, 'src')

import narwhals as nw
import polars as pl
import ibis

from mountainash_expressions.core.constants import CONST_LOGIC_TYPES
from mountainash_expressions.core.expression_visitors import ExpressionVisitorFactory


def test_same_visitor_different_backends():
    """Test that the SAME visitor code works with different backends."""
    print("\n" + "="*60)
    print("Testing Cross-Backend Compatibility")
    print("="*60)

    # Create identical test data in different backends
    data = {
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95],
        'name': ['Alice', 'Bob', 'Charlie', 'David']
    }

    # Narwhals backend
    print("\n--- Narwhals Backend ---")
    pl_df = pl.DataFrame(data)
    nw_df = nw.from_native(pl_df)

    narwhals_visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        nw_df,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )
    print(f"✓ Created visitor: {type(narwhals_visitor).__name__}")
    print(f"  Backend type: {narwhals_visitor.backend_type}")

    # Polars backend
    print("\n--- Polars Backend ---")
    pl_df2 = pl.DataFrame(data)

    polars_visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        pl_df2,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )
    print(f"✓ Created visitor: {type(polars_visitor).__name__}")
    print(f"  Backend type: {polars_visitor.backend_type}")

    # Ibis backend
    print("\n--- Ibis Backend ---")
    ibis_table = ibis.memtable(data)

    ibis_visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        ibis_table,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )
    print(f"✓ Created visitor: {type(ibis_visitor).__name__}")
    print(f"  Backend type: {ibis_visitor.backend_type}")

    # Verify all three are the same visitor class (UniversalBooleanExpressionVisitor)
    assert type(narwhals_visitor).__name__ == type(polars_visitor).__name__ == type(ibis_visitor).__name__
    print("\n✓ SAME visitor class used for ALL THREE backends!")

    # Test 1: Simple equality
    print("\n=== Test 1: Simple Equality ===")

    # SAME CODE for all three backends
    nw_expr = narwhals_visitor._B_eq('age', 30)
    pl_expr = polars_visitor._B_eq('age', 30)
    ibis_expr = ibis_visitor._B_eq('age', 30)

    nw_result = nw_df.filter(nw_expr)
    pl_result = pl_df2.filter(pl_expr)
    ibis_result = ibis_table.filter(ibis_expr)

    nw_count = nw_result.shape[0]
    pl_count = pl_result.shape[0]
    ibis_count = ibis_result.count().execute()

    print(f"Narwhals result: {nw_count} rows")
    print(f"Polars result: {pl_count} rows")
    print(f"Ibis result: {ibis_count} rows")
    assert nw_count == pl_count == ibis_count == 1
    print("✓ All three backends match!")

    # Test 2: Greater than
    print("\n=== Test 2: Greater Than ===")

    nw_expr = narwhals_visitor._B_gt('age', 30)
    pl_expr = polars_visitor._B_gt('age', 30)
    ibis_expr = ibis_visitor._B_gt('age', 30)

    nw_result = nw_df.filter(nw_expr)
    pl_result = pl_df2.filter(pl_expr)
    ibis_result = ibis_table.filter(ibis_expr)

    nw_count = nw_result.shape[0]
    pl_count = pl_result.shape[0]
    ibis_count = ibis_result.count().execute()

    print(f"Narwhals result: {nw_count} rows")
    print(f"Polars result: {pl_count} rows")
    print(f"Ibis result: {ibis_count} rows")
    assert nw_count == pl_count == ibis_count == 2
    print("✓ All three backends match!")

    # Test 3: Logical AND
    print("\n=== Test 3: Logical AND ===")

    # SAME CODE for all three backends
    nw_age_gt = narwhals_visitor._B_gt('age', 25)
    nw_score_ge = narwhals_visitor._B_ge('score', 85)
    nw_expr = narwhals_visitor._B_and([nw_age_gt, nw_score_ge])

    pl_age_gt = polars_visitor._B_gt('age', 25)
    pl_score_ge = polars_visitor._B_ge('score', 85)
    pl_expr = polars_visitor._B_and([pl_age_gt, pl_score_ge])

    ibis_age_gt = ibis_visitor._B_gt('age', 25)
    ibis_score_ge = ibis_visitor._B_ge('score', 85)
    ibis_expr = ibis_visitor._B_and([ibis_age_gt, ibis_score_ge])

    nw_result = nw_df.filter(nw_expr)
    pl_result = pl_df2.filter(pl_expr)
    ibis_result = ibis_table.filter(ibis_expr)

    nw_count = nw_result.shape[0]
    pl_count = pl_result.shape[0]
    ibis_count = ibis_result.count().execute()

    print(f"Narwhals result: {nw_count} rows")
    print(f"Polars result: {pl_count} rows")
    print(f"Ibis result: {ibis_count} rows")
    assert nw_count == pl_count == ibis_count == 2
    print("✓ All three backends match!")

    # Test 4: IN operation
    print("\n=== Test 4: IN Operation ===")

    nw_expr = narwhals_visitor._B_in('name', ['Alice', 'Charlie'])
    pl_expr = polars_visitor._B_in('name', ['Alice', 'Charlie'])
    ibis_expr = ibis_visitor._B_in('name', ['Alice', 'Charlie'])

    nw_result = nw_df.filter(nw_expr)
    pl_result = pl_df2.filter(pl_expr)
    ibis_result = ibis_table.filter(ibis_expr)

    nw_count = nw_result.shape[0]
    pl_count = pl_result.shape[0]
    ibis_count = ibis_result.count().execute()

    print(f"Narwhals result: {nw_count} rows")
    print(f"Polars result: {pl_count} rows")
    print(f"Ibis result: {ibis_count} rows")
    assert nw_count == pl_count == ibis_count == 2
    print("✓ All three backends match!")

    # Test 5: Complex expression
    print("\n=== Test 5: Complex Expression ===")

    # (age > 25 AND score >= 85) OR name IN ['Alice']
    nw_cond1 = narwhals_visitor._B_and([
        narwhals_visitor._B_gt('age', 25),
        narwhals_visitor._B_ge('score', 85)
    ])
    nw_cond2 = narwhals_visitor._B_in('name', ['Alice'])
    nw_expr = narwhals_visitor._B_or([nw_cond1, nw_cond2])

    pl_cond1 = polars_visitor._B_and([
        polars_visitor._B_gt('age', 25),
        polars_visitor._B_ge('score', 85)
    ])
    pl_cond2 = polars_visitor._B_in('name', ['Alice'])
    pl_expr = polars_visitor._B_or([pl_cond1, pl_cond2])

    ibis_cond1 = ibis_visitor._B_and([
        ibis_visitor._B_gt('age', 25),
        ibis_visitor._B_ge('score', 85)
    ])
    ibis_cond2 = ibis_visitor._B_in('name', ['Alice'])
    ibis_expr = ibis_visitor._B_or([ibis_cond1, ibis_cond2])

    nw_result = nw_df.filter(nw_expr)
    pl_result = pl_df2.filter(pl_expr)
    ibis_result = ibis_table.filter(ibis_expr)

    nw_count = nw_result.shape[0]
    pl_count = pl_result.shape[0]
    ibis_count = ibis_result.count().execute()

    print(f"Narwhals result: {nw_count} rows")
    print(f"Polars result: {pl_count} rows")
    print(f"Ibis result: {ibis_count} rows")
    assert nw_count == pl_count == ibis_count == 3
    print("✓ All three backends match!")

    print("\n" + "="*60)
    print("✅ ALL CROSS-BACKEND TESTS PASSED!")
    print("="*60)
    print("\nKey Achievement:")
    print("  • ONE visitor implementation (UniversalBooleanExpressionVisitor)")
    print("  • Works with THREE backends (Narwhals, Polars, Ibis)")
    print("  • SAME CODE produces SAME RESULTS across all backends")
    print("  • Clean separation: Backend primitives vs Logic dispatch")
    print("="*60)


def test_expression_reusability():
    """Test that expressions can be built once and applied to multiple dataframes."""
    print("\n" + "="*60)
    print("Testing Expression Reusability")
    print("="*60)

    # Create two different dataframes with same schema
    df1 = pl.DataFrame({
        'age': [25, 30, 35],
        'score': [85, 90, 75]
    })

    df2 = pl.DataFrame({
        'age': [40, 45, 50],
        'score': [95, 80, 88]
    })

    # Get visitor for first dataframe
    visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        df1,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )

    # Build expression ONCE
    print("\nBuilding expression: (age > 35) AND (score >= 85)")
    age_gt_35 = visitor._B_gt('age', 35)
    score_ge_85 = visitor._B_ge('score', 85)
    expr = visitor._B_and([age_gt_35, score_ge_85])
    print(f"✓ Expression built: {type(expr)}")

    # Apply to MULTIPLE dataframes
    print("\nApplying to df1...")
    result1 = df1.filter(expr)
    print(f"✓ df1 result: {result1.shape[0]} rows")

    print("Applying to df2...")
    result2 = df2.filter(expr)
    print(f"✓ df2 result: {result2.shape[0]} rows")

    # Verify results
    assert result1.shape[0] == 0  # No rows in df1 match (max age is 35)
    assert result2.shape[0] == 2  # Two rows in df2 match

    print("\n✓ Same expression successfully applied to multiple dataframes!")
    print("\nKey Achievement:")
    print("  • Expression compiled ONCE")
    print("  • Applied to MULTIPLE dataframes")
    print("  • No recompilation needed")
    print("="*60)


def main():
    """Run all cross-backend tests."""
    try:
        test_same_visitor_different_backends()
        test_expression_reusability()
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
