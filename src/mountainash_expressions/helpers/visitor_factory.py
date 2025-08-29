from typing import Any, Callable
from ..visitors import ExpressionVisitor
from ..visitors.boolean import BooleanExpressionVisitor, IbisBooleanExpressionVisitor, PolarsBooleanExpressionVisitor, PandasBooleanExpressionVisitor, PyArrowBooleanExpressionVisitor
from ..visitors.ternary import TernaryExpressionVisitor, IbisTernaryExpressionVisitor, PolarsTernaryExpressionVisitor, PandasTernaryExpressionVisitor, PyArrowTernaryExpressionVisitor

import pandas as pd
import pyarrow as pa
import polars as pl
import ibis.expr.types as ir

from mountainash_dataframes import BaseDataFrame
# from .raw


class ExpressionVisitorFactory:
    """Ensures consistent backend selection across mixed expression trees"""


        # Registry of visitor implementations
    _visitors_registry = {
        "boolean":{
            'polars':   PolarsBooleanExpressionVisitor,
            'ibis':     IbisBooleanExpressionVisitor,
            'pandas':   PandasBooleanExpressionVisitor,
            'pyarrow':  PyArrowBooleanExpressionVisitor
        },
        "ternary": {
            'polars':   PolarsTernaryExpressionVisitor,
            'ibis':     IbisTernaryExpressionVisitor,
            'pandas':   PandasTernaryExpressionVisitor,
            'pyarrow':  PyArrowTernaryExpressionVisitor
        }
    }

    @classmethod
    def create_visitor(cls, backend: str, logic_type: str) -> ExpressionVisitor:
        """Get visitor for current backend"""
        try:
            return cls._visitors_registry[logic_type][backend]()
        except KeyError:
            raise ValueError(f"Unsupported backend '{backend}' for logic type '{logic_type}'")


    @classmethod
    def create_visitor_for_backend(cls, table: Any, logic_type: str) -> ExpressionVisitor:
        """Get visitor for current backend and logic type"""
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, logic_type)


    @classmethod
    def create_boolean_visitor_for_backend(cls, table: Any, **kwargs) -> BooleanExpressionVisitor:
        """Get boolean visitor for current backend"""
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, "boolean")

    @classmethod
    def create_ternary_visitor_for_backend(cls, table: Any, **kwargs) -> TernaryExpressionVisitor:
        """Get ternary visitor for current backend"""
        backend = cls._identify_backend(table)
        return cls.create_visitor(backend, "ternary")


    @classmethod
    def _identify_backend(cls, table: Any) -> str:

        # Always available strategies first
        if isinstance(table, (BaseDataFrame, ir.Table)):
            return "ibis"
        elif isinstance(table, pd.DataFrame):
            return "pandas"
        elif isinstance(table, (pl.DataFrame, pl.LazyFrame)):
            return "polars"

        # PyArrow detection
        elif hasattr(pa, 'Table') and isinstance(table, pa.Table):
            return "pyarrow"
        elif (isinstance(table, pa.RecordBatch) if hasattr(pa, 'RecordBatch') else False):
            return "pyarrow"
        else:
            raise ValueError(f"Unsupported dataframe type: {type(table)}")




    # def get_raw_visitor(self) -> RawExpressionVisitor:
    #     """Get raw visitor for current backend"""
    #     return self._raw_visitors[self.backend](visitor_factory=self)

    # def get_fuzzy_visitor(self, **kwargs) -> FuzzyExpressionVisitor:  # FUTURE
    #     """Get fuzzy visitor for current backend"""
    #     return self._fuzzy_visitors[self.backend](visitor_factory=self, **kwargs)
