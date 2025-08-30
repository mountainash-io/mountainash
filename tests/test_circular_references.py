#!/usr/bin/env python3
"""
Test script to verify circular reference issues have been resolved
"""

def test_core_imports():
    """Test that core modules can be imported without circular reference errors"""
    
    # Test core logic imports
    from src.mountainash_expressions.core.logic.expression_nodes import ExpressionNode
    from src.mountainash_expressions.core.logic.expression_node_protocol import ExpressionNodeProtocol
    
    # Test visitor imports
    from src.mountainash_expressions.core.visitor.expression_visitor import ExpressionVisitor
    from src.mountainash_expressions.core.visitor.expression_visitor_protocol import ExpressionVisitorProtocol
    
    # Test specific logic implementations
    from src.mountainash_expressions.core.logic.boolean.boolean_nodes import BooleanExpressionNode
    from src.mountainash_expressions.core.logic.ternary.ternary_nodes import TernaryExpressionNode
    
    # Test specific visitor implementations 
    from src.mountainash_expressions.core.visitor.logic.boolean_visitor import BooleanExpressionVisitor
    from src.mountainash_expressions.core.visitor.logic.ternary_visitor import TernaryExpressionVisitor
    
    print("✓ All core modules imported successfully")

def test_backend_imports():
    """Test that backend visitor classes can be imported"""
    
    from src.mountainash_expressions.backends.polars.polars_boolean_visitor import PolarsBooleanExpressionVisitor
    from src.mountainash_expressions.backends.polars.polars_ternary_visitor import PolarsTernaryExpressionVisitor
    
    from src.mountainash_expressions.backends.pandas.pandas_boolean_visitor import PandasBooleanExpressionVisitor
    from src.mountainash_expressions.backends.pandas.pandas_ternary_visitor import PandasTernaryExpressionVisitor
    
    print("✓ All backend modules imported successfully")

def test_package_import():
    """Test that the main package can be imported"""
    
    import sys
    sys.path.insert(0, 'src')
    
    from mountainash_expressions import (
        TernaryExpressionBuilder,
        PolarsTernaryExpressionVisitor,
        PandasTernaryExpressionVisitor
    )
    
    print("✓ Main package imports successfully")

def test_visitor_pattern():
    """Test that the visitor pattern objects can be created without circular reference issues"""
    
    import sys
    sys.path.insert(0, 'src')
    
    from mountainash_expressions.core.logic.boolean.boolean_nodes import BooleanColumnExpressionNode
    from mountainash_expressions.backends.polars.polars_boolean_visitor import PolarsBooleanExpressionVisitor
    
    # Create expression node and visitor - this would fail with circular references
    expr = BooleanColumnExpressionNode("is_null", "test_column", None)
    visitor = PolarsBooleanExpressionVisitor()
    
    # Just check that objects can be created without import errors
    assert expr is not None
    assert visitor is not None
    
    print("✓ Visitor pattern objects can be created without circular references")

if __name__ == "__main__":
    test_core_imports()
    test_backend_imports() 
    test_package_import()
    test_visitor_pattern()
    
    print("\n🎉 All circular reference tests passed!")