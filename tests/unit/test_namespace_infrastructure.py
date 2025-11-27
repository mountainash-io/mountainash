"""Tests for the namespace-based expression API infrastructure.

Tests the foundational components:
- NamespaceDescriptor
- BaseNamespace
- BaseExpressionAPI
- __getattr__ dispatch mechanism
"""

import pytest
from mountainash_expressions.core.expression_api import (
    NamespaceDescriptor,
    BaseExpressionAPI,
    BooleanExpressionAPI,
)
from mountainash_expressions.core.namespaces import BaseNamespace
from mountainash_expressions.core.expression_nodes import ColumnExpressionNode
from mountainash_expressions.core.protocols import ENUM_CORE_OPERATORS


# ========================================
# Test Fixtures
# ========================================

class MockExpressionNode:
    """Mock expression node for testing."""
    pass


class MockNamespace(BaseNamespace):
    """Mock namespace for testing dispatch."""

    def mock_method(self) -> str:
        return "mock_method_called"

    def method_with_arg(self, value: int) -> int:
        return value * 2


class MockNamespaceWithBuild(BaseNamespace):
    """Mock namespace that tests _build()."""

    def build_new_node(self, value: str) -> BaseExpressionAPI:
        new_node = MockExpressionNode()
        return self._build(new_node)


# ========================================
# NamespaceDescriptor Tests
# ========================================

class TestNamespaceDescriptor:
    """Tests for NamespaceDescriptor."""

    def test_class_access_returns_descriptor(self):
        """Accessing descriptor on class returns the descriptor itself."""

        class TestAPI(BaseExpressionAPI):
            mock = NamespaceDescriptor(MockNamespace)
            _FLAT_NAMESPACES = ()

        assert isinstance(TestAPI.mock, NamespaceDescriptor)

    def test_instance_access_returns_namespace(self):
        """Accessing descriptor on instance returns namespace instance."""

        class TestAPI(BaseExpressionAPI):
            mock = NamespaceDescriptor(MockNamespace)
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        assert isinstance(api.mock, MockNamespace)

    def test_namespace_bound_to_correct_api(self):
        """Namespace instance has reference to parent API."""

        class TestAPI(BaseExpressionAPI):
            mock = NamespaceDescriptor(MockNamespace)
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        ns = api.mock
        assert ns._api is api

    def test_descriptor_repr(self):
        """Descriptor has meaningful repr."""
        desc = NamespaceDescriptor(MockNamespace)
        assert "MockNamespace" in repr(desc)


# ========================================
# BaseNamespace Tests
# ========================================

class TestBaseNamespace:
    """Tests for BaseNamespace."""

    def test_node_property_returns_api_node(self):
        """_node property returns the parent API's node."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        node = MockExpressionNode()
        api = TestAPI(node)
        ns = BaseNamespace(api)

        assert ns._node is node

    def test_to_node_or_value_with_api(self):
        """_to_node_or_value extracts node from API instance."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        node1 = MockExpressionNode()
        node2 = MockExpressionNode()
        api1 = TestAPI(node1)
        api2 = TestAPI(node2)

        ns = BaseNamespace(api1)
        result = ns._to_node_or_value(api2)

        assert result is node2

    def test_to_node_or_value_with_raw_value(self):
        """_to_node_or_value passes through raw values."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        ns = BaseNamespace(api)

        assert ns._to_node_or_value(42) == 42
        assert ns._to_node_or_value("hello") == "hello"
        assert ns._to_node_or_value(None) is None

    def test_coerce_if_needed_default_passthrough(self):
        """Default _coerce_if_needed returns input unchanged."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        ns = BaseNamespace(api)

        node = MockExpressionNode()
        assert ns._coerce_if_needed(node) is node

    def test_build_preserves_api_type(self):
        """_build returns instance of same API type."""

        class CustomAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        api = CustomAPI(MockExpressionNode())
        ns = MockNamespaceWithBuild(api)

        result = ns.build_new_node("test")

        assert isinstance(result, CustomAPI)
        assert type(result) is CustomAPI


