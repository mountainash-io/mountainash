"""
Simplified Visitor Template Pattern

This example demonstrates the new simplified visitor implementation where
the conversion system handles all decision logic, and visitors do minimal work.
"""

from typing import Any
from mountainash_expressions.logic.ternary import (
    should_delegate_to_alternate_logic,
    should_convert_node,
    convert_expression,
    create_delegate_visitor
)


class SimplifiedBooleanVisitor:
    """
    Example visitor implementation with minimal logic.
    
    The visitor delegates all decision-making to the conversion system
    and focuses only on backend-specific expression generation.
    """
    
    def __init__(self, table: Any):
        self.table = table
        self.logic_type = "boolean"
    
    def visit_logical_expression(self, node):
        """
        Simplified visit method - conversion system handles all decisions.
        """
        # Let the conversion system decide what to do
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        # Convert node if needed
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
        
        # Delegate to alternate visitor if needed  
        if visitor_delegate_required:
            delegate_visitor = create_delegate_visitor(self.table, "ternary", self)
            return node.accept(delegate_visitor)
        
        # Otherwise continue with normal processing
        return self._process_boolean_logical_node(node)
    
    def visit_column_expression(self, node):
        """Example column expression handler."""
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = create_delegate_visitor(self.table, "ternary", self)
            return node.accept(delegate_visitor)
            
        return self._process_boolean_column_node(node)
    
    def visit_literal_expression(self, node):
        """Example literal expression handler.""" 
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = create_delegate_visitor(self.table, "ternary", self)
            return node.accept(delegate_visitor)
            
        return self._process_boolean_literal_node(node)
    
    def _process_boolean_logical_node(self, node):
        """Backend-specific boolean logical processing."""
        # This is where actual backend-specific code goes
        return f"boolean_logical({node.operator})"
    
    def _process_boolean_column_node(self, node):
        """Backend-specific boolean column processing."""
        return f"boolean_column({node.column_name}, {node.operator}, {node.value})"
    
    def _process_boolean_literal_node(self, node):
        """Backend-specific boolean literal processing."""
        return f"boolean_literal({node.value})"


class SimplifiedTernaryVisitor:
    """
    Example ternary visitor with the same simplified pattern.
    """
    
    def __init__(self, table: Any):
        self.table = table
        self.logic_type = "ternary"
    
    def visit_logical_expression(self, node):
        """Simplified ternary logical expression handler."""
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = create_delegate_visitor(self.table, "boolean", self)
            return node.accept(delegate_visitor)
            
        return self._process_ternary_logical_node(node)
    
    def visit_column_expression(self, node):
        """Simplified ternary column expression handler."""
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = create_delegate_visitor(self.table, "boolean", self)
            return node.accept(delegate_visitor)
            
        return self._process_ternary_column_node(node)
    
    def visit_literal_expression(self, node):
        """Simplified ternary literal expression handler."""
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            delegate_visitor = create_delegate_visitor(self.table, "boolean", self)
            return node.accept(delegate_visitor)
            
        return self._process_ternary_literal_node(node)
    
    def _process_ternary_logical_node(self, node):
        """Backend-specific ternary logical processing."""
        return f"ternary_logical({node.operator})"
    
    def _process_ternary_column_node(self, node):
        """Backend-specific ternary column processing."""
        return f"ternary_column({node.column_name}, {node.operator}, {node.value})"
    
    def _process_ternary_literal_node(self, node):
        """Backend-specific ternary literal processing."""
        return f"ternary_literal({node.value})"


