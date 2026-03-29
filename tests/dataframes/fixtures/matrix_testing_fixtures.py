"""Advanced matrix testing fixtures for comprehensive backend and datastructure testing.

This module provides specialized fixtures designed specifically for matrix parametrization
testing across multiple backends, data formats, and transformation chains. These fixtures
complement the existing realistic data fixtures by providing test configurations,
backend combinations, and advanced test scenarios specifically optimized for matrix testing.
"""

import pytest
from typing import Dict, List, Any, Tuple, Optional, Union
import itertools
from datetime import datetime, date, timedelta
import random
import string
from dataclasses import dataclass
from enum import Enum


class TestComplexity(Enum):
    """Test complexity levels for matrix testing."""
    SMOKE = "smoke"          # Basic functionality tests
    INTEGRATION = "integration"    # Cross-component tests
    STRESS = "stress"        # High-load tests
    EDGE_CASE = "edge_case"  # Boundary condition tests


class BackendCapability(Enum):
    """Backend capabilities for test filtering."""
    SQL_QUERIES = "sql_queries"
    COMPLEX_TYPES = "complex_types"
    LARGE_DATASETS = "large_datasets"
    REAL_TIME = "real_time"
    ANALYTICS = "analytics"
    GEOSPATIAL = "geospatial"


@dataclass
class MatrixTestConfig:
    """Configuration for matrix test scenarios."""
    test_id: str
    description: str
    complexity: TestComplexity
    backends: List[str]
    data_sizes: List[str]
    required_capabilities: List[BackendCapability]
    expected_performance_threshold: Optional[float] = None
    memory_threshold_mb: Optional[float] = None


@pytest.fixture(scope="session")
def matrix_test_configurations():
    """Comprehensive test configuration matrix for different scenarios."""

    return {
        "basic_operations": MatrixTestConfig(
            test_id="basic_ops",
            description="Basic DataFrame operations across all backends",
            complexity=TestComplexity.SMOKE,
            backends=["sqlite", "duckdb",  "polars"],
            data_sizes=["small", "medium"],
            required_capabilities=[],
            expected_performance_threshold=5.0,  # 5 seconds max
            memory_threshold_mb=100.0
        ),

        "sql_intensive": MatrixTestConfig(
            test_id="sql_ops",
            description="SQL-heavy operations for SQL-capable backends",
            complexity=TestComplexity.INTEGRATION,
            backends=["sqlite_memory", "duckdb_memory", "polars"],
            data_sizes=["medium", "large"],
            required_capabilities=[BackendCapability.SQL_QUERIES],
            expected_performance_threshold=30.0,
            memory_threshold_mb=500.0
        ),

        "large_dataset": MatrixTestConfig(
            test_id="large_data",
            description="Large dataset processing capabilities",
            complexity=TestComplexity.STRESS,
            backends=["duckdb_memory", "polars"],  # Only most capable backends
            data_sizes=["large", "xlarge"],
            required_capabilities=[BackendCapability.LARGE_DATASETS],
            expected_performance_threshold=60.0,
            memory_threshold_mb=1000.0
        ),

        "complex_types": MatrixTestConfig(
            test_id="complex_types",
            description="Complex data type handling",
            complexity=TestComplexity.EDGE_CASE,
            backends=["sqlite_memory", "duckdb_memory",  "polars"],
            data_sizes=["small"],
            required_capabilities=[BackendCapability.COMPLEX_TYPES],
            expected_performance_threshold=10.0,
            memory_threshold_mb=200.0
        ),

        "analytics_workload": MatrixTestConfig(
            test_id="analytics",
            description="Analytics and aggregation workloads",
            complexity=TestComplexity.INTEGRATION,
            backends=["duckdb_memory", "polars"],
            data_sizes=["medium", "large"],
            required_capabilities=[BackendCapability.ANALYTICS],
            expected_performance_threshold=45.0,
            memory_threshold_mb=800.0
        )
    }


