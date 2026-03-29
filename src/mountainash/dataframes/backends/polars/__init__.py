"""
Polars backend implementation.

Primary backend for mountainash-dataframes, providing native Polars support
for both eager DataFrames and lazy LazyFrames.

This module exports:
- PolarsDataFrameSystem: Complete DataFrameSystem implementation for Polars

The system is auto-registered via @register_dataframe_system decorator.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=[],
    submod_attrs={
        "dataframe_system": ["PolarsDataFrameSystem"],
    },
)
