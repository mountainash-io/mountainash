"""
Cross-module lazy import utilities for mountainash.

Provides functions to lazily import optional dependencies (polars, pandas,
narwhals, ibis, pyarrow, pydantic) with helpful error messages.

These are shared by schema, pydata, dataframes, and expressions modules.
"""

import importlib
import importlib.util
from typing import Any, Optional, Dict


def is_available(module_name: str) -> bool:
    """Check if a module is available without importing it."""
    return importlib.util.find_spec(module_name) is not None


def require_module(module_name: str, install_hint: Optional[str] = None) -> Any:
    """Import a module or raise a helpful error."""
    try:
        return importlib.import_module(module_name)
    except ImportError as e:
        if not install_hint:
            install_hint = get_missing_dependency_error(module_name)

        raise ImportError(
            f"{module_name} is required. Example installation: {install_hint}"
        ) from e


# ============================================================================
# Convenience Functions
# ============================================================================

def import_pandas() -> Any:
    """Lazy import of pandas."""
    return require_module("pandas", "pip install pandas>=2.2.0")


def import_polars() -> Any:
    """Lazy import of polars."""
    return require_module("polars", "pip install polars>=1.35.1")


def import_pyarrow() -> Any:
    """Lazy import of pyarrow."""
    return require_module("pyarrow", "pip install pyarrow==17.0.0")


def import_ibis() -> Any:
    """Lazy import of ibis."""
    return require_module("ibis", "pip install 'ibis-framework[polars,sqlite,duckdb]'")


def import_ibis_expr_types() -> Any:
    """Lazy import of ibis.expr.types."""
    if not require_module("ibis", "pip install 'ibis-framework[polars,sqlite,duckdb]'"):
        return None
    return require_module("ibis.expr.types", "pip install 'ibis-framework[polars,sqlite,duckdb]'")


def import_ibis_expr_ops() -> Any:
    """Lazy import of ibis.expr.operations."""
    if not require_module("ibis", "pip install 'ibis-framework[polars,sqlite,duckdb]'"):
        return None
    return require_module("ibis.expr.operations", "pip install 'ibis-framework[polars,sqlite,duckdb]'")


def import_narwhals() -> Any:
    """Lazy import of narwhals."""
    return require_module("narwhals")


def import_pydantic() -> Any:
    """Lazy import of pydantic."""
    return require_module("pydantic")


# ============================================================================
# Backend Detection
# ============================================================================

def get_available_backends() -> Dict[str, bool]:
    """
    Check which backends are currently available WITHOUT importing them.

    Returns:
        Dictionary mapping backend names to availability status
    """
    backends = [
        "pandas",
        "polars",
        "pyarrow",
        "ibis",
        "narwhals",
        "pydantic",
    ]

    return {backend: is_available(backend) for backend in backends}


# ============================================================================
# Installation Info
# ============================================================================

INSTALL_COMMANDS = {
    "pandas": "pip install pandas>=2.2.0",
    "polars": "pip install polars>=1.35.1",
    "pyarrow": "pip install pyarrow==17.0.0",
    "ibis": "pip install 'ibis-framework[polars,sqlite,duckdb]'",
    "ibis.expr.types": "pip install 'ibis-framework[polars,sqlite,duckdb]'",
    "narwhals": "pip install narwhals",
    "pydantic": "pip install pydantic>=2.0.0",
}


def get_missing_dependency_error(backend: str, operation: str = "") -> str:
    """
    Generate a helpful error message for missing dependencies.

    Args:
        backend: Name of the missing backend
        operation: Optional operation that requires the backend

    Returns:
        Formatted error message with installation instructions
    """
    operation_msg = f" for {operation}" if operation else ""
    install_cmd = INSTALL_COMMANDS.get(backend.lower(), f"pip install {backend}")

    return (
        f"The {backend} backend is required{operation_msg} but is not installed.\n"
        f"Install it with: {install_cmd}\n"
        f"Or install all optional dependencies with: pip install 'mountainash[all]'"
    )
