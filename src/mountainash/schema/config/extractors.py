"""DEPRECATED: Use mountainash.typespec.extraction instead.

Re-exports with old names for backward compatibility with pydata.
"""
from mountainash.typespec.extraction import (  # noqa: F401
    extract_from_dataframe as from_dataframe,
    extract_from_dataclass as from_dataclass,
    extract_from_pydantic as from_pydantic,
    extract_from_dataframe as extract_schema_from_dataframe,
    extract_schema_from_dataclass,
    extract_schema_from_pydantic,
    _DATACLASS_SCHEMA_CACHE,  # noqa: F401
    _PYDANTIC_SCHEMA_CACHE,  # noqa: F401
)

# build_schema_config_with_fuzzy_matching was not moved to typespec;
# keep a local implementation that delegates to SchemaConfig.from_schemas
def build_schema_config_with_fuzzy_matching(  # noqa: F401
    source_schema,
    target_schema,
    fuzzy_match_threshold: float = 0.6,
    strict: bool = False,
):
    """
    Build SchemaConfig from source and target schemas with fuzzy matching.

    DEPRECATED: This function wraps SchemaConfig.from_schemas for backward compatibility.
    """
    from mountainash.schema.config.schema_config import SchemaConfig

    config = SchemaConfig.from_schemas(
        source_schema=source_schema,
        target_schema=target_schema,
        fuzzy_match_threshold=fuzzy_match_threshold,
        auto_cast=True,
        keep_unmapped_source=False,
    )
    config.strict = strict
    return config
