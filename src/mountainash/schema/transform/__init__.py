# ==================== BACKEND-AGNOSTIC COLUMN TRANSFORMATION ====================
# DataFrame-independent column mapping, casting, and null handling
# Works with pandas, polars, ibis, pyarrow, and narwhals DataFrames

from .cast_schema_factory import (
    CastSchemaFactory,
)
from .base_schema_transform_strategy import (
    BaseCastSchemaStrategy,
    SchemaTransformError,
)

# Backend-specific strategies (for lazy loading)
from .cast_schema_polars import CastSchemaPolars, CastSchemaPolarsLazy
from .cast_schema_pandas import CastSchemaPandas
from .cast_schema_narwhals import CastSchemaNarwhals
from .cast_schema_ibis import CastSchemaIbis
from .cast_schema_pyarrow import CastSchemaPyArrow

# Backward compatibility aliases
SchemaTransformFactory = CastSchemaFactory
BaseSchemaTransformStrategy = BaseCastSchemaStrategy


__all__ = [
    # Factory and base classes
    'CastSchemaFactory',
    'BaseCastSchemaStrategy',
    'SchemaTransformError',

    # Backward compatibility aliases
    'SchemaTransformFactory',
    'BaseSchemaTransformStrategy',

    # Backend-specific strategies (exported for factory loading)
    'CastSchemaPolars',
    'CastSchemaPolarsLazy',
    'CastSchemaPandas',
    'CastSchemaNarwhals',
    'CastSchemaIbis',
    'CastSchemaPyArrow',
]