# ========================================
# BaseExpressionAPI Tests
# ========================================

class TestBaseExpressionAPI:
    """Tests for BaseExpressionAPI."""

    def test_init_stores_node(self):
        """__init__ stores the node."""
        node = MockExpressionNode()
        api = BooleanExpressionAPI(node)
        assert api._node is node

    def test_node_property(self):
        """node property returns stored node."""
        node = MockExpressionNode()
        api = BooleanExpressionAPI(node)
        assert api.node is node

    def test_create_returns_same_type(self):
        """create() classmethod returns instance of same type."""

        class CustomAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        node = MockExpressionNode()
        api = CustomAPI.create(node)

        assert type(api) is CustomAPI

    def test_repr(self):
        """API has meaningful repr."""
        node = MockExpressionNode()
        api = BooleanExpressionAPI(node)
        repr_str = repr(api)

        assert "BooleanExpressionAPI" in repr_str


# ========================================
# __getattr__ Dispatch Tests
# ========================================

class TestGetAttrDispatch:
    """Tests for __getattr__ namespace dispatch."""

    def test_finds_method_in_flat_namespace(self):
        """__getattr__ finds methods in flat namespaces."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = (MockNamespace,)

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        result = api.mock_method()

        assert result == "mock_method_called"

    def test_method_with_argument(self):
        """Found methods work with arguments."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = (MockNamespace,)

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        result = api.method_with_arg(21)

        assert result == 42

    def test_unknown_attribute_raises_attribute_error(self):
        """Unknown attributes raise AttributeError."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = (MockNamespace,)

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())

        with pytest.raises(AttributeError) as exc_info:
            api.nonexistent_method

        assert "nonexistent_method" in str(exc_info.value)

    def test_private_attributes_not_dispatched(self):
        """Private attributes (starting with _) are not dispatched."""
        api = BooleanExpressionAPI(MockExpressionNode())

        with pytest.raises(AttributeError):
            api._some_private_attr

    def test_namespace_search_order(self):
        """Namespaces are searched in order defined in _FLAT_NAMESPACES."""

        class FirstNamespace(BaseNamespace):
            def shared_method(self) -> str:
                return "first"

        class SecondNamespace(BaseNamespace):
            def shared_method(self) -> str:
                return "second"

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = (FirstNamespace, SecondNamespace)

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())
        result = api.shared_method()

        assert result == "first"

    def test_empty_flat_namespaces(self):
        """API with empty _FLAT_NAMESPACES raises AttributeError for any method."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        api = TestAPI(MockExpressionNode())

        with pytest.raises(AttributeError):
            api.any_method


# ========================================
# Integration Tests
# ========================================

class TestInfrastructureIntegration:
    """Integration tests for the namespace infrastructure."""

    def test_col_returns_boolean_expression_api(self):
        """col() factory returns BooleanExpressionAPI."""
        from mountainash_expressions import col

        expr = col("test_column")
        assert isinstance(expr, BooleanExpressionAPI)

    def test_lit_returns_boolean_expression_api(self):
        """lit() factory returns BooleanExpressionAPI."""
        from mountainash_expressions import lit

        expr = lit(42)
        assert isinstance(expr, BooleanExpressionAPI)

    # def test_expression_builder_alias(self):
    #     """ExpressionBuilder is alias for BooleanExpressionAPI."""
    #     from mountainash_expressions import ExpressionBuilder

    #     assert ExpressionBuilder is BooleanExpressionAPI

    def test_col_creates_column_node(self):
        """col() creates a ColumnExpressionNode."""
        from mountainash_expressions import col

        expr = col("my_column")
        assert isinstance(expr._node, ColumnExpressionNode)
        assert expr._node.column == "my_column"


# ========================================
# Real Namespace Tests
# ========================================

