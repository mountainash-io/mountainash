from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
import logging
# from enum import Enum

# from mountainash.core.factories import BaseStrategyFactory
# from mountainash.pydata.constants import CONST_PYTHON_DATAFORMAT

from.pydata_ingress_factory import PydataIngressFactory
# from .base_pydata_converter import BasePydataConverter

if TYPE_CHECKING:
    from mountainash.core.types import PolarsFrame
    from mountainash.typespec.spec import TypeSpec

logger = logging.getLogger(__name__)


def schema_literal_ingress_safe(value: Any) -> bool:
    """Whether schema inspection may safely convert this held literal value."""
    from datetime import date, datetime, time, timedelta
    from decimal import Decimal
    from uuid import UUID

    if type(value) in {str, bytes, int, float, bool, type(None)}:
        return True
    if isinstance(value, (date, datetime, time, timedelta, Decimal, UUID)):
        return True
    if type(value).__module__.startswith("numpy"):
        import numpy as np

        if isinstance(value, (np.ndarray, np.generic)):
            return not value.dtype.hasobject
    if type(value) in {list, tuple, set, frozenset}:
        return all(schema_literal_ingress_safe(item) for item in value)
    if type(value) is dict:
        return all(
            schema_literal_ingress_safe(key) and schema_literal_ingress_safe(item)
            for key, item in value.items()
        )
    return False

class PydataIngress():
    """Factory for creating appropriate Python data conversion strategies with lazy loading."""

    @classmethod
    def convert(cls,
                data: Any, /,
                type_spec: Optional['TypeSpec'] = None,
                *,
                source_spec: Optional['TypeSpec'] = None,
                inline_conform: bool = True,
    ) -> PolarsFrame:
        """
        Convert Python data structure to Polars DataFrame.

        Source dtypes resolve per column: explicit source_spec, then model
        annotations, then bounded native inference. Unrefined ANY is no override.
        type_spec is a conversion target, never source-type evidence.

        Args:
            data: Input data (dataclass, Pydantic model, dict of lists, or list of dicts)
            type_spec: Optional TypeSpec for column type coercion and renaming
            source_spec: Optional input dtype declarations, not transformations.
            inline_conform: Run target conversions (default True). False still
                applies source typing during construction.

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
        return strategy.convert(
            data, type_spec=type_spec, source_spec=source_spec,
            inline_conform=inline_conform,
        )
