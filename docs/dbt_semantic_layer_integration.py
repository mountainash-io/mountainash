"""
Proof of Concept: mountainash-expressions + dbt Semantic Layer SDK Integration

This demonstrates how mountainash-expressions can enhance the dbt Semantic Layer SDK
with sophisticated expression building, ternary logic, and cross-backend support.
"""

from typing import Dict, List, Optional, Any
import polars as pl
import pandas as pd
from dbtsl import SemanticLayerClient
from dbtsl.lib.models import Metric, Dimension

from mountainash_expressions.logic.ternary import (
    TernaryExpressionBuilder,
    TernaryLogicalExpressionNode,
    TernaryColumnExpressionNode
)
from mountainash_expressions.logic.boolean import (
    BooleanExpressionBuilder,
    BooleanLogicalExpressionNode
)


class SemanticLayerExpressionIntegration:
    """
    Bridges dbt Semantic Layer SDK with mountainash-expressions for enhanced
    query building and data processing capabilities.
    """
    
    def __init__(self, sl_client: SemanticLayerClient):
        self.client = sl_client
        self.metadata_cache = {}
    
    def build_typed_filter(
        self, 
        metric_name: str, 
        conditions: Dict[str, Any],
        use_ternary: bool = True
    ) -> Any:
        """
        Build type-aware filter expressions from semantic layer metadata.
        
        Args:
            metric_name: Name of the metric to query
            conditions: Dictionary of dimension filters
            use_ternary: Whether to use ternary logic for UNKNOWN handling
        
        Returns:
            Expression node ready for evaluation
        """
        with self.client.session():
            # Get metric metadata
            metrics = self.client.metrics()
            metric = next((m for m in metrics if m.name == metric_name), None)
            if not metric:
                raise ValueError(f"Metric '{metric_name}' not found")
            
            # Load dimensions for type information
            dimensions = metric.dimensions
            
            # Build expressions based on dimension types
            expr_builder = TernaryExpressionBuilder if use_ternary else BooleanExpressionBuilder
            expressions = []
            
            for dim in dimensions:
                if dim.name in conditions:
                    value = conditions[dim.name]
                    
                    # Handle different dimension types
                    if dim.data_type == "NUMERIC":
                        if isinstance(value, dict):
                            if "min" in value and "max" in value:
                                expressions.append(
                                    expr_builder.between(dim.name, value["min"], value["max"])
                                )
                            elif "gt" in value:
                                expressions.append(
                                    expr_builder.gt(dim.name, value["gt"])
                                )
                            elif "lt" in value:
                                expressions.append(
                                    expr_builder.lt(dim.name, value["lt"])
                                )
                        else:
                            expressions.append(
                                expr_builder.eq(dim.name, value)
                            )
                    
                    elif dim.data_type == "TIME":
                        if isinstance(value, dict) and "start" in value and "end" in value:
                            expressions.append(
                                expr_builder.between(dim.name, value["start"], value["end"])
                            )
                        else:
                            expressions.append(
                                expr_builder.eq(dim.name, value)
                            )
                    
                    elif dim.data_type == "CATEGORICAL":
                        if isinstance(value, list):
                            expressions.append(
                                expr_builder.in_(dim.name, value)
                            )
                        else:
                            expressions.append(
                                expr_builder.eq(dim.name, value)
                            )
            
            # Combine all expressions with AND
            if len(expressions) == 0:
                return None
            elif len(expressions) == 1:
                return expressions[0]
            else:
                return expr_builder.and_(*expressions)
    
    def query_with_post_processing(
        self,
        metrics: List[str],
        group_by: List[str],
        sl_filters: Optional[Dict] = None,
        post_process_expr: Optional[Any] = None,
        backend: str = "polars"
    ) -> Any:
        """
        Query semantic layer and apply post-processing expressions.
        
        Args:
            metrics: List of metric names to query
            group_by: List of dimensions to group by
            sl_filters: Filters to apply at semantic layer level
            post_process_expr: mountainash expression for local filtering
            backend: DataFrame backend for post-processing ("polars", "pandas")
        
        Returns:
            Processed DataFrame
        """
        with self.client.session():
            # Execute semantic layer query
            arrow_table = self.client.query(
                metrics=metrics,
                group_by=group_by,
                where=sl_filters or {}
            )
            
            # Convert to desired backend
            if backend == "polars":
                df = pl.from_arrow(arrow_table)
            elif backend == "pandas":
                df = arrow_table.to_pandas()
            else:
                raise ValueError(f"Unsupported backend: {backend}")
            
            # Apply post-processing expression if provided
            if post_process_expr:
                # Use appropriate evaluation based on expression type
                if hasattr(post_process_expr, 'eval_maybe_true'):
                    # Ternary expression - handle UNKNOWN values
                    filter_func = post_process_expr.eval_maybe_true()
                else:
                    # Boolean expression
                    filter_func = post_process_expr.eval_is_true()
                
                df = filter_func(df)
            
            return df
    
    def generate_data_quality_rules(
        self, 
        semantic_model_name: str,
        use_ternary: bool = True
    ) -> Any:
        """
        Generate data quality validation rules from semantic model metadata.
        
        Args:
            semantic_model_name: Name of the semantic model
            use_ternary: Whether to use ternary logic
        
        Returns:
            Expression node with validation rules
        """
        with self.client.session():
            models = self.client.semantic_models()
            model = next((m for m in models if m.name == semantic_model_name), None)
            
            if not model:
                raise ValueError(f"Semantic model '{semantic_model_name}' not found")
            
            expr_builder = TernaryExpressionBuilder if use_ternary else BooleanExpressionBuilder
            rules = []
            
            # Generate rules based on measure types
            for measure in model.measures:
                if measure.agg == "sum":
                    # Sum measures should be non-negative
                    rules.append(
                        expr_builder.gte(measure.name, 0)
                    )
                elif measure.agg == "count":
                    # Count measures should be positive
                    rules.append(
                        expr_builder.gt(measure.name, 0)
                    )
                elif measure.agg == "avg":
                    # Average measures should be within reasonable bounds
                    # (this is domain-specific, using placeholder values)
                    rules.append(
                        expr_builder.between(measure.name, -1000000, 1000000)
                    )
            
            # Combine all rules
            if rules:
                return expr_builder.and_(*rules)
            return None
    
    def build_metric_filter_from_expression(
        self,
        expr: Any
    ) -> Dict[str, Any]:
        """
        Convert a mountainash expression to dbt Semantic Layer filter format.
        
        Args:
            expr: mountainash expression node
        
        Returns:
            Dictionary filter for semantic layer query
        """
        if isinstance(expr, (TernaryColumnExpressionNode, BooleanColumnExpressionNode)):
            # Simple column expression
            if expr.operator == "==":
                return {expr.column: expr.value}
            elif expr.operator == ">":
                return {expr.column: {"gt": expr.value}}
            elif expr.operator == "<":
                return {expr.column: {"lt": expr.value}}
            elif expr.operator == ">=":
                return {expr.column: {"gte": expr.value}}
            elif expr.operator == "<=":
                return {expr.column: {"lte": expr.value}}
            elif expr.operator == "in":
                return {expr.column: {"in": expr.value}}
        
        elif isinstance(expr, (TernaryLogicalExpressionNode, BooleanLogicalExpressionNode)):
            if expr.operator == "AND":
                # Merge all child filters
                result = {}
                for child in expr.children:
                    child_filter = self.build_metric_filter_from_expression(child)
                    result.update(child_filter)
                return result
            elif expr.operator == "OR":
                # OR is not directly supported by simple dict filters
                # Would need to use advanced expression syntax
                raise NotImplementedError("OR filters require advanced expression syntax")
        
        return {}


