"""Enhanced fixture collection for mountainash-data testing.

This package provides comprehensive test fixtures covering:
- Realistic business data scenarios
- Edge cases and boundary conditions  
- Comprehensive data type coverage
- Performance and stress testing data

Usage:
    Import specific fixture modules as needed:
    
    from tests.fixtures.realistic_data_fixtures import financial_transactions_data
    from tests.fixtures.edge_case_fixtures import numeric_boundary_data
    from tests.fixtures.data_type_fixtures import comprehensive_data_types
    from tests.fixtures.performance_fixtures import large_dataset_configs
"""

# Re-export commonly used fixtures for convenience
from .realistic_data_fixtures import (
    financial_transactions_data,
    ecommerce_orders_data, 
    time_series_data,
    user_behavior_data,
    data_generator
)

from .edge_case_fixtures import (
    numeric_boundary_data,
    string_boundary_data,
    datetime_boundary_data,
    null_and_missing_data,
    edge_case_dataframes
)

from .data_type_fixtures import (
    comprehensive_data_types,
    null_patterns_comprehensive,
    data_type_conversions,
    temporal_data_comprehensive,
    data_type_factory
)

from .performance_fixtures import (
    large_dataset_configs,
    performance_data_generator,
    memory_monitor,
    performance_timer
)

__all__ = [
    # Realistic data fixtures
    "financial_transactions_data",
    "ecommerce_orders_data", 
    "time_series_data",
    "user_behavior_data",
    "data_generator",
    
    # Edge case fixtures
    "numeric_boundary_data",
    "string_boundary_data", 
    "datetime_boundary_data",
    "null_and_missing_data",
    "edge_case_dataframes",
    
    # Data type fixtures
    "comprehensive_data_types",
    "null_patterns_comprehensive",
    "data_type_conversions",
    "temporal_data_comprehensive", 
    "data_type_factory",
    
    # Performance fixtures
    "large_dataset_configs",
    "performance_data_generator",
    "memory_monitor",
    "performance_timer"
]