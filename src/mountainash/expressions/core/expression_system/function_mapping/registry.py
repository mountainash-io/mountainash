"""Function registry for Substrait-aligned operations.

This module provides a central registry that maps function names to:
1. Substrait extension URIs and function names (for serialization)
2. Backend method names (for compilation)

The registry enables:
- Adding new operations by adding a single FunctionDef
- Looking up Substrait metadata for serialization
- Looking up backend methods for compilation
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, TYPE_CHECKING, get_type_hints

import inspect

from mountainash.core.dtypes.metadata import FixedResultType, PreserveResultType

from mountainash.expressions.core.expression_system.function_keys.enums import (
    SubstraitExtension,
    MountainashExtension,
)

if TYPE_CHECKING:
    from enum import Enum


# class SubstraitExtension(str, Enum):
#     """Standard Substrait extension URIs.

#     These URIs identify the source of function definitions.
#     Standard functions come from the official Substrait extensions.
#     Mountainash-specific functions use a custom extension.
#     """

#     COMPARISON = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_comparison.yaml"
#     BOOLEAN = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_boolean.yaml"
#     ARITHMETIC = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_arithmetic.yaml"
#     STRING = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_string.yaml"
#     DATETIME = "https://github.com/substrait-io/substrait/blob/main/extensions/functions_datetime.yaml"
#     # Mountainash extensions for non-standard operations
#     MOUNTAINASH = "https://mountainash.io/extensions/functions.yaml"



_RESERVED_OPERAND_TYPES = "__operand_types__"


def _expression_parameter_names(method: Callable) -> frozenset[str]:
    signature = inspect.signature(method)
    annotations = get_type_hints(method)
    return frozenset(
        name
        for name, parameter in signature.parameters.items()
        if name != "self"
        and "ExpressionT" in str(annotations.get(name, parameter.annotation))
    )

@dataclass(frozen=True)
class ExpressionFunctionDef:
    """Definition of a function with Substrait mapping and protocol reference.

    Attributes:
        function_key: Internal name used in code (e.g., "eq", "add", "upper")
        substrait_uri: Substrait extension URI
        substrait_name: Function name in Substrait (e.g., "equal", "add")
        backend_method: Method name on ExpressionSystem (e.g., "eq", "add")
        category: Category for organization ("comparison", "boolean", etc.)
        is_extension: True if this is a mountainash-specific extension
        # n_args: Number of arguments (None = variadic)
        options: List of valid option names for this function
        protocol: Protocol class that defines the method signature (for introspection)
        protocol_method_name: Method name on the protocol (may differ from backend_method)
    """

    function_key: Enum
    substrait_uri: str | None
    substrait_name: str | None
    # backend_method: str
    # category: str
    is_extension: bool = False
    # n_args: Optional[int] = None
    options: tuple[str, ...] = field(default_factory=tuple)
    protocol_method: Optional[Callable] = None
    result_type: FixedResultType | PreserveResultType | None = None
    type_arguments: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.result_type is not None and not isinstance(
            self.result_type, (FixedResultType, PreserveResultType)
        ):
            raise TypeError(
                "result_type must be FixedResultType, PreserveResultType, or None"
            )
        if not isinstance(self.type_arguments, tuple):
            raise TypeError("type_arguments must be a tuple of protocol parameter names")
        if len(set(self.type_arguments)) != len(self.type_arguments):
            raise ValueError("type_arguments must not contain duplicates")
        if _RESERVED_OPERAND_TYPES in self.options:
            raise ValueError(
                f"{_RESERVED_OPERAND_TYPES!r} is reserved for compiler operand metadata"
            )

        method = self.protocol_method
        if method is None:
            if self.type_arguments or isinstance(self.result_type, PreserveResultType):
                raise ValueError("metadata rules requiring operands need a protocol method")
            return

        signature = inspect.signature(method)
        if _RESERVED_OPERAND_TYPES in signature.parameters:
            raise ValueError(
                f"{_RESERVED_OPERAND_TYPES!r} is reserved for compiler operand metadata"
            )
        if not self.type_arguments and not isinstance(
            self.result_type, PreserveResultType
        ):
            return


        expression_parameters = _expression_parameter_names(method)
        for argument in self.type_arguments:
            if argument not in signature.parameters:
                raise ValueError(
                    f"type_argument {argument!r} does not name a protocol parameter"
                )
            if argument not in expression_parameters:
                raise ValueError(
                    f"type_argument {argument!r} must name an expression parameter"
                )

        if (
            isinstance(self.result_type, PreserveResultType)
            and self.result_type.argument not in expression_parameters
        ):
            raise ValueError(
                f"result_type argument {self.result_type.argument!r} "
                "must name an expression parameter"
            )

    def get_signature(self) -> Optional[inspect.Signature]:
        """Get the method signature from the protocol for type introspection.

        Returns:
            Method signature, or None if no protocol is defined.
        """
        method = self.protocol_method
        if method is None:
            return None
        return inspect.signature(method)


def _uri_values(holder: type) -> frozenset[str]:
    return frozenset(
        v for k, v in vars(holder).items()
        if not k.startswith("_") and isinstance(v, str)
    )


_SUBSTRAIT_URIS = _uri_values(SubstraitExtension)
_MOUNTAINASH_URIS = _uri_values(MountainashExtension)


