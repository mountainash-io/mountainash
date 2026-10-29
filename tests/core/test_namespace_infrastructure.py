"""Tests for the namespace-based expression API infrastructure.

Tests the foundational components:
- NamespaceDescriptor
- BaseExpressionNamespace
- BaseExpressionAPI
- __getattr__ dispatch mechanism
"""

import pytest
from mountainash.expressions.core.expression_api import (
    NamespaceDescriptor,
    BaseExpressionAPI,
    BooleanExpressionAPI,
)
from mountainash.expressions.core.expression_api.api_builders.api_builder_base import BaseExpressionAPIBuilder as BaseExpressionNamespace
from mountainash.expressions.core.expression_nodes import FieldReferenceNode
# from mountainash.expressions.core.protocols import ENUM_CORE_OPERATORS


# ========================================
# Test Fixtures
# ========================================

class MockExpressionNode:
    """Mock expression node for testing."""
    pass


class MockNamespace(BaseExpressionNamespace):
    """Mock namespace for testing dispatch."""

    def mock_method(self) -> str:
        return "mock_method_called"

    def method_with_arg(self, value: int) -> int:
        return value * 2


class MockNamespaceWithBuild(BaseExpressionNamespace):
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
# BaseExpressionNamespace Tests
# ========================================

class TestBaseExpressionNamespace:
    """Tests for BaseExpressionNamespace."""

    def test_node_property_returns_api_node(self):
        """_node property returns the parent API's node."""

        class TestAPI(BaseExpressionAPI):
            _FLAT_NAMESPACES = ()

            @classmethod
            def create(cls, node):
                return cls(node)

        node = MockExpressionNode()
        api = TestAPI(node)
        ns = BaseExpressionNamespace(api)

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

        ns = BaseExpressionNamespace(api1)
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
        ns = BaseExpressionNamespace(api)

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
        ns = BaseExpressionNamespace(api)

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

        class FirstNamespace(BaseExpressionNamespace):
            def shared_method(self) -> str:
                return "first"

        class SecondNamespace(BaseExpressionNamespace):
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
        from mountainash.expressions import col

        expr = col("test_column")
        assert isinstance(expr, BooleanExpressionAPI)

    def test_lit_returns_boolean_expression_api(self):
        """lit() factory returns BooleanExpressionAPI."""
        from mountainash.expressions import lit

        expr = lit(42)
        assert isinstance(expr, BooleanExpressionAPI)

    # def test_expression_builder_alias(self):
    #     """ExpressionBuilder is alias for BooleanExpressionAPI."""
    #     from mountainash.expressions import ExpressionBuilder

    #     assert ExpressionBuilder is BooleanExpressionAPI

    def test_col_creates_column_node(self):
        """col() creates a FieldReferenceNode."""
        from mountainash.expressions import col

        expr = col("my_column")
        assert isinstance(expr._node, FieldReferenceNode)
        assert expr._node.field == "my_column"


# ========================================
# Real Namespace Tests
# ========================================

