#!/usr/bin/env python3
"""Test script to validate the new plugin architecture."""

import sys
import os

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_imports():
    """Test that basic imports work."""
    print("Testing basic imports...")
    
    try:
        from mountainash_expressions.core.visitor.visitor_factory import ExpressionVisitorFactory, BackendPlugin
        print("✓ Successfully imported ExpressionVisitorFactory and BackendPlugin")
    except Exception as e:
        print(f"✗ Failed to import basic classes: {e}")
        return False
    
    try:
        from mountainash_expressions.backends.backend_registry import (
            PandasBackendPlugin, PolarsBackendPlugin, IbisBackendPlugin, PyArrowBackendPlugin
        )
        print("✓ Successfully imported backend plugins")
    except Exception as e:
        print(f"✗ Failed to import backend plugins: {e}")
        return False
    
    return True


def test_plugin_registration():
    """Test the plugin registration system."""
    print("\nTesting plugin registration...")
    
    try:
        from mountainash_expressions.core.visitor.visitor_factory import ExpressionVisitorFactory
        from mountainash_expressions.backends.backend_registry import PandasBackendPlugin
        from mountainash_expressions.core.constants import CONST_LOGIC_TYPES
        
        # Clear the factory for clean test
        ExpressionVisitorFactory.clear_registry()
        
        # Register a plugin
        plugin = PandasBackendPlugin()
        ExpressionVisitorFactory.register_backend_plugin(plugin)
        
        # Check if backend is registered
        if ExpressionVisitorFactory.is_backend_registered("pandas", CONST_LOGIC_TYPES.BOOLEAN):
            print("✓ Plugin registration successful")
        else:
            print("✗ Plugin not registered correctly")
            return False
        
        # Check registry contents
        backends = ExpressionVisitorFactory.get_registered_backends()
        print(f"✓ Registered backends: {backends}")
        
        return True
        
    except Exception as e:
        print(f"✗ Plugin registration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_detection():
    """Test the backend detection system."""
    print("\nTesting backend detection...")
    
    try:
        from mountainash_expressions.core.visitor.visitor_factory import ExpressionVisitorFactory
        from mountainash_expressions.backends.backend_registry import register_all_backends
        import pandas as pd
        
        # Register all backends
        register_all_backends()
        
        # Create test dataframes
        test_data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
        pandas_df = pd.DataFrame(test_data)
        
        # Test pandas detection
        backend = ExpressionVisitorFactory._identify_backend(pandas_df)
        if backend == "pandas":
            print("✓ Pandas backend detection successful")
        else:
            print(f"✗ Expected 'pandas', got '{backend}'")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Backend detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visitor_creation():
    """Test visitor creation through the factory."""
    print("\nTesting visitor creation...")
    
    try:
        from mountainash_expressions.core.visitor.visitor_factory import ExpressionVisitorFactory
        from mountainash_expressions.backends.backend_registry import register_all_backends
        from mountainash_expressions.core.constants import CONST_LOGIC_TYPES, CONST_VISITOR_BACKENDS
        import pandas as pd
        
        # Register all backends
        register_all_backends()
        
        # Create test dataframe
        test_data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}
        pandas_df = pd.DataFrame(test_data)
        
        # Test visitor creation
        visitor = ExpressionVisitorFactory.create_boolean_visitor_for_backend(pandas_df)
        if visitor is not None:
            print(f"✓ Successfully created boolean visitor: {type(visitor).__name__}")
        else:
            print("✗ Failed to create boolean visitor")
            return False
        
        # Test direct creation
        visitor2 = ExpressionVisitorFactory.create_visitor(
            CONST_VISITOR_BACKENDS.PANDAS,
            CONST_LOGIC_TYPES.TERNARY
        )
        if visitor2 is not None:
            print(f"✓ Successfully created ternary visitor: {type(visitor2).__name__}")
        else:
            print("✗ Failed to create ternary visitor")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Visitor creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("Testing new plugin architecture for mountainash-expressions")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_plugin_registration,
        test_backend_detection,
        test_visitor_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Plugin architecture is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Plugin architecture needs fixes.")
        return 1


if __name__ == "__main__":
    sys.exit(main())