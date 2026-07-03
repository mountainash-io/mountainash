"""Backend detection — one identify_backend() for expressions AND relations.

Moved verbatim from expressions/core/expression_system/expsys_base.py so both
subsystems share a single detection mechanism (spec §3.2). expsys_base
re-exports these names for backwards compatibility.
"""
from __future__ import annotations

from typing import Any, Dict

from mountainash.core.constants import CONST_BACKEND

# Backend alias mapping
_BACKEND_ALIASES: Dict[str, CONST_BACKEND] = {
    # Polars
    "polars": CONST_BACKEND.POLARS,
    "pl": CONST_BACKEND.POLARS,
    # Ibis
    "ibis": CONST_BACKEND.IBIS,
    "ir": CONST_BACKEND.IBIS,
    # Narwhals
    "narwhals": CONST_BACKEND.NARWHALS,
    "nw": CONST_BACKEND.NARWHALS,
    # Pandas
    "pandas": CONST_BACKEND.PANDAS,
    "pd": CONST_BACKEND.PANDAS,
}


def identify_backend(dataframe_or_backend: Any) -> CONST_BACKEND:
    """
    Identify the backend framework from a DataFrame/Table object or string identifier.

    Args:
        dataframe_or_backend: Either:
            - A DataFrame/Table object (pl.DataFrame, nw.DataFrame, ir.Table, etc.)
            - A string identifier ("polars", "pl", "ibis", "ir", "narwhals", "nw")
            - A CONST_BACKEND enum value

    Returns:
        The identified backend constant

    Raises:
        ValueError: If backend cannot be identified

    Examples:
        >>> identify_backend(polars_df)  # Auto-detect from DataFrame
        >>> identify_backend("polars")   # Explicit string
        >>> identify_backend("ibis")     # Explicit string
        >>> identify_backend(CONST_BACKEND.POLARS)  # Pass-through
    """
    # Handle string identifiers
    if isinstance(dataframe_or_backend, str):
        backend_lower = dataframe_or_backend.lower()
        if backend_lower in _BACKEND_ALIASES:
            return _BACKEND_ALIASES[backend_lower]
        raise ValueError(
            f"Unknown backend identifier: '{dataframe_or_backend}'. "
            f"Valid options: {list(_BACKEND_ALIASES.keys())}"
        )

    # Handle CONST_BACKEND enum directly (pass-through)
    if isinstance(dataframe_or_backend, CONST_BACKEND):
        return dataframe_or_backend

    # Auto-detect from DataFrame object
    dataframe = dataframe_or_backend

    # Get the module and class name
    module_name = type(dataframe).__module__
    class_name = type(dataframe).__name__

    # Narwhals detection FIRST - check for narwhals DataFrame/LazyFrame
    # Narwhals wraps other backends, so we need to check for it before checking for polars/pandas
    if "narwhals" in module_name or hasattr(dataframe, "_compliant_frame"):
        # Check if Narwhals is wrapping Ibis - this is not supported
        if hasattr(dataframe, "implementation"):
            impl = dataframe.implementation
            # Check if it's wrapping Ibis (impl.value == 'ibis')
            if hasattr(impl, "value") and impl.value == "ibis":
                raise ValueError(
                    "Narwhals-wrapped Ibis tables are not supported due to upstream compatibility issues. "
                    "Please unwrap the Ibis table using `df.to_native()` and use the Ibis backend directly."
                )
        # Use Narwhals backend for other implementations (Polars, Pandas, etc.)
        return CONST_BACKEND.NARWHALS

    # Ibis detection
    if "ibis" in module_name:
        return CONST_BACKEND.IBIS

    # Polars detection
    if "polars" in module_name or class_name in ("DataFrame", "LazyFrame"):
        # Check if it's really polars
        if hasattr(dataframe, "lazy"):  # polars-specific method
            return CONST_BACKEND.POLARS

    # Fallback: try wrapping in narwhals
    # This handles pandas, pyarrow, and other narwhals-compatible backends
    try:
        import narwhals as nw
        nw.from_native(dataframe)
        # If we get here, narwhals can handle it
        return CONST_BACKEND.NARWHALS
    except (TypeError, ValueError):
        # Narwhals couldn't wrap it
        pass

    raise ValueError(
        f"Cannot identify backend for type {type(dataframe)}. "
        f"Module: {module_name}, Class: {class_name}. "
        f"Tip: Try wrapping your DataFrame with narwhals: nw.from_native(df)"
    )
