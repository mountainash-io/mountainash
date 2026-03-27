from __future__ import annotations

from .__version__ import __version__

# Keep only essential API exports that don't trigger heavy imports
from .constants import CONST_DATAFRAME_FRAMEWORK, CONST_IBIS_INMEMORY_BACKEND, CONST_EXPRESSION_TYPE, CONST_JOIN_BACKEND_TYPE, CONST_DATAFRAME_BACKEND, CONST_DATAFRAME_TYPE
from .core.typing import SupportedDataFrames, SupportedExpressions, SupportedPythonData, SupportedSeries

# Import new DataFrameSystem architecture (primary API going forward)
from .core.dataframe_system import (
    DataFrameSystem,
    DataFrameSystemFactory,
    CONST_DATAFRAME_BACKEND as CONST_DF_BACKEND,  # New 3-backend enum
)

# Import protocols
from .core.protocols import (
    CastProtocol,
    IntrospectProtocol,
    SelectProtocol,
    JoinProtocol,
    FilterProtocol,
    RowProtocol,
    LazyProtocol,
    DataFrameSystemProtocol,
)

# Import TableBuilder fluent API
from .core.table_builder import (
    TableBuilder,
    table,
    from_polars,
    from_pandas,
    from_pyarrow,
    from_ibis,
    from_dict,
    from_records,
)

# Lazy load DataFrameUtils for backward compatibility
def __getattr__(name: str):
    """Lazy load modules to avoid circular imports."""
    if name == "DataFrameUtils":
        from .core.api.dataframe_utils import DataFrameUtils
        return DataFrameUtils
    if name == "SchemaConfig":
        from .schema_config import SchemaConfig
        return SchemaConfig
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Combine lazy loaded subpackages with essential exports
__all__ = [
    "__version__",
    # High-level API (lazy loaded for now)
    "DataFrameUtils",
    # New DataFrameSystem architecture (primary API)
    "DataFrameSystem",
    "DataFrameSystemFactory",
    # Protocols
    "CastProtocol",
    "IntrospectProtocol",
    "SelectProtocol",
    "JoinProtocol",
    "FilterProtocol",
    "RowProtocol",
    "LazyProtocol",
    "DataFrameSystemProtocol",
    # TableBuilder fluent API
    "TableBuilder",
    "table",
    "from_polars",
    "from_pandas",
    "from_pyarrow",
    "from_ibis",
    "from_dict",
    "from_records",
    # Type aliases
    "SupportedDataFrames",
    "SupportedExpressions",
    "SupportedPythonData",
    "SupportedSeries",
    # Schema (lazy loaded)
    "SchemaConfig",
    # Constants
    "CONST_DATAFRAME_FRAMEWORK",
    "CONST_IBIS_INMEMORY_BACKEND",
    "CONST_EXPRESSION_TYPE",
    "CONST_JOIN_BACKEND_TYPE",
    "CONST_DATAFRAME_BACKEND",
    "CONST_DATAFRAME_TYPE",
    "CONST_DF_BACKEND",  # New 3-backend enum
]
