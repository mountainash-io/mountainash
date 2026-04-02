"""
mountainash.typespec — Universal type system foundation.

This package provides the type vocabulary that all schema and conformance
operations depend on. It is deliberately minimal at this stage; further
modules will be added as Tasks 2–7 are completed.
"""
from __future__ import annotations

from mountainash.typespec.universal_types import (
    UniversalType,
    UNIVERSAL_TO_PANDAS,
    UNIVERSAL_TO_IBIS,
    POLARS_TO_UNIVERSAL,
    PANDAS_TO_UNIVERSAL,
    ARROW_TO_UNIVERSAL,
    IBIS_TO_UNIVERSAL,
    PYTHON_TO_UNIVERSAL,
    SAFE_CASTS,
    UNSAFE_CASTS,
    normalize_type,
    is_safe_cast,
    get_polars_type,
    get_arrow_type,
    get_universal_to_backend_mapping,
    get_backend_to_universal_mapping,
)
from mountainash.typespec.type_bridge import (
    UNIVERSAL_TO_MOUNTAINASH,
    bridge_type,
)

__all__ = [
    # Universal type enum
    "UniversalType",

    # Forward mappings
    "UNIVERSAL_TO_PANDAS",
    "UNIVERSAL_TO_IBIS",

    # Reverse mappings
    "POLARS_TO_UNIVERSAL",
    "PANDAS_TO_UNIVERSAL",
    "ARROW_TO_UNIVERSAL",
    "IBIS_TO_UNIVERSAL",
    "PYTHON_TO_UNIVERSAL",

    # Safe casts
    "SAFE_CASTS",
    "UNSAFE_CASTS",

    # Utility functions
    "normalize_type",
    "is_safe_cast",
    "get_polars_type",
    "get_arrow_type",
    "get_universal_to_backend_mapping",
    "get_backend_to_universal_mapping",

    # Type bridge
    "UNIVERSAL_TO_MOUNTAINASH",
    "bridge_type",
]
