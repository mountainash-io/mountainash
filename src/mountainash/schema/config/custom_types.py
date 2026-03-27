"""
Custom Type Conversion System

Provides a registry-based system for registering and applying custom type converters
that work at the edges (Python layer) for semantic transformations that cannot be
expressed as simple native type conversions.

Architecture (Dual-Mode):
- Python converters: Applied at EDGES (Python layer) - row-by-row, semantic logic
- Narwhals converters: Applied in CENTER (DataFrame layer) - vectorized, FAST!
- Native conversions: Applied in CENTER (DataFrame layer) - structural types
- Hybrid strategy for optimal performance

This is Layer 2 of the two-layer type system:
- Layer 1: Structural Types (types.py) - native DataFrame operations
- Layer 2: Semantic Converters (this module) - custom Python + Narwhals logic

Examples of custom types:
- safe_float: NaN → None handling (Python + Narwhals)
- xml_string: XML entity escaping (Python + Narwhals)
- rich_boolean: Parse "yes"/"no"/"1"/"0" (Python + Narwhals)
- email: Validation and normalization
- phone: Format to E.164
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Protocol
from dataclasses import dataclass
from enum import StrEnum

if TYPE_CHECKING:
    from .types import UniversalType
    import narwhals as nw

logger = logging.getLogger(__name__)


# ============================================================================
# Type Converter Protocols
# ============================================================================

class TypeConverter(Protocol):
    """
    Protocol for custom type converter functions (Python-based, row-by-row).

    A type converter is a callable that takes a value and returns the converted value.
    It should handle None values appropriately and raise ValueError on conversion errors.
    """
    def __call__(self, value: Any, *, field_name: Optional[str] = None) -> Any:
        """
        Convert a value to the target type.

        Args:
            value: Value to convert
            field_name: Optional field name for error messages

        Returns:
            Converted value

        Raises:
            ValueError: If conversion fails
        """
        ...


class NarwhalsConverter(Protocol):
    """
    Protocol for Narwhals-based vectorized converter functions.

    A Narwhals converter is a callable that takes a column name and returns
    a function that generates a Narwhals expression for that column.

    This enables vectorized conversion for significant performance improvements.
    """
    def __call__(self, column_name: str) -> Callable[[Any], 'nw.Expr']:
        """
        Build Narwhals expression for converting a column.

        Args:
            column_name: Name of the column to convert

        Returns:
            Function that takes a DataFrame and returns a Narwhals expression

        Example:
            >>> def safe_float_narwhals(column_name: str):
            ...     def _expr(df):
            ...         import narwhals as nw
            ...         return nw.col(column_name).cast(nw.Float64).fill_nan(None)
            ...     return _expr
        """
        ...


# ============================================================================
# Type Converter Specification
# ============================================================================

@dataclass
class TypeConverterSpec:
    """
    Specification for a registered custom type converter with dual-mode support.

    Attributes:
        name: Unique name for this converter (e.g., "safe_float")
        python_converter: Python function for row-by-row conversion (optional)
        narwhals_converter: Narwhals expression builder for vectorization (optional)
        target_universal_type: Universal type this converts to (e.g., UniversalType.NUMBER)
        description: Human-readable description of what this converter does
        direction: Whether converter applies to ingress, egress, or both

    Note:
        At least one of python_converter or narwhals_converter must be provided.
        Priority order for ingress:
        1. narwhals_converter (if available) - vectorized, FAST!
        2. python_converter (fallback) - row-by-row

        For egress, only python_converter is used (operating on extracted data).
    """
    name: str
    target_universal_type: str  # Universal type string
    python_converter: Optional[TypeConverter] = None
    narwhals_converter: Optional[NarwhalsConverter] = None
    description: str = ""
    direction: str = "both"  # "ingress", "egress", or "both"

    # Backward compatibility: accept 'converter' parameter
    converter: Optional[TypeConverter] = None

    def __post_init__(self):
        """Validate spec and handle backward compatibility."""
        # Backward compatibility: if converter provided, use as python_converter
        if self.converter is not None and self.python_converter is None:
            self.python_converter = self.converter

        # Validate at least one implementation exists
        if self.python_converter is None and self.narwhals_converter is None:
            raise ValueError(
                f"Custom type '{self.name}' must have at least one implementation: "
                "python_converter or narwhals_converter"
            )

        # Validate direction
        if self.direction not in ("ingress", "egress", "both"):
            raise ValueError(
                f"Invalid direction '{self.direction}'. "
                f"Must be 'ingress', 'egress', or 'both'."
            )

    @property
    def is_vectorized(self) -> bool:
        """Check if Narwhals vectorized implementation exists."""
        return self.narwhals_converter is not None

    def has_python_fallback(self) -> bool:
        """Check if Python fallback is available."""
        return self.python_converter is not None


# ============================================================================
# Custom Type Registry
# ============================================================================

class CustomTypeRegistry:
    """
    Global registry for custom type converters.

    This registry stores custom type converters that can be used throughout
    the package for semantic transformations that cannot be expressed as
    simple native type conversions.

    Custom converters should be applied at the EDGES (Python layer):
    - INGRESS: Before DataFrame creation
    - EGRESS: After DataFrame extraction

    Native conversions should be applied in the CENTER (DataFrame layer):
    - Use vectorized DataFrame operations for optimal performance

    Example:
        >>> def convert_safe_float(value, *, field_name=None):
        ...     if value is None or (isinstance(value, float) and np.isnan(value)):
        ...         return None
        ...     return float(value)
        ...
        >>> CustomTypeRegistry.register(
        ...     name="safe_float",
        ...     converter=convert_safe_float,
        ...     target_universal_type="number",
        ...     description="Float with NaN → None handling"
        ... )
    """

    # Class-level storage for registered converters
    _converters: Dict[str, TypeConverterSpec] = {}

    @classmethod
    def register(
        cls,
        name: str,
        target_universal_type: str,
        python_converter: Optional[TypeConverter] = None,
        narwhals_converter: Optional[NarwhalsConverter] = None,
        description: str = "",
        direction: str = "both",
        # Backward compatibility
        converter: Optional[TypeConverter] = None
    ) -> None:
        """
        Register a custom type converter with optional dual-mode support.

        Args:
            name: Unique name for this converter (e.g., "safe_float")
            target_universal_type: Universal type this converts to (e.g., "number")
            python_converter: Python function for row-by-row conversion (optional)
            narwhals_converter: Narwhals expression builder for vectorization (optional)
            description: Human-readable description
            direction: Whether converter applies to ingress, egress, or both
            converter: (Deprecated) Alias for python_converter for backward compatibility

        Raises:
            ValueError: If converter with this name already exists, or if no implementation provided

        Note:
            At least one of python_converter or narwhals_converter must be provided.
            If both provided:
            - Narwhals used for ingress (vectorized, FAST!)
            - Python used for egress (extracted data)

        Examples:
            # Python-only (backward compatible):
            >>> CustomTypeRegistry.register(
            ...     name="email",
            ...     target_universal_type="string",
            ...     python_converter=validate_email,
            ...     description="Email validation"
            ... )

            # Dual-mode (Python + Narwhals):
            >>> CustomTypeRegistry.register(
            ...     name="safe_float",
            ...     target_universal_type="number",
            ...     python_converter=safe_float_python,
            ...     narwhals_converter=safe_float_narwhals,
            ...     description="NaN-safe float (vectorized!)"
            ... )

            # Narwhals-only (advanced):
            >>> CustomTypeRegistry.register(
            ...     name="complex_transform",
            ...     target_universal_type="string",
            ...     narwhals_converter=complex_narwhals_expr,
            ...     description="Complex vectorized transform"
            ... )
        """
        if name in cls._converters:
            raise ValueError(
                f"Converter '{name}' is already registered. "
                f"Use unregister() first to replace it."
            )

        # Backward compatibility: use converter param as python_converter
        if converter is not None and python_converter is None:
            python_converter = converter

        spec = TypeConverterSpec(
            name=name,
            target_universal_type=target_universal_type,
            python_converter=python_converter,
            narwhals_converter=narwhals_converter,
            description=description,
            direction=direction
        )

        cls._converters[name] = spec

        vectorized_info = " (vectorized)" if spec.is_vectorized else ""
        logger.info(
            f"Registered custom type converter: '{name}' → {target_universal_type}{vectorized_info}"
        )

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a custom type converter.

        Args:
            name: Name of converter to unregister

        Returns:
            True if converter was found and removed, False otherwise
        """
        if name in cls._converters:
            del cls._converters[name]
            logger.info(f"Unregistered custom type converter: '{name}'")
            return True
        return False

    @classmethod
    def has_converter(cls, name: str) -> bool:
        """
        Check if a converter is registered.

        Args:
            name: Converter name to check

        Returns:
            True if converter exists, False otherwise
        """
        return name in cls._converters

    @classmethod
    def get_spec(cls, name: str) -> Optional[TypeConverterSpec]:
        """
        Get specification for a registered converter.

        Args:
            name: Converter name

        Returns:
            TypeConverterSpec if found, None otherwise
        """
        return cls._converters.get(name)

    @classmethod
    def convert(
        cls,
        value: Any,
        converter_name: str,
        field_name: Optional[str] = None,
        raise_on_error: bool = True
    ) -> Any:
        """
        Apply a registered converter to a value.

        Args:
            value: Value to convert
            converter_name: Name of registered converter to use
            field_name: Optional field name for error messages
            raise_on_error: If True, raise on conversion errors. If False, return value unchanged.

        Returns:
            Converted value

        Raises:
            ValueError: If converter not found or conversion fails (when raise_on_error=True)
        """
        spec = cls.get_spec(converter_name)
        if spec is None:
            if raise_on_error:
                raise ValueError(f"No converter registered for type '{converter_name}'")
            else:
                logger.warning(f"No converter registered for type '{converter_name}', returning value unchanged")
                return value

        # Use python_converter (for backward compatibility, try spec.converter first)
        python_conv = spec.python_converter or spec.converter
        if python_conv is None:
            if raise_on_error:
                raise ValueError(
                    f"Converter '{converter_name}' has no Python implementation. "
                    "It requires Narwhals vectorized evaluation."
                )
            else:
                logger.warning(
                    f"Converter '{converter_name}' has no Python implementation. "
                    "Returning value unchanged."
                )
                return value

        try:
            return python_conv(value, field_name=field_name)
        except Exception as e:
            if raise_on_error:
                field_info = f" in field '{field_name}'" if field_name else ""
                raise ValueError(
                    f"Conversion failed for '{converter_name}'{field_info}: {e}"
                ) from e
            else:
                field_info = f" in field '{field_name}'" if field_name else ""
                logger.warning(
                    f"Conversion failed for '{converter_name}'{field_info}: {e}. "
                    f"Returning value unchanged."
                )
                return value

    @classmethod
    def is_vectorized(cls, converter_name: str) -> bool:
        """
        Check if custom type has Narwhals vectorized implementation.

        Args:
            converter_name: Name of converter to check

        Returns:
            True if Narwhals converter exists, False otherwise

        Example:
            >>> CustomTypeRegistry.is_vectorized("safe_float")
            True  # Has narwhals_converter
            >>> CustomTypeRegistry.is_vectorized("email")
            False  # Python-only
        """
        spec = cls.get_spec(converter_name)
        if spec is None:
            return False
        return spec.is_vectorized

    @classmethod
    def get_narwhals_converter(cls, converter_name: str) -> Optional[NarwhalsConverter]:
        """
        Get Narwhals converter for a custom type.

        Args:
            converter_name: Name of converter

        Returns:
            Narwhals converter function if available, None otherwise

        Example:
            >>> conv = CustomTypeRegistry.get_narwhals_converter("safe_float")
            >>> if conv is not None:
            ...     expr_func = conv("amount")  # Get expression builder
            ...     expr = expr_func(df)  # Generate Narwhals expression
        """
        spec = cls.get_spec(converter_name)
        if spec is None:
            return None
        return spec.narwhals_converter

    @classmethod
    def is_native_type(cls, type_name: str) -> bool:
        """
        Check if type is native (not custom).

        Native types should be handled by DataFrame operations (vectorized, FAST!).
        Custom types should be handled at edges (Python layer).

        This is a KEY METHOD for the hybrid strategy:
        - Returns True → Apply in DataFrame (native operations, 12x faster!)
        - Returns False → Apply at edges (custom logic, necessary for semantics)

        Args:
            type_name: Type name to check

        Returns:
            True if type is native (should use DataFrame operations)
            False if type is custom (should use edge conversion)

        Example:
            >>> CustomTypeRegistry.is_native_type("integer")  # Native
            True
            >>> CustomTypeRegistry.is_native_type("safe_float")  # Custom
            False
        """
        from .types import UniversalType

        # Check if it's a standard universal type (native)
        try:
            # Try to check if it's in UniversalType enum
            if type_name in UniversalType.__members__.values():
                return True
        except Exception:
            pass

        # Check if it's a custom type
        if cls.has_converter(type_name):
            return False

        # Unknown type - assume native to be safe
        # (let DataFrame operations handle it)
        return True

    @classmethod
    def list_converters(cls) -> Dict[str, str]:
        """
        List all registered converters.

        Returns:
            Dict mapping converter names to their descriptions
        """
        return {
            name: spec.description
            for name, spec in cls._converters.items()
        }

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered converters.

        Primarily for testing purposes.
        """
        cls._converters.clear()
        logger.info("Cleared all custom type converters")


# ============================================================================
# Standard Custom Type Converters
# ============================================================================

def _convert_safe_float(value: Any, *, field_name: Optional[str] = None) -> Optional[float]:
    """
    Convert value to float with NaN → None handling.

    Handles:
    - None → None
    - NaN → None
    - Valid numbers → float

    Args:
        value: Value to convert
        field_name: Optional field name for error messages

    Returns:
        Float value or None

    Raises:
        ValueError: If conversion fails
    """
    if value is None:
        return None

    # Handle NaN
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return None

    # Convert to float
    try:
        return float(value)
    except (ValueError, TypeError) as e:
        field_info = f" in field '{field_name}'" if field_name else ""
        raise ValueError(f"Cannot convert '{value}' to float{field_info}") from e


def _convert_safe_int(value: Any, *, field_name: Optional[str] = None) -> Optional[int]:
    """
    Convert value to integer with None handling.

    Handles:
    - None → None
    - NaN → None
    - Valid numbers → int (truncates floats)

    Args:
        value: Value to convert
        field_name: Optional field name for error messages

    Returns:
        Integer value or None

    Raises:
        ValueError: If conversion fails
    """
    if value is None:
        return None

    # Handle NaN
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return None

    # Convert to int
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        field_info = f" in field '{field_name}'" if field_name else ""
        raise ValueError(f"Cannot convert '{value}' to integer{field_info}") from e


def _convert_xml_string(value: Any, *, field_name: Optional[str] = None) -> Optional[str]:
    """
    Convert value to string with XML entity escaping.

    Handles:
    - None → None
    - Escapes: &, <, >, ", '

    Args:
        value: Value to convert
        field_name: Optional field name for error messages

    Returns:
        XML-escaped string or None
    """
    if value is None:
        return None

    # Convert to string
    str_value = str(value)

    # Escape XML entities
    str_value = str_value.replace("&", "&amp;")
    str_value = str_value.replace("<", "&lt;")
    str_value = str_value.replace(">", "&gt;")
    str_value = str_value.replace('"', "&quot;")
    str_value = str_value.replace("'", "&apos;")

    return str_value


def _convert_rich_boolean(value: Any, *, field_name: Optional[str] = None) -> Optional[bool]:
    """
    Convert value to boolean with rich parsing.

    Handles:
    - None → None
    - True/False → bool
    - "yes"/"no" (case-insensitive) → bool
    - "1"/"0" → bool
    - 1/0 → bool
    - "true"/"false" (case-insensitive) → bool

    Args:
        value: Value to convert
        field_name: Optional field name for error messages

    Returns:
        Boolean value or None

    Raises:
        ValueError: If conversion fails
    """
    if value is None:
        return None

    # Already a boolean
    if isinstance(value, bool):
        return value

    # Numeric values
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        elif value == 0:
            return False
        else:
            field_info = f" in field '{field_name}'" if field_name else ""
            raise ValueError(f"Cannot convert numeric '{value}' to boolean{field_info} (expected 0 or 1)")

    # String values
    if isinstance(value, str):
        value_lower = value.lower().strip()

        if value_lower in ("yes", "true", "1"):
            return True
        elif value_lower in ("no", "false", "0"):
            return False
        else:
            field_info = f" in field '{field_name}'" if field_name else ""
            raise ValueError(
                f"Cannot convert string '{value}' to boolean{field_info} "
                f"(expected yes/no, true/false, or 1/0)"
            )

    # Unsupported type
    field_info = f" in field '{field_name}'" if field_name else ""
    raise ValueError(
        f"Cannot convert {type(value).__name__} value '{value}' to boolean{field_info}"
    )


# ============================================================================
# Standard Custom Type Converters - Narwhals (Vectorized)
# ============================================================================

def _convert_safe_float_narwhals(column_name: str) -> Callable:
    """
    Narwhals vectorized implementation for safe_float conversion.

    Converts column to float with NaN/Inf → None handling (vectorized!).

    Args:
        column_name: Name of the column to convert

    Returns:
        Function that takes a DataFrame and returns a Narwhals expression

    Example:
        >>> expr_func = _convert_safe_float_narwhals("amount")
        >>> import polars as pl
        >>> df = pl.DataFrame({"amount": ["42.5", "NaN", "inf"]})
        >>> expr = expr_func(df)  # Returns Narwhals expression
    """
    def _safe_float_expr(df: Any) -> 'nw.Expr':
        """Generate Narwhals expression for safe_float conversion."""
        from mountainash.dataframes.runtime_imports import import_narwhals

        nw = import_narwhals()
        if nw is None:
            raise ImportError("narwhals is required for vectorized custom type conversion")

        col = nw.col(column_name)

        # Cast to float
        float_col = col.cast(nw.Float64)

        # Replace NaN with None
        cleaned = float_col.fill_nan(None)

        # Replace inf/-inf with None using is_finite()
        # Note: is_finite() returns False for inf/-inf AND None values
        # So we use a negated condition: replace non-finite values with None
        result = nw.when(~cleaned.is_finite()).then(None).otherwise(cleaned)

        return result

    return _safe_float_expr


def _convert_safe_int_narwhals(column_name: str) -> Callable:
    """
    Narwhals vectorized implementation for safe_int conversion.

    Converts column to integer with NaN → None handling (vectorized!).

    Args:
        column_name: Name of the column to convert

    Returns:
        Function that takes a DataFrame and returns a Narwhals expression
    """
    def _safe_int_expr(df: Any) -> 'nw.Expr':
        """Generate Narwhals expression for safe_int conversion."""
        from mountainash.dataframes.runtime_imports import import_narwhals

        nw = import_narwhals()
        if nw is None:
            raise ImportError("narwhals is required for vectorized custom type conversion")

        col = nw.col(column_name)

        # Strategy: cast to float first, check for NaN/inf, then cast to int
        float_col = col.cast(nw.Float64)

        # Replace NaN with None
        cleaned = float_col.fill_nan(None)

        # Replace inf/-inf with None using is_finite()
        # Note: is_finite() returns False for inf/-inf AND None values
        cleaned = nw.when(~cleaned.is_finite()).then(None).otherwise(cleaned)

        # Cast to int (None values preserved)
        result = cleaned.cast(nw.Int64)

        return result

    return _safe_int_expr


def _convert_xml_string_narwhals(column_name: str) -> Callable:
    """
    Narwhals vectorized implementation for xml_string conversion.

    Escapes XML entities in string column (vectorized!).

    Args:
        column_name: Name of the column to convert

    Returns:
        Function that takes a DataFrame and returns a Narwhals expression
    """
    def _xml_string_expr(df: Any) -> 'nw.Expr':
        """Generate Narwhals expression for XML entity escaping."""
        from mountainash.dataframes.runtime_imports import import_narwhals

        nw = import_narwhals()
        if nw is None:
            raise ImportError("narwhals is required for vectorized custom type conversion")

        col = nw.col(column_name)

        # Cast to string first
        str_col = col.cast(nw.String)

        # Chain of string replacements (all vectorized!)
        # Order matters: & must be first to avoid double-escaping
        result = (
            str_col
            .str.replace_all("&", "&amp;")
            .str.replace_all("<", "&lt;")
            .str.replace_all(">", "&gt;")
            .str.replace_all('"', "&quot;")
            .str.replace_all("'", "&apos;")
        )

        return result

    return _xml_string_expr


def _convert_rich_boolean_narwhals(column_name: str) -> Callable:
    """
    Narwhals vectorized implementation for rich_boolean conversion.

    Parses yes/no, true/false, 1/0 to boolean (vectorized!).

    Args:
        column_name: Name of the column to convert

    Returns:
        Function that takes a DataFrame and returns a Narwhals expression
    """
    def _rich_boolean_expr(df: Any) -> 'nw.Expr':
        """Generate Narwhals expression for rich boolean parsing."""
        from mountainash.dataframes.runtime_imports import import_narwhals

        nw = import_narwhals()
        if nw is None:
            raise ImportError("narwhals is required for vectorized custom type conversion")

        col = nw.col(column_name)

        # Convert to lowercase string for comparison
        str_col = col.cast(nw.String).str.to_lowercase()

        # Nested conditionals using when/then/otherwise
        # Use nested pattern: when(A).then(X).otherwise(when(B).then(Y).otherwise(Z))
        result = (
            nw.when(str_col.is_in(["yes", "y", "true", "t", "1"]))
            .then(True)
            .otherwise(
                nw.when(str_col.is_in(["no", "n", "false", "f", "0"]))
                .then(False)
                .otherwise(None)  # Invalid values → None
            )
        )

        return result

    return _rich_boolean_expr


# ============================================================================
# Auto-Register Standard Converters
# ============================================================================

def _register_standard_converters() -> None:
    """
    Register standard custom type converters with dual-mode support.

    This is called automatically on module import to make standard
    converters available by default.

    All standard converters are registered with both Python and Narwhals
    implementations for optimal performance.
    """
    from .types import UniversalType

    # Only register if not already registered (allows for re-imports)
    if not CustomTypeRegistry.has_converter("safe_float"):
        CustomTypeRegistry.register(
            name="safe_float",
            target_universal_type=UniversalType.NUMBER,
            python_converter=_convert_safe_float,
            narwhals_converter=_convert_safe_float_narwhals,
            description="Float with NaN/Inf → None handling (VECTORIZED)"
        )

    if not CustomTypeRegistry.has_converter("safe_int"):
        CustomTypeRegistry.register(
            name="safe_int",
            target_universal_type=UniversalType.INTEGER,
            python_converter=_convert_safe_int,
            narwhals_converter=_convert_safe_int_narwhals,
            description="Integer with NaN → None handling (VECTORIZED)"
        )

    if not CustomTypeRegistry.has_converter("xml_string"):
        CustomTypeRegistry.register(
            name="xml_string",
            target_universal_type=UniversalType.STRING,
            python_converter=_convert_xml_string,
            narwhals_converter=_convert_xml_string_narwhals,
            description="String with XML entity escaping (&, <, >, \", ') (VECTORIZED)"
        )

    if not CustomTypeRegistry.has_converter("rich_boolean"):
        CustomTypeRegistry.register(
            name="rich_boolean",
            target_universal_type=UniversalType.BOOLEAN,
            python_converter=_convert_rich_boolean,
            narwhals_converter=_convert_rich_boolean_narwhals,
            description="Boolean with rich parsing (yes/no, true/false, 1/0) (VECTORIZED)"
        )


# Auto-register standard converters on module import
_register_standard_converters()


__all__ = [
    # Protocols
    "TypeConverter",
    "NarwhalsConverter",

    # Dataclass
    "TypeConverterSpec",

    # Registry
    "CustomTypeRegistry",

    # Standard converters (functions are internal, access via registry)
]
