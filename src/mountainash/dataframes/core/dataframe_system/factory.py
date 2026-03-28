"""
DataFrameSystemFactory - Factory for creating backend-specific DataFrameSystems.

Provides:
- Automatic backend detection from DataFrame objects
- @register_dataframe_system decorator for auto-registration
- Caching of instantiated systems
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type

from .base import DataFrameSystem
from .constants import CONST_DATAFRAME_BACKEND

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Registry for backend systems
_dataframe_systems_registry: Dict[CONST_DATAFRAME_BACKEND, Type[DataFrameSystem]] = {}

# Cache for instantiated systems (singleton per backend)
_dataframe_systems_cache: Dict[CONST_DATAFRAME_BACKEND, DataFrameSystem] = {}


def register_dataframe_system(
    backend: CONST_DATAFRAME_BACKEND,
) -> Callable[[Type[DataFrameSystem]], Type[DataFrameSystem]]:
    """
    Decorator for registering DataFrameSystem implementations.

    Usage:
        @register_dataframe_system(CONST_DATAFRAME_BACKEND.POLARS)
        class PolarsDataFrameSystem(DataFrameSystem):
            ...

    Args:
        backend: The backend type this system handles

    Returns:
        Decorator function that registers the class
    """

    def decorator(cls: Type[DataFrameSystem]) -> Type[DataFrameSystem]:
        _dataframe_systems_registry[backend] = cls
        logger.debug(f"Registered DataFrameSystem: {backend.name} -> {cls.__name__}")
        return cls

    return decorator


class DataFrameSystemFactory:
    """
    Factory for creating and caching DataFrameSystem instances.

    Features:
    - Automatic backend detection from DataFrame objects
    - Substring-based module detection (robust against __module__ path variations)
    - Narwhals fallback for unknown types
    - Singleton caching of system instances
    - Auto-registration via @register_dataframe_system decorator
    """

    # Cache: type identity → backend (populated on first detection)
    _runtime_type_map: Dict[type, CONST_DATAFRAME_BACKEND] = {}

    # =========================================================================
    # Public API
    # =========================================================================

    @classmethod
    def get_system(cls, df: Any) -> DataFrameSystem:
        """
        Get the appropriate DataFrameSystem for a DataFrame.

        Args:
            df: Any supported DataFrame type

        Returns:
            DataFrameSystem instance for the detected backend

        Raises:
            ValueError: If no system found for the DataFrame type
        """
        backend = cls._detect_backend(df)
        return cls._get_or_create_system(backend)

    @classmethod
    def get_system_for_backend(cls, backend: CONST_DATAFRAME_BACKEND) -> DataFrameSystem:
        """
        Get DataFrameSystem for a specific backend.

        Args:
            backend: The backend to get system for

        Returns:
            DataFrameSystem instance for the backend
        """
        return cls._get_or_create_system(backend)

    @classmethod
    def detect_backend(cls, df: Any) -> CONST_DATAFRAME_BACKEND:
        """
        Detect the backend type for a DataFrame (public method).

        Args:
            df: Any supported DataFrame type

        Returns:
            CONST_DATAFRAME_BACKEND enum value
        """
        return cls._detect_backend(df)

    # =========================================================================
    # Backend Detection
    # =========================================================================

    @classmethod
    def _detect_backend(cls, df: Any) -> CONST_DATAFRAME_BACKEND:
        """
        Detect backend using substring module checks and narwhals fallback.

        Uses the same proven approach as expressions.identify_backend():
        simple ``"library" in module`` checks that work regardless of how
        a library sets ``__module__`` (e.g. ``"pandas"`` vs ``"pandas.core.frame"``).

        Detection order matters — narwhals wraps other backends, so it must
        be checked before polars/pandas. Ibis is checked before polars because
        ibis module names are unambiguous.

        Results are cached by type identity for fast repeated lookups.
        """
        obj_type = type(df)

        # Fast path: cached type
        if obj_type in cls._runtime_type_map:
            return cls._runtime_type_map[obj_type]

        backend = cls._identify_backend(df)
        cls._runtime_type_map[obj_type] = backend
        return backend

    @classmethod
    def _identify_backend(cls, df: Any) -> CONST_DATAFRAME_BACKEND:
        """Core detection logic — no caching, called once per type."""
        module = type(df).__module__

        # Narwhals detection FIRST — it wraps other backends
        if "narwhals" in module or hasattr(df, "_compliant_frame"):
            return CONST_DATAFRAME_BACKEND.NARWHALS

        # Ibis detection — unambiguous module names
        if "ibis" in module:
            return CONST_DATAFRAME_BACKEND.IBIS

        # Polars detection — check for polars-specific attribute to disambiguate
        if "polars" in module:
            return CONST_DATAFRAME_BACKEND.POLARS

        # Narwhals fallback — try wrapping unknown types (handles pandas, pyarrow, cudf)
        try:
            import narwhals as nw
            nw.from_native(df)
            return CONST_DATAFRAME_BACKEND.NARWHALS
        except (TypeError, ValueError, ImportError):
            pass

        raise ValueError(
            f"No DataFrameSystem found for type: {module}.{type(df).__name__}. "
            f"Tip: Ensure the DataFrame type is supported (polars, pandas, pyarrow, ibis, narwhals)."
        )

    # =========================================================================
    # System Instantiation and Caching
    # =========================================================================

    @classmethod
    def _get_or_create_system(cls, backend: CONST_DATAFRAME_BACKEND) -> DataFrameSystem:
        """
        Get cached system or create new one.

        Args:
            backend: Backend to get system for

        Returns:
            DataFrameSystem instance (cached singleton)
        """
        if backend in _dataframe_systems_cache:
            return _dataframe_systems_cache[backend]

        # Ensure backend is registered
        cls._ensure_backend_registered(backend)

        if backend not in _dataframe_systems_registry:
            raise ValueError(
                f"No DataFrameSystem registered for backend: {backend.name}. "
                f"Available: {[b.name for b in _dataframe_systems_registry.keys()]}"
            )

        # Create and cache
        system_class = _dataframe_systems_registry[backend]
        system = system_class()
        _dataframe_systems_cache[backend] = system
        logger.debug(f"Created DataFrameSystem: {backend.name} -> {system_class.__name__}")
        return system

    @classmethod
    def _ensure_backend_registered(cls, backend: CONST_DATAFRAME_BACKEND) -> None:
        """
        Ensure backend system is imported and registered.

        Auto-imports backend modules to trigger @register_dataframe_system decorators.
        """
        if backend in _dataframe_systems_registry:
            return

        # Import backend module to trigger registration
        try:
            if backend == CONST_DATAFRAME_BACKEND.POLARS:
                from ...backends.polars import dataframe_system  # noqa: F401
            elif backend == CONST_DATAFRAME_BACKEND.NARWHALS:
                from ...backends.narwhals import dataframe_system  # noqa: F401
            elif backend == CONST_DATAFRAME_BACKEND.IBIS:
                from ...backends.ibis import dataframe_system  # noqa: F401
        except ImportError as e:
            logger.warning(f"Failed to import backend {backend.name}: {e}")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    @classmethod
    def get_registered_backends(cls) -> list[CONST_DATAFRAME_BACKEND]:
        """Get list of registered backends."""
        return list(_dataframe_systems_registry.keys())

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the system cache (for testing)."""
        _dataframe_systems_cache.clear()
        cls._runtime_type_map.clear()
        logger.debug("DataFrameSystem cache cleared")

    @classmethod
    def register_type_object(
        cls,
        obj_type: type,
        backend: CONST_DATAFRAME_BACKEND,
    ) -> None:
        """
        Runtime registration of a type for a specific backend.

        Args:
            obj_type: The type class to register
            backend: Backend to route to
        """
        cls._runtime_type_map[obj_type] = backend
        logger.info(f"Registered type: {obj_type.__module__}.{obj_type.__name__} -> {backend.name}")
