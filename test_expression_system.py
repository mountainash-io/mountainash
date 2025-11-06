#!/usr/bin/env python3
"""Test script for ExpressionSystem pattern implementation."""

import sys
sys.path.insert(0, 'src')

import narwhals as nw
import polars as pl

from mountainash_expressions.core.constants import CONST_LOGIC_TYPES
from mountainash_expressions.core.expression_visitors import ExpressionVisitorFactory
from mountainash_expressions.backends.narwhals.expression_system import NarwhalsExpressionSystem


def test_expression_system_direct():
    """Test ExpressionSystem directly."""
    print("\n=== Testing ExpressionSystem Direct Usage ===")

    # Create test dataframe
    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'name': ['Alice', 'Bob', 'Charlie', 'David']
    })
    nw_df = nw.from_native(df)

    # Create ExpressionSystem
    expr_system = NarwhalsExpressionSystem()

    # Test basic operations
    age_col = expr_system.col('age')
    print(f"✓ Created column reference: {age_col}")

    thirty_lit = expr_system.lit(30)
    print(f"✓ Created literal: {thirty_lit}")

    eq_expr = expr_system.eq(age_col, thirty_lit)
    print(f"✓ Created equality expression: {eq_expr}")

    # Test with dataframe
    result = nw_df.filter(eq_expr)
    print(f"✓ Filtered dataframe: {result.shape} rows")
    print(f"  Result: {result.to_native()}")

    assert result.shape[0] == 1, "Expected 1 row"
    print("✓ ExpressionSystem direct test passed!")


def test_universal_visitor_basic():
    """Test UniversalBooleanExpressionVisitor with basic operations."""
    print("\n=== Testing Universal Visitor Basic Operations ===")

    # Create test dataframe
    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95]
    })
    nw_df = nw.from_native(df)

    # Get visitor from factory
    visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        nw_df,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )
    print(f"✓ Created visitor: {type(visitor).__name__}")

    # Test comparison operations
    print("\n--- Testing Comparison Operations ---")

    # Test _B_eq
    eq_expr = visitor._B_eq('age', 30)
    result = nw_df.filter(eq_expr)
    print(f"✓ _B_eq: age == 30 -> {result.shape[0]} rows")
    assert result.shape[0] == 1

    # Test _B_gt
    gt_expr = visitor._B_gt('age', 30)
    result = nw_df.filter(gt_expr)
    print(f"✓ _B_gt: age > 30 -> {result.shape[0]} rows")
    assert result.shape[0] == 2

    # Test _B_le
    le_expr = visitor._B_le('score', 85)
    result = nw_df.filter(le_expr)
    print(f"✓ _B_le: score <= 85 -> {result.shape[0]} rows")
    assert result.shape[0] == 2

    print("✓ Basic comparison operations passed!")


def test_universal_visitor_logical():
    """Test UniversalBooleanExpressionVisitor with logical operations."""
    print("\n=== Testing Universal Visitor Logical Operations ===")

    # Create test dataframe
    df = pl.DataFrame({
        'age': [25, 30, 35, 40],
        'score': [85, 90, 75, 95],
        'active': [True, True, False, True]
    })
    nw_df = nw.from_native(df)

    # Get visitor
    visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        nw_df,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )

    # Test AND operation
    print("\n--- Testing Logical AND ---")
    age_gt_25 = visitor._B_gt('age', 25)
    score_ge_85 = visitor._B_ge('score', 85)
    and_expr = visitor._B_and([age_gt_25, score_ge_85])
    result = nw_df.filter(and_expr)
    print(f"✓ _B_and: (age > 25) AND (score >= 85) -> {result.shape[0]} rows")
    # Row 1: 30, 90 (True, True) = True
    # Row 3: 40, 95 (True, True) = True
    assert result.shape[0] == 2

    # Test OR operation
    print("\n--- Testing Logical OR ---")
    age_lt_28 = visitor._B_lt('age', 28)
    age_gt_38 = visitor._B_gt('age', 38)
    or_expr = visitor._B_or([age_lt_28, age_gt_38])
    result = nw_df.filter(or_expr)
    print(f"✓ _B_or: (age < 28) OR (age > 38) -> {result.shape[0]} rows")
    assert result.shape[0] == 2

    # Test NOT operation
    print("\n--- Testing Logical NOT ---")
    active_col = visitor._process_operand('active')
    not_expr = visitor._B_negate([active_col])
    result = nw_df.filter(not_expr)
    print(f"✓ _B_negate: NOT active -> {result.shape[0]} rows")
    assert result.shape[0] == 1

    print("✓ Logical operations passed!")


