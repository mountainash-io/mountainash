"""Expression visitor factory for automatic backend and logic type detection."""

from __future__ import annotations

from typing import Any, Dict, Type
from ..constants import CONST_VISITOR_BACKENDS, CONST_LOGIC_TYPES
from ..expression_system import ExpressionSystem
from .expression_visitor import ExpressionVisitor


class ExpressionVisitorFactory:
    """
    Factory for creating appropriate expression visitors based on backend and logic type.

    This factory automatically detects the DataFrame/Table type and creates
    the appropriate visitor (Boolean or Ternary) for that backend.
    """

    # Registry: backend -> logic_type -> visitor_class
    _visitors_registry: Dict[CONST_VISITOR_BACKENDS, Dict[CONST_LOGIC_TYPES, Type[ExpressionVisitor]]] = {}

    # Registry: backend -> expression_system_class
    _expression_systems_registry: Dict[CONST_VISITOR_BACKENDS, Type[ExpressionSystem]] = {}

    @classmethod
    def register(
        cls,
        backend: CONST_VISITOR_BACKENDS,
        logic_type: CONST_LOGIC_TYPES,
        visitor_class: Type[ExpressionVisitor]
    ) -> None:
        """
        Register a visitor class for a specific backend and logic type.

        Args:
            backend: The backend framework (PANDAS, POLARS, IBIS, etc.)
            logic_type: The logic system (BOOLEAN, TERNARY, FUZZY)
            visitor_class: The visitor class to instantiate
        """
        if backend not in cls._visitors_registry:
            cls._visitors_registry[backend] = {}
        cls._visitors_registry[backend][logic_type] = visitor_class

    @classmethod
    def register_expression_system(
        cls,
        backend: CONST_VISITOR_BACKENDS,
        expression_system_class: Type[ExpressionSystem]
    ) -> None:
        """
        Register an ExpressionSystem class for a specific backend.

        Args:
            backend: The backend framework (PANDAS, POLARS, IBIS, etc.)
            expression_system_class: The ExpressionSystem class to instantiate
        """
        cls._expression_systems_registry[backend] = expression_system_class

    @classmethod
    def get_visitor_for_node(
        cls,
        node: Any,
        expression_system: ExpressionSystem,
        logic_type: CONST_LOGIC_TYPES = CONST_LOGIC_TYPES.BOOLEAN
    ) -> ExpressionVisitor:
        """
        Get appropriate visitor for a specific node type.

        This enables self-organising dispatch where each visitor can create
        the appropriate visitor for child nodes of different types.

        Args:
            node: The expression node to visit
            expression_system: The ExpressionSystem to inject into the visitor
            logic_type: Logic system (BOOLEAN/TERNARY)

        Returns:
            Appropriate visitor instance for this node type

        Raises:
            ValueError: If no visitor is registered for the node type
        """
        from ..expression_nodes import (
            BooleanComparisonExpressionNode,
            BooleanIterableExpressionNode,
            BooleanCollectionExpressionNode,
            BooleanUnaryExpressionNode,
            BooleanConstantExpressionNode,
            BooleanIsCloseExpressionNode,
            BooleanBetweenExpressionNode,
            ArithmeticExpressionNode,
            ArithmeticIterableExpressionNode,
            ColumnExpressionNode,
            LiteralExpressionNode,
            StringExpressionNode,
            StringPatternNode,
            StringReplaceNode,
            StringSliceNode,
            StringConcatNode,
            TemporalExtractExpressionNode,
            TemporalDiffExpressionNode,
            TemporalAdditionExpressionNode,
            TemporalTruncateExpressionNode,
            TemporalOffsetExpressionNode,
            TemporalSnapshotExpressionNode,
            NullExpressionNode,
            NullConstantExpressionNode,
            NullConditionalExpressionNode,
            NullLogicalExpressionNode,
            TypeExpressionNode,
            NameAliasExpressionNode,
            NamePrefixExpressionNode,
            NameSuffixExpressionNode,
            NameExpressionNode,
            HorizontalExpressionNode,
            NativeExpressionNode,
            # Ternary nodes
            TernaryComparisonExpressionNode,
            TernaryIterableExpressionNode,
            TernaryUnaryExpressionNode,
            TernaryConstantExpressionNode,
            TernaryCollectionExpressionNode,
            TernaryColumnExpressionNode,
        )
        from ..expression_nodes.conditional_expression_nodes import ConditionalExpressionNode

        # Boolean nodes
        if isinstance(node, (
            BooleanComparisonExpressionNode,
            BooleanIterableExpressionNode,
            BooleanCollectionExpressionNode,
            BooleanUnaryExpressionNode,
            BooleanConstantExpressionNode,
            BooleanIsCloseExpressionNode,
            BooleanBetweenExpressionNode
        )):
            from .boolean_visitor import BooleanExpressionVisitor
            return BooleanExpressionVisitor(expression_system)

        # Arithmetic nodes
        elif isinstance(node, (ArithmeticExpressionNode, ArithmeticIterableExpressionNode)):
            from .arithmetic_visitor import ArithmeticExpressionVisitor
            return ArithmeticExpressionVisitor(expression_system)

        # Core nodes (col, lit)
        elif isinstance(node, (ColumnExpressionNode, LiteralExpressionNode)):
            from .core_visitor import CoreExpressionVisitor
            return CoreExpressionVisitor(expression_system)

        # String nodes
        elif isinstance(node, (
            StringExpressionNode,
            StringPatternNode,
            StringReplaceNode,
            StringSliceNode,
            StringConcatNode,
        )):
            from .string_visitor import StringExpressionVisitor
            return StringExpressionVisitor(expression_system)

        # Temporal nodes
        elif isinstance(node, (
            TemporalExtractExpressionNode,
            TemporalDiffExpressionNode,
            TemporalAdditionExpressionNode,
            TemporalTruncateExpressionNode,
            TemporalOffsetExpressionNode,
            TemporalSnapshotExpressionNode
        )):
            from .temporal_visitor import TemporalExpressionVisitor
            return TemporalExpressionVisitor(expression_system)

        # Null nodes
        elif isinstance(node, (
            NullExpressionNode,
            NullConstantExpressionNode,
            NullConditionalExpressionNode,
            NullLogicalExpressionNode
        )):
            from .null_visitor import NullExpressionVisitor
            return NullExpressionVisitor(expression_system)

        # Type nodes
        elif isinstance(node, TypeExpressionNode):
            from .type_visitor import TypeExpressionVisitor
            return TypeExpressionVisitor(expression_system)

        # Name nodes
        elif isinstance(node, (
            NameAliasExpressionNode,
            NamePrefixExpressionNode,
            NameSuffixExpressionNode,
            NameExpressionNode
        )):
            from .name_visitor import NameExpressionVisitor
            return NameExpressionVisitor(expression_system)

        # Horizontal nodes
        elif isinstance(node, HorizontalExpressionNode):
            from .horizontal_visitor import HorizontalExpressionVisitor
            return HorizontalExpressionVisitor(expression_system)

        # Native nodes
        elif isinstance(node, NativeExpressionNode):
            from .native_visitor import NativeExpressionVisitor
            return NativeExpressionVisitor(expression_system)

        # Conditional nodes
        elif isinstance(node, ConditionalExpressionNode):
            from .conditional_visitor import ConditionalExpressionVisitor
            return ConditionalExpressionVisitor(expression_system)

        # Ternary nodes
        elif isinstance(node, (
            TernaryComparisonExpressionNode,
            TernaryIterableExpressionNode,
            TernaryUnaryExpressionNode,
            TernaryConstantExpressionNode,
            TernaryCollectionExpressionNode,
            TernaryColumnExpressionNode,
        )):
            from .ternary_visitor import TernaryExpressionVisitor
            return TernaryExpressionVisitor(expression_system)

        else:
            raise ValueError(
                f"No visitor registered for node type {type(node).__name__}. "
                f"Node: {node}"
            )

    # String aliases for backend identification
    _BACKEND_ALIASES: Dict[str, CONST_VISITOR_BACKENDS] = {
        # Polars
        "polars": CONST_VISITOR_BACKENDS.POLARS,
        "pl": CONST_VISITOR_BACKENDS.POLARS,
        # Ibis
        "ibis": CONST_VISITOR_BACKENDS.IBIS,
        "ir": CONST_VISITOR_BACKENDS.IBIS,
        # Narwhals
        "narwhals": CONST_VISITOR_BACKENDS.NARWHALS,
        "nw": CONST_VISITOR_BACKENDS.NARWHALS,
        # Pandas (for future)
        "pandas": CONST_VISITOR_BACKENDS.PANDAS,
        "pd": CONST_VISITOR_BACKENDS.PANDAS,
    }

    @classmethod
    def _identify_backend(cls, dataframe_or_backend: Any) -> CONST_VISITOR_BACKENDS:
        """
        Identify the backend framework from a DataFrame/Table object or string identifier.

        Args:
            dataframe_or_backend: Either:
                - A DataFrame/Table object (pl.DataFrame, nw.DataFrame, ir.Table, etc.)
                - A string identifier ("polars", "pl", "ibis", "ir", "narwhals", "nw")
                - A CONST_VISITOR_BACKENDS enum value

        Returns:
            The identified backend constant

        Raises:
            ValueError: If backend cannot be identified

        Examples:
            >>> _identify_backend(polars_df)  # Auto-detect from DataFrame
            >>> _identify_backend("polars")   # Explicit string
            >>> _identify_backend("ibis")     # Explicit string
            >>> _identify_backend(CONST_VISITOR_BACKENDS.POLARS)  # Pass-through
        """
        # Handle string identifiers
        if isinstance(dataframe_or_backend, str):
            backend_lower = dataframe_or_backend.lower()
            if backend_lower in cls._BACKEND_ALIASES:
                return cls._BACKEND_ALIASES[backend_lower]
            raise ValueError(
                f"Unknown backend identifier: '{dataframe_or_backend}'. "
                f"Valid options: {list(cls._BACKEND_ALIASES.keys())}"
            )

        # Handle CONST_VISITOR_BACKENDS enum directly (pass-through)
        if isinstance(dataframe_or_backend, CONST_VISITOR_BACKENDS):
            return dataframe_or_backend

        # Auto-detect from DataFrame object
        dataframe = dataframe_or_backend

        # Get the module and class name
        module_name = type(dataframe).__module__
        class_name = type(dataframe).__name__

        # Narwhals detection FIRST - check for narwhals DataFrame/LazyFrame
        # Narwhals wraps other backends, so we need to check for it before checking for polars/pandas
        if "narwhals" in module_name or hasattr(dataframe, "_compliant_frame"):
            # Check if Narwhals is wrapping Ibis - this is not supported
            if hasattr(dataframe, "implementation"):
                impl = dataframe.implementation
                # Check if it's wrapping Ibis (impl.value == 'ibis')
                if hasattr(impl, "value") and impl.value == "ibis":
                    raise ValueError(
                        "Narwhals-wrapped Ibis tables are not supported due to upstream compatibility issues. "
                        "Please unwrap the Ibis table using `df.to_native()` and use the Ibis backend directly."
                    )
            # Use Narwhals backend for other implementations (Polars, Pandas, etc.)
            return CONST_VISITOR_BACKENDS.NARWHALS

        # Ibis detection
        if "ibis" in module_name:
            return CONST_VISITOR_BACKENDS.IBIS

        # # Pandas detection
        # if "pandas" in module_name or class_name == "DataFrame":
        #     # Check if it's really pandas (not polars.DataFrame)
        #     if hasattr(dataframe, "iloc"):  # pandas-specific attribute
        #         return CONST_VISITOR_BACKENDS.PANDAS

        # Polars detection
        if "polars" in module_name or class_name in ("DataFrame", "LazyFrame"):
            # Check if it's really polars
            if hasattr(dataframe, "lazy"):  # polars-specific method
                return CONST_VISITOR_BACKENDS.POLARS

        # # PyArrow detection
        # if "pyarrow" in module_name or class_name in ("Table", "RecordBatch"):
        #     return CONST_VISITOR_BACKENDS.PYARROW

        raise ValueError(
            f"Cannot identify backend for type {type(dataframe)}. "
            f"Module: {module_name}, Class: {class_name}"
        )

    @classmethod
    def get_visitor_for_backend(
        cls,
        backend: Any,
        logic_type: CONST_LOGIC_TYPES,
        use_universal: bool = True
    ) -> ExpressionVisitor:
        """
        Get the appropriate visitor for a backend DataFrame/Table and logic type.

        This is the main factory method that automatically detects the backend
        and returns an instantiated visitor.

        Args:
            backend: A DataFrame/Table object (will be auto-detected)
            logic_type: The logic system to use (BOOLEAN, TERNARY)
            use_universal: If True, use universal visitor with ExpressionSystem injection.
                          If False, use legacy backend-specific visitor.

        Returns:
            An instantiated visitor for the backend and logic type

        Raises:
            ValueError: If no visitor is registered for the backend/logic combination
        """
        # Identify the backend from the dataframe object
        backend_type = cls._identify_backend(backend)

        # If using universal visitor with ExpressionSystem
        if use_universal:
            # Check if ExpressionSystem is registered for this backend
            if backend_type not in cls._expression_systems_registry:
                raise ValueError(
                    f"No ExpressionSystem registered for backend {backend_type.value}. "
                    f"Available backends: {[b.value for b in cls._expression_systems_registry.keys()]}"
                )

            # Create ExpressionSystem instance
            expression_system_class = cls._expression_systems_registry[backend_type]
            expression_system = expression_system_class()

            # Import and use universal visitor
            if logic_type == CONST_LOGIC_TYPES.BOOLEAN:
                from .universal_boolean_visitor import UniversalBooleanExpressionVisitor
                return UniversalBooleanExpressionVisitor(expression_system)
            else:
                raise ValueError(f"Universal visitor not yet implemented for logic type {logic_type.value}")

        # Legacy path: use backend-specific visitor
        if backend_type not in cls._visitors_registry:
            raise ValueError(
                f"No visitors registered for backend {backend_type.value}. "
                f"Available backends: {[b.value for b in cls._visitors_registry.keys()]}"
            )

        if logic_type not in cls._visitors_registry[backend_type]:
            raise ValueError(
                f"No {logic_type.value} visitor registered for backend {backend_type.value}. "
                f"Available logic types: {[lt.value for lt in cls._visitors_registry[backend_type].keys()]}"
            )

        visitor_class = cls._visitors_registry[backend_type][logic_type]
        return visitor_class()

    @classmethod
    def create_visitor_for_backend(
        cls,
        backend: Any,
        logic_type: CONST_LOGIC_TYPES
    ) -> ExpressionVisitor:
        """
        Alias for get_visitor_for_backend for backwards compatibility.

        Args:
            backend: A DataFrame/Table object (will be auto-detected)
            logic_type: The logic system to use (BOOLEAN, TERNARY)

        Returns:
            An instantiated visitor for the backend and logic type
        """
        return cls.get_visitor_for_backend(backend, logic_type)

    @classmethod
    def list_registered_visitors(cls) -> Dict[str, Dict[str, str]]:
        """
        List all registered visitors for debugging.

        Returns:
            Dictionary mapping backend names to logic types to visitor class names
        """
        result = {}
        for backend, logic_dict in cls._visitors_registry.items():
            result[backend.value] = {
                logic.value: visitor_class.__name__
                for logic, visitor_class in logic_dict.items()
            }
        return result


