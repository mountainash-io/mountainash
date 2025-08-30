from typing import Any

import pandas as pd
import pyarrow as pa
import polars as pl
import ibis.expr.types as ir

from . import ExpressionVisitor
from . import BooleanExpressionVisitor #, IbisBooleanExpressionVisitor, PolarsBooleanExpressionVisitor, PandasBooleanExpressionVisitor, PyArrowBooleanExpressionVisitor
from . import TernaryExpressionVisitor #, IbisTernaryExpressionVisitor, PolarsTernaryExpressionVisitor, PandasTernaryExpressionVisitor, PyArrowTernaryExpressionVisitor


from ..constants import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES


class ExpressionVisitorFactory:
    """Ensures consistent backend selection across mixed expression trees"""


        # Registry of visitor implementations
    _visitors_registry = {
        CONST_LOGIC_TYPES.BOOLEAN:{
            CONST_VISITOR_BACKENDS.POLARS:   PolarsBooleanExpressionVisitor,
            CONST_VISITOR_BACKENDS.IBIS:     IbisBooleanExpressionVisitor,
            CONST_VISITOR_BACKENDS.PANDAS:   PandasBooleanExpressionVisitor,
            CONST_VISITOR_BACKENDS.PYARROW:  PyArrowBooleanExpressionVisitor
        },
        CONST_LOGIC_TYPES.TERNARY: {
            CONST_VISITOR_BACKENDS.POLARS:   PolarsTernaryExpressionVisitor,
            CONST_VISITOR_BACKENDS.IBIS:     IbisTernaryExpressionVisitor,
            CONST_VISITOR_BACKENDS.PANDAS:   PandasTernaryExpressionVisitor,
            CONST_VISITOR_BACKENDS.PYARROW:  PyArrowTernaryExpressionVisitor
        }
    }

    @classmethod
    def create_visitor(cls, backend: CONST_VISITOR_BACKENDS, logic_type: CONST_LOGIC_TYPES) -> ExpressionVisitor:
        """Get visitor for current backend"""
        try:
            return cls._visitors_registry[logic_type][backend]()
        except KeyError:
            raise ValueError(f"Unsupported backend '{backend}' for logic type '{logic_type}'")


    @classmethod
    def create_visitor_for_backend(cls, table: Any, logic_type: CONST_LOGIC_TYPES) -> ExpressionVisitor:
        """Get visitor for current backend and logic type"""
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, logic_type)


    @classmethod
    def create_boolean_visitor_for_backend(cls, table: Any, **kwargs) -> BooleanExpressionVisitor:
        """Get boolean visitor for current backend"""
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, CONST_LOGIC_TYPES.BOOLEAN)

    @classmethod
    def create_ternary_visitor_for_backend(cls, table: Any, **kwargs) -> TernaryExpressionVisitor:
        """Get ternary visitor for current backend"""
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, CONST_LOGIC_TYPES.TERNARY)


    @classmethod
    def _identify_backend(cls, table: Any) -> CONST_VISITOR_BACKENDS:

        # Always available strategies first
        if isinstance(table, (ir.Table)):
            return CONST_VISITOR_BACKENDS.IBIS
        elif isinstance(table, pd.DataFrame):
            return CONST_VISITOR_BACKENDS.PANDAS
        elif isinstance(table, (pl.DataFrame, pl.LazyFrame)):
            return CONST_VISITOR_BACKENDS.POLARS

        # PyArrow detection
        elif hasattr(pa, 'Table') and isinstance(table, pa.Table):
            return CONST_VISITOR_BACKENDS.PYARROW
        elif (isinstance(table, pa.RecordBatch) if hasattr(pa, 'RecordBatch') else False):
            return CONST_VISITOR_BACKENDS.PYARROW
        else:
            raise ValueError(f"Unsupported dataframe type: {type(table)}")




    # def get_raw_visitor(self) -> RawExpressionVisitor:
    #     """Get raw visitor for current backend"""
    #     return self._raw_visitors[self.backend](visitor_factory=self)

    # def get_fuzzy_visitor(self, **kwargs) -> FuzzyExpressionVisitor:  # FUTURE
    #     """Get fuzzy visitor for current backend"""
    #     return self._fuzzy_visitors[self.backend](visitor_factory=self, **kwargs)
