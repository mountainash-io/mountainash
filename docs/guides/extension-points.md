# Extension Points

Mountainash exposes three registries that let third-party code extend the relation AST without forking the core: `RelationVisitRegistry`, `OptimisationRegistry`, and the `PipelineStorage` protocol. The pipelines module is the canonical reference consumer of all three. The shared-schema boundaries (native type adapters, native schema adapters, schema codecs and physical output description) are covered under [Schema extension recipes](#schema-extension-recipes); they reuse existing registries and are not a plugin framework.

> **Stability:** Public extension points but not yet versioned. The signatures below are accurate as of the current `develop` branch.

## When to use what

| You want to… | Use |
|--------------|-----|
| Add a new `RelationNode` subclass and tell the visitor how to compile it | `RelationVisitRegistry` |
| Rewrite the AST before the visitor runs (algebraic optimisation, predicate pushdown, parameter folding, …) | `OptimisationRegistry` |
| Plug a custom cache into the pipeline runner | `PipelineStorage` |
| Add a new operation to existing nodes (e.g. a new scalar function on `ScalarFunctionNode`) | Not these — see [adding-operations.md](adding-operations.md) |
| Add a native dtype family, schema carrier, interchange format, or physical-schema description | [Schema extension recipes](#schema-extension-recipes) |

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

## Schema extension recipes

Schema meaning lives once, in the immutable `FieldDefinition` and the ordered `TableSchema` (`mountainash.typespec.spec`). Extensions translate at a boundary; they never reinterpret field precedence, constraints, source bindings or null-fill, and they add no backend branches to conform, validation, contracts or inference. Conform compiles conversion instructions and validation compiles checks; both execute through the ordinary expression/relation backends.

| Boundary | Contract | Registration route |
|----------|----------|--------------------|
| Native type adapter | `NativeTypeAdapter[NativeTypeT]` (`core/dtypes/protocols.py`): `from_native`, `to_native_schema`, `to_native_cast`, `parse_type_string`, `types_equal`; class attribute `target: TypeTarget` | `TypeTarget` member, then `_MODULES` and `_ADAPTER_CLASSES` in `core/dtypes/registry.py`; the `DtypeRegistry` loads the `target_*.py` module lazily and keeps one stateless instance |
| Arrow transport companion | `NativeArrowTransportAdapter[NativeTypeT, ArrowTypeT]`: `to_arrow_transport(value)` | The same adapter class implements it; `DtypeRegistry.to_arrow_transport(dtype)` selects the owner of a native refinement by its `TypeTarget`, not by execution backend |
| Native schema adapter | `NativeSchemaAdapter[CarrierT, NativeSchemaT]` (`typespec/protocols.py`): `extract_schema`, `decode_schema`, `encode_schema(schema, *, resolved_types)` | `NATIVE_SCHEMA_ADAPTERS.register(target, "module:Class")` in `typespec/adapter_registry.py`; fetch with `get_native_schema_adapter(target)` |
| Interchange codec | `SchemaCodec[DescriptorT]`: `decode(descriptor) -> TableSchema`, `encode(schema) -> DescriptorT` | `SCHEMA_CODECS.register("format", "module:Class")`; fetch with `get_schema_codec("format")` |
| Physical output description | `RelationSystem.describe_output_schema(native, *, location)` (`relations/core/relation_protocols/relsys_base.py`) | The relation system already registered with `@register_relation_system(CONST_BACKEND.X)`; no new registry |

Registrations are lazy `"module:attribute"` strings: importing declarations or one codec does not import every optional library, and there is no entry-point or filesystem discovery.

### Recipes

**New native dtype family.** Add the `TypeTarget` member, a `target_<name>.py` module holding one stateless adapter class that explicitly subclasses `NativeTypeAdapter` (and implements `to_arrow_transport` if it can be a native refinement), and the two registry map entries. Add `detect_target` recognition (`_MODULE_PREFIX_TO_TARGET` in `core/dtypes/targets.py`) if native dtype objects must be recognised. A dtype family is not an execution backend, and Python-type support does not imply a table adapter; `TypeTarget` is deliberately distinct from `CONST_BACKEND`.

**New table/schema carrier.** Implement a `NativeSchemaAdapter` (reuse the existing type adapter for its dtypes), register it in `NATIVE_SCHEMA_ADAPTERS`, and extend central carrier recognition once in `detect_schema_carrier` (`core/types.py`). `extract_source_shapes(native)` then reaches it; consumers must not add their own recognition. Recognition is by schema representation, independent of execution placement: a pandas frame has a pandas schema even when it executes through Narwhals.

**New execution backend or dialect.** Follow the existing expression/relation protocol implementation and `register_relation_system` path in [Backend architecture](backend-architecture.md); supply the native type/schema adapters its representations need. Implement `describe_output_schema` only where the native carrier's schema is not its physical output; `BaseRelationSystem` already derives it from the schema adapter, and the Ibis system overrides it with backend-local, private dialect inspectors (`relations/backends/relation_systems/ibis/schema_metadata.py`, selected by the location's dialect). A new SQL dialect adds a private technique there; it adds no registry, hierarchy or public setting, and schema declarations, codecs and resolution are untouched.

**New interchange format.** Implement `SchemaCodec` with the format's own vocabulary and wire validation, and register it under an explicit format key. Frictionless is the only registered format (`"frictionless"`, `FrictionlessSchemaCodec`); `TableSchema.from_frictionless()` / `to_frictionless()` delegate to it. A codec is a pure import/export over resolved mappings: no file, network or reference resolution, no backend selection.

**Reader/file dialect changes** (delimiter, quote) stay in resource/reader dialect handling; they are not type targets or SQL dialects.

### Verification obligations

Two kinds of evidence exist, and neither substitutes for the other.

- **Registration/protocol alignment** (structural): `tests/core/test_protocol_alignment.py` and `tests/core/dtypes/test_completeness.py` check that adapters fulfil the protocols with matching parameter names, that registered keys are reachable, and that inherited protocol stubs do not count as implementations. They do not prove that any conversion is correct.
- **Behavioural tests**: supply cases for precision, nesting, unknown evidence, extraction, interchange fidelity (through serialized JSON text for codecs) and consumer consistency, with expected values taken from the declared contract rather than from the helper under test.

Implemented support is not the same as qualified support: a path that is compiled or rendered but not executed (for example an unavailable service dialect) is unexecuted, not qualified, and optional dependencies that are absent in an environment leave their implementations unqualified. Final contract qualification is tracked in the central plan, not claimed by this guide.

Smoke check of the registration surface:

```python
from mountainash.core.dtypes import TypeTarget
from mountainash.typespec.adapter_registry import get_native_schema_adapter, get_schema_codec
from mountainash.typespec.spec import TableSchema

schema = TableSchema.from_simple_dict({"id": "integer", "name": "string"})
codec = get_schema_codec("frictionless")
descriptor = codec.encode(schema)
assert [f["name"] for f in descriptor["fields"]] == ["id", "name"]
assert list(codec.decode(descriptor).fields) == ["id", "name"]
assert get_native_schema_adapter(TypeTarget.POLARS) is get_native_schema_adapter(TypeTarget.POLARS)
```

## Other extension surfaces

These exist but are out of scope for this guide; see the relevant module:

- **`CustomTypeRegistry`** (`typespec.custom_types`) — register new semantic types for `FieldDefinition` declarations.
- **`ResolverRegistry`** (`pipelines.resolution`) — multi-tenant pipeline resolution.
- **Function key registries** (`expressions.core.expression_system.function_keys`) — for adding scalar/aggregate/window functions, see [adding-operations.md](adding-operations.md) (six-step process).

## Testing your extension

Cross-backend coverage is enforced by the wiring-verification suite for in-tree operations; for out-of-tree extensions, write end-to-end tests that call `relation(...).my_new_thing(...).to_polars()` on each backend you claim to support. Use per-backend `xfail` for known limitations.

## Pitfalls

- **Registering the same handler twice does not error.** Whichever was registered last wins. Build your registration into a single `register_*()` function and call it on import.
- **Pydantic forward refs** in `RelationNode` subclasses: avoid typed forward references to runtime-only objects. Either use `Any` or import inside `TYPE_CHECKING`.
- **`_leaf_backend` is a `ClassVar`,** not a model field. Set it at class-body scope; Pydantic will not accept it as `__init__` data.
