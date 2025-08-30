# mountainash-semantic-layer Package Structure

A bridge package that integrates mountainash-expressions with various semantic layer APIs.

## Package Structure

```
mountainash-semantic-layer/
├── pyproject.toml
├── README.md
├── src/
│   └── mountainash_semantic_layer/
│       ├── __init__.py
│       ├── base/
│       │   ├── __init__.py
│       │   ├── adapter.py              # Abstract base adapter
│       │   ├── metadata_mapper.py      # Common metadata mapping
│       │   └── expression_converter.py # Expression conversion interface
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── dbt/
│       │   │   ├── __init__.py
│       │   │   ├── dbt_adapter.py      # dbt Semantic Layer adapter
│       │   │   ├── dbt_converter.py    # dbt-specific conversions
│       │   │   └── dbt_metadata.py     # dbt metadata handling
│       │   ├── cube/
│       │   │   ├── __init__.py
│       │   │   ├── cube_adapter.py     # Cube.js adapter
│       │   │   └── cube_converter.py   # Cube-specific conversions
│       │   ├── metriql/
│       │   │   ├── __init__.py
│       │   │   ├── metriql_adapter.py  # MetriQL adapter
│       │   │   └── metriql_converter.py
│       │   ├── looker/
│       │   │   ├── __init__.py
│       │   │   ├── lookml_adapter.py   # LookML adapter
│       │   │   └── lookml_converter.py
│       │   └── malloy/
│       │       ├── __init__.py
│       │       ├── malloy_adapter.py   # Malloy adapter
│       │       └── malloy_converter.py
│       ├── builders/
│       │   ├── __init__.py
│       │   ├── metric_expression_builder.py  # Build expressions from metrics
│       │   ├── dimension_validator.py        # Validate dimensions
│       │   └── query_optimizer.py           # Optimize queries
│       ├── processors/
│       │   ├── __init__.py
│       │   ├── post_processor.py       # Post-query processing
│       │   ├── data_quality.py         # Data quality rules
│       │   └── cache_manager.py        # Metadata caching
│       └── utils/
│           ├── __init__.py
│           ├── type_mapping.py         # Map semantic types to expression types
│           └── filter_translator.py    # Translate between filter formats
└── tests/
    ├── test_dbt_adapter.py
    ├── test_cube_adapter.py
    └── ...
```

## Core Components

### 1. Base Adapter Interface

```python
# src/mountainash_semantic_layer/base/adapter.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from mountainash_expressions.logic.core import ExpressionNode

class SemanticLayerAdapter(ABC):
    """Abstract base for semantic layer adapters."""
    
    @abstractmethod
    def connect(self, **config) -> None:
        """Connect to the semantic layer."""
        pass
    
    @abstractmethod
    def get_metrics(self) -> List[Dict]:
        """Retrieve available metrics."""
        pass
    
    @abstractmethod
    def get_dimensions(self, metric: str) -> List[Dict]:
        """Get dimensions for a metric."""
        pass
    
    @abstractmethod
    def build_expression(
        self, 
        metric: str, 
        filters: Dict,
        use_ternary: bool = True
    ) -> ExpressionNode:
        """Build mountainash expression from metadata."""
        pass
    
    @abstractmethod
    def convert_to_native_filter(
        self, 
        expression: ExpressionNode
    ) -> Any:
        """Convert expression to native filter format."""
        pass
    
    @abstractmethod
    def query(
        self,
        metrics: List[str],
        dimensions: List[str],
        expression: Optional[ExpressionNode] = None
    ) -> Any:
        """Execute query with expression-based filtering."""
        pass
```

### 2. dbt Semantic Layer Adapter

```python
# src/mountainash_semantic_layer/adapters/dbt/dbt_adapter.py
from dbtsl import SemanticLayerClient
from mountainash_expressions.logic.ternary import TernaryExpressionBuilder
from mountainash_expressions.logic.boolean import BooleanExpressionBuilder
from ...base import SemanticLayerAdapter

class DbtSemanticLayerAdapter(SemanticLayerAdapter):
    """Adapter for dbt Semantic Layer."""
    
    def __init__(self):
        self.client = None
        self.metadata_cache = {}
    
    def connect(self, environment_id: int, auth_token: str, host: str):
        self.client = SemanticLayerClient(
            environment_id=environment_id,
            auth_token=auth_token,
            host=host
        )
    
    def build_expression(self, metric: str, filters: Dict, use_ternary: bool = True):
        """Build typed expressions from dbt semantic metadata."""
        builder = TernaryExpressionBuilder if use_ternary else BooleanExpressionBuilder
        
        with self.client.session():
            metric_obj = self._get_metric(metric)
            dimensions = metric_obj.dimensions
            
            expressions = []
            for dim in dimensions:
                if dim.name in filters:
                    expr = self._build_dimension_expression(
                        dim, filters[dim.name], builder
                    )
                    expressions.append(expr)
            
            return builder.and_(*expressions) if expressions else None
    
    def convert_to_native_filter(self, expression):
        """Convert mountainash expression to dbt filter format."""
        # Implementation for converting expressions to dbt dict filters
        pass
```

### 3. Universal Query Builder

