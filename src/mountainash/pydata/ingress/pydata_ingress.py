from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union
import logging
# from enum import Enum

# from mountainash.core.factories import BaseStrategyFactory
# from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

from.pydata_ingress_factory import PydataIngressFactory
# from .base_pydata_converter import BasePydataConverter
from mountainash.core.types import PolarsFrame

if TYPE_CHECKING:
    import polars as pl
    from mountainash.schema.config import SchemaConfig

logger = logging.getLogger(__name__)

class PydataIngress():
    """Factory for creating appropriate Python data conversion strategies with lazy loading."""

    @classmethod
    def convert(cls,
                data: Any, /,
                column_config: Optional[Union["SchemaConfig", Dict[str, Any], str]] = None
    ) -> PolarsFrame:
        """
        Convert Python data structure to Polars DataFrame.

        This is the main public interface for data conversion.

        Args:
            data: Input data (dataclass, Pydantic model, dict of lists, or list of dicts)
            column_config: Optional column transformation configuration

        Returns:
            pl.DataFrame: Converted DataFrame

        Raises:
            ValueError: If no suitable strategy is found or conversion fails

        Example:
            >>> df = PydataIngress.convert([{"id": 1, "name": "Alice"}])
            >>> isinstance(df, pl.DataFrame)
            True
        """
        strategy = PydataIngressFactory.get_strategy(data)
        return strategy.convert(data, column_config=column_config)
