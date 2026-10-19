from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import logging

# Runtime imports for actual functionality
from mountainash.core.lazy_imports import import_polars, import_pydantic

if TYPE_CHECKING:
    from mountainash.typespec.spec import TypeSpec
    from mountainash.core.types import PolarsFrame

from .base_pydata_ingress_handler import BasePydataIngressHandler
from mountainash.core.lowering_reuse import OCCURRENCE, declare_lowering

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
                type_spec: Optional['TypeSpec'] = None,
                *,
                source_spec: Optional['TypeSpec'] = None,
                inline_conform: bool = True,
    ) -> PolarsFrame:
        """
        Convert Pydantic model(s) to Polars DataFrame.

        Uses HYBRID STRATEGY for optimal performance:
        - Custom converters: Apply at EDGES (Python layer, before DataFrame)
        - Native conversions: Apply in CENTER (DataFrame layer, vectorized)

        This is ~10x faster than applying custom conversions in DataFrame!

        Args:
            data: Single Pydantic model or list of Pydantic models
            type_spec: Optional TypeSpec for column type coercion and renaming
            source_spec: Explicit source dtypes, overriding scalar model declarations.
            inline_conform: Apply type_spec conversions after source extraction.

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

        from mountainash.typespec.extraction import extract_from_pydantic
        from .custom_type_helpers import _source_schema_overrides, apply_hybrid_conversion

        model_type = type(data[0]) if isinstance(data, list) and data else type(data)
        model_spec = extract_from_pydantic(model_type) if data_dicts else None
        overrides = _source_schema_overrides(source_spec, model_spec=model_spec)
        df = apply_hybrid_conversion(
            data_dicts, type_spec, schema_overrides=overrides,
            inline_conform=inline_conform,
        )

        return df
declare_lowering(DataframeFromPydantic.convert.__func__, OCCURRENCE)
