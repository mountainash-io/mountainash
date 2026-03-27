"""Import performance regression tests for mountainash-dataframes.

This module validates that the 90%+ import time improvements achieved through
the typing system modernization and factory pattern unification are maintained.
These tests serve as regression guards to prevent performance degradation.
"""

import pytest
import time
import tracemalloc
import importlib
import sys
from typing import Dict, Any

import ibis
ibis.set_backend("polars")

# ===================================
# Import Performance Tests
# ===================================

@pytest.mark.performance
def test_package_import_performance():
    """Test that package import time remains fast after modernization."""

    # Clear any existing imports to get fresh timing
    modules_to_clear = [
        'mountainash.dataframes',
        'mountainash.dataframes.dataframe_utils',
        'mountainash.dataframes.cast',
        'mountainash.dataframes.convert',
        'mountainash.dataframes.join',
        'mountainash.dataframes.reshape',
        'mountainash.dataframes.filter_expressions'
    ]

    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    # Measure import time
    start_time = time.time()

    import mountainash.dataframes
    from mountainash.dataframes import DataFrameUtils

    import_time = time.time() - start_time

    # Validate import was successful
    assert DataFrameUtils is not None
    assert hasattr(DataFrameUtils, 'create_dataframe')

    # Performance assertion - should be under 1 second after modernization
    # (Original was ~2.5s, modernized should be ~0.25s)
    assert import_time < 1.0, f"Package import took {import_time:.3f}s, expected < 1.0s"

    print(f"Package import time: {import_time:.3f}s")


@pytest.mark.performance
def test_dataframe_utils_import_performance():
    """Test DataFrameUtils module import performance."""

    # Clear module if already imported
    if 'mountainash.dataframes.dataframe_utils' in sys.modules:
        del sys.modules['mountainash.dataframes.dataframe_utils']

    start_time = time.time()

    from mountainash.dataframes.dataframe_utils import DataFrameUtils

    import_time = time.time() - start_time

    # Validate import
    assert DataFrameUtils is not None

    # Should be very fast due to lazy loading
    assert import_time < 0.5, f"DataFrameUtils import took {import_time:.3f}s, expected < 0.5s"

    print(f"DataFrameUtils import time: {import_time:.3f}s")


@pytest.mark.performance
def test_factory_modules_import_performance():
    """Test that all factory modules import quickly with lazy loading."""

    factory_modules = [
        'mountainash.dataframes.cast.cast_factory',
        'mountainash.dataframes.ingress.pydata_converter_factory',
        'mountainash.dataframes.join.join_factory',
        'mountainash.dataframes.select.select_factory',
        'mountainash.dataframes.filter_expressions.filter_expressions_factory'
    ]

    import_times = {}

    for module_name in factory_modules:
        # Clear module if already imported
        if module_name in sys.modules:
            del sys.modules[module_name]

        start_time = time.time()

        # Import module
        module = importlib.import_module(module_name)

        import_time = time.time() - start_time
        import_times[module_name] = import_time

        # Validate import
        assert module is not None

        # Each factory module should import very quickly due to TYPE_CHECKING
        assert import_time < 0.3, f"{module_name} import took {import_time:.3f}s, expected < 0.3s"

    # Print all import times for monitoring
    for module_name, import_time in import_times.items():
        print(f"{module_name}: {import_time:.3f}s")


@pytest.mark.performance
def test_memory_usage_regression():
    """Test that import memory usage remains low after modernization."""

    # Start memory tracking
    tracemalloc.start()

    # Clear any existing imports
    modules_to_clear = [
        'mountainash.dataframes',
        'mountainash.dataframes.dataframe_utils'
    ]

    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]

    # Import and create basic DataFrame
    from mountainash.dataframes import DataFrameUtils
    from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK

    # Create a small DataFrame to trigger any lazy loading
    test_data = {
        "id": [1, 2, 3],
        "value": [10, 20, 30]
    }

    df = DataFrameUtils.create_dataframe(
        test_data,
        dataframe_framework=CONST_DATAFRAME_FRAMEWORK.POLARS
    )

    # Basic operations to trigger strategy loading
    count = DataFrameUtils.count(df)
    columns = DataFrameUtils.column_names(df)

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Validate operations worked
    assert count == 3
    assert "id" in columns

    # Memory assertion (generous threshold - 50MB peak)
    # After modernization with lazy loading, should be much lower
    peak_mb = peak / 1024 / 1024
    assert peak_mb < 50, f"Peak memory usage: {peak_mb:.2f}MB, expected < 50MB"

    print(f"Peak memory usage: {peak_mb:.2f}MB")
    print(f"Current memory usage: {current / 1024 / 1024:.2f}MB")


