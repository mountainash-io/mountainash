"""Backend plugin implementations for the visitor factory using Narwhals for multi-backend support."""

from typing import Dict, Type, Any
import logging

from ..core.visitor import ExpressionVisitor
from ..core.visitor.visitor_factory import BackendPlugin
from ..core.constants import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

logger = logging.getLogger(__name__)


class NarwhalsUniversalBackendPlugin(BackendPlugin):
    """
    Universal backend plugin using Narwhals for multi-backend support.
    
    This single plugin handles all dataframe backends that Narwhals supports:
    - Pandas
    - Polars
    - PyArrow
    - cuDF
    - Modin
    - Dask
    - DuckDB
    - Ibis
    - PySpark
    
    Priority is determined by the underlying backend type.
    """
    
    def __init__(self):
        self._backend_type = None
    
    def get_backend_id(self) -> str:
        """Return backend ID based on detected type."""
        if self._backend_type:
            return self._backend_type
        return "narwhals"
    
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        """Return Narwhals-based visitors for all logic types."""
        from .narwhals import NarwhalsBooleanExpressionVisitor, NarwhalsTernaryExpressionVisitor
        return {
            CONST_LOGIC_TYPES.BOOLEAN: NarwhalsBooleanExpressionVisitor,
            CONST_LOGIC_TYPES.TERNARY: NarwhalsTernaryExpressionVisitor,
        }
    
    def can_handle(self, table: Any) -> bool:
        """
        Check if Narwhals can handle this table type.
        Also detects and stores the underlying backend type.
        """
        try:
            import narwhals as nw
            
            # Check if it's already a Narwhals DataFrame
            if isinstance(table, (nw.DataFrame, nw.LazyFrame)):
                self._detect_backend_type(table)
                return True
            
            # Try to convert to Narwhals
            try:
                nw_table = nw.from_native(table)
                self._detect_backend_type(nw_table)
                return True
            except Exception:
                return False
                
        except ImportError:
            logger.warning("Narwhals not installed. Install with: pip install narwhals")
            return False
    
    def _detect_backend_type(self, nw_table: Any) -> None:
        """Detect the underlying backend type from a Narwhals object."""
        try:
            import narwhals as nw
            
            # Get the native object to determine backend
            native = nw.to_native(nw_table)
            
            # Detect backend type
            if self._is_pandas(native):
                self._backend_type = CONST_VISITOR_BACKENDS.PANDAS
            elif self._is_polars(native):
                self._backend_type = CONST_VISITOR_BACKENDS.POLARS
            elif self._is_pyarrow(native):
                self._backend_type = CONST_VISITOR_BACKENDS.PYARROW
            elif self._is_ibis(native):
                self._backend_type = CONST_VISITOR_BACKENDS.IBIS
            else:
                # For other backends (cuDF, Modin, Dask, etc.)
                self._backend_type = "narwhals"
                
        except Exception as e:
            logger.debug(f"Could not detect backend type: {e}")
            self._backend_type = "narwhals"
    
    def _is_pandas(self, obj: Any) -> bool:
        """Check if object is a Pandas DataFrame."""
        try:
            import pandas as pd
            return isinstance(obj, pd.DataFrame)
        except ImportError:
            return False
    
    def _is_polars(self, obj: Any) -> bool:
        """Check if object is a Polars DataFrame or LazyFrame."""
        try:
            import polars as pl
            return isinstance(obj, (pl.DataFrame, pl.LazyFrame))
        except ImportError:
            return False
    
    def _is_pyarrow(self, obj: Any) -> bool:
        """Check if object is a PyArrow Table or RecordBatch."""
        try:
            import pyarrow as pa
            return isinstance(obj, (pa.Table, pa.RecordBatch)) if hasattr(pa, 'Table') else False
        except ImportError:
            return False
    
    def _is_ibis(self, obj: Any) -> bool:
        """Check if object is an Ibis Table."""
        try:
            import ibis.expr.types as ir
            return isinstance(obj, ir.Table)
        except ImportError:
            return False
    
    @property
    def priority(self) -> int:
        """
        Return priority based on detected backend type.
        Higher priority for SQL-based backends (Ibis, DuckDB).
        """
        if self._backend_type == CONST_VISITOR_BACKENDS.IBIS:
            return 10
        elif self._backend_type == CONST_VISITOR_BACKENDS.POLARS:
            return 7
        elif self._backend_type == CONST_VISITOR_BACKENDS.PYARROW:
            return 5
        elif self._backend_type == CONST_VISITOR_BACKENDS.PANDAS:
            return 3
        else:
            return 1  # Default priority for unknown backends