def classify_expression_def(d: ExpressionFunctionDef) -> str | None:
    """Return the provenance class of a def, or None if its metadata is invalid.

    Valid states (see spec §4.4):
      - "substrait":  is_extension is False, substrait_uri is a SubstraitExtension
                      value, substrait_name is not None.
      - "extension":  is_extension is True, substrait_uri is a MountainashExtension
                      value, substrait_name is not None.
    """
    if d.substrait_name is None or d.substrait_uri is None:
        return None
    if d.is_extension is False and d.substrait_uri in _SUBSTRAIT_URIS:
        return "substrait"
    if d.is_extension is True and d.substrait_uri in _MOUNTAINASH_URIS:
        return "extension"
    return None


class ExpressionFunctionRegistry:
    """Central registry mapping function names to definitions.

    This singleton registry provides lookup of function definitions
    by name, enabling both compilation and serialization.

    Usage:
        # Register a function
        FunctionRegistry.register(FunctionDef(...))

        # Look up a function
        func_def = FunctionRegistry.get("eq")
        backend_method = FunctionRegistry.get_backend_method("eq")
        substrait_uri = FunctionRegistry.get_substrait_uri("eq")
    """

    _functions: Dict[Enum, ExpressionFunctionDef] = {}
    # _by_category: Dict[str, List[FunctionDef]] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, func: ExpressionFunctionDef) -> None:
        """Register a function definition.

        Args:
            func: Function definition to register
        """
        cls._functions[func.function_key] = func

        # # Index by category for organizational queries
        # if func.category not in cls._by_category:
        #     cls._by_category[func.category] = []
        # cls._by_category[func.category].append(func)

    @classmethod
    def get(cls, function_key: Enum) -> ExpressionFunctionDef:
        """Get a function definition by ENUM key.

        Args:
            function_key: Function ENUM key (e.g., KEY_SCALAR_COMPARISON.EQUAL)

        Returns:
            ExpressionFunctionDef for the function

        Raises:
            KeyError: If function is not registered
        """
        if not cls._initialized:
            cls._init_registry()

        if function_key not in cls._functions:
            raise KeyError(f"Unknown function: {function_key}. Available: {list(cls._functions.keys())}")
        return cls._functions[function_key]

    @classmethod
    def get_substrait_uri(cls, function_key: Enum) -> str | None:
        """Get the Substrait extension URI for a function.

        Args:
            function_key: Function ENUM key

        Returns:
            Substrait extension URI
        """
        return cls.get(function_key).substrait_uri

    @classmethod
    def get_substrait_name(cls, function_key: Enum) -> str | None:
        """Get the Substrait function name.

        Args:
            function_key: Function ENUM key

        Returns:
            Substrait function name
        """
        return cls.get(function_key).substrait_name

    @classmethod
    def get_protocol_method(cls, function_key: Enum) -> Optional[Callable]:
        """Get the protocol method for a function.

        Args:
            function_key: Function ENUM key

        Returns:
            Protocol method callable
        """
        return cls.get(function_key).protocol_method

    # @classmethod
    # def get_by_category(cls, category: str) -> List[FunctionDef]:
    #     """Get all functions in a category.

    #     Args:
    #         category: Category name (e.g., "comparison", "boolean")

    #     Returns:
    #         List of FunctionDefs in that category
    #     """
    #     if not cls._initialized:
    #         cls._init_registry()
    #     return cls._by_category.get(category, [])

    @classmethod
    def list_all(cls) -> List[Enum]:
        """List all registered function enum keys.

        Returns:
            List of function enum keys
        """
        if not cls._initialized:
            cls._init_registry()
        return list(cls._functions.keys())

    @classmethod
    def is_extension(cls, function_key: Enum) -> bool:
        """Check if a function is a mountainash extension.

        Args:
            function_key: Function ENUM key

        Returns:
            True if function is mountainash-specific
        """
        return cls.get(function_key).is_extension

    @classmethod
    def get_method_signature(cls, function_key: Enum) -> Optional[inspect.Signature]:
        """Get the protocol method signature for type introspection.

        Args:
            function_key: Function ENUM key

        Returns:
            Method signature for introspection, or None if no protocol is defined.

        Example:
            >>> sig = FunctionRegistry.get_method_signature(KEY_SCALAR_STRING.CONTAINS)
            >>> for param in sig.parameters.values():
            ...     print(f"{param.name}: {param.annotation}")
            # operand: SupportedExpressions
            # substring: str
        """
        return cls.get(function_key).get_signature()

    # @classmethod
    # def get_protocol(cls, name_or_enum: str | Enum) -> Optional[Type]:
    #     """Get the protocol class for a function.

    #     Args:
    #         name_or_enum: Function name (str) or function ENUM

    #     Returns:
    #         Protocol class, or None if no protocol is defined.
    #     """
    #     return cls.get(name_or_enum).protocol

    @classmethod
    def _init_registry(cls) -> None:
        """Initialize the registry with all function definitions."""
        if cls._initialized:
            return
        from .definitions import register_all_functions
        register_all_functions()
        cls._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing)."""
        cls._functions.clear()
        # cls._by_category.clear()
        cls._initialized = False
