"""
Core framework infrastructure for mountainash-dataframes.

This module contains:
- protocols/: Abstract interfaces that backends must implement
- dataframe_system/: DataFrameSystem abstraction and factory
- api/: User-facing facades (DataFrameUtils)
- factory/: Backend routing and strategy factory
- typing/: Type definitions and type guards
"""

import lazy_loader

__getattr__, __dir__, __all__ = lazy_loader.attach(
    __name__,
    submodules=["protocols", "dataframe_system", "api", "factory", "typing", "constants"],
    submod_attrs={
        "constants": [
            "Backend",
            "InputType",
            "DataFrameSystemBackend",
            "backend_to_system",
        ],
    },
)