```python
# src/mountainash_semantic_layer/builders/metric_expression_builder.py
from typing import Dict, List, Optional, Union
from mountainash_expressions.logic.core import ExpressionNode

class UniversalMetricExpressionBuilder:
    """Build expressions that work across semantic layers."""
    
    def __init__(self, adapter):
        self.adapter = adapter
    
    def build_metric_filter(
        self,
        metric: str,
        conditions: Dict,
        logic_type: str = "ternary"
    ) -> ExpressionNode:
        """Build filter expression for any semantic layer."""
        return self.adapter.build_expression(
            metric=metric,
            filters=conditions,
            use_ternary=(logic_type == "ternary")
        )
    
    def build_cross_metric_rule(
        self,
        metrics: List[str],
        rule_definition: Dict
    ) -> ExpressionNode:
        """Build complex rules across multiple metrics."""
        # Implementation for cross-metric expressions
        pass
```

### 4. Post-Processing Pipeline

```python
# src/mountainash_semantic_layer/processors/post_processor.py
import polars as pl
import pandas as pd
from mountainash_expressions.logic.core import ExpressionNode

class SemanticLayerPostProcessor:
    """Apply expressions to semantic layer query results."""
    
    def __init__(self, adapter):
        self.adapter = adapter
    
    def query_and_process(
        self,
        metrics: List[str],
        dimensions: List[str],
        pre_filter: Optional[Dict] = None,
        post_expression: Optional[ExpressionNode] = None,
        backend: str = "polars"
    ):
        """Query semantic layer and apply post-processing."""
        # Query with pre-filters
        result = self.adapter.query(
            metrics=metrics,
            dimensions=dimensions,
            expression=self.adapter.build_expression(metrics[0], pre_filter) if pre_filter else None
        )
        
        # Convert to desired backend
        if backend == "polars":
            df = pl.from_arrow(result) if hasattr(result, 'to_arrow') else result
        elif backend == "pandas":
            df = pd.DataFrame(result) if not isinstance(result, pd.DataFrame) else result
        
        # Apply post-processing expression
        if post_expression:
            filter_func = (
                post_expression.eval_maybe_true() 
                if hasattr(post_expression, 'eval_maybe_true')
                else post_expression.eval_is_true()
            )
            df = filter_func(df)
        
        return df
```

## pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mountainash-semantic-layer"
version = "0.1.0"
description = "Bridge between mountainash-expressions and semantic layer APIs"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "mountainash-expressions>=0.1.0",
    "typing-extensions>=4.5.0",
]

[project.optional-dependencies]
dbt = [
    "dbt-sl-sdk[sync]>=0.11.0",
]
cube = [
    "cube-client>=0.1.0",  # hypothetical
]
metriql = [
    "metriql-client>=0.1.0",  # hypothetical
]
looker = [
    "looker-sdk>=22.0.0",
]
malloy = [
    "malloy-py>=0.1.0",  # hypothetical
]
all = [
    "mountainash-semantic-layer[dbt,cube,metriql,looker,malloy]",
]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.10.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/mountainash-semantic-layer"
Documentation = "https://mountainash-semantic-layer.readthedocs.io"
Repository = "https://github.com/yourusername/mountainash-semantic-layer"
```

## Usage Examples

```python
from mountainash_semantic_layer import SemanticLayerFactory
from mountainash_expressions.logic.ternary import TernaryExpressionBuilder

# Initialize adapter for your semantic layer
adapter = SemanticLayerFactory.create("dbt", 
    environment_id=123,
    auth_token="token",
    host="semantic-layer.cloud.getdbt.com"
)

# Build expression from semantic metadata
expression = adapter.build_expression(
    metric="revenue",
    filters={
        "region": ["US", "CA"],
        "customer_tier": "premium",
        "order_value": {"min": 1000, "max": 10000}
    },
    use_ternary=True  # Handle UNKNOWN values
)

# Query with expression-based filtering
result = adapter.query(
    metrics=["revenue", "customer_count"],
    dimensions=["region", "metric_time"],
    expression=expression
)

# Or use the universal builder
from mountainash_semantic_layer.builders import UniversalMetricExpressionBuilder

builder = UniversalMetricExpressionBuilder(adapter)
complex_rule = builder.build_cross_metric_rule(
    metrics=["revenue", "churn_rate"],
    rule_definition={
        "type": "high_value_at_risk",
        "revenue_threshold": 100000,
        "churn_risk_threshold": 0.3
    }
)

# Post-process results with complex expressions
from mountainash_semantic_layer.processors import SemanticLayerPostProcessor

processor = SemanticLayerPostProcessor(adapter)
filtered_df = processor.query_and_process(
    metrics=["revenue", "customer_count", "churn_rate"],
    dimensions=["region", "customer_segment"],
    pre_filter={"country": "US"},  # Simple filter at semantic layer
    post_expression=complex_rule,   # Complex expression locally
    backend="polars"
)
```

## Supported Semantic Layers

- **dbt Semantic Layer**: Full support with type-aware expression building
- **Cube.js**: Build expressions from Cube schema definitions
- **MetriQL**: Convert MetriQL models to expressions
- **Looker/LookML**: Generate expressions from LookML explores
- **Malloy**: Build expressions from Malloy semantic models

## Key Features

1. **Unified Interface**: Single API for multiple semantic layers
2. **Type-Safe Expressions**: Build expressions based on semantic metadata
3. **Ternary Logic**: Handle UNKNOWN values in real-world data
4. **Query Optimization**: Push filters to semantic layer when possible
5. **Post-Processing**: Apply complex rules after semantic layer queries
6. **Metadata Caching**: Efficient metadata retrieval and caching
7. **Cross-Backend Support**: Works with pandas, polars, Ibis, PyArrow