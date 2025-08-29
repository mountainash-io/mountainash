"""
Ultra-Simple Visitor Pattern

This demonstrates the cleanest possible visitor implementation using your
simplified approach where we just delegate to the visitor that matches 
the node's logic type.
"""

from mountainash_expressions.logic.ternary import (
    should_delegate_to_node_logic_type,
    should_convert_node, 
    convert_expression
)
from mountainash_expressions.helpers.visitor_factory import ExpressionVisitorFactory


class UltraSimpleBooleanVisitor:
    """
    Ultra-simplified visitor using the cleaner delegation approach.
    
    We don't need to figure out WHICH visitor to create - we already know!
    Just create a visitor that matches the node's logic type.
    """
    
    def __init__(self, table):
        self.table = table
        self.logic_type = "boolean"
        self.backend_type = "polars"  # Would be determined by visitor subclass
    
    def visit_logical_expression(self, node):
        """Ultra-simple template - just 3 decision points."""
        visitor_delegate_required = should_delegate_to_node_logic_type(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)
            return node.accept(delegate_visitor)
        
        # Otherwise continue processing
        return self._process_boolean_logical(node)
    
    def visit_column_expression(self, node):
        """Same pattern for all visit methods."""
        visitor_delegate_required = should_delegate_to_node_logic_type(node, self.logic_type)  
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)
            return node.accept(delegate_visitor)
            
        return self._process_boolean_column(node)
    
    def visit_literal_expression(self, node):
        """Same pattern for all visit methods."""
        visitor_delegate_required = should_delegate_to_node_logic_type(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)
            return node.accept(delegate_visitor)
            
        return self._process_boolean_literal(node)
    
    def _process_boolean_logical(self, node):
        return f"polars_boolean_logical({node.operator})"
    
    def _process_boolean_column(self, node):
        return f"polars_boolean_column({node.column_name} {node.operator} {node.value})"
    
    def _process_boolean_literal(self, node):
        return f"polars_boolean_literal({node.value})"


def demonstrate_ultra_simple_pattern():
    """Show how clean and simple the visitor pattern becomes."""
    
    print("=== Ultra-Simple Visitor Pattern ===\n")
    
    print("Key insight: We don't need to decide WHICH visitor to delegate to.")
    print("We already know - it's the one that matches the node's logic type!\n")
    
    print("Standard visitor method template:")
    print("```python")
    print("def visit_*_expression(self, node):")
    print("    visitor_delegate_required = should_delegate_to_node_logic_type(node, self.logic_type)")
    print("    node_conversion_required = should_convert_node(node, self.logic_type)")
    print("    ")
    print("    if node_conversion_required:")
    print("        node = convert_expression(node, self.logic_type)")
    print("    ")
    print("    if visitor_delegate_required:")
    print("        delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)")
    print("        return node.accept(delegate_visitor)")
    print("    ")
    print("    return self._process_*_node(node)")
    print("```\n")
    
    print("Benefits of this approach:")
    print("✓ No need to determine target logic type - use node.logic_type")
    print("✓ No complex delegation logic - just create visitor that matches node")
    print("✓ Consistent backend (self.backend_type) with different logic type")
    print("✓ Extremely simple to understand and implement")
    print("✓ All complexity hidden in conversion system")
    
    print("\nDecision flow:")
    print("1. Should I delegate? (based on node vs visitor logic type)")
    print("2. Should I convert? (based on semantic preservation)")
    print("3. Do the right thing automatically")


# Even more simplified with mixin
class UltraSimpleVisitorMixin:
    """Mixin that provides the ultra-simple delegation pattern."""
    
    def _handle_node(self, node):
        """Ultra-simple node handling template."""
        visitor_delegate_required = should_delegate_to_node_logic_type(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = ExpressionVisitorFactory.create_visitor(self.backend_type, node.logic_type)
            return node.accept(delegate_visitor)
        
        return None  # Continue with normal processing
    
    def visit_logical_expression(self, node):
        result = self._handle_node(node)
        return result if result is not None else self._process_logical(node)
    
    def visit_column_expression(self, node):
        result = self._handle_node(node)
        return result if result is not None else self._process_column(node)
    
    def visit_literal_expression(self, node):
        result = self._handle_node(node)
        return result if result is not None else self._process_literal(node)


class ExamplePolarsVisitor(UltraSimpleVisitorMixin):
    """Example visitor using the ultra-simple mixin."""
    
    def __init__(self, table):
        self.table = table
        self.logic_type = "boolean"
        self.backend_type = "polars"
    
    # Only need to implement the actual processing methods
    def _process_logical(self, node):
        return f"pl.{node.operator}(...)"
    
    def _process_column(self, node):
        return f"pl.col('{node.column_name}').{node.operator}({node.value})"
    
    def _process_literal(self, node):
        return f"pl.lit({node.value})"


if __name__ == "__main__":
    demonstrate_ultra_simple_pattern()