class PolarsNativeBackendPlugin(BackendPlugin):
    """
    Native Polars backend plugin for when direct Polars operations are preferred.
    
    This can be used alongside the Narwhals plugin when you need Polars-specific
    optimizations that aren't available through Narwhals.
    """
    
    def get_backend_id(self) -> str:
        return CONST_VISITOR_BACKENDS.POLARS
    
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        from .polars import PolarsBooleanExpressionVisitor, PolarsTernaryExpressionVisitor
        return {
            CONST_LOGIC_TYPES.BOOLEAN: PolarsBooleanExpressionVisitor,
            CONST_LOGIC_TYPES.TERNARY: PolarsTernaryExpressionVisitor,
        }
    
    def can_handle(self, table: Any) -> bool:
        try:
            import polars as pl
            return isinstance(table, (pl.DataFrame, pl.LazyFrame))
        except ImportError:
            return False
    
    @property
    def priority(self) -> int:
        return 8  # Higher than Narwhals for Polars to prefer native when available


class IbisNativeBackendPlugin(BackendPlugin):
    """
    Native Ibis backend plugin for SQL-based operations.
    
    Ibis provides a unified interface to many SQL backends, so this can be
    useful when you need SQL-specific optimizations.
    """
    
    def get_backend_id(self) -> str:
        return CONST_VISITOR_BACKENDS.IBIS
    
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        from .ibis import IbisBooleanExpressionVisitor, IbisTernaryExpressionVisitor
        return {
            CONST_LOGIC_TYPES.BOOLEAN: IbisBooleanExpressionVisitor,
            CONST_LOGIC_TYPES.TERNARY: IbisTernaryExpressionVisitor,
        }
    
    def can_handle(self, table: Any) -> bool:
        try:
            import ibis.expr.types as ir
            return isinstance(table, ir.Table)
        except ImportError:
            return False
    
    @property
    def priority(self) -> int:
        return 11  # Highest priority for SQL operations


def register_all_backends(use_native_backends: bool = False):
    """
    Register backend plugins with the visitor factory.
    
    Args:
        use_native_backends: If True, also register native Polars and Ibis backends
                            alongside the Narwhals universal backend. This allows
                            backend-specific optimizations when needed.
    
    The Narwhals backend will handle:
    - Pandas
    - PyArrow
    - cuDF
    - Modin
    - Dask
    - DuckDB
    - PySpark
    - And any other backend Narwhals supports
    
    Native backends (optional) provide optimized implementations for:
    - Polars
    - Ibis
    """
    from ..core.visitor.visitor_factory import ExpressionVisitorFactory
    
    # Always register the universal Narwhals backend
    backends = [NarwhalsUniversalBackendPlugin()]
    
    # Optionally add native backends for specific optimizations
    if use_native_backends:
        backends.extend([
            IbisNativeBackendPlugin(),
            PolarsNativeBackendPlugin(),
        ])
    
    for backend in backends:
        try:
            ExpressionVisitorFactory.register_backend_plugin(backend)
            logger.info(f"Registered backend plugin: {backend.get_backend_id()}")
        except Exception as e:
            logger.warning(f"Failed to register backend {backend.get_backend_id()}: {e}")


def configure_narwhals_backends(backends_config: Dict[str, Any] = None):
    """
    Configure Narwhals backend settings.
    
    Args:
        backends_config: Optional configuration dictionary with settings like:
            {
                'use_native_backends': bool,  # Use native Polars/Ibis alongside Narwhals
                'lazy_evaluation': bool,       # Prefer lazy evaluation when available
                'backend_priority': {          # Override default backend priorities
                    'polars': 10,
                    'pandas': 5,
                    'pyarrow': 3
                }
            }
    
    Example:
        >>> configure_narwhals_backends({
        ...     'use_native_backends': True,  # Use optimized native backends
        ...     'lazy_evaluation': True        # Prefer lazy frames when possible
        ... })
    """
    config = backends_config or {}
    
    # Register backends based on configuration
    use_native = config.get('use_native_backends', False)
    register_all_backends(use_native_backends=use_native)
    
    # Additional configuration can be added here
    if config.get('lazy_evaluation'):
        logger.info("Configured for lazy evaluation preference")
    
    # Log active configuration
    logger.info(f"Narwhals backends configured with: {config}")