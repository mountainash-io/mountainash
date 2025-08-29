from typing import Any, Callable
from ..core import ExpressionVisitor
from ..boolean import BooleanExpressionVisitor, IbisBooleanExpressionVisitor, PolarsBooleanExpressionVisitor, PandasBooleanExpressionVisitor, PyArrowBooleanExpressionVisitor
from ..ternary import TernaryExpressionVisitor, IbisTernaryExpressionVisitor, PolarsTernaryExpressionVisitor, PandasTernaryExpressionVisitor, PyArrowTernaryExpressionVisitor

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
            'pandas':   PyArrowBooleanExpressionVisitor
        },
        "ternary": {
            'polars':   PolarsTernaryExpressionVisitor,
            'ibis':     IbisTernaryExpressionVisitor,
            'pandas':   PandasTernaryExpressionVisitor,
            'pyarrow':  PyArrowTernaryExpressionVisitor
        }
    }

    @classmethod
    def _get_strategy(cls, df: Any, logic_type: str) -> ExpressionVisitor:

        # Always available strategies first
        if isinstance(df, (BaseDataFrame, ir.Table)):
            return cls._visitors_registry[logic_type]["ibis"]()
        elif isinstance(df, pd.DataFrame):
            return cls._visitors_registry[logic_type]["pandas"]()
        elif isinstance(df, (pl.DataFrame, pl.LazyFrame)):
            return cls._visitors_registry[logic_type]["polars"]()

        # PyArrow detection
        elif hasattr(pa, 'Table') and isinstance(df, pa.Table):
            return cls._visitors_registry[logic_type]["pyarrow"]()
        elif (isinstance(df, pa.RecordBatch) if hasattr(pa, 'RecordBatch') else False):
            return cls._visitors_registry[logic_type]["pyarrow"]()
        else:
            raise ValueError(f"Unsupported dataframe type: {type(df)}")

    @classmethod
    def get_boolean_visitor(cls, table: Any,  **kwargs) -> BooleanExpressionVisitor:
        """Get boolean visitor for current backend"""
        return cls._get_strategy(table, "boolean")

    @classmethod
    def get_ternary_visitor(cls, table: Any, **kwargs) -> TernaryExpressionVisitor:
        """Get ternary visitor for current backend"""
        return cls._get_strategy(table, "ternary")

    # def get_raw_visitor(self) -> RawExpressionVisitor:
    #     """Get raw visitor for current backend"""
    #     return self._raw_visitors[self.backend](visitor_factory=self)

    # def get_fuzzy_visitor(self, **kwargs) -> FuzzyExpressionVisitor:  # FUTURE
    #     """Get fuzzy visitor for current backend"""
    #     return self._fuzzy_visitors[self.backend](visitor_factory=self, **kwargs)
