# Extension Points

Mountainash exposes three registries that let third-party code extend the relation AST without forking the core: `RelationVisitRegistry`, `OptimisationRegistry`, and the `PipelineStorage` protocol. The pipelines module is the canonical reference consumer of all three.

> **Stability:** Public extension points but not yet versioned. The signatures below are accurate as of the current `develop` branch.

## When to use what

| You want to… | Use |
|--------------|-----|
| Add a new `RelationNode` subclass and tell the visitor how to compile it | `RelationVisitRegistry` |
| Rewrite the AST before the visitor runs (algebraic optimisation, predicate pushdown, parameter folding, …) | `OptimisationRegistry` |
| Plug a custom cache into the pipeline runner | `PipelineStorage` |
| Add a new operation to existing nodes (e.g. a new scalar function on `ScalarFunctionNode`) | Not these — see [adding-operations.md](adding-operations.md) |

## `RelationVisitRegistry` — custom node types

Define a custom `RelationNode` subclass with an `accept(visitor)` method, then register a handler that takes `(node, visitor)` and returns the backend-native result.

```python
from typing import Any, ClassVar
from pydantic import ConfigDict

from mountainash.core.constants import CONST_BACKEND
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.unified_visitor.visit_registry import RelationVisitRegistry


class MyCustomRelNode(RelationNode):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)
    _leaf_backend: ClassVar[CONST_BACKEND | None] = CONST_BACKEND.POLARS

    step_name: str
    payload: dict[str, Any]

    def accept(self, visitor: Any) -> Any:
        return visitor.visit(self)


def _visit_my_node(node: MyCustomRelNode, visitor: Any) -> Any:
    # Build / fetch the backend-native frame here.
    return _materialise(node)


RelationVisitRegistry.register(MyCustomRelNode, _visit_my_node)
```

Once registered, `MyCustomRelNode` can be embedded anywhere a `RelationNode` is expected, and `relation.collect()` will dispatch to your handler when it encounters it.

**Reference implementation:** `src/mountainash/pipelines/integration/relation.py` registers `PipelineStepRelNode` and `ParamsRelNode` via `register_pipeline_bridge()`.

### Rules

- The handler must be a pure function (or a method captured into a free function) — the registry stores it as a callable.
- The handler must call `visitor.visit(child)` for any child `RelationNode` it wants the visitor to process.
- For leaf nodes (no upstream input), set `_leaf_backend` to declare which backend's native frame the handler returns. The visitor uses this to choose the right backend system when the rest of the plan is backend-agnostic.

## `OptimisationRegistry` — AST rewrites

Register a function that takes a node and returns either the same node or a rewritten one. The optimiser walks the tree post-order and applies registered handlers when their target node type matches.

```python
from mountainash.relations.core.relation_api.optimisation_registry import register_optimisation


def fold_my_thing(node: MyCustomRelNode) -> Any:
    # Inspect node.input, node.options, …
    # Return a rewritten node (or the same node if no rewrite applies).
    if _can_collapse(node):
        return node.input
    return node


register_optimisation(MyCustomRelNode, fold_my_thing)
```

Optimisations run before the visitor compiles the plan. Registered handlers fire each time `.collect()` is invoked, so they must be idempotent and side-effect-free.

**Reference implementation:** `register_params_optimisation()` in `src/mountainash/pipelines/integration/relation.py` registers `fold_params` against `ParamsRelNode`. The optimiser folds `ParamsRelNode(input=PipelineStepRelNode(…))` into a `PipelineStepRelNode` with merged `bound_params`.

### Rules

- Return the same node unchanged when your rewrite does not apply. **Do not** raise or return `None`.
- A rewrite that returns a different node type changes the visitor dispatch — make sure the new node has a handler registered.
- Don't introduce cycles. If your rewrite produces a node that itself triggers your rewrite, you'll loop forever; the optimiser does not detect this.

## `PipelineStorage` protocol — custom caches

```python
from typing import Protocol


class PipelineStorage(Protocol):
    def get(self, cache_key: str) -> Any | None: ...
    def put(self, cache_key: str, value: Any) -> None: ...
    def has(self, cache_key: str) -> bool: ...
    def delete(self, cache_key: str) -> None: ...
```

Built-in implementations: `MemoryPipelineStorage`, `FileSystemPipelineStorage`, `DualPipelineStorage` (memory + disk fallback).

Pass an instance to `SimplePipelineRunner(pipeline, pipeline_storage=…)` or to a custom executor via `source(..., executor=...)`.

### Cache-key contract

Cache keys are derived from `(pipeline_name, step_name, version, sorted(bound_params), upstream_cache_keys)`. If your storage wraps a system that needs different keying (e.g. content-addressed), do the translation inside `get`/`put`/`has`.

## Other extension surfaces

These exist but are out of scope for this guide; see the relevant module:

- **`CustomTypeRegistry`** (`typespec.custom_types`) — register new semantic types with TypeSpec.
- **`ResolverRegistry`** (`pipelines.resolution`) — multi-tenant pipeline resolution.
- **Function key registries** (`expressions.core.expression_system.function_keys`) — for adding scalar/aggregate/window functions, see [adding-operations.md](adding-operations.md) (six-step process).

## Testing your extension

Cross-backend coverage is enforced by the wiring-verification suite for in-tree operations; for out-of-tree extensions, write end-to-end tests that call `relation(...).my_new_thing(...).to_polars()` on each backend you claim to support. Use per-backend `xfail` for known limitations.

## Pitfalls

- **Registering the same handler twice does not error.** Whichever was registered last wins. Build your registration into a single `register_*()` function and call it on import.
- **Pydantic forward refs** in `RelationNode` subclasses: avoid typed forward references to runtime-only objects. Either use `Any` or import inside `TYPE_CHECKING`.
- **`_leaf_backend` is a `ClassVar`,** not a model field. Set it at class-body scope; Pydantic will not accept it as `__init__` data.