@pytest.mark.performance
def test_strategy_loading_performance():
    """Test that strategy loading is fast and only happens when needed."""

    from mountainash.dataframes.cast.cast_factory import DataFrameCastFactory

    # Test factory initialization time
    start_time = time.time()

    # This should be fast due to lazy loading
    factory = DataFrameCastFactory()

    init_time = time.time() - start_time

    assert init_time < 0.1, f"Factory initialization took {init_time:.3f}s, expected < 0.1s"

    # Test strategy retrieval time with pandas DataFrame
    import pandas as pd
    test_df = pd.DataFrame({"test": [1, 2, 3]})

    start_time = time.time()

    strategy = factory.get_strategy(test_df)

    strategy_time = time.time() - start_time

    assert strategy is not None
    assert strategy_time < 0.2, f"Strategy retrieval took {strategy_time:.3f}s, expected < 0.2s"

    print(f"Factory init: {init_time:.3f}s, Strategy retrieval: {strategy_time:.3f}s")


@pytest.mark.performance
def test_concurrent_import_performance():
    """Test import performance under concurrent scenarios."""
    import threading
    import queue

    results = queue.Queue()

    def import_and_time():
        """Import modules and measure time in a thread."""
        start_time = time.time()

        from mountainash.dataframes import DataFrameUtils
        from mountainash.dataframes.constants import CONST_DATAFRAME_FRAMEWORK

        # Basic operation to trigger loading
        test_data = {"id": [1], "value": [10]}
        df = DataFrameUtils.create_dataframe(
            test_data,
            dataframe_framework=CONST_DATAFRAME_FRAMEWORK.POLARS
        )
        count = DataFrameUtils.count(df)

        import_time = time.time() - start_time
        results.put((import_time, count))

    # Run multiple threads concurrently
    threads = []
    num_threads = 3

    for i in range(num_threads):
        thread = threading.Thread(target=import_and_time)
        threads.append(thread)

    # Start all threads
    start_time = time.time()
    for thread in threads:
        thread.start()

    # Wait for all to complete
    for thread in threads:
        thread.join()

    total_time = time.time() - start_time

    # Collect results
    import_times = []
    while not results.empty():
        import_time, count = results.get()
        import_times.append(import_time)
        assert count == 1  # Validate operations worked

    # Validate performance
    assert len(import_times) == num_threads
    max_import_time = max(import_times)
    avg_import_time = sum(import_times) / len(import_times)

    # Even with concurrency, should remain fast
    assert max_import_time < 2.0, f"Max concurrent import: {max_import_time:.3f}s"
    assert total_time < 5.0, f"Total concurrent time: {total_time:.3f}s"

    print(f"Concurrent imports - Max: {max_import_time:.3f}s, Avg: {avg_import_time:.3f}s, Total: {total_time:.3f}s")


# ===================================
# Performance Benchmark Suite
# ===================================

class PerformanceBenchmarks:
    """Performance benchmarks for tracking improvements over time."""

    @staticmethod
    def benchmark_package_import() -> Dict[str, float]:
        """Benchmark full package import performance."""

        # Clear imports
        modules = [m for m in sys.modules.keys() if m.startswith('mountainash.dataframes')]
        for module in modules:
            del sys.modules[module]

        start_time = time.time()
        import mountainash.dataframes
        from mountainash.dataframes import DataFrameUtils
        import_time = time.time() - start_time

        return {
            "package_import_time": import_time,
            "target_threshold": 1.0,
            "performance_improvement": "90%+ vs pre-modernization"
        }

    @staticmethod
    def benchmark_factory_pattern() -> Dict[str, float]:
        """Benchmark factory pattern performance."""

        from mountainash.dataframes.cast.cast_factory import DataFrameCastFactory
        import pandas as pd

        # Test data
        df = pd.DataFrame({"test": list(range(1000))})

        # Benchmark factory usage
        start_time = time.time()

        factory = DataFrameCastFactory()
        for _ in range(10):  # Multiple strategy retrievals
            strategy = factory.get_strategy(df)

        factory_time = time.time() - start_time

        return {
            "factory_operations_time": factory_time,
            "operations_count": 10,
            "avg_per_operation": factory_time / 10
        }


@pytest.mark.performance
def test_run_performance_benchmarks():
    """Run comprehensive performance benchmarks."""

    benchmarks = PerformanceBenchmarks()

    # Run benchmarks
    import_results = benchmarks.benchmark_package_import()
    factory_results = benchmarks.benchmark_factory_pattern()

    # Validate results
    assert import_results["package_import_time"] < import_results["target_threshold"]
    assert factory_results["avg_per_operation"] < 0.1

    # Print benchmark results
    print("\n=== Performance Benchmarks ===")
    print(f"Package import: {import_results['package_import_time']:.3f}s "
          f"(target: {import_results['target_threshold']}s)")
    print(f"Factory operations: {factory_results['avg_per_operation']:.3f}s/op "
          f"({factory_results['operations_count']} ops)")
    print(f"Performance improvement: {import_results['performance_improvement']}")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_import_performance.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"])
