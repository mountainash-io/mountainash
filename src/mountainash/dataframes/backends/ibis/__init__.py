"""
Ibis backend implementation.

SQL backend support for:
- DuckDB
- PostgreSQL
- BigQuery
- Snowflake
- And other Ibis-supported backends

This module exports:
- IbisDataFrameSystem: Complete DataFrameSystem implementation for Ibis

The system is auto-registered via @register_dataframe_system decorator.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=[],
    submod_attrs={
        "dataframe_system": ["IbisDataFrameSystem"],
    },
)
