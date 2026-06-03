---
title: Pipeline Framework
description: Declarative multi-step pipelines with PipelineBuilder, step decorators, parameter binding, and the SimplePipelineRunner execution model.
generated_by: claude skill chapter-content-generator
date: 2026-06-03
version: 0.08
---

# Chapter 12: Pipeline Framework

## Summary

Declarative multi-step pipelines: PipelineBuilder, step decorator, source function, PipelineSpec, StepDefinition, StepContext, StepResult, SimplePipelineRunner, ParamSpec, parameter binding, relation.params method, and fold_params.

## Concepts Covered

- PipelineBuilder
- step Decorator
- source Function
- PipelineSpec
- StepDefinition
- StepContext
- StepResult
- SimplePipelineRunner
- ParamSpec
- Parameter Binding
- relation.params Method
- fold_params Function

## Prerequisites

- [Chapter 1. Foundation Concepts](../01-foundations/)
- [Chapter 10. Relation API Core Operations](../10-relation-api-core/)

---

## Introduction

Individual relation operations handle single transformations. Real-world data processing requires orchestrating multiple steps with dependencies, parameters, and execution policies. The pipeline framework provides a declarative way to define multi-step data pipelines where each step is a function that produces a relation, steps can depend on each other, and parameters are bound at execution time rather than definition time.

## PipelineBuilder

`PipelineBuilder` is a fluent API for constructing pipeline specifications. You create a builder with a name and version, add steps to it, and call `.build()` to produce an immutable `PipelineSpec` object.

```python
from mountainash.pipelines.fluent.builder import PipelineBuilder

pipeline = (
    PipelineBuilder("customer_analytics", "1.0")
    .step("load_customers", load_fn)
    .step("filter_active", filter_fn, depends_on=["load_customers"])
    .step("compute_metrics", metrics_fn, depends_on=["filter_active"])
    .build()
)
```

The builder follows the immutable builder pattern. Each `.step()` call returns a new `PipelineBuilder` instance with the step added, leaving the original unchanged. This enables branching pipeline definitions from shared prefixes.

Key parameters for each step include:

- **name**: Unique identifier for the step
- **fn**: The function that executes the step
- **depends_on**: List of step names that must complete first
- **params**: Parameter specifications for runtime configuration
- **retry**: Retry configuration for transient failures
- **cache_ttl**: How long to cache step results
- **empty_policy**: What to do if the step produces empty output

## step Decorator

The `step` decorator marks a function as a pipeline step and associates it with metadata like dependencies and parameter specifications. Decorated functions can be passed directly to `PipelineBuilder.step()` and carry their configuration with them.

```python
from mountainash.pipelines.core.step import step

@step(depends_on=["raw_data"], params=("date_range",))
def filter_by_date(context):
    """Filter data to the configured date range."""
    start, end = context.params["date_range"]
    return (
        context.inputs["raw_data"]
        .filter(ma.col("date").ge(start) & ma.col("date").le(end))
    )
```

The decorator stores a `StepDefinition` on the function object (`fn._step_definition`). When the function is passed to `PipelineBuilder.step()`, the builder extracts this definition and uses its metadata (overriding with explicit parameters if both are provided).

## source Function

The `source` function defines the entry points of a pipeline: steps that load data from external sources rather than transforming outputs from previous steps. Source steps have no dependencies and typically wrap I/O operations (file reads, database queries, API calls).

```python
from mountainash.pipelines.fluent.source import source

@source
def load_orders():
    """Load orders from the data warehouse."""
    return ma.relation(pl.read_parquet("data/orders.parquet"))
```

Source functions differ from regular step functions in that they receive no inputs from other steps. They are the leaves of the pipeline DAG, providing the initial data that flows through downstream transformations.

## PipelineSpec

`PipelineSpec` is the immutable specification object produced by `PipelineBuilder.build()`. It captures the complete pipeline definition including all steps, their dependencies, and configuration.

```python
@dataclass
class PipelineSpec:
    name: str
    version: str
    steps: dict[str, StepDefinition]
```

The PipelineSpec is a data object, not an executor. It describes what the pipeline does but not how to run it. Execution is handled by a runner (like `SimplePipelineRunner`) that accepts a PipelineSpec and manages the actual computation.

This separation between specification and execution enables multiple execution strategies (simple sequential, parallel, distributed) to operate on the same pipeline definition.

#### Diagram: Pipeline Framework Architecture
<iframe src="../../sims/pipeline-architecture/main.html" width="100%" height="500px" scrolling="no"></iframe>
<details markdown="1">
<summary>Pipeline Framework Architecture</summary>
Type: diagram
**sim-id:** pipeline-architecture<br/>
**Library:** vis-network<br/>
**Status:** Specified

A layered architecture diagram showing three layers. Top layer: "User API" with PipelineBuilder and step decorator. Middle layer: "Specification" with PipelineSpec and StepDefinition. Bottom layer: "Execution" with SimplePipelineRunner, StepContext, and StepResult. Arrows flow downward showing how user code produces specs which are consumed by runners. Side panel shows ParamSpec connecting to both Specification and Execution layers. Interactive: clicking a component shows its fields and relationships. Colors: DarkOrchid for pipeline framework elements. Learning objective: Explain the separation between pipeline specification and execution and identify which components belong to each layer (Bloom: Understand).
</details>

## StepDefinition

`StepDefinition` captures all metadata about a single pipeline step. It is the internal representation that the runner uses to understand what each step needs and produces.

