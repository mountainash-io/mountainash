"""
Narwhals backend implementation.

Universal adapter providing support for:
- pandas DataFrames
- PyArrow Tables
- cuDF DataFrames
- Any other Narwhals-supported backend

This module exports:
- NarwhalsDataFrameSystem: Complete DataFrameSystem implementation via Narwhals

The system is auto-registered via @register_dataframe_system decorator.
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=[],
    submod_attrs={
        "dataframe_system": ["NarwhalsDataFrameSystem"],
    },
)