class TestRealNamespaces:
    """Tests for the actual namespace implementations."""

    def test_comparison_namespace_eq(self):
        """ScalarBooleanNamespace.eq creates correct node."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON

        # Use namespace method via mixin (current path)
        expr = col("age").eq(30)

        # Verify node structure - now uses ScalarFunctionNode with function_key
        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL
        # Arguments are now in a list: [FieldReferenceNode, LiteralNode]
        assert expr._node.arguments[0].field == "age"
        assert expr._node.arguments[1].value == 30

    def test_logical_namespace_and_(self):
        """ScalarBooleanNamespace.and_ creates correct node."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_BOOLEAN

        expr = col("a").gt(10).and_(col("b").lt(5))

        # Verify node structure - now uses ScalarFunctionNode with function_key
        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_BOOLEAN.AND
        # Arguments are now in a list
        assert len(expr._node.arguments) == 2

    def test_arithmetic_namespace_add(self):
        """ScalarArithmeticNamespace.add creates correct node."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_ARITHMETIC

        expr = col("price").add(10)

        # Verify node structure - now uses ScalarFunctionNode with function_key
        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_ARITHMETIC.ADD

    def test_null_namespace_is_null(self):
        """is_null creates correct node (now in ScalarComparisonNamespace)."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_COMPARISON

        expr = col("value").is_null()

        # Verify node structure - now uses ScalarFunctionNode with function_key
        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_COMPARISON.IS_NULL

    def test_type_namespace_cast(self):
        """CastNamespace.cast creates correct node."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import CastNode

        expr = col("value").cast("int64")

        # Verify node structure - now uses CastNode with target_type
        assert isinstance(expr._node, CastNode)
        assert expr._node.target_type == "i64"

    def test_chained_operations_preserve_type(self):
        """Chained operations preserve BooleanExpressionAPI type."""
        from mountainash.expressions import col

        expr = col("age").gt(18).and_(col("score").ge(80)).or_(col("premium").eq(True))

        assert isinstance(expr, BooleanExpressionAPI)

    def test_flat_namespaces_are_populated(self):
        """BooleanExpressionAPI has flat namespaces configured."""
        from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash import (
            MountainAshScalarTernaryAPIBuilder as TernaryNamespace,
            MountainAshNullAPIBuilder as NullNamespace,
            MountainAshNativeAPIBuilder as NativeNamespace,
        )
        from mountainash.expressions.core.expression_api.api_builders.substrait import (
            SubstraitScalarBooleanAPIBuilder as ScalarBooleanNamespace,
            SubstraitScalarComparisonAPIBuilder as ScalarComparisonNamespace,
            SubstraitScalarArithmeticAPIBuilder as ScalarArithmeticNamespace,
            SubstraitScalarRoundingAPIBuilder as ScalarRoundingNamespace,
            SubstraitScalarLogarithmicAPIBuilder as ScalarLogarithmicNamespace,
            SubstraitCastAPIBuilder as CastNamespace,
        )

        namespaces = BooleanExpressionAPI._FLAT_NAMESPACES

        # Verify all expected namespaces are present
        assert TernaryNamespace in namespaces
        assert ScalarBooleanNamespace in namespaces
        assert ScalarComparisonNamespace in namespaces
        assert ScalarArithmeticNamespace in namespaces
        assert ScalarRoundingNamespace in namespaces
        assert ScalarLogarithmicNamespace in namespaces
        assert CastNamespace in namespaces
        assert NullNamespace in namespaces
        assert NativeNamespace in namespaces


# ========================================
# Explicit Namespace Tests (.str, .dt, .name)
# ========================================

class TestExplicitNamespaces:
    """Tests for explicit namespace access via descriptors."""

    def test_str_namespace_access(self):
        """Accessing .str returns StringNamespace."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_api.api_builders.substrait import SubstraitScalarStringAPIBuilder as StringNamespace

        expr = col("text")
        assert isinstance(expr.str, StringNamespace)

    def test_str_upper_creates_correct_node(self):
        """col('x').str.upper() creates ScalarFunctionNode."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

        expr = col("text").str.upper()

        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.UPPER

    def test_str_contains_creates_correct_node(self):
        """col('x').str.contains('y') creates ScalarFunctionNode."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_SUBSTRAIT_SCALAR_STRING

        expr = col("text").str.contains("hello")

        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_SUBSTRAIT_SCALAR_STRING.CONTAINS

    def test_dt_namespace_access(self):
        """Accessing .dt returns DateTimeNamespace."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_api.api_builders.substrait import SubstraitScalarDatetimeAPIBuilder as DateTimeNamespace

        expr = col("timestamp")
        assert isinstance(expr.dt, DateTimeNamespace)

    def test_dt_year_creates_correct_node(self):
        """col('x').dt.year() creates ScalarFunctionNode."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME

        expr = col("timestamp").dt.year()

        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.EXTRACT_YEAR

    def test_dt_add_days_creates_correct_node(self):
        """col('x').dt.add_days(7) creates ScalarFunctionNode."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_SCALAR_DATETIME

        expr = col("date").dt.add_days(7)

        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_MOUNTAINASH_SCALAR_DATETIME.ADD_DAYS

    def test_name_namespace_access(self):
        """Accessing .name returns NameNamespace."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_api.api_builders.extensions_mountainash import MountainAshNameAPIBuilder as NameNamespace

        expr = col("x")
        assert isinstance(expr.name, NameNamespace)

    def test_name_alias_creates_correct_node(self):
        """col('x').name.alias('y') creates ScalarFunctionNode."""
        from mountainash.expressions import col
        from mountainash.expressions.core.expression_nodes import ScalarFunctionNode
        from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NAME

        expr = col("x").name.alias("y")

        assert isinstance(expr._node, ScalarFunctionNode)
        assert expr._node.function_key == FKEY_MOUNTAINASH_NAME.ALIAS

    def test_chaining_explicit_namespaces(self):
        """Can chain explicit namespace operations."""
        from mountainash.expressions import col

        # Chain string operations
        expr = col("text").str.upper().str.trim()
        assert isinstance(expr, BooleanExpressionAPI)

    def test_mixing_explicit_and_flat_namespaces(self):
        """Can mix explicit namespace access with flat namespace methods."""
        from mountainash.expressions import col

        # Use .str namespace then flat namespace method
        expr = col("text").str.upper().eq("HELLO")
        assert isinstance(expr, BooleanExpressionAPI)

        # Use flat method then .dt namespace
        expr2 = col("timestamp").gt(col("other")).dt.year()
        # Note: This doesn't make semantic sense, but structurally it works
        assert isinstance(expr2, BooleanExpressionAPI)