# Auto-register Narwhals visitors and ExpressionSystem on import
def _auto_register_narwhals():
    """Automatically register Narwhals visitors and ExpressionSystem if available."""
    # Register ExpressionSystem first
    try:
        from ...backends.expression_systems.narwhals import NarwhalsExpressionSystem
        ExpressionVisitorFactory.register_expression_system(
            CONST_VISITOR_BACKENDS.NARWHALS,
            NarwhalsExpressionSystem
        )
    except ImportError:
        # ExpressionSystem not available, skip registration
        pass

    # # Register boolean visitor (legacy, for backwards compatibility)
    # try:
    #     from ...backends.narwhals.narwhals_boolean_visitor import NarwhalsBooleanExpressionVisitor
    #     ExpressionVisitorFactory.register(
    #         CONST_VISITOR_BACKENDS.NARWHALS,
    #         CONST_LOGIC_TYPES.BOOLEAN,
    #         NarwhalsBooleanExpressionVisitor
    #     )
    # except ImportError:
    #     # Boolean visitor not available, skip registration
    #     pass

    # # Register ternary visitor (separate try-except so boolean can work independently)
    # try:
    #     from ...backends.narwhals.narwhals_ternary_visitor import NarwhalsTernaryExpressionVisitor
    #     ExpressionVisitorFactory.register(
    #         CONST_VISITOR_BACKENDS.NARWHALS,
    #         CONST_LOGIC_TYPES.TERNARY,
    #         NarwhalsTernaryExpressionVisitor
    #     )
    # except ImportError:
    #     # Ternary visitor not available, skip registration
    #     pass


