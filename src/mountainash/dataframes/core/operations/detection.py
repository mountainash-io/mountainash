"""
Unified input detection for mountainash-dataframes.

This module provides a single source of truth for detecting:
- What type of input (DataFrame, Expression, Series)
- Which backend it belongs to (Polars, pandas, PyArrow, Ibis, Narwhals)

Uses module/class name inspection to avoid importing backend libraries.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..constants import Backend, InputType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectedInput:
    """
    Result of detecting an input's type and backend.

    Attributes:
        input_type: Category of input (DATAFRAME, EXPRESSION, SERIES)
        backend: Library backend (POLARS, PANDAS, etc.)
        obj: The original object
    """

    input_type: InputType
    backend: Backend
    obj: Any

    def __repr__(self) -> str:
        return f"DetectedInput({self.input_type.name}, {self.backend.name})"


# =============================================================================
# Detection Tables
# =============================================================================

# Exact match: (module, classname) -> (InputType, Backend)
_EXACT_MATCH_TABLE: Dict[Tuple[str, str], Tuple[InputType, Backend]] = {
    # -------------------------------------------------------------------------
    # Polars
    # -------------------------------------------------------------------------
    # DataFrames
    ("polars.dataframe.frame", "DataFrame"): (InputType.DATAFRAME, Backend.POLARS),
    ("polars.lazyframe.frame", "LazyFrame"): (InputType.DATAFRAME, Backend.POLARS),
    ("polars", "DataFrame"): (InputType.DATAFRAME, Backend.POLARS),
    ("polars", "LazyFrame"): (InputType.DATAFRAME, Backend.POLARS),
    # Series
    ("polars.series.series", "Series"): (InputType.SERIES, Backend.POLARS),
    ("polars", "Series"): (InputType.SERIES, Backend.POLARS),
    # Expressions
    ("polars.expr.expr", "Expr"): (InputType.EXPRESSION, Backend.POLARS),
    ("polars", "Expr"): (InputType.EXPRESSION, Backend.POLARS),
    # -------------------------------------------------------------------------
    # pandas
    # -------------------------------------------------------------------------
    ("pandas.core.frame", "DataFrame"): (InputType.DATAFRAME, Backend.PANDAS),
    ("pandas", "DataFrame"): (InputType.DATAFRAME, Backend.PANDAS),
    ("pandas.core.series", "Series"): (InputType.SERIES, Backend.PANDAS),
    ("pandas", "Series"): (InputType.SERIES, Backend.PANDAS),
    # -------------------------------------------------------------------------
    # PyArrow
    # -------------------------------------------------------------------------
    ("pyarrow.lib", "Table"): (InputType.DATAFRAME, Backend.PYARROW),
    ("pyarrow", "Table"): (InputType.DATAFRAME, Backend.PYARROW),
    ("pyarrow.lib", "Array"): (InputType.SERIES, Backend.PYARROW),
    ("pyarrow", "Array"): (InputType.SERIES, Backend.PYARROW),
    ("pyarrow.lib", "ChunkedArray"): (InputType.SERIES, Backend.PYARROW),
    ("pyarrow", "ChunkedArray"): (InputType.SERIES, Backend.PYARROW),
    # -------------------------------------------------------------------------
    # Ibis
    # -------------------------------------------------------------------------
    ("ibis.expr.types.relations", "Table"): (InputType.DATAFRAME, Backend.IBIS),
    ("ibis.expr.types.joins", "Join"): (InputType.DATAFRAME, Backend.IBIS),
    # -------------------------------------------------------------------------
    # Narwhals
    # -------------------------------------------------------------------------
    ("narwhals.dataframe", "DataFrame"): (InputType.DATAFRAME, Backend.NARWHALS),
    ("narwhals", "DataFrame"): (InputType.DATAFRAME, Backend.NARWHALS),
    ("narwhals.dataframe", "LazyFrame"): (InputType.DATAFRAME, Backend.NARWHALS),
    ("narwhals", "LazyFrame"): (InputType.DATAFRAME, Backend.NARWHALS),
    ("narwhals.series", "Series"): (InputType.SERIES, Backend.NARWHALS),
    ("narwhals", "Series"): (InputType.SERIES, Backend.NARWHALS),
    ("narwhals.expr", "Expr"): (InputType.EXPRESSION, Backend.NARWHALS),
    ("narwhals", "Expr"): (InputType.EXPRESSION, Backend.NARWHALS),
}

# Pattern match: regex -> list of (classname, InputType, Backend)
_PATTERN_MATCH_TABLE: Dict[str, List[Tuple[str, InputType, Backend]]] = {
    # Polars patterns (handles internal module reorganizations)
    r"^polars\.": [
        ("DataFrame", InputType.DATAFRAME, Backend.POLARS),
        ("LazyFrame", InputType.DATAFRAME, Backend.POLARS),
        ("Series", InputType.SERIES, Backend.POLARS),
        ("Expr", InputType.EXPRESSION, Backend.POLARS),
    ],
    # pandas patterns
    r"^pandas\.": [
        ("DataFrame", InputType.DATAFRAME, Backend.PANDAS),
        ("Series", InputType.SERIES, Backend.PANDAS),
    ],
    # PyArrow patterns - Array has many subtypes (BooleanArray, Int64Array, etc.)
    r"^pyarrow\.": [
        ("Table", InputType.DATAFRAME, Backend.PYARROW),
        ("Array", InputType.SERIES, Backend.PYARROW),
        ("ChunkedArray", InputType.SERIES, Backend.PYARROW),
        # Array subtypes (all end with "Array")
        ("BooleanArray", InputType.SERIES, Backend.PYARROW),
        ("Int64Array", InputType.SERIES, Backend.PYARROW),
        ("Int32Array", InputType.SERIES, Backend.PYARROW),
        ("FloatArray", InputType.SERIES, Backend.PYARROW),
        ("DoubleArray", InputType.SERIES, Backend.PYARROW),
        ("StringArray", InputType.SERIES, Backend.PYARROW),
        ("LargeStringArray", InputType.SERIES, Backend.PYARROW),
    ],
    # Ibis patterns
    r"^ibis\.": [
        ("Table", InputType.DATAFRAME, Backend.IBIS),
        ("Join", InputType.DATAFRAME, Backend.IBIS),
        # Ibis expressions have various class names
    ],
    # Narwhals patterns
    r"^narwhals\.": [
        ("DataFrame", InputType.DATAFRAME, Backend.NARWHALS),
        ("LazyFrame", InputType.DATAFRAME, Backend.NARWHALS),
        ("Series", InputType.SERIES, Backend.NARWHALS),
        ("Expr", InputType.EXPRESSION, Backend.NARWHALS),
    ],
}

# Ibis expression class name patterns (Ibis has many expression types)
_IBIS_EXPRESSION_PATTERNS = {"Column", "Scalar", "Expr", "Value", "Boolean", "Deferred"}

# Runtime cache for pattern-matched types
_runtime_cache: Dict[Tuple[str, str], Tuple[InputType, Backend]] = {}


# =============================================================================
# InputDetector
# =============================================================================


class InputDetector:
    """
    Single source of truth for input type and backend detection.

    Uses a three-tier detection approach:
    1. Exact match (fastest) - O(1) lookup
    2. Pattern match (fallback) - regex matching with caching
    3. Attribute inspection (last resort) - for mountainash expressions

    Usage:
        detected = InputDetector.detect(obj)
        if detected.input_type == InputType.EXPRESSION:
            # Handle expression
        if detected.backend == Backend.POLARS:
            # Polars-specific handling
    """

    @classmethod
    def detect(cls, obj: Any) -> DetectedInput:
        """
        Detect the input type and backend of an object.

        Args:
            obj: Any input object (DataFrame, Expression, Series)

        Returns:
            DetectedInput with input_type, backend, and original obj

        Raises:
            ValueError: If object type is not recognized
        """
        obj_type = type(obj)
        module = obj_type.__module__
        name = obj_type.__name__
        type_key = (module, name)

        # Tier 1: Exact match (fast path)
        if type_key in _EXACT_MATCH_TABLE:
            input_type, backend = _EXACT_MATCH_TABLE[type_key]
            logger.debug(f"Exact match: {type_key} -> {input_type.name}, {backend.name}")
            return DetectedInput(input_type, backend, obj)

        # Check runtime cache (pattern matches get cached here)
        if type_key in _runtime_cache:
            input_type, backend = _runtime_cache[type_key]
            logger.debug(f"Cache hit: {type_key} -> {input_type.name}, {backend.name}")
            return DetectedInput(input_type, backend, obj)

        # Tier 2: Pattern match
        result = cls._match_by_pattern(module, name)
        if result is not None:
            input_type, backend = result
            _runtime_cache[type_key] = result
            logger.info(f"Pattern match: {type_key} -> {input_type.name}, {backend.name}")
            return DetectedInput(input_type, backend, obj)

        # Tier 3: Special cases (Ibis expressions, mountainash)
        result = cls._detect_special_cases(obj, module, name)
        if result is not None:
            input_type, backend = result
            _runtime_cache[type_key] = result
            logger.info(f"Special case: {type_key} -> {input_type.name}, {backend.name}")
            return DetectedInput(input_type, backend, obj)

        # Not recognized
        logger.warning(
            f"Unrecognized input type: {module}.{name}\n"
            f"  MRO: {[c.__module__ + '.' + c.__name__ for c in obj_type.__mro__[:5]]}"
        )
        raise ValueError(f"Unrecognized input type: {module}.{name}")

    @classmethod
    def detect_safe(cls, obj: Any) -> Optional[DetectedInput]:
        """
        Detect input type and backend, returning None if not recognized.

        Same as detect() but returns None instead of raising ValueError.

        Args:
            obj: Any input object

        Returns:
            DetectedInput or None if not recognized
        """
        try:
            return cls.detect(obj)
        except ValueError:
            return None

    @classmethod
    def is_dataframe(cls, obj: Any) -> bool:
        """Check if object is a supported DataFrame type."""
        detected = cls.detect_safe(obj)
        return detected is not None and detected.input_type == InputType.DATAFRAME

    @classmethod
    def is_expression(cls, obj: Any) -> bool:
        """Check if object is a supported expression type."""
        detected = cls.detect_safe(obj)
        return detected is not None and detected.input_type == InputType.EXPRESSION

    @classmethod
    def is_series(cls, obj: Any) -> bool:
        """Check if object is a supported series type."""
        detected = cls.detect_safe(obj)
        return detected is not None and detected.input_type == InputType.SERIES

    @classmethod
    def get_backend(cls, obj: Any) -> Backend:
        """
        Get the backend of an object.

        Args:
            obj: Any supported input object

        Returns:
            Backend enum value

        Raises:
            ValueError: If object type is not recognized
        """
        return cls.detect(obj).backend

    @classmethod
    def get_input_type(cls, obj: Any) -> InputType:
        """
        Get the input type category of an object.

        Args:
            obj: Any supported input object

        Returns:
            InputType enum value

        Raises:
            ValueError: If object type is not recognized
        """
        return cls.detect(obj).input_type

    # =========================================================================
    # Internal Detection Methods
    # =========================================================================

    @classmethod
    def _match_by_pattern(
        cls, module: str, name: str
    ) -> Optional[Tuple[InputType, Backend]]:
        """Match module and classname against pattern table."""
        for pattern, mappings in _PATTERN_MATCH_TABLE.items():
            if re.match(pattern, module):
                for class_name, input_type, backend in mappings:
                    if name == class_name:
                        return (input_type, backend)
        return None

    @classmethod
    def _detect_special_cases(
        cls, obj: Any, module: str, name: str
    ) -> Optional[Tuple[InputType, Backend]]:
        """Handle special detection cases."""
        # Ibis expressions have many class names
        if module.startswith("ibis"):
            for pattern in _IBIS_EXPRESSION_PATTERNS:
                if pattern in name:
                    return (InputType.EXPRESSION, Backend.IBIS)

        # PyArrow has many array subtypes (BooleanArray, Int64Array, etc.)
        # Check if the class name ends with "Array" and module is pyarrow
        if module.startswith("pyarrow") and name.endswith("Array"):
            return (InputType.SERIES, Backend.PYARROW)

        # Mountainash expressions (checked by attribute, not module)
        if cls._is_mountainash_expression(obj):
            # Return as expression but with a special marker
            # The caller should compile it to native first
            # For now, we don't have a Backend.MOUNTAINASH so we raise
            # This is intentional - mountainash expressions should be
            # compiled before reaching the resolver
            pass

        return None

    @classmethod
    def _is_mountainash_expression(cls, obj: Any) -> bool:
        """Check if object is a mountainash expression."""
        obj_type = type(obj)
        module = obj_type.__module__
        name = obj_type.__name__

        # Check module prefix
        if module.startswith(("mountainash_expressions", "mountainash.expressions")):
            return True

        # Check class name patterns
        if name in ("BooleanExpressionAPI", "BaseExpressionAPI") or name.endswith(
            "ExpressionNode"
        ):
            return True

        # Check for expression API pattern
        if hasattr(obj, "_node") and hasattr(obj, "compile"):
            return True

        return False

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the runtime detection cache (for testing)."""
        _runtime_cache.clear()
        logger.debug("InputDetector cache cleared")


__all__ = [
    "InputDetector",
    "DetectedInput",
]
