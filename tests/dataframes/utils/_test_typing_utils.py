"""
Tests for the new typing system with TYPE_CHECKING and lazy imports.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock

def test_typing_utils_imports():
    """Test that typing_utils can be imported without loading dataframe libraries."""
    # Test if typing_utils imports work when modules are already loaded
    # This simulates the normal case where libraries are available
    try:
        from mountainash.dataframes.typing import (
            SupportedDataFrames,
            # DataFrameT,
            is_pandas_dataframe,
            # detect_backend_type,
        )

        # Type aliases should be available
        assert SupportedDataFrames is not None
        # assert DataFrameT is not None

        # Functions should be available
        assert callable(is_pandas_dataframe)
        # assert callable(detect_backend_type)

    except ImportError as e:
        pytest.fail(f"typing_utils should import successfully: {e}")

def test_type_guards_with_real_objects(
    sample_pandas_df, sample_polars_df, sample_pyarrow_table, real_ibis_table
):
    """Test type guard functions with REAL dataframe objects."""
    from mountainash.dataframes.typing import (
        is_pandas_dataframe,
        is_polars_dataframe,
        is_pyarrow_table,
        is_supported_dataframe,
    )

    # Test with REAL objects - can actually fail if logic is wrong
    assert is_pandas_dataframe(sample_pandas_df) is True
    assert is_pandas_dataframe(sample_polars_df) is False
    assert is_pandas_dataframe(sample_pyarrow_table) is False
    assert is_pandas_dataframe(real_ibis_table) is False

    assert is_polars_dataframe(sample_polars_df) is True
    assert is_polars_dataframe(sample_pandas_df) is False
    assert is_polars_dataframe(sample_pyarrow_table) is False
    assert is_polars_dataframe(real_ibis_table) is False

    assert is_pyarrow_table(sample_pyarrow_table) is True
    assert is_pyarrow_table(sample_pandas_df) is False
    assert is_pyarrow_table(sample_polars_df) is False
    assert is_pyarrow_table(real_ibis_table) is False

    # Test combined type guard with real objects
    assert is_supported_dataframe(sample_pandas_df) is True
    assert is_supported_dataframe(sample_polars_df) is True
    assert is_supported_dataframe(sample_pyarrow_table) is True
    assert is_supported_dataframe(real_ibis_table) is True
    assert is_supported_dataframe("not a dataframe") is False

# def test_detect_backend_type_with_real_objects(
#     sample_pandas_df, sample_polars_df, sample_pyarrow_table, real_ibis_table
# ):
#     """Test backend detection with REAL dataframe objects."""
#     from mountainash.dataframes.typing import detect_backend_type

#     # Test with REAL objects - verifies actual module/class detection
#     assert detect_backend_type(sample_pandas_df) == "pandas"
#     assert detect_backend_type(sample_polars_df) == "polars"
#     assert detect_backend_type(sample_pyarrow_table) == "pyarrow"
#     assert detect_backend_type(real_ibis_table) == "ibis"

#     # Test unknown type raises error - still need mock for this edge case
#     unknown_obj = MagicMock()
#     unknown_obj.__class__.__module__ = "unknown.module"
#     unknown_obj.__class__.__name__ = "UnknownType"

#     with pytest.raises(ValueError, match="Unknown dataframe type"):
#         detect_backend_type(unknown_obj)

def test_runtime_imports():
    """Test runtime import management."""
    from mountainash.dataframes.runtime_imports import (
#         import_pandas,
#         import_polars,
#         get_backend_for_type,
#         get_available_backends,
#     )

    # Test that import functions return modules or None
    pandas = import_pandas()
    if pandas is not None:
        assert hasattr(pandas, "DataFrame")

    polars = import_polars()
    if polars is not None:
        assert hasattr(polars, "DataFrame")

    # Test backend detection with real objects when available
    pandas = import_pandas()
    if pandas is not None:
#         # Create a real pandas DataFrame for testing
#         real_df = pandas.DataFrame({"test": [1, 2, 3]})
#         assert get_backend_for_type(real_df) == "pandas"

#     # Test available backends returns dict
    backends = get_available_backends()
    assert isinstance(backends, dict)
    assert "pandas" in backends
    assert "polars" in backends
    assert all(isinstance(v, bool) for v in backends.values())

def test_backend_requirements():
    """Test backend requirement checking."""
    from mountainash.dataframes.runtime_imports import check_backend_requirements

    # Check pandas requirements
    info = check_backend_requirements("pandas")
    assert "available" in info
    assert "backend" in info
    assert info["backend"] == "pandas"

    if not info["available"]:
        assert "install_command" in info
        assert "pip install" in info["install_command"]

def test_missing_dependency_error():
    """Test error message generation for missing dependencies."""
    from mountainash.dataframes.runtime_imports import get_missing_dependency_error

    error_msg = get_missing_dependency_error("polars", "DataFrame conversion")
    assert "polars" in error_msg
    assert "DataFrame conversion" in error_msg
    assert "pip install" in error_msg

def test_ensure_backend_available():
    """Test backend availability checking with error raising."""
    from mountainash.dataframes.runtime_imports import ensure_backend_available

    # This should either pass silently or raise ImportError
    try:
        ensure_backend_available("pandas")
    except ImportError as e:
        assert "pandas" in str(e)
        assert "pip install" in str(e)

def test_lazy_loading_caching():
    """Test that modules are cached after first import."""
    from mountainash.dataframes.runtime_imports import import_pandas, _module_cache

    # Clear cache first
    if "pandas" in _module_cache:
        del _module_cache["pandas"]

    # First import
    pandas1 = import_pandas()

    # Second import should return cached value
    pandas2 = import_pandas()

    # Should be the same object if pandas is available
    if pandas1 is not None:
        assert pandas1 is pandas2

def test_safe_import():
    """Test safe import utility."""
    from mountainash.dataframes.runtime_imports import safe_import

    # Test importing a standard library module (should always work)
    module, success = safe_import("sys")
    assert success is True
    assert module is not None
    assert module is sys

    # Test importing a non-existent module
    module, success = safe_import("definitely_not_a_real_module_xyz123")
    assert success is False
    assert module is None

def test_protocols():
    """Test that Protocol classes are defined correctly."""
    from mountainash.dataframes.typing import (
        DataFrameLike,
        LazyFrameLike,
        ExpressionLike,
    )

    # Protocols should have required methods/properties
    assert hasattr(DataFrameLike, "shape")
    assert hasattr(DataFrameLike, "columns")
    assert hasattr(DataFrameLike, "__len__")

    assert hasattr(LazyFrameLike, "collect")
    assert hasattr(LazyFrameLike, "columns")

    assert hasattr(ExpressionLike, "alias")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