# Auto-register Polars ExpressionSystem on import
def _auto_register_polars():
    """Automatically register Polars ExpressionSystem if available."""
    # Register ExpressionSystem
    try:
        from ...backends.expression_systems.polars import PolarsExpressionSystem
        ExpressionVisitorFactory.register_expression_system(
            CONST_VISITOR_BACKENDS.POLARS,
            PolarsExpressionSystem
        )
    except ImportError:
        # ExpressionSystem not available, skip registration
        pass


# Auto-register Ibis ExpressionSystem on import
def _auto_register_ibis():
    """Automatically register Ibis ExpressionSystem if available."""
    # Register ExpressionSystem
    try:
        from ...backends.expression_systems.ibis import IbisExpressionSystem
        ExpressionVisitorFactory.register_expression_system(
            CONST_VISITOR_BACKENDS.IBIS,
            IbisExpressionSystem
        )
    except ImportError:
        # ExpressionSystem not available, skip registration
        pass


# Decorator for registering ExpressionSystems
def register_expression_system(backend: CONST_VISITOR_BACKENDS):
    """
    Decorator for registering ExpressionSystem classes.

    Usage:
        @register_expression_system(CONST_VISITOR_BACKENDS.POLARS)
        class PolarsExpressionSystem(ExpressionSystem):
            ...
    """
    def decorator(cls: Type[ExpressionSystem]) -> Type[ExpressionSystem]:
        ExpressionVisitorFactory.register_expression_system(backend, cls)
        return cls
    return decorator


# Run auto-registration on module import
_auto_register_narwhals()
_auto_register_polars()
_auto_register_ibis()