def demonstrate_simplified_pattern():
    """
    Demonstrate the benefits of the simplified visitor pattern.
    """
    print("=== Simplified Visitor Template Pattern ===\n")
    
    print("Benefits of this pattern:")
    print("1. ✓ Visitors contain minimal logic - just delegation and backend-specific processing")
    print("2. ✓ All decision-making is centralized in the conversion system")
    print("3. ✓ Consistent behavior across all visitor implementations")
    print("4. ✓ Easy to maintain and extend")
    print("5. ✓ Clear separation of concerns")
    
    print(f"\nVisitor template structure:")
    print("```python")
    print("def visit_*_expression(self, node):")
    print("    visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)")
    print("    node_conversion_required = should_convert_node(node, self.logic_type)")
    print("    ")
    print("    if node_conversion_required:")
    print("        node = convert_expression(node, self.logic_type)")
    print("    ")
    print("    if visitor_delegate_required:")
    print("        delegate_visitor = create_delegate_visitor(self.table, target_logic_type, self)")
    print("        return node.accept(delegate_visitor)")
    print("    ")
    print("    # Otherwise continue with backend-specific processing")
    print("    return self._process_*_node(node)")
    print("```")
    
    print(f"\nConversion system handles:")
    print("• When to delegate vs when to convert")
    print("• Which nodes are booleanizing operations") 
    print("• Cross-logic type compatibility")
    print("• Backend consistency during delegation")
    
    print(f"\nVisitor focuses only on:")
    print("• Backend-specific expression generation")
    print("• Actual DataFrame/table operations")
    print("• Performance optimization for their backend")


# Template mixin class for even easier implementation
class VisitorTemplateMixin:
    """
    Mixin class that provides the standard visitor template logic.
    
    Visitors can inherit from this to get the standard delegation/conversion
    pattern without implementing it repeatedly.
    """
    
    def _handle_cross_logic_expression(self, node):
        """
        Standard cross-logic expression handling template.
        
        This method implements the pattern you specified and can be called
        by any visit_*_expression method.
        """
        visitor_delegate_required = should_delegate_to_alternate_logic(node, self.logic_type)
        node_conversion_required = should_convert_node(node, self.logic_type)
        
        if node_conversion_required:
            node = convert_expression(node, self.logic_type)
            
        if visitor_delegate_required:
            # Determine target logic type (opposite of current)
            target_logic_type = "ternary" if self.logic_type == "boolean" else "boolean"
            delegate_visitor = create_delegate_visitor(self.table, target_logic_type, self)
            return node.accept(delegate_visitor)
        
        # Return None to indicate normal processing should continue
        return None
    
    def visit_logical_expression(self, node):
        """Template method using the mixin pattern."""
        result = self._handle_cross_logic_expression(node)
        if result is not None:
            return result
        return self._process_logical_node(node)
    
    def visit_column_expression(self, node):
        """Template method using the mixin pattern."""
        result = self._handle_cross_logic_expression(node)
        if result is not None:
            return result
        return self._process_column_node(node)
    
    def visit_literal_expression(self, node):
        """Template method using the mixin pattern."""
        result = self._handle_cross_logic_expression(node)
        if result is not None:
            return result
        return self._process_literal_node(node)
    
    # Abstract methods that concrete visitors must implement
    def _process_logical_node(self, node):
        raise NotImplementedError("Concrete visitor must implement _process_logical_node")
    
    def _process_column_node(self, node):
        raise NotImplementedError("Concrete visitor must implement _process_column_node")
        
    def _process_literal_node(self, node):
        raise NotImplementedError("Concrete visitor must implement _process_literal_node")


class ExamplePolarsVisitorWithMixin(VisitorTemplateMixin):
    """Example of using the mixin for even simpler visitor implementation."""
    
    def __init__(self, table):
        self.table = table
        self.logic_type = "boolean"
    
    def _process_logical_node(self, node):
        """Only need to implement backend-specific logic."""
        return f"pl.col(...).{node.operator}(...)"
    
    def _process_column_node(self, node):
        """Only need to implement backend-specific logic."""
        return f"pl.col('{node.column_name}').{node.operator}({node.value})"
    
    def _process_literal_node(self, node):
        """Only need to implement backend-specific logic."""
        return f"pl.lit({node.value})"


if __name__ == "__main__":
    demonstrate_simplified_pattern()