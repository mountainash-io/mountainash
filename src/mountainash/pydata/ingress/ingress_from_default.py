from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars

if TYPE_CHECKING:
    import polars as pl

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.schema.config import SchemaConfig, init_column_config
from mountainash.core.types import PolarsFrame

logger = logging.getLogger(__name__)


class DataframeFromDefault(BasePydataIngressHandler):
    """Default strategy for handling any data that can be passed to polars.DataFrame."""

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        return True

    @classmethod
    def convert(cls,
                data: Any, /,
                column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None,
    ) -> PolarsFrame:
        """Convert data to Polars DataFrame using default behavior."""
        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Create DataFrame
        df = pl.DataFrame(data, strict=False)

        if column_config is not None:
            column_transforms: SchemaConfig = init_column_config(column_config)
            df = column_transforms.apply(df)

        return df