```python
@dataclass
class StepDefinition:
    name: str
    fn: Callable
    depends_on: list[str]
    params: tuple[ParamSpec, ...]
    retry: Optional[RetryConfig] = None
    cache_ttl: Optional[timedelta] = None
    empty_policy: EmptyPolicy = EmptyPolicy.WARN
```

The `depends_on` field establishes the execution order. A step can only run after all its dependencies have completed successfully. The runner uses these dependencies to determine topological order.

## StepContext

`StepContext` is the object passed to each step function at execution time. It provides access to the outputs of upstream steps (via `inputs`) and the resolved parameter values (via `params`).

```python
def my_step(context: StepContext):
    # Access outputs from upstream steps
    raw_data = context.inputs["load_data"]

    # Access resolved parameters
    threshold = context.params["min_score"]

    return raw_data.filter(ma.col("score") >= threshold)
```

The context object ensures that step functions receive only what they need: their declared dependencies' outputs and their declared parameters' values. This makes steps self-contained and testable in isolation.

## StepResult

`StepResult` captures the output of a step execution along with metadata about the execution (timing, success/failure, row counts). It is what the runner stores after each step completes.

The step result enables the runner to make decisions about downstream steps (skip if upstream failed), provide execution reports, and cache results for reuse.

## SimplePipelineRunner

`SimplePipelineRunner` is the basic execution engine for pipeline specs. It processes steps in topological order, passing outputs from completed steps to their dependents via `StepContext` objects.

```python
from mountainash.pipelines.orchestration.simple import SimplePipelineRunner

runner = SimplePipelineRunner()
results = runner.run(pipeline_spec, params={"date_range": ("2024-01-01", "2024-12-31")})
```

The runner's execution algorithm works as follows. It computes the topological order of steps from the dependency graph. For each step in order, it collects the outputs of all declared dependencies, creates a `StepContext` with those outputs and the resolved parameters, calls the step function, and stores the `StepResult`.

The simple runner executes steps sequentially. For parallel execution of independent steps, more advanced runners can be used (the runner interface is pluggable).

## ParamSpec

`ParamSpec` defines a parameter that a pipeline step accepts. It specifies the parameter name, expected type, default value, and validation rules. Parameters are resolved at execution time, allowing the same pipeline definition to be run with different configurations.

```python
from mountainash.pipelines.core.capabilities import ParamSpec

date_param = ParamSpec(
    name="start_date",
    type=str,
    default="2024-01-01",
    description="Start date for data filtering",
)
```

ParamSpecs serve as documentation and validation. They tell pipeline users what parameters are available, what types they expect, and what happens if no value is provided (the default is used).

## Parameter Binding

Parameter binding is the process of resolving `ParamSpec` declarations against actual values at execution time. When a runner starts a pipeline, it takes a dictionary of parameter values and matches them against the ParamSpec declarations of each step.

```python
# At execution time, bind parameters
results = runner.run(pipeline_spec, params={
    "start_date": "2024-06-01",
    "min_score": 75,
    "output_format": "parquet",
})
```

The binding process validates that required parameters are provided, applies defaults for missing optional parameters, and type-checks values against their ParamSpec type declarations.

## relation.params Method

The `relation.params()` method attaches parameter placeholders to a relation pipeline. These placeholders are resolved when the relation is compiled within a pipeline context, enabling parameterized relation definitions.

```python
import mountainash as ma

# Define a parameterized relation
filtered = (
    ma.relation(df)
    .params(min_age=18, max_age=65)
    .filter(
        (ma.col("age") >= ma.col("min_age")) &
        (ma.col("age") <= ma.col("max_age"))
    )
)
```

Under the hood, `.params()` creates a `ParamsRelNode` in the relational AST. During compilation within a pipeline context, these parameter references are replaced with their bound values. Outside a pipeline context, parameters must be provided explicitly.

## fold_params Function

The `fold_params` function resolves parameter placeholders in a relation AST by substituting actual values for parameter references. It walks the AST tree, finds `ParamsRelNode` instances, and replaces them with the concrete values provided.

```python
from mountainash.pipelines.integration.relation import fold_params

# Resolve parameters in a relation's AST
resolved_relation = fold_params(parameterized_relation, {
    "min_age": 21,
    "max_age": 55,
})
```

This function is the bridge between the pipeline parameter system and the relation compilation system. The runner calls `fold_params` before compiling each step's relation output, ensuring that parameter references are concrete values by the time the expression visitor encounters them.

The fold operation is idempotent: calling it on a relation with no parameter nodes produces the relation unchanged. This means it is safe to call unconditionally on any relation before compilation.

## Key Takeaways

- `PipelineBuilder` provides a fluent, immutable API for constructing pipeline specifications with named steps, dependencies, and parameters.
- The step decorator associates metadata (dependencies, params) with step functions, enabling self-documenting pipeline definitions.
- `PipelineSpec` separates specification from execution, allowing multiple runner implementations to operate on the same pipeline definition.
- `StepContext` provides step functions with their declared inputs and resolved parameters, ensuring isolation and testability.
- `SimplePipelineRunner` executes steps in topological order, managing the flow of data between steps via StepContext objects.
- `ParamSpec` defines typed, validated parameters with defaults, enabling the same pipeline to run with different configurations.
- `relation.params()` creates parameterized relation pipelines whose placeholders are resolved at execution time via `fold_params`.
- The pipeline framework builds on top of the relation system rather than replacing it: each step produces relations that compose with the standard relational operations.
