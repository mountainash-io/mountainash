"""Dynamic visitor factory with plugin-based backend registration."""

from typing import Any, Dict, Type, Optional, Callable, Tuple
from abc import ABC, abstractmethod
import logging

from . import ExpressionVisitor
from . import BooleanExpressionVisitor
from . import TernaryExpressionVisitor
from ..constants import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

logger = logging.getLogger(__name__)


class BackendPlugin(ABC):
    """Abstract base class for backend plugins."""

    @abstractmethod
    def get_backend_id(self) -> str:
        """Return the unique identifier for this backend."""
        pass

    @abstractmethod
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        """Return a mapping of logic types to visitor classes."""
        pass

    @abstractmethod
    def can_handle(self, table: Any) -> bool:
        """Check if this backend can handle the given table type."""
        pass

    @property
    def priority(self) -> int:
        """Priority for backend detection (higher = checked first). Default is 0."""
        return 0


class ExpressionVisitorFactory:
    """Dynamic visitor factory with plugin-based backend registration.

    This factory supports:
    - Dynamic backend registration via plugins
    - Automatic backend detection
    - Lazy loading of backend implementations
    - Custom backend type checking
    """

    # Registry of backend plugins
    _backend_plugins: Dict[str, BackendPlugin] = {}

    # Registry of visitor implementations (populated by plugins)
    _visitors_registry: Dict[str, Dict[str, Type[ExpressionVisitor]]] = {
        CONST_LOGIC_TYPES.BOOLEAN: {},
        CONST_LOGIC_TYPES.TERNARY: {},
    }

    # Backend detection functions (populated by plugins)
    _backend_detectors: list[Tuple[int, str, Callable[[Any], bool]]] = []

    # Flag to track if built-in backends have been loaded
    _builtin_backends_loaded: bool = False

    @classmethod
    def register_backend_plugin(cls, plugin: BackendPlugin) -> None:
        """Register a backend plugin.

        Args:
            plugin: The backend plugin to register
        """
        backend_id = plugin.get_backend_id()

        # Register the plugin
        cls._backend_plugins[backend_id] = plugin

        # Register visitors for each logic type
        visitors = plugin.get_visitors()
        for logic_type, visitor_class in visitors.items():
            if logic_type not in cls._visitors_registry:
                cls._visitors_registry[logic_type] = {}
            cls._visitors_registry[logic_type][backend_id] = visitor_class

        # Register backend detector with priority
        cls._backend_detectors.append((plugin.priority, backend_id, plugin.can_handle))

        # Keep detectors sorted by priority (descending)
        cls._backend_detectors.sort(key=lambda x: -x[0])

        logger.debug(f"Registered backend plugin: {backend_id}")

    @classmethod
    def register_backend(
        cls,
        backend_id: str,
        visitors: Dict[str, Type[ExpressionVisitor]],
        detector: Callable[[Any], bool],
        priority: int = 0
    ) -> None:
        """Register a backend directly without a plugin class.

        Args:
            backend_id: Unique identifier for the backend
            visitors: Mapping of logic types to visitor classes
            detector: Function to detect if a table is of this backend type
            priority: Priority for backend detection (higher = checked first)
        """
        # Register visitors for each logic type
        for logic_type, visitor_class in visitors.items():
            if logic_type not in cls._visitors_registry:
                cls._visitors_registry[logic_type] = {}
            cls._visitors_registry[logic_type][backend_id] = visitor_class

        # Register backend detector with priority
        cls._backend_detectors.append((priority, backend_id, detector))

        # Keep detectors sorted by priority (descending)
        cls._backend_detectors.sort(key=lambda x: -x[0])

        logger.debug(f"Registered backend: {backend_id}")

    @classmethod
    def _load_builtin_backends(cls) -> None:
        """Lazily load built-in backend implementations."""
        if cls._builtin_backends_loaded:
            return

        try:
            # Try to import all built-in backends
            from ...backends import (
                IbisBooleanExpressionVisitor, IbisTernaryExpressionVisitor,
                PandasBooleanExpressionVisitor, PandasTernaryExpressionVisitor,
                PolarsBooleanExpressionVisitor, PolarsTernaryExpressionVisitor,
                PyArrowBooleanExpressionVisitor, PyArrowTernaryExpressionVisitor
            )

            # Register Ibis backend
            import ibis.expr.types as ir
            cls.register_backend(
                backend_id=CONST_VISITOR_BACKENDS.IBIS,
                visitors={
                    CONST_LOGIC_TYPES.BOOLEAN: IbisBooleanExpressionVisitor,
                    CONST_LOGIC_TYPES.TERNARY: IbisTernaryExpressionVisitor,
                },
                detector=lambda table: isinstance(table, ir.Table),
                priority=10
            )

            # Register Pandas backend
            import pandas as pd
            cls.register_backend(
                backend_id=CONST_VISITOR_BACKENDS.PANDAS,
                visitors={
                    CONST_LOGIC_TYPES.BOOLEAN: PandasBooleanExpressionVisitor,
                    CONST_LOGIC_TYPES.TERNARY: PandasTernaryExpressionVisitor,
                },
                detector=lambda table: isinstance(table, pd.DataFrame),
                priority=5
            )

            # Register Polars backend
            import polars as pl
            cls.register_backend(
                backend_id=CONST_VISITOR_BACKENDS.POLARS,
                visitors={
                    CONST_LOGIC_TYPES.BOOLEAN: PolarsBooleanExpressionVisitor,
                    CONST_LOGIC_TYPES.TERNARY: PolarsTernaryExpressionVisitor,
                },
                detector=lambda table: isinstance(table, (pl.DataFrame, pl.LazyFrame)),
                priority=5
            )

            # Register PyArrow backend
            import pyarrow as pa
            cls.register_backend(
                backend_id=CONST_VISITOR_BACKENDS.PYARROW,
                visitors={
                    CONST_LOGIC_TYPES.BOOLEAN: PyArrowBooleanExpressionVisitor,
                    CONST_LOGIC_TYPES.TERNARY: PyArrowTernaryExpressionVisitor,
                },
                detector=lambda table: (
                    (hasattr(pa, 'Table') and isinstance(table, pa.Table)) or
                    (hasattr(pa, 'RecordBatch') and isinstance(table, pa.RecordBatch))
                ),
                priority=3
            )

            cls._builtin_backends_loaded = True
            logger.debug("Loaded built-in backends")

        except ImportError as e:
            logger.warning(f"Could not load all built-in backends: {e}")
            cls._builtin_backends_loaded = True  # Prevent repeated attempts

    @classmethod
    def create_visitor(cls, backend: str, logic_type: str) -> ExpressionVisitor:
        """Create a visitor for the specified backend and logic type.

        Args:
            backend: Backend identifier (e.g., CONST_VISITOR_BACKENDS.PANDAS)
            logic_type: Logic type (e.g., CONST_LOGIC_TYPES.BOOLEAN)

        Returns:
            An instance of the appropriate visitor

        Raises:
            ValueError: If the backend/logic combination is not supported
        """
        # Ensure built-in backends are loaded
        cls._load_builtin_backends()

        try:
            visitor_class = cls._visitors_registry[logic_type][backend]
            return visitor_class()
        except KeyError:
            available_backends = list(cls._visitors_registry.get(logic_type, {}).keys())
            raise ValueError(
                f"Unsupported backend '{backend}' for logic type '{logic_type}'. "
                f"Available backends: {available_backends}"
            )

    @classmethod
    def create_visitor_for_backend(cls, table: Any, logic_type: str) -> ExpressionVisitor:
        """Create a visitor by auto-detecting the backend from the table.

        Args:
            table: The dataframe/table to detect backend from
            logic_type: Logic type (e.g., CONST_LOGIC_TYPES.BOOLEAN)

        Returns:
            An instance of the appropriate visitor

        Raises:
            ValueError: If backend cannot be detected or is not supported
        """
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, logic_type)

    @classmethod
    def create_boolean_visitor_for_backend(cls, table: Any, **kwargs) -> BooleanExpressionVisitor:
        """Create a boolean visitor by auto-detecting the backend.

        Args:
            table: The dataframe/table to detect backend from
            **kwargs: Additional arguments (for compatibility)

        Returns:
            An instance of the appropriate boolean visitor
        """
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, CONST_LOGIC_TYPES.BOOLEAN)

    @classmethod
    def create_ternary_visitor_for_backend(cls, table: Any, **kwargs) -> TernaryExpressionVisitor:
        """Create a ternary visitor by auto-detecting the backend.

        Args:
            table: The dataframe/table to detect backend from
            **kwargs: Additional arguments (for compatibility)

        Returns:
            An instance of the appropriate ternary visitor
        """
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, CONST_LOGIC_TYPES.TERNARY)

    @classmethod
    def _identify_backend(cls, table: Any) -> str:
        """Identify the backend type from a table/dataframe.

        Args:
            table: The dataframe/table to identify

        Returns:
            Backend identifier string

        Raises:
            ValueError: If the table type is not supported
        """
        # Ensure built-in backends are loaded
        cls._load_builtin_backends()

        # Check each registered detector in priority order
        for priority, backend_id, detector in cls._backend_detectors:
            try:
                if detector(table):
                    return backend_id
            except Exception as e:
                logger.debug(f"Detector for {backend_id} failed: {e}")
                continue

        # If no detector matched, raise an error
        raise ValueError(
            f"Unsupported dataframe type: {type(table)}. "
            f"Registered backends: {[bid for _, bid, _ in cls._backend_detectors]}"
        )

    @classmethod
    def get_registered_backends(cls) -> Dict[str, list[str]]:
        """Get all registered backends grouped by logic type.

        Returns:
            Dictionary mapping logic types to lists of backend IDs
        """
        cls._load_builtin_backends()
        return {
            logic_type: list(backends.keys())
            for logic_type, backends in cls._visitors_registry.items()
        }

    @classmethod
    def is_backend_registered(cls, backend_id: str, logic_type: Optional[str] = None) -> bool:
        """Check if a backend is registered.

        Args:
            backend_id: Backend identifier to check
            logic_type: Optional logic type to check for specific support

        Returns:
            True if the backend is registered (for the given logic type if specified)
        """
        cls._load_builtin_backends()

        if logic_type:
            return backend_id in cls._visitors_registry.get(logic_type, {})

        # Check if backend is registered for any logic type
        for backends in cls._visitors_registry.values():
            if backend_id in backends:
                return True
        return False

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registered backends (useful for testing)."""
        cls._backend_plugins.clear()
        cls._visitors_registry = {
            CONST_LOGIC_TYPES.BOOLEAN: {},
            CONST_LOGIC_TYPES.TERNARY: {},
        }
        cls._backend_detectors.clear()
        cls._builtin_backends_loaded = False
        logger.debug("Cleared visitor factory registry")