@pytest.fixture(scope="session")
def backend_capability_matrix():
    """Matrix defining capabilities of different backends."""

    return {
        "sqlite_memory": {
            "capabilities": [
                BackendCapability.SQL_QUERIES,
                BackendCapability.COMPLEX_TYPES
            ],
            "max_recommended_rows": 1_000_000,
            "performance_class": "medium",
            "memory_efficiency": "medium"
        },

        "duckdb_memory": {
            "capabilities": [
                BackendCapability.SQL_QUERIES,
                BackendCapability.COMPLEX_TYPES,
                BackendCapability.LARGE_DATASETS,
                BackendCapability.ANALYTICS,
                BackendCapability.GEOSPATIAL
            ],
            "max_recommended_rows": 100_000_000,
            "performance_class": "high",
            "memory_efficiency": "high"
        },

        "pandas_df": {
            "capabilities": [
                BackendCapability.COMPLEX_TYPES,
                BackendCapability.ANALYTICS
            ],
            "max_recommended_rows": 10_000_000,
            "performance_class": "medium",
            "memory_efficiency": "low"
        },

        "polars": {
            "capabilities": [
                BackendCapability.SQL_QUERIES,
                BackendCapability.COMPLEX_TYPES,
                BackendCapability.LARGE_DATASETS,
                BackendCapability.ANALYTICS
            ],
            "max_recommended_rows": 1_000_000_000,
            "performance_class": "high",
            "memory_efficiency": "high"
        }
    }