def test_universal_visitor_collection():
    """Test UniversalBooleanExpressionVisitor with collection operations."""
    print("\n=== Testing Universal Visitor Collection Operations ===")

    # Create test dataframe
    df = pl.DataFrame({
        'category': ['A', 'B', 'C', 'D', 'E'],
        'value': [10, 20, 30, 40, 50]
    })
    nw_df = nw.from_native(df)

    # Get visitor
    visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        nw_df,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )

    # Test IN operation
    print("\n--- Testing IN Operation ---")
    in_expr = visitor._B_in('category', ['A', 'C', 'E'])
    result = nw_df.filter(in_expr)
    print(f"✓ _B_in: category IN ['A', 'C', 'E'] -> {result.shape[0]} rows")
    assert result.shape[0] == 3

    # Test NOT IN operation
    print("\n--- Testing NOT IN Operation ---")
    not_in_expr = visitor._B_not_in('category', ['B', 'D'])
    result = nw_df.filter(not_in_expr)
    print(f"✓ _B_not_in: category NOT IN ['B', 'D'] -> {result.shape[0]} rows")
    assert result.shape[0] == 3

    print("✓ Collection operations passed!")


def test_universal_visitor_null():
    """Test UniversalBooleanExpressionVisitor with null operations."""
    print("\n=== Testing Universal Visitor Null Operations ===")

    # Create test dataframe with nulls
    df = pl.DataFrame({
        'value': [10, None, 30, None, 50]
    })
    nw_df = nw.from_native(df)

    # Get visitor
    visitor = ExpressionVisitorFactory.get_visitor_for_backend(
        nw_df,
        CONST_LOGIC_TYPES.BOOLEAN,
        use_universal=True
    )

    # Test IS NULL
    print("\n--- Testing IS NULL ---")
    is_null_expr = visitor._B_is_null('value')
    result = nw_df.filter(is_null_expr)
    print(f"✓ _B_is_null: value IS NULL -> {result.shape[0]} rows")
    assert result.shape[0] == 2

    # Test IS NOT NULL
    print("\n--- Testing IS NOT NULL ---")
    is_not_null_expr = visitor._B_is_not_null('value')
    result = nw_df.filter(is_not_null_expr)
    print(f"✓ _B_is_not_null: value IS NOT NULL -> {result.shape[0]} rows")
    assert result.shape[0] == 3

    print("✓ Null operations passed!")


def test_factory_registration():
    """Test factory registration."""
    print("\n=== Testing Factory Registration ===")

    # Check registrations
    registered = ExpressionVisitorFactory.list_registered_visitors()
    print(f"✓ Registered visitors: {registered}")

    # Verify Narwhals is registered
    assert 'narwhals' in registered, "Narwhals should be registered"
    print("✓ Narwhals visitor registered")

    # Verify ExpressionSystem is registered
    from mountainash_expressions.core.constants import CONST_VISITOR_BACKENDS
    assert CONST_VISITOR_BACKENDS.NARWHALS in ExpressionVisitorFactory._expression_systems_registry
    print("✓ Narwhals ExpressionSystem registered")

    print("✓ Factory registration test passed!")


def main():
    """Run all tests."""
    print("="*60)
    print("Testing ExpressionSystem Pattern Implementation")
    print("="*60)

    try:
        test_expression_system_direct()
        test_universal_visitor_basic()
        test_universal_visitor_logical()
        test_universal_visitor_collection()
        test_universal_visitor_null()
        test_factory_registration()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
