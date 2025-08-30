"""Example of how to create and register a custom backend plugin.

This file demonstrates how third-party libraries or users can create
their own backend plugins and register them with the visitor factory.
"""

from typing import Dict, Type, Any
from ..core.visitor import ExpressionVisitor, BooleanExpressionVisitor, TernaryExpressionVisitor
from ..core.visitor.visitor_factory import BackendPlugin, ExpressionVisitorFactory
from ..core.constants import CONST_LOGIC_TYPES


# Example: Custom DataFrame type (for demonstration)
class CustomDataFrame:
    """A hypothetical custom DataFrame implementation."""
    def __init__(self, data: dict):
        self.data = data
        self.columns = list(data.keys())


# Example: Custom visitor implementations
class CustomBooleanVisitor(BooleanExpressionVisitor):
    """Boolean expression visitor for custom backend."""
    
    def visit_column(self, node, column_name: str):
        # Return backend-specific column reference
        return f"custom_col({column_name})"
    
    def visit_literal(self, node, value: Any):
        return f"custom_lit({value})"
    
    def visit_logical_and(self, node, left, right):
        return f"({left} AND {right})"
    
    def visit_logical_or(self, node, left, right):
        return f"({left} OR {right})"
    
    def visit_logical_not(self, node, operand):
        return f"NOT ({operand})"
    
    def visit_comparison(self, node, left, operator: str, right):
        return f"({left} {operator} {right})"


class CustomTernaryVisitor(TernaryExpressionVisitor):
    """Ternary expression visitor for custom backend."""
    
    def visit_column(self, node, column_name: str):
        return f"custom_ternary_col({column_name})"
    
    def visit_literal(self, node, value: Any):
        return f"custom_ternary_lit({value})"
    
    def visit_logical_and(self, node, left, right):
        return f"ternary_and({left}, {right})"
    
    def visit_logical_or(self, node, left, right):
        return f"ternary_or({left}, {right})"
    
    def visit_logical_not(self, node, operand):
        return f"ternary_not({operand})"
    
    def visit_comparison(self, node, left, operator: str, right):
        return f"ternary_compare({left}, '{operator}', {right})"


# Example: Custom backend plugin
class CustomBackendPlugin(BackendPlugin):
    """Plugin for a custom DataFrame backend."""
    
    def get_backend_id(self) -> str:
        return "custom_backend"
    
    def get_visitors(self) -> Dict[str, Type[ExpressionVisitor]]:
        return {
            CONST_LOGIC_TYPES.BOOLEAN: CustomBooleanVisitor,
            CONST_LOGIC_TYPES.TERNARY: CustomTernaryVisitor,
        }
    
    def can_handle(self, table: Any) -> bool:
        return isinstance(table, CustomDataFrame)
    
    @property
    def priority(self) -> int:
        return 1  # Low priority, checked after built-in backends


# Example: Registration methods

def register_custom_backend_as_plugin():
    """Register custom backend using the plugin approach."""
    plugin = CustomBackendPlugin()
    ExpressionVisitorFactory.register_backend_plugin(plugin)


def register_custom_backend_directly():
    """Register custom backend using the direct registration approach."""
    ExpressionVisitorFactory.register_backend(
        backend_id="custom_backend",
        visitors={
            CONST_LOGIC_TYPES.BOOLEAN: CustomBooleanVisitor,
            CONST_LOGIC_TYPES.TERNARY: CustomTernaryVisitor,
        },
        detector=lambda table: isinstance(table, CustomDataFrame),
        priority=1
    )


# Example: Usage
def demo_custom_backend():
    """Demonstrate using a custom backend."""
    
    # Register the custom backend
    register_custom_backend_as_plugin()
    
    # Create a custom dataframe
    df = CustomDataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
    
    # The factory will automatically detect and use the custom backend
    from ..core.logic.boolean import BooleanColumnExpressionNode
    
    expr = BooleanColumnExpressionNode("col1")
    
    # This will use the CustomBooleanVisitor
    visitor = ExpressionVisitorFactory.create_boolean_visitor_for_backend(df)
    result = expr.accept(visitor)
    
    print(f"Result: {result}")  # Output: custom_col(col1)
    
    # Check if backend is registered
    if ExpressionVisitorFactory.is_backend_registered("custom_backend"):
        print("Custom backend is registered!")
    
    # Get all registered backends
    backends = ExpressionVisitorFactory.get_registered_backends()
    print(f"Registered backends: {backends}")


if __name__ == "__main__":
    demo_custom_backend()