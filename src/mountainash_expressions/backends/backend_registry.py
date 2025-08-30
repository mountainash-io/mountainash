"""Backend plugin implementations for the visitor factory."""

from typing import Dict, Type, Any
import logging

from ..core.visitor import ExpressionVisitor
from ..core.visitor.visitor_factory import BackendPlugin
from ..core.constants import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES

logger = logging.getLogger(__name__)


class PandasBackendPlugin(BackendPlugin):
    """Plugin for Pandas backend support."""
    
    def get_backend_id(self) -> str:
        return CONST_VISITOR_BACKENDS.PANDAS
    
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        from .pandas import PandasBooleanExpressionVisitor, PandasTernaryExpressionVisitor
        return {
            CONST_LOGIC_TYPES.BOOLEAN: PandasBooleanExpressionVisitor,
            CONST_LOGIC_TYPES.TERNARY: PandasTernaryExpressionVisitor,
        }
    
    def can_handle(self, table: Any) -> bool:
        try:
            import pandas as pd
            return isinstance(table, pd.DataFrame)
        except ImportError:
            return False
    
    @property
    def priority(self) -> int:
        return 5


class PolarsBackendPlugin(BackendPlugin):
    """Plugin for Polars backend support."""
    
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
        return 5


class IbisBackendPlugin(BackendPlugin):
    """Plugin for Ibis backend support."""
    
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
        return 10  # Higher priority for Ibis


class PyArrowBackendPlugin(BackendPlugin):
    """Plugin for PyArrow backend support."""
    
    def get_backend_id(self) -> str:
        return CONST_VISITOR_BACKENDS.PYARROW
    
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        from .pyarrow import PyArrowBooleanExpressionVisitor, PyArrowTernaryExpressionVisitor
        return {
            CONST_LOGIC_TYPES.BOOLEAN: PyArrowBooleanExpressionVisitor,
            CONST_LOGIC_TYPES.TERNARY: PyArrowTernaryExpressionVisitor,
        }
    
    def can_handle(self, table: Any) -> bool:
        try:
            import pyarrow as pa
            return (
                (hasattr(pa, 'Table') and isinstance(table, pa.Table)) or
                (hasattr(pa, 'RecordBatch') and isinstance(table, pa.RecordBatch))
            )
        except ImportError:
            return False
    
    @property
    def priority(self) -> int:
        return 3


def register_all_backends():
    """Register all available backend plugins with the visitor factory.
    
    This function can be called to explicitly register all backends.
    The factory will also lazily load them as needed.
    """
    from ..core.visitor.visitor_factory import ExpressionVisitorFactory
    
    backends = [
        IbisBackendPlugin(),
        PandasBackendPlugin(),
        PolarsBackendPlugin(),
        PyArrowBackendPlugin(),
    ]
    
    for backend in backends:
        try:
            ExpressionVisitorFactory.register_backend_plugin(backend)
            logger.info(f"Registered backend plugin: {backend.get_backend_id()}")
        except Exception as e:
            logger.warning(f"Failed to register backend {backend.get_backend_id()}: {e}")