"""
DataFrameSystem - Backend abstraction layer for DataFrame operations.

This module provides the DataFrameSystem pattern, aligned with mountainash-expressions'
ExpressionSystem architecture:

- **DataFrameSystem**: Abstract base combining all operation protocols
- **Backend Systems**: PolarsDataFrameSystem, NarwhalsDataFrameSystem, IbisDataFrameSystem
- **Auto-registration**: @register_dataframe_system decorator

Architecture:

    ┌─────────────────────────────────────────────────────────────────┐
    │                    DataFrameSystem                               │
    │  (Inherits from all Protocol classes)                           │
    ├─────────────────────────────────────────────────────────────────┤
    │  CastProtocol      → to_polars(), to_pandas(), to_ibis()       │
    │  IntrospectProtocol → get_shape(), get_schema(), get_dtypes()  │
    │  JoinProtocol      → join()                                     │
    │  SelectProtocol    → select(), rename(), reorder()             │
    │  FilterProtocol    → filter()                                   │
    └─────────────────────────────────────────────────────────────────┘
                                   │
                                   │ inherits
                                   ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │              Backend-Specific Systems                            │
    ├─────────────────┬─────────────────┬─────────────────────────────┤
    │  PolarsSystem   │  NarwhalsSystem │  IbisSystem                 │
    │  (native Polars)│  (pandas/arrow) │  (SQL backends)             │
    └─────────────────┴─────────────────┴─────────────────────────────┘

Usage:
    from mountainash.dataframes.core.dataframe_system import DataFrameSystemFactory

    # Auto-detect backend and get system
    system = DataFrameSystemFactory.get_system(df)

    # Use any operation
    pandas_df = system.to_pandas(df)
    shape = system.get_shape(df)
    result = system.join(left, right, on="key")
"""

from .base import DataFrameSystem
from .factory import DataFrameSystemFactory, register_dataframe_system
from .constants import CONST_DATAFRAME_BACKEND

__all__ = [
    "DataFrameSystem",
    "DataFrameSystemFactory",
    "register_dataframe_system",
    "CONST_DATAFRAME_BACKEND",
]