# Example Usage
def demonstrate_integration():
    """
    Comprehensive example showing the integration in action.
    """
    # Initialize semantic layer client
    sl_client = SemanticLayerClient(
        environment_id=123,
        auth_token="<your-token>",
        host="semantic-layer.cloud.getdbt.com"
    )
    
    # Create integration bridge
    integration = SemanticLayerExpressionIntegration(sl_client)
    
    # Example 1: Build typed filters from metadata
    print("Example 1: Typed Filter Building")
    revenue_filter = integration.build_typed_filter(
        metric_name="total_revenue",
        conditions={
            "region": ["US", "CA", "UK"],
            "customer_tier": "premium",
            "order_date": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            }
        },
        use_ternary=True  # Handle UNKNOWN values gracefully
    )
    print(f"Generated filter expression: {revenue_filter}")
    
    # Example 2: Query with post-processing
    print("\nExample 2: Query with Post-Processing")
    
    # Build complex business rule for post-processing
    high_value_rule = TernaryLogicalExpressionNode("AND", [
        TernaryColumnExpressionNode("revenue", ">", 100000),
        TernaryColumnExpressionNode("customer_count", ">", 50),
        TernaryColumnExpressionNode("growth_rate", ">", 0.1)
    ])
    
    # Execute query and apply rule
    result_df = integration.query_with_post_processing(
        metrics=["revenue", "customer_count", "growth_rate"],
        group_by=["region", "metric_time"],
        sl_filters={"country": "US"},  # Simple filter at SL level
        post_process_expr=high_value_rule,  # Complex rule locally
        backend="polars"
    )
    print(f"Filtered results shape: {result_df.shape}")
    
    # Example 3: Generate data quality rules
    print("\nExample 3: Data Quality Rules Generation")
    quality_rules = integration.generate_data_quality_rules(
        semantic_model_name="orders",
        use_ternary=True
    )
    print(f"Generated quality rules: {quality_rules}")
    
    # Example 4: Combine semantic metadata with business logic
    print("\nExample 4: Metadata-Driven Business Rules")
    
    # Build expression that combines semantic layer awareness with business logic
    with sl_client.session():
        # Get available dimensions for a metric
        metrics = sl_client.metrics()
        revenue_metric = next(m for m in metrics if m.name == "revenue")
        
        # Build expression based on available dimensions
        expressions = []
        for dim in revenue_metric.dimensions:
            if dim.data_type == "CATEGORICAL" and dim.name == "status":
                # Only include active status
                expressions.append(
                    TernaryExpressionBuilder.eq(dim.name, "active")
                )
            elif dim.data_type == "NUMERIC" and "score" in dim.name:
                # High scores only
                expressions.append(
                    TernaryExpressionBuilder.gt(dim.name, 700)
                )
        
        combined_rule = TernaryExpressionBuilder.and_(*expressions)
        
        # Convert to semantic layer filter
        sl_filter = integration.build_metric_filter_from_expression(combined_rule)
        print(f"Semantic layer filter: {sl_filter}")


if __name__ == "__main__":
    # This would run the demonstration with a real semantic layer connection
    # demonstrate_integration()
    
    # For testing without connection, show the integration structure
    print("Integration Points:")
    print("1. Typed filter building from semantic metadata")
    print("2. Post-query processing with complex expressions")
    print("3. Data quality rule generation")
    print("4. Expression to semantic layer filter conversion")
    print("5. Ternary logic for real-world UNKNOWN handling")