class TestRealNamespaces:
    """Tests for the actual namespace implementations."""

    def test_comparison_namespace_eq(self):
        """BooleanComparisonNamespace.eq creates correct node."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import BooleanComparisonExpressionNode
        from mountainash_expressions.core.protocols import ENUM_BOOLEAN_OPERATORS

        # Use namespace method via mixin (current path)
        expr = col("age").eq(30)

        # Verify node structure
        assert isinstance(expr._node, BooleanComparisonExpressionNode)
        assert expr._node.operator == ENUM_BOOLEAN_OPERATORS.EQ
        assert expr._node.left.column == "age"
        assert expr._node.right == 30

    def test_logical_namespace_and_(self):
        """BooleanLogicalNamespace.and_ creates correct node."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import BooleanIterableExpressionNode
        from mountainash_expressions.core.protocols import ENUM_BOOLEAN_OPERATORS

        expr = col("a").gt(10).and_(col("b").lt(5))

        # Verify node structure
        assert isinstance(expr._node, BooleanIterableExpressionNode)
        assert expr._node.operator == ENUM_BOOLEAN_OPERATORS.AND
        # operands is a Pydantic iterator, so convert to list
        assert len(list(expr._node.operands)) == 2

    def test_arithmetic_namespace_add(self):
        """ArithmeticNamespace.add creates correct node."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import ArithmeticIterableExpressionNode
        from mountainash_expressions.core.protocols import ENUM_ARITHMETIC_OPERATORS

        expr = col("price").add(10)

        # Verify node structure
        assert isinstance(expr._node, ArithmeticIterableExpressionNode)
        assert expr._node.operator == ENUM_ARITHMETIC_OPERATORS.ADD

    def test_null_namespace_is_null(self):
        """NullNamespace.is_null creates correct node."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import NullLogicalExpressionNode
        from mountainash_expressions.core.protocols import ENUM_NULL_OPERATORS

        expr = col("value").is_null()

        # Verify node structure
        assert isinstance(expr._node, NullLogicalExpressionNode)
        assert expr._node.operator == ENUM_NULL_OPERATORS.IS_NULL

    def test_type_namespace_cast(self):
        """TypeNamespace.cast creates correct node."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import TypeExpressionNode
        from mountainash_expressions.core.protocols import ENUM_TYPE_OPERATORS

        expr = col("value").cast("int64")

        # Verify node structure
        assert isinstance(expr._node, TypeExpressionNode)
        assert expr._node.operator == ENUM_TYPE_OPERATORS.CAST

    def test_chained_operations_preserve_type(self):
        """Chained operations preserve BooleanExpressionAPI type."""
        from mountainash_expressions import col

        expr = col("age").gt(18).and_(col("score").ge(80)).or_(col("premium").eq(True))

        assert isinstance(expr, BooleanExpressionAPI)

    def test_flat_namespaces_are_populated(self):
        """BooleanExpressionAPI has flat namespaces configured."""
        from mountainash_expressions.core.namespaces import (
            BooleanComparisonNamespace,
            BooleanLogicalNamespace,
            ArithmeticNamespace,
            NullNamespace,
            TypeNamespace,
            HorizontalNamespace,
            NativeNamespace,
        )

        namespaces = BooleanExpressionAPI._FLAT_NAMESPACES

        # Verify all expected namespaces are present
        assert BooleanComparisonNamespace in namespaces
        assert BooleanLogicalNamespace in namespaces
        assert ArithmeticNamespace in namespaces
        assert NullNamespace in namespaces
        assert TypeNamespace in namespaces
        assert HorizontalNamespace in namespaces
        assert NativeNamespace in namespaces


# ========================================
# Explicit Namespace Tests (.str, .dt, .name)
# ========================================

class TestExplicitNamespaces:
    """Tests for explicit namespace access via descriptors."""

    def test_str_namespace_access(self):
        """Accessing .str returns StringNamespace."""
        from mountainash_expressions import col
        from mountainash_expressions.core.namespaces import StringNamespace

        expr = col("text")
        assert isinstance(expr.str, StringNamespace)

    def test_str_upper_creates_correct_node(self):
        """col('x').str.upper() creates StringExpressionNode."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import StringExpressionNode
        from mountainash_expressions.core.protocols import ENUM_STRING_OPERATORS

        expr = col("text").str.upper()

        assert isinstance(expr._node, StringExpressionNode)
        assert expr._node.operator == ENUM_STRING_OPERATORS.STR_UPPER

    def test_str_contains_creates_correct_node(self):
        """col('x').str.contains('y') creates StringSearchExpressionNode."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import StringSearchExpressionNode
        from mountainash_expressions.core.protocols import ENUM_STRING_OPERATORS

        expr = col("text").str.contains("hello")

        assert isinstance(expr._node, StringSearchExpressionNode)
        assert expr._node.operator == ENUM_STRING_OPERATORS.STR_CONTAINS

    def test_dt_namespace_access(self):
        """Accessing .dt returns DateTimeNamespace."""
        from mountainash_expressions import col
        from mountainash_expressions.core.namespaces import DateTimeNamespace

        expr = col("timestamp")
        assert isinstance(expr.dt, DateTimeNamespace)

    def test_dt_year_creates_correct_node(self):
        """col('x').dt.year() creates TemporalExtractExpressionNode."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import TemporalExtractExpressionNode
        from mountainash_expressions.core.protocols import ENUM_TEMPORAL_OPERATORS

        expr = col("timestamp").dt.year()

        assert isinstance(expr._node, TemporalExtractExpressionNode)
        assert expr._node.operator == ENUM_TEMPORAL_OPERATORS.DT_EXTRACT_YEAR

    def test_dt_add_days_creates_correct_node(self):
        """col('x').dt.add_days(7) creates TemporalAdditionExpressionNode."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import TemporalAdditionExpressionNode
        from mountainash_expressions.core.protocols import ENUM_TEMPORAL_OPERATORS

        expr = col("date").dt.add_days(7)

        assert isinstance(expr._node, TemporalAdditionExpressionNode)
        assert expr._node.operator == ENUM_TEMPORAL_OPERATORS.DT_ADD_DAYS

    def test_name_namespace_access(self):
        """Accessing .name returns NameNamespace."""
        from mountainash_expressions import col
        from mountainash_expressions.core.namespaces import NameNamespace

        expr = col("x")
        assert isinstance(expr.name, NameNamespace)

    def test_name_alias_creates_correct_node(self):
        """col('x').name.alias('y') creates NameAliasExpressionNode."""
        from mountainash_expressions import col
        from mountainash_expressions.core.expression_nodes import NameAliasExpressionNode
        from mountainash_expressions.core.protocols import ENUM_NAME_OPERATORS

        expr = col("x").name.alias("y")

        assert isinstance(expr._node, NameAliasExpressionNode)
        assert expr._node.operator == ENUM_NAME_OPERATORS.ALIAS

    def test_chaining_explicit_namespaces(self):
        """Can chain explicit namespace operations."""
        from mountainash_expressions import col

        # Chain string operations
        expr = col("text").str.upper().str.trim()
        assert isinstance(expr, BooleanExpressionAPI)

    def test_mixing_explicit_and_flat_namespaces(self):
        """Can mix explicit namespace access with flat namespace methods."""
        from mountainash_expressions import col

        # Use .str namespace then flat namespace method
        expr = col("text").str.upper().eq("HELLO")
        assert isinstance(expr, BooleanExpressionAPI)

        # Use flat method then .dt namespace
        expr2 = col("timestamp").gt(col("other")).dt.year()
        # Note: This doesn't make semantic sense, but structurally it works
        assert isinstance(expr2, BooleanExpressionAPI)