@pytest.fixture
def matrix_test_data_generator():
    """Advanced data generator for matrix testing scenarios."""

    def generate_scenario_data(
        scenario: str,
        size_config: Dict[str, int],
        complexity: TestComplexity = TestComplexity.INTEGRATION,
        include_edge_cases: bool = True
    ) -> Dict[str, Any]:
        """Generate test data for specific matrix testing scenarios."""

        rows = size_config.get("rows", 1000)
        cols = size_config.get("cols", 10)

        if scenario == "financial_analytics":
            return _generate_financial_analytics_data(rows, cols, complexity, include_edge_cases)

        elif scenario == "customer_360":
            return _generate_customer_360_data(rows, cols, complexity, include_edge_cases)

        elif scenario == "iot_time_series":
            return _generate_iot_time_series_data(rows, cols, complexity, include_edge_cases)

        elif scenario == "data_quality_assessment":
            return _generate_data_quality_assessment_data(rows, cols, complexity, include_edge_cases)

        elif scenario == "multi_format_integration":
            return _generate_multi_format_data(rows, cols, complexity, include_edge_cases)

        else:
            # Generate generic test data
            return _generate_generic_test_data(rows, cols, complexity, include_edge_cases)

    def _generate_financial_analytics_data(rows: int, cols: int, complexity: TestComplexity, edge_cases: bool):
        """Generate financial analytics test data."""

        base_data = {
            "transaction_id": [f"TXN_{i:08d}" for i in range(rows)],
            "account_id": [f"ACC_{random.randint(1000, 9999):04d}" for _ in range(rows)],
            "transaction_date": [
                datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
                for _ in range(rows)
            ],
            "amount": [
                round(random.uniform(-10000.0, 50000.0), 2)
                for _ in range(rows)
            ],
            "currency": random.choices(["USD", "EUR", "GBP", "JPY"], k=rows, weights=[60, 20, 15, 5]),
            "transaction_type": random.choices(
                ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT", "FEE"],
                k=rows, weights=[25, 20, 20, 30, 5]
            )
        }

        if complexity in [TestComplexity.INTEGRATION, TestComplexity.STRESS]:
            # Add more complex analytics columns
            base_data.update({
                "risk_score": [random.uniform(0, 1) for _ in range(rows)],
                "category_l1": random.choices(["RETAIL", "BUSINESS", "INVESTMENT"], k=rows),
                "category_l2": random.choices(["GROCERY", "RESTAURANT", "ONLINE", "ATM"], k=rows),
                "merchant_id": [f"MER_{random.randint(1, 10000):05d}" for _ in range(rows)],
                "geolocation": [
                    f"{random.uniform(25, 50):.6f},{random.uniform(-125, -70):.6f}"
                    for _ in range(rows)
                ]
            })

        if edge_cases:
            # Introduce edge cases
            edge_indices = random.sample(range(rows), min(rows // 20, 50))  # 5% edge cases
            for idx in edge_indices:
                if random.random() < 0.3:
                    base_data["amount"][idx] = 0.0  # Zero amounts
                elif random.random() < 0.3:
                    base_data["transaction_date"][idx] = None  # Missing dates
                elif random.random() < 0.3:
                    base_data["currency"][idx] = "UNKNOWN"  # Invalid currency

        return base_data

    def _generate_customer_360_data(rows: int, cols: int, complexity: TestComplexity, edge_cases: bool):
        """Generate customer 360 view test data."""

        customers = [f"CUST_{i:06d}" for i in range(1, min(rows // 5, 10000))]

        base_data = {
            "customer_id": random.choices(customers, k=rows),  # Multiple records per customer
            "record_date": [
                datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))
                for _ in range(rows)
            ],
            "channel": random.choices(["WEB", "MOBILE", "STORE", "CALL_CENTER"], k=rows),
            "interaction_type": random.choices(
                ["PURCHASE", "SUPPORT", "BROWSE", "RETURN", "COMPLAINT"],
                k=rows, weights=[40, 20, 25, 10, 5]
            ),
            "value": [round(random.uniform(0, 5000), 2) for _ in range(rows)],
            "satisfaction_score": [random.randint(1, 5) for _ in range(rows)]
        }

        if complexity in [TestComplexity.INTEGRATION, TestComplexity.STRESS]:
            # Add customer demographics and advanced metrics
            base_data.update({
                "age_group": random.choices(["18-25", "26-35", "36-45", "46-55", "56+"], k=rows),
                "segment": random.choices(["PREMIUM", "STANDARD", "BUDGET"], k=rows, weights=[20, 60, 20]),
                "lifetime_value": [round(random.uniform(100, 50000), 2) for _ in range(rows)],
                "churn_probability": [random.uniform(0, 1) for _ in range(rows)],
                "product_affinity": [
                    f"PROD_{random.randint(1, 100):03d}" for _ in range(rows)
                ]
            })

        return base_data

    def _generate_iot_time_series_data(rows: int, cols: int, complexity: TestComplexity, edge_cases: bool):
        """Generate IoT time series test data."""

        sensors = [f"SENSOR_{i:03d}" for i in range(1, min(cols, 100))]

        base_timestamp = datetime(2024, 1, 1, 0, 0, 0)

        base_data = {
            "timestamp": [
                base_timestamp + timedelta(seconds=i * 60)  # Minute intervals
                for i in range(rows)
            ],
            "device_id": random.choices(sensors, k=rows)
        }

        # Generate sensor readings
        for i, sensor in enumerate(sensors[:cols-2]):  # Leave room for timestamp and device_id
            # Each sensor has different characteristics
            base_value = 20 + (i * 5)  # Different base values
            noise_level = 1 + (i * 0.5)  # Different noise levels

            readings = []
            for j in range(rows):
                # Simulate realistic sensor readings with trends and noise
                trend = 0.01 * j  # Slight upward trend
                seasonal = 5 * random.random() * (1 if j % 100 < 50 else -1)  # Seasonal variation
                noise = random.gauss(0, noise_level)

                value = base_value + trend + seasonal + noise

                if edge_cases and random.random() < 0.02:  # 2% chance of anomaly
                    value *= random.choice([0.1, 0.2, 5.0, 10.0])  # Outlier

                readings.append(round(value, 3))

            base_data[f"sensor_{i:02d}_reading"] = readings

        if complexity in [TestComplexity.INTEGRATION, TestComplexity.STRESS]:
            # Add device metadata
            base_data.update({
                "device_status": random.choices(["ONLINE", "OFFLINE", "MAINTENANCE"], k=rows, weights=[80, 15, 5]),
                "location": random.choices(["BUILDING_A", "BUILDING_B", "OUTDOOR"], k=rows),
                "battery_level": [random.uniform(0, 100) for _ in range(rows)]
            })

        return base_data

    def _generate_data_quality_assessment_data(rows: int, cols: int, complexity: TestComplexity, edge_cases: bool):
        """Generate data with intentional quality issues for testing."""

        base_data = {
            "record_id": [f"REC_{i:06d}" for i in range(rows)],
            "customer_name": [
                random.choice(["Alice Johnson", "Bob Smith", "Charlie Brown", "", None, "UNKNOWN"])
                for _ in range(rows)
            ],
            "email": [
                random.choice([
                    "alice@example.com", "bob@example.COM", "charlie@invalid",
                    "diana@", "@example.com", None, "", "not_an_email"
                ])
                for _ in range(rows)
            ],
            "phone": [
                random.choice([
                    "555-123-4567", "(555) 234-5678", "5552345678",
                    "+1-555-345-6789", "invalid_phone", None, ""
                ])
                for _ in range(rows)
            ],
            "age": [
                random.choice([25, 30, -5, 999, None, 0, 150, 35])  # Mix valid and invalid ages
                for _ in range(rows)
            ]
        }

        # Introduce systematic quality issues
        if edge_cases:
            # Add duplicate records
            duplicate_indices = random.sample(range(rows), min(rows // 10, 100))
            for i in range(0, len(duplicate_indices), 2):
                if i + 1 < len(duplicate_indices):
                    source_idx = duplicate_indices[i]
                    target_idx = duplicate_indices[i + 1]
                    # Copy data from source to target (creating duplicate)
                    for col in base_data:
                        base_data[col][target_idx] = base_data[col][source_idx]

        return base_data

    def _generate_multi_format_data(rows: int, cols: int, complexity: TestComplexity, edge_cases: bool):
        """Generate data that tests multiple format handling."""

        base_data = {
            "id": list(range(rows)),
            "json_data": [
                f'{{"key": "value_{i}", "nested": {{"count": {i}}}}}'
                for i in range(rows)
            ],
            "csv_like": [
                f"value1,value2,value3,{i}" for i in range(rows)
            ],
            "xml_like": [
                f"<record><id>{i}</id><value>data_{i}</value></record>"
                for i in range(rows)
            ],
            "binary_hex": [
                bytes(f"binary_data_{i}", 'utf-8').hex()
                for i in range(rows)
            ]
        }

        if complexity in [TestComplexity.INTEGRATION, TestComplexity.STRESS]:
            # Add more complex formats
            base_data.update({
                "nested_json": [
                    f'{{"level1": {{"level2": {{"level3": {{"value": {i}}}}}}}'
                    for i in range(rows)
                ],
                "array_json": [
                    f'[{i}, {i+1}, {i+2}, {i+3}]' for i in range(rows)
                ]
            })

        return base_data

    def _generate_generic_test_data(rows: int, cols: int, complexity: TestComplexity, edge_cases: bool):
        """Generate generic test data for fallback scenarios."""

        data = {}

        for i in range(cols):
            col_name = f"col_{i:03d}"

            if i % 5 == 0:  # Integer columns
                data[col_name] = [random.randint(-1000, 1000) for _ in range(rows)]
            elif i % 5 == 1:  # Float columns
                data[col_name] = [round(random.uniform(-100.0, 100.0), 3) for _ in range(rows)]
            elif i % 5 == 2:  # String columns
                data[col_name] = [
                    ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                    for _ in range(rows)
                ]
            elif i % 5 == 3:  # Date columns
                base_date = datetime(2020, 1, 1)
                data[col_name] = [
                    base_date + timedelta(days=random.randint(0, 1825))
                    for _ in range(rows)
                ]
            else:  # Boolean columns
                data[col_name] = [random.choice([True, False]) for _ in range(rows)]

            # Add nulls based on complexity
            if complexity in [TestComplexity.EDGE_CASE, TestComplexity.STRESS]:
                null_rate = 0.1  # 10% nulls
                null_indices = random.sample(range(rows), int(rows * null_rate))
                for idx in null_indices:
                    data[col_name][idx] = None

        return data

    return generate_scenario_data


@pytest.fixture(scope="session")
def cross_backend_operation_matrix():
    """Matrix of operations to test across different backends."""

    return {
        "basic_operations": [
            {"operation": "count", "description": "Row count"},
            {"operation": "column_names", "description": "Column enumeration"},
            {"operation": "head", "description": "First N rows", "params": {"n": 10}},
            {"operation": "sample", "description": "Random sampling", "params": {"n": 5}}
        ],

        "filtering_operations": [
            {"operation": "filter_equals", "description": "Equality filter"},
            {"operation": "filter_greater", "description": "Greater than filter"},
            {"operation": "filter_range", "description": "Range filter"},
            {"operation": "filter_null", "description": "Null value filter"},
            {"operation": "filter_not_null", "description": "Non-null filter"}
        ],

        "aggregation_operations": [
            {"operation": "sum", "description": "Sum aggregation"},
            {"operation": "mean", "description": "Average calculation"},
            {"operation": "count_distinct", "description": "Distinct count"},
            {"operation": "group_by", "description": "Group by operation"},
            {"operation": "min_max", "description": "Min/Max calculation"}
        ],

        "transformation_operations": [
            {"operation": "select_columns", "description": "Column selection"},
            {"operation": "rename_columns", "description": "Column renaming"},
            {"operation": "add_column", "description": "Computed column"},
            {"operation": "sort", "description": "Sort operation"},
            {"operation": "deduplicate", "description": "Remove duplicates"}
        ],

        "join_operations": [
            {"operation": "inner_join", "description": "Inner join"},
            {"operation": "left_join", "description": "Left outer join"},
            {"operation": "self_join", "description": "Self join"},
            {"operation": "union", "description": "Union operation"}
        ],

        "materialization_operations": [
            {"operation": "to_pandas", "description": "Pandas materialization"},
            {"operation": "to_polars", "description": "Polars materialization"},
            {"operation": "to_pyarrow", "description": "PyArrow materialization"},
            {"operation": "to_dict", "description": "Dictionary materialization"},
            {"operation": "to_csv", "description": "CSV export"}
        ]
    }


@pytest.fixture
def matrix_test_validator():
    """Validator for matrix test results across backends."""

    class MatrixTestValidator:
        def __init__(self):
            self.tolerance = 1e-6
            self.results_cache = {}

        def validate_cross_backend_consistency(
            self,
            operation_results: Dict[str, Any],
            operation_name: str,
            tolerance: Optional[float] = None
        ) -> bool:
            """Validate that operation results are consistent across backends."""

            if not operation_results:
                return False

            tol = tolerance or self.tolerance

            # Get reference result (first backend)
            reference_backend = list(operation_results.keys())[0]
            reference_result = operation_results[reference_backend]

            # Compare all other backends to reference
            for backend, result in operation_results.items():
                if backend == reference_backend:
                    continue

                if not self._compare_results(reference_result, result, tol):
                    print(f"Inconsistency in {operation_name}: {reference_backend} vs {backend}")
                    print(f"Reference: {reference_result}")
                    print(f"Comparison: {result}")
                    return False

            return True

        def _compare_results(self, ref, comp, tolerance):
            """Compare two results with appropriate tolerance."""

            # Handle None values
            if ref is None and comp is None:
                return True
            if ref is None or comp is None:
                return False

            # Handle numeric values
            if isinstance(ref, (int, float)) and isinstance(comp, (int, float)):
                return abs(ref - comp) <= tolerance

            # Handle lists/arrays
            if isinstance(ref, (list, tuple)) and isinstance(comp, (list, tuple)):
                if len(ref) != len(comp):
                    return False
                return all(
                    self._compare_results(r, c, tolerance)
                    for r, c in zip(ref, comp)
                )

            # Handle dictionaries
            if isinstance(ref, dict) and isinstance(comp, dict):
                if set(ref.keys()) != set(comp.keys()):
                    return False
                return all(
                    self._compare_results(ref[k], comp[k], tolerance)
                    for k in ref.keys()
                )

            # Handle DataFrames (basic comparison)
            if hasattr(ref, 'shape') and hasattr(comp, 'shape'):
                return ref.shape == comp.shape

            # Default: exact equality
            return ref == comp

        def validate_performance_thresholds(
            self,
            performance_results: Dict[str, float],
            thresholds: Dict[str, float]
        ) -> Dict[str, bool]:
            """Validate that performance results meet specified thresholds."""

            validation_results = {}

            for operation, duration in performance_results.items():
                threshold = thresholds.get(operation, float('inf'))
                validation_results[operation] = duration <= threshold

                if duration > threshold:
                    print(f"Performance threshold exceeded for {operation}: "
                          f"{duration:.3f}s > {threshold:.3f}s")

            return validation_results

        def cache_result(self, test_id: str, backend: str, result: Any):
            """Cache test result for comparison."""
            if test_id not in self.results_cache:
                self.results_cache[test_id] = {}
            self.results_cache[test_id][backend] = result

        def get_cached_results(self, test_id: str) -> Dict[str, Any]:
            """Get cached results for a test."""
            return self.results_cache.get(test_id, {})

    return MatrixTestValidator()


@pytest.fixture(scope="session")
def matrix_test_scenarios():
    """Predefined test scenarios for comprehensive matrix testing."""

    return {
        "smoke_test_matrix": {
            "description": "Basic smoke test across all backends",
            "backends": ["sqlite_memory", "duckdb_memory",  "polars"],
            "operations": ["count", "column_names", "head"],
            "data_scenarios": ["financial_analytics"],
            "complexity": TestComplexity.SMOKE
        },

        "integration_test_matrix": {
            "description": "Integration testing with realistic workloads",
            "backends": ["sqlite_memory", "duckdb_memory", "polars"],
            "operations": ["filter_equals", "group_by", "aggregation", "join"],
            "data_scenarios": ["customer_360", "financial_analytics"],
            "complexity": TestComplexity.INTEGRATION
        },

        "performance_test_matrix": {
            "description": "Performance comparison across backends",
            "backends": ["duckdb_memory", "polars"],
            "operations": ["large_aggregation", "complex_join", "materialization"],
            "data_scenarios": ["iot_time_series"],
            "complexity": TestComplexity.STRESS
        },

        "edge_case_matrix": {
            "description": "Edge case handling across backends",
            "backends": ["sqlite_memory", "duckdb_memory",  "polars"],
            "operations": ["null_handling", "type_coercion", "error_recovery"],
            "data_scenarios": ["data_quality_assessment"],
            "complexity": TestComplexity.EDGE_CASE
        }
    }
