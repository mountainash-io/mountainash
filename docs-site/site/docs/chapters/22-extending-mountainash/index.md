---
title: Extending mountainash
---

# Extending mountainash

mountainash has two kinds of extension point. Some accept your own objects at run time: a relation node with its visit handler, an optimisation pass, a schema codec, a custom semantic type, pipeline units, sinks and checkpoint stores, and rules and validation checks. The others are changes to the package itself, made in a source checkout: a new expression or relation operation, a backend, capability declarations, a type or schema adapter for a new target, a Python ingress handler and a new value validator. The table lists every extension point and where its mechanism is explained.

Assumes: [Architecture](../17-architecture/index.md), [How expressions compile](../18-expression-compilation/index.md), [How relations compile](../19-relation-compilation/index.md) and [The capability spine](../20-capability-spine/index.md).

| Extension point | How it is added | Mechanism |
|---|---|---|
| Expression operation | Package change in six steps | [Adding an expression operation](#adding-an-expression-operation) |
| Relation operation | Package change | [Adding a relation operation](#adding-a-relation-operation) |
| Relation node and visit handler | Run-time registration | [Custom relation nodes](#custom-relation-nodes) |
| Optimisation pass | Run-time registration | [Optimisation passes](../19-relation-compilation/index.md#optimisation-passes) |
| Backend | Package change | [Composition and registration](../21-backends/index.md#composition-and-registration) |
| Capability declarations | Package change | [Declaring capability segments](#declaring-capability-segments) |
| Native type adapter, native schema adapter | Package change | [Type and schema adapters](#type-and-schema-adapters) |
| Schema codec | Run-time registration | [Type and schema adapters](#type-and-schema-adapters) |
| Custom semantic type | Run-time registration | [Custom semantic types](../10-table-schemas-and-datapackage/index.md#custom-semantic-types) |
| Python ingress handler | Package change | [Ingress handlers, units and rules](#ingress-handlers-units-and-rules) |
| Pipeline unit, source, sink, checkpoint store | Your own class, passed to the pipeline | [Pipelines and units](../15-pipelines/index.md#pipelines-and-units) |
| Data-contract rule | Your own object | [Writing custom rules](../12-data-contracts/index.md#writing-custom-rules) |
| Row, scalar and relation checks | Your own object | [Check IR and rule kinds](../13-validation/index.md#check-ir-and-rule-kinds) |
| Value validator | Package change | [Ingress handlers, units and rules](#ingress-handlers-units-and-rules) |

Run-time registries are process-wide: a registration lasts for the life of the interpreter, and registering a key twice raises `ValueError`. Tests that discover what exists (protocols, keys, nodes, adapters) check package changes, and fail for any new item that is unwired and absent from the known-gap lists; [Contributing and testing](../23-contributing-and-testing/index.md) describes those tests and how to run them.

## Adding an expression operation

<!-- concept:540 -->
An expression operation is added in six steps, the same for a Substrait-standard function and a mountainash extension. Each step adds the operation to one layer of the [three-layer separation](../17-architecture/index.md#three-layer-separation), and a missing step surfaces as a failing alignment test or a dispatch error. The operation's origin decides the directory at every layer: Substrait functions live under `substrait/` with `FKEY_SUBSTRAIT_*` keys, mountainash extensions under `extensions_mountainash/` with `FKEY_MOUNTAINASH_*` keys and an `ext_ma_` file infix (see [Function keys](../18-expression-compilation/index.md#function-keys)).

`fill_nan`, which replaces NaN with a value, is a compact extension operation to follow. Paths below are relative to `src/mountainash/expressions/`:

1. Function key. Add the enum member in `core/expression_system/function_keys/enums.py` (`FKEY_MOUNTAINASH_NULL.FILL_NAN`).
2. Protocols. Declare the backend method on the expression-system protocol (`MountainAshNullExpressionSystemProtocol.fill_nan` in `core/expression_protocols/expression_systems/extensions_mountainash/prtcl_expsys_ext_ma_null.py`), with `ExpressionT` parameters for arguments and keyword parameters for literal-only options, following the rule in [Expression AST nodes](../18-expression-compilation/index.md#expression-ast-nodes). Declare the user-facing method on the API builder protocol in `core/expression_protocols/api_builders/extensions_mountainash/prtcl_api_bldr_ext_ma_null.py`.
3. API builder. Implement the user-facing method that builds a `ScalarFunctionNode` carrying the new key (`MountainAshNullAPIBuilder.fill_nan` in `core/expression_api/api_builders/extensions_mountainash/api_bldr_ext_ma_null.py`).
4. Every backend. Implement the protocol method in the matching category class of each backend: `expsys_pl_ext_ma_null.py`, `expsys_nw_ext_ma_null.py` and `expsys_ib_ext_ma_null.py` under `backends/expression_systems/{polars,narwhals,ibis}/extensions_mountainash/`. A new category class also goes into each backend's composition class, whose body stays empty (see [Composition and registration](../21-backends/index.md#composition-and-registration)).
5. Function mapping. Register an `ExpressionFunctionDef` in `core/expression_system/function_mapping/definitions.py` that binds the key to the protocol method, the extension URI and name, and the output-naming rule. The [function registry](../18-expression-compilation/index.md#the-function-registry) dispatches the key only through this definition.
6. Tests. Add a cross-backend test (`tests/expressions/cross_backend/test_null_nan_clip.py`), an argument-channel case for every expression parameter (`tests/expressions/argument_types/test_arg_types_null.py`) and an AST test (`tests/expressions/ast/test_ast_null.py`).

The finished wiring is visible from outside: the key on the built node, the registry entry, and the category class in the Polars composition.

```python
import mountainash as ma
from mountainash.expressions.introspect import walk
from mountainash.expressions.core.expression_system.function_keys.enums import FKEY_MOUNTAINASH_NULL
from mountainash.expressions.core.expression_system.function_mapping.registry import (
    ExpressionFunctionRegistry,
)
from mountainash.expressions.backends.expression_systems.polars import PolarsExpressionSystem

key = FKEY_MOUNTAINASH_NULL.FILL_NAN
print([getattr(node, "function_key", None) for node in walk(ma.col("val").fill_nan(0.0))])
print(ExpressionFunctionRegistry.get_protocol_method(key).__qualname__)
print(ExpressionFunctionRegistry.get_substrait_uri(key), ExpressionFunctionRegistry.get_substrait_name(key))
print([c.__name__ for c in PolarsExpressionSystem.__mro__ if c.__name__.endswith("NullExpressionSystem")])
```

```text
[<FKEY_MOUNTAINASH_NULL.FILL_NAN: 'fill_nan'>, None, None]
MountainAshNullExpressionSystemProtocol.fill_nan
file://extensions/functions_null.yaml fill_nan
['MountainAshPolarsNullExpressionSystem']
```

A backend that cannot honour an operation keeps its implementation and test case. A [capability declaration](#declaring-capability-segments) records the limit; for a wrong result such as `fill_nan` on Ibis DuckDB (SQL engines store NaN as null), a per-backend expected failure in the test records it instead (see [Known divergences and per-backend xfail](../23-contributing-and-testing/index.md#known-divergences-and-per-backend-xfail)). The wiring audit in `tests/core/test_protocol_alignment.py` fails for a protocol method missing from a backend, a backend method with no protocol, or a key with no mapping. `KNOWN_ASPIRATIONAL` in the same file lists protocol methods that are deliberately left unwired for now, each with a reason and a date.

An alias reuses an existing operation. Short and Polars-style names (`eq`, `strip_chars`, `sub`) live only in the extension builders (`api_bldr_ext_ma_*`) and build the same node as the Substrait-canonical method in the Substrait builder (`equal`, `trim`, `subtract`), so an alias skips the key, mapping and backend steps:

```python
for expr in (ma.col("a").eq(1), ma.col("a").equal(1),
             ma.col("s").str.strip_chars(), ma.col("s").str.trim()):
    print(next(iter(walk(expr))).function_key)
```

```text
FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL
FKEY_SUBSTRAIT_SCALAR_COMPARISON.EQUAL
FKEY_SUBSTRAIT_SCALAR_STRING.TRIM
FKEY_SUBSTRAIT_SCALAR_STRING.TRIM
```

## Adding a relation operation

<!-- concept:541 -->
A relation operation follows the same pattern through the relation layers described in [Relation operation keys and registry](../19-relation-compilation/index.md#relation-operation-keys-and-registry) and [Relation systems](../19-relation-compilation/index.md#relation-systems). `drop_nulls` is the reference; paths are relative to `src/mountainash/relations/`:

1. Operation key. Add the member to `RKEY_SUBSTRAIT_REL` or `RKEY_MOUNTAINASH_REL` in `core/relation_system/relation_keys/enums.py` (`RKEY_MOUNTAINASH_REL.DROP_NULLS`).
2. Node. Reuse a node type or add one under `core/relation_nodes/substrait/` or `core/relation_nodes/extensions_mountainash/` (`reln_` prefix). Single-input utility operations share `ExtensionRelNode`, which carries the key and an options dictionary.
3. Protocols. Declare the backend method on the relation-system protocol (`MountainashExtensionRelationSystemProtocol.drop_nulls` in `core/relation_protocols/relation_systems/extensions_mountainash/prtcl_relsys_ext_ma_util.py`) and the user method in `core/relation_protocols/prtcl_relation_api.py`.
4. Relation API. Add the fluent method to `Relation` in `core/relation_api/relation.py`.
5. Every backend. Implement the method in `relsys_pl_ext_ma_util.py`, `relsys_nw_ext_ma_util.py` and `relsys_ib_ext_ma_util.py` under `backends/relation_systems/{polars,narwhals,ibis}/extensions_mountainash/`.
6. Operation mapping. Register a `RelationOperationDef` in `core/relation_system/relation_mapping/definitions.py` (for `drop_nulls`, an `_ext(...)` entry in `MOUNTAINASH_OPERATIONS`).

Relations need two more decisions than expressions. Output names and schema must be inferable from the plan alone, so a new key also goes into the name-preserving or name-changing cases in `schema_inference.py` and `schema_resolution.py`, and to the structured-lineage table in `core/structured_lineage.py`. Tests go in `tests/relations/cross_backend/` (results), `tests/relations/protocol_alignment/` and `tests/relations/test_rel_wiring_audit.py`, which fails for any node type that has neither a key nor a handler.

```python
import polars as pl
from mountainash.relations.core.relation_system.relation_mapping.registry import (
    RelationOperationRegistry,
)

rel = ma.relation(pl.DataFrame({"a": [1, None]})).drop_nulls()
node = rel._node
definition = RelationOperationRegistry.get(node.operation_key)
print(type(node).__name__, node.operation_key)
print(definition.protocol_method.__qualname__, definition.extension_uri)
print(rel.explain())
```

```text
ExtensionRelNode RKEY_MOUNTAINASH_REL.DROP_NULLS
MountainashExtensionRelationSystemProtocol.drop_nulls file://extensions/relations/mountainash_util.yaml
FILTER col("a").is_not_null()
FROM
  DF ["a"]; PROJECT */1 COLUMNS
```

## Custom relation nodes

<!-- concept:542 -->
A package outside mountainash can add a relation node at run time: subclass `RelationNode`, register a visit handler for the class in `RelationVisitRegistry`, and wrap the node in a `Relation`. The [unified relation visitor](../19-relation-compilation/index.md#the-unified-relation-visitor) checks the registry before it looks up an operation key, so it calls a registered handler with the node and the visitor. The handler visits its child, which returns the child's native result, and returns a native result of its own. Using the visitor's relation system (`visitor.backend`) and `visitor.compile_expression()` keeps the handler backend-agnostic:

```python
import ibis
from mountainash.relations.core.relation_api.relation import Relation
from mountainash.relations.core.relation_nodes.reln_base import RelationNode
from mountainash.relations.core.unified_visitor.visit_registry import RelationVisitRegistry

class EveryNthRelNode(RelationNode):
    input: RelationNode
    n: int

def visit_every_nth(node, visitor):
    native = visitor.visit(node.input)
    system = visitor.backend
    indexed = system.with_row_index(native, name="_row")
    keep = visitor.compile_expression((ma.col("_row") % node.n) == 0)
    return system.project_drop(system.filter(indexed, keep), ["_row"])

RelationVisitRegistry.register(EveryNthRelNode, visit_every_nth)

def every_nth(rel, n):
    return Relation(EveryNthRelNode(input=rel._node, n=n))

data = {"x": [10, 20, 30, 40, 50]}
print(every_nth(ma.relation(pl.DataFrame(data)), 2).to_dict())
con = ibis.duckdb.connect()
print(every_nth(ma.relation(con.create_table("t", data)).filter(ma.col("x") > 10), 2).to_dict())
```

```text
{'x': [10, 30, 50]}
{'x': [20, 40]}
```

The result is an ordinary `Relation`, so later operations chain onto it. The rules the registry enforces:

- The Substrait-aligned nodes and mountainash's own extension nodes are protected; registering a handler for one raises `TypeError`.
- A second registration for the same class raises `ValueError`; `RelationVisitRegistry.unregister(cls)` removes one.
- A node with neither a handler nor an operation key raises `UnregisteredRelationNodeError` (from `mountainash.relations.core.errors`) when the plan compiles.
- A handler may visit only the children the node declares (`input`, `left`, `right` or `inputs`); the plan is prepared before visiting, so building new nodes inside a handler and visiting them fails.

A third-party handler has no schema-phase contract, so inferring names and types through it requires running the plan:

```python
rel = every_nth(ma.relation(pl.DataFrame(data)), 2)
print(rel.columns, rel.schema)
try:
    rel.collect_schema()
except Exception as exc:
    print(type(exc).__name__, exc)
print(rel.collect_schema(allow_execution=True))
```

```text
[] {}
IncompleteSchemaError Incomplete schema (output names/order): Third-party visitor handler visit_every_nth has no schema-phase contract
{'x': <MountainashDtype.I64: 'i64'>}
```

`columns` and `schema` return empty results for such a plan, and `collect_schema()` raises, so code that needs the schema should call `collect_schema(allow_execution=True)`. A rewrite of the tree around your node type (for example, pushing a filter below it) is a separate extension, registered with `register_optimisation`; see [Optimisation passes](../19-relation-compilation/index.md#optimisation-passes).

## Declaring capability segments

<!-- concept:543 -->
A capability segment declares, as data, what a backend family or dialect cannot do or does differently. API builders stay free of backend-detection code. A segment is a module-level `SEGMENT = CapabilitySegment(...)` in a module whose path encodes everything else: `src/mountainash/{expressions,relations}/backends/capabilities/<backend>/family/<origin>/<domain>.py` for a family-wide declaration or `.../<backend>/dialects/<dialect>/<origin>/<domain>.py` for one dialect, where `<origin>` is `substrait` or `extensions_mountainash` and `<domain>` matches the operation's key family. The enclosing `_scope.py` supplies the scope. Bootstrap discovers these modules by walking the package, so the module path alone registers a segment. A segment outside the capability roots is refused. Executable policies (gates) are allowed only in dialect scopes; family-wide segments carry information only.

The model, the validation rules and a worked declaration are in [Declaring a new segment](../20-capability-spine/index.md#declaring-a-new-segment). After adding one, regenerate the support matrix as described in [Backend support and known limits](../16-backend-support-and-limits/index.md#support-matrix), and remove any test expectation the declaration now makes redundant.

## Type and schema adapters

<!-- concept:544 -->
A native type adapter translates canonical dtypes to and from one [type target](../03-dtypes/index.md#native-type-targets). There is one stateless adapter class per `TypeTarget`, implementing `NativeTypeAdapter` and `NativeArrowTransportAdapter` from `mountainash.core.dtypes.protocols`. The set of targets is closed: `DtypeRegistry` maps each `TypeTarget` member to a `target_<name>.py` module and adapter class name in `src/mountainash/core/dtypes/registry.py` and imports the module on first use. Adding a target is therefore a package change: a `TypeTarget` member in `core/dtypes/targets.py`, a `core/dtypes/target_<name>.py` module with the adapter, and the two registry entries. `tests/core/dtypes/test_completeness.py` fails until every canonical dtype maps on the new target, and the `TestNativeAdapterAlignment` class in `tests/core/test_protocol_alignment.py` checks that each registered adapter implements its protocols with matching signatures.

```python
from mountainash.core.dtypes import registry
from mountainash.core.dtypes.protocols import NativeTypeAdapter
from mountainash.core.dtypes.targets import TypeTarget

for target in TypeTarget:
    adapter = registry._adapter(target)
    print(target.value, type(adapter).__name__, isinstance(adapter, NativeTypeAdapter))
```

```text
polars PolarsTypeAdapter True
pandas PandasTypeAdapter True
pyarrow PyArrowTypeAdapter True
ibis IbisTypeAdapter True
narwhals NarwhalsTypeAdapter True
python PythonTypeAdapter True
```

<!-- concept:545 -->
Schemas have two contracts of their own, in `mountainash.typespec.protocols`. A `NativeSchemaAdapter` reads column names and schema evidence from a native carrier and encodes a `TableSchema` into a native schema object; it backs [native schema conversion](../10-table-schemas-and-datapackage/index.md#extracting-and-converting-schemas). A `SchemaCodec` decodes and encodes a complete schema in one interchange format; the [Frictionless descriptor](../10-table-schemas-and-datapackage/index.md#frictionless-descriptors) format is the one built in. Both live in keyed registries in `mountainash.typespec.adapter_registry`. Schema adapters are keyed by `TypeTarget`, so a new one comes with a new target. Codecs are keyed by a format name, so a codec of your own registers at run time as an instance (or a `"module:attribute"` string, imported on first lookup):

```python
from mountainash.typespec.adapter_registry import (
    NATIVE_SCHEMA_ADAPTERS, SCHEMA_CODECS, get_schema_codec,
)

class ColumnMapCodec:
    """Reads and writes {"column": "frictionless type"} mappings."""
    def decode(self, descriptor):
        return ma.table_schema(descriptor)
    def encode(self, schema):
        return {name: field.type.value for name, field in schema.fields.items()}

print([t.value for t in NATIVE_SCHEMA_ADAPTERS.list_keys()], SCHEMA_CODECS.list_keys())
SCHEMA_CODECS.register("column-map", ColumnMapCodec())
codec = get_schema_codec("column-map")
schema = codec.decode({"id": "integer", "joined": "date"})
print(codec.encode(schema))
print(get_schema_codec("frictionless").encode(schema))
```

```text
['polars', 'pandas', 'pyarrow', 'ibis', 'narwhals'] ['frictionless']
{'id': 'integer', 'joined': 'date'}
{'fields': [{'name': 'id', 'type': 'integer'}, {'name': 'joined', 'type': 'date'}]}
```

A registered codec is reached through `get_schema_codec(name)`; `TableSchema`'s own descriptor methods always use the Frictionless codec. Value-level conversion for a semantic type is a different extension point: [custom semantic types](../10-table-schemas-and-datapackage/index.md#custom-semantic-types) register converters by name in `CustomTypeRegistry`.

## Ingress handlers, units and rules

<!-- concept:546 -->
[Python data ingress](../07-relations/index.md#relations-from-python-data) chooses one handler per input shape. `PydataIngressFactory` (in `mountainash.pydata.ingress`) detects the shape, maps it to a `CONST_PYTHON_DATAFORMAT` member and lazily imports the handler class for it; anything unrecognised falls through to `DataframeFromDefault`. The mapping is closed, so a new shape is a package change:

1. Add a `CONST_PYTHON_DATAFORMAT` member in `src/mountainash/pydata/constants.py`.
2. Add a handler subclassing `BasePydataIngressHandler` in `pydata/ingress/ingress_from_<shape>.py`, with `can_handle(data)` and `convert(data, table_schema=None, *, source_table_schema=None, inline_conform=True)` returning a Polars frame, and export it from `pydata/ingress/__init__.py`.
3. Add the module and class name in `PydataIngressFactory._configure_strategy_mapping`, and a detection branch in `_get_strategy_key`, ordered before any shape it could be mistaken for.
4. If `ma.relation()` should accept the shape directly, extend `_is_python_data` in `relations/core/relation_api/relation.py`. It routes only lists, dicts, dataclass instances and Pydantic models to ingress; other shapes the factory knows (tuples, sets) reach it only through `ma.PydataIngress.convert`.
5. Add cases to `tests/pydata/test_ingress_factory.py` and `tests/pydata/test_ingress_handlers.py`.

Before registration, the same class works when called directly, and `ma.relation` accepts its Polars frame:

```python
from mountainash.pydata.ingress import BasePydataIngressHandler, PydataIngressFactory

class Ledger:
    def __init__(self, *entries):
        self.entries = entries  # (account, amount) pairs

class LedgerIngress(BasePydataIngressHandler):
    @classmethod
    def can_handle(cls, data, /):
        return isinstance(data, Ledger)

    @classmethod
    def convert(cls, data, /, table_schema=None, *, source_table_schema=None, inline_conform=True):
        rows = [{"account": a, "amount": m} for a, m in data.entries]
        return ma.PydataIngress.convert(rows, table_schema, source_table_schema=source_table_schema,
                                        inline_conform=inline_conform)

ledger = Ledger(("cash", 120), ("bank", 80))
print(PydataIngressFactory.get_strategy(ledger).__name__)
accounts = ma.table_schema({"account": "string", "amount": "number"})
print(ma.relation(LedgerIngress.convert(ledger, accounts)).to_dicts())
print(ma.relation(ma.PydataIngress.convert(((1, "a"), (2, "b")))).to_dicts())
```

```text
DataframeFromDefault
[{'account': 'cash', 'amount': 120.0}, {'account': 'bank', 'amount': 80.0}]
[{'col_0': 1, 'col_1': 'a'}, {'col_0': 2, 'col_1': 'b'}]
```

<!-- concept:547 -->
Pipeline extensions are plain objects with no registration step. A unit is any object satisfying the `Unit` protocol, usually a subclass of `BaseUnit`, `PythonUnit` or `SourceUnit`; a new destination is a `SinkUnit` subclass with `destination()`, `write(value)` and `reference_exists(ref)`; a new checkpoint store implements the `Checkpoint` protocol in `mountainash.pipelines.runtime.checkpoint`. Each is passed straight to `Pipeline.add()` or the `Runner`. [Pipelines and units](../15-pipelines/index.md#pipelines-and-units) gives the contracts and lifecycle rules, and [Values, identity and checkpoints](../15-pipelines/index.md#values-identity-and-checkpoints) the checkpoint store.

<!-- concept:548 -->
Checks come from three sources, and each extends differently. Data-contract rules are expressions, written as `Rule` or, when they need run-time values, `ContextualRule` ([Writing custom rules](../12-data-contracts/index.md#writing-custom-rules)). Direct checks for the validation runner (`RowRule`, `ScalarRule`, `RelationRule`) are your own objects too, so a reusable check is a function that returns one ([Check IR and rule kinds](../13-validation/index.md#check-ir-and-rule-kinds)). A `RelationRule` covers anything the relation API can express and runs on every backend:

```python
from mountainash.validation import RelationRule, ValidationRunner, ValueValidatorKey
from mountainash.validation.value import VALUE_RULE_REGISTRY

def at_most_per_key(key, limit):
    """No key value may appear more than `limit` times."""
    return RelationRule(
        id=f"{key}_at_most_{limit}",
        plan=lambda rel: rel.group_by(key)
            .agg(ma.count_records().alias("n"))
            .filter(ma.col("n").gt(limit)),
    )

orders = {"customer": ["a", "a", "b", "a"], "amount": [5, 7, 3, 1]}
for frame in (pl.DataFrame(orders), con.create_table("orders", orders)):
    result = ValidationRunner().validate_relation(ma.relation(frame), [at_most_per_key("customer", 2)])
    print(result.check_summaries.select("check_id", "status", "fail_count").row(0))
```

```text
('customer_at_most_2', 'failed', 1)
('customer_at_most_2', 'failed', 1)
```

The third source, schema constraints, compiles to value validators, and those are a closed vocabulary. `VALUE_RULE_REGISTRY` in `src/mountainash/validation/value.py` is a read-only mapping from each `ValueValidatorKey` to its option check, its per-value executor, its check-id prefix and its scope (row or column):

```python
print(len(VALUE_RULE_REGISTRY) == len(ValueValidatorKey))
try:
    VALUE_RULE_REGISTRY["my_validator"] = None
except TypeError as exc:
    print(type(exc).__name__, exc)
```

```text
True
TypeError 'mappingproxy' object does not support item assignment
```

A new value validator is a package change: a `ValueValidatorKey` member in `validation/checks.py`; an option checker and executor with their registry entry in `validation/value.py` (plus a branch in `structured_value_diagnostics` when it reports paths inside nested values); and, if a schema constraint should produce it, the compilation in `constraint_checks` in `src/mountainash/datacontracts/compiler.py`. The option checker runs when a `ValueRule` is constructed, so a missing or malformed option (for `MEMBERSHIP`, an `allowed` that is not a sequence) raises `CheckDeclarationError` before any data is read.
