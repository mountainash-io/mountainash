"""
Abstract base class for backend-specific column transformation strategies.

Follows the established strategy pattern used throughout mountainash-dataframes.
Integrates with Universal Schema system for type safety and validation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional
import logging

if TYPE_CHECKING:
    from mountainash.dataframes.core.typing import SupportedDataFrames
    from mountainash.schema.config import SchemaConfig, TableSchema

logger = logging.getLogger(__name__)


class SchemaTransformError(Exception):
    """Raised when column transformation fails."""
    pass


class BaseCastSchemaStrategy(ABC):
    """
    Abstract base class for backend-specific column transformation.

    Each backend (pandas, polars, ibis, etc.) implements this interface
    to provide column renaming, casting, null filling, and default values.
    """

    @classmethod
    @abstractmethod
    def _apply(cls,
               df: Any,
               config: 'SchemaConfig') -> Any:
        """
        Apply column transformations to DataFrame.

        Backend-specific implementation.

        Args:
            df: Input DataFrame (specific backend type)
            config: ColumnTransformConfig with transformation specs

        Returns:
            Transformed DataFrame (same backend)

        Raises:
            ColumnTransformError: If transformation fails
        """
        pass

    @classmethod
    def apply(cls,
              df: 'SupportedDataFrames',
              config: 'SchemaConfig',
              validate_input: bool = False,
              validate_output: bool = False) -> 'SupportedDataFrames':
        """
        Public API with error handling and optional schema validation.

        Args:
            df: Input DataFrame
            config: SchemaConfig with transformation specifications
            validate_input: If True, validate input against source_schema
            validate_output: If True, validate output against target_schema

        Returns:
            Transformed DataFrame (same backend as input)

        Raises:
            SchemaTransformError: If transformation fails or validation fails
        """
        try:
            # Pre-transformation validation
            if validate_input and config.source_schema is not None:
                cls._validate_input_schema(df, config)

            # Apply transformation
            result = cls._apply(df, config)

            # Post-transformation validation
            if validate_output:
                cls._validate_output_schema(result, df, config)

            return result

        except Exception as e:
            # Get backend name for error message
            backend_name = type(df).__module__.split('.')[0]
            raise SchemaTransformError(
                f"Failed to apply column transformations to {backend_name} DataFrame: {e}"
            ) from e

    @classmethod
    def _validate_input_schema(
        cls,
        df: 'SupportedDataFrames',
        config: 'SchemaConfig'
    ) -> None:
        """
        Validate input DataFrame against source schema.

        Args:
            df: Input DataFrame
            config: SchemaConfig with source_schema

        Raises:
            SchemaTransformError: If validation fails
        """
        from mountainash.schema.config import from_dataframe, validate_schema_match

        if config.source_schema is None:
            return

        is_valid, errors = validate_schema_match(
            df,
            config.source_schema,
            strict=False  # Allow extra columns
        )

        if not is_valid:
            logger.warning(
                f"Input schema validation issues: {'; '.join(errors)}"
            )

    @classmethod
    def _validate_output_schema(
        cls,
        result_df: 'SupportedDataFrames',
        source_df: 'SupportedDataFrames',
        config: 'SchemaConfig'
    ) -> None:
        """
        Validate output DataFrame against predicted/target schema.

        Args:
            result_df: Output DataFrame
            source_df: Input DataFrame
            config: SchemaConfig

        Raises:
            SchemaTransformError: If validation fails
        """
        from mountainash.schema.config import validate_round_trip

        is_valid, errors = validate_round_trip(result_df, source_df, config)

        if not is_valid:
            raise SchemaTransformError(
                f"Output validation failed: {'; '.join(errors)}"
            )

    @classmethod
    def _check_type_safety(
        cls,
        source_type: str,
        target_type: str,
        column_name: str
    ) -> None:
        """
        Check if type cast is safe and log warnings for unsafe casts.

        Args:
            source_type: Source universal type
            target_type: Target universal type
            column_name: Column being cast

        Logs:
            Warning if cast is potentially unsafe
        """
        from mountainash.schema.config.types import is_safe_cast

        if not is_safe_cast(source_type, target_type):
            logger.warning(
                f"Unsafe type cast for column '{column_name}': "
                f"{source_type} → {target_type}. Data loss may occur."
            )

    @classmethod
    def convert_exception(cls, df: Any, exception: Exception) -> Exception:
        """
        Convert backend-specific exceptions to SchemaTransformError.

        Args:
            df: The DataFrame that caused the error
            exception: The original exception

        Returns:
            SchemaTransformError with helpful message
        """
        backend_name = type(df).__module__.split('.')[0]
        return SchemaTransformError(
            f"Column transformation failed for {backend_name} backend: {exception}"
        )
