from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import logging
# from enum import Enum

# from mountainash.core.factories import BaseStrategyFactory
# from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

from.pydata_ingress_factory import PydataIngressFactory
# from .base_pydata_converter import BasePydataConverter
from mountainash.core.types import PolarsFrame

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec

logger = logging.getLogger(__name__)

class PydataIngress():
    """Factory for creating appropriate Python data conversion strategies with lazy loading."""

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None
    ) -> PolarsFrame:
        """
        Convert Python data structure to Polars DataFrame.

        This is the main public interface for data conversion.

        Args:
            data: Input data (dataclass, Pydantic model, dict of lists, or list of dicts)
            type_spec: Optional TypeSpec for column type coercion and renaming

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
        return strategy.convert(data, type_spec=type_spec)
