from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Union
import logging

# Runtime imports for actual functionality
from mountainash.dataframes.runtime_imports import import_polars, import_pydantic

if TYPE_CHECKING:
    import polars as pl

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.dataframes.schema_config import SchemaConfig, init_column_config
from mountainash.dataframes.typing import PolarsFrame

logger = logging.getLogger(__name__)

class DataframeFromPydantic(BasePydataIngressHandler):
    """Strategy for handling Pydantic models."""

    @classmethod
    def can_handle(cls, data: Any, /) -> bool:
        """Check if data is a Pydantic model."""
        pydantic = import_pydantic()
        if pydantic is None:
            return False

        # Check if data has Pydantic model characteristics
        if hasattr(data, '__pydantic_core_schema__'):
            return True

        # Check for list of Pydantic models
        if isinstance(data, list) and data and hasattr(data[0], '__pydantic_core_schema__'):
            return True

        return False

    @classmethod
    def convert(cls,
                data: Any, /,
                column_config: Optional[Union[SchemaConfig, Dict[str, Any], str]] = None,
    ) -> PolarsFrame:
        """
        Convert Pydantic model(s) to Polars DataFrame.

        Uses HYBRID STRATEGY for optimal performance:
        - Custom converters: Apply at EDGES (Python layer, before DataFrame)
        - Native conversions: Apply in CENTER (DataFrame layer, vectorized)

        This is ~10x faster than applying custom conversions in DataFrame!

        Args:
            data: Single Pydantic model or list of Pydantic models
            column_config: Optional column transformation config

        Returns:
            Polars DataFrame with hybrid conversions applied
        """
        pydantic = import_pydantic()
        if pydantic is None:
            raise ImportError("pydantic is required for this operation")

        pl = import_polars()
        if pl is None:
            raise ImportError("polars is required for this operation")

        # Convert to list of dicts
        if isinstance(data, list):
            data_dicts = []
            for item in data:
                # Use model_dump if available (Pydantic v2), otherwise dict (Pydantic v1)
                if hasattr(item, 'model_dump'):
                    data_dicts.append(item.model_dump())
                elif hasattr(item, 'dict'):
                    data_dicts.append(item.dict())
                else:
                    raise ValueError(f"Unknown Pydantic model type: {type(item)}")
        else:
            # Use model_dump if available (Pydantic v2), otherwise dict (Pydantic v1)
            if hasattr(data, 'model_dump'):
                data_dicts = [data.model_dump()]
            elif hasattr(data, 'dict'):
                data_dicts = [data.dict()]
            else:
                raise ValueError(f"Unknown Pydantic model type: {type(data)}")

        # Apply hybrid conversion strategy if config provided
        if column_config is not None:
            from .custom_type_helpers import apply_hybrid_conversion

            column_transforms: SchemaConfig = init_column_config(column_config)

            # HYBRID STRATEGY:
            # 1. Custom converters at edges (Python layer)
            # 2. Native conversions in DataFrame (vectorized, FAST!)
            df = apply_hybrid_conversion(data_dicts, column_transforms)
        else:
            # No config - just create DataFrame
            df = pl.DataFrame(data_dicts, strict=False)

        return df
