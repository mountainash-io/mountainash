---
title: Data contracts
---

# Data contracts

A data contract states what a table must look like and what its values must satisfy, and checks data against that statement on any supported backend. You declare a contract as a `BaseDataContract` subclass (or build one from an existing schema with `ma.datacontract`), add cross-column rules as `Rule` objects collected in a `RuleRegistry`, and run everything through a `Validator`. Every run returns a `ValidationResult` with one summary row per check and a frame of failing rows.

Assumes: [TableSchema and fields](../10-table-schemas-and-datapackage/index.md#tableschema-and-fields), [Booleanization](../06-ternary-logic/index.md#booleanization) and [Relation conform](../11-conforming-data/index.md#relation-conform).

## Declaring a contract

<!-- concept:430 -->
A contract is a schema plus the checks that schema implies. Each member is a `FieldDefinition`, the same declaration a `TableSchema` holds, so a contract carries the dtype, constraints and keys of every column. Constraints such as `required`, `minimum` or `enum` compile to validation checks. The column types become a conformance target, and the data is cast to it before the checks run. A contract declares; the validation engine described in [Validation](../13-validation/index.md) executes.

```python
import datetime as dt
import polars as pl
import mountainash as ma
from mountainash.datacontracts import BaseDataContract

D = ma.MountainashDtype

class Orders(BaseDataContract):
    order_id = ma.FieldDefinition(dtype=D.I64, required=True)
    status = ma.FieldDefinition(dtype=D.STRING, enum=["open", "shipped", "cancelled"])
    qty = ma.FieldDefinition(dtype=D.I64, minimum=1)
    shipped_qty = ma.FieldDefinition(dtype=D.I64)

    class Config:
        name = "orders"
        natural_key = ["order_id"]

orders = pl.DataFrame({
    "order_id": [1, 2, 3, 4],
    "status": ["open", "shipped", "lost", "shipped"],
    "qty": [2, 0, 5, 3],
    "shipped_qty": [0, 0, 6, None],
})

result = Orders.validate_datacontract(orders)
print(result.passes)
print(result.check_summaries.select("check_id", "check_kind", "status", "fail_count"))
```

```text
False
shape: (8, 4)
┌─────────────────────────┬────────────┬────────┬────────────┐
│ check_id                ┆ check_kind ┆ status ┆ fail_count │
│ ---                     ┆ ---        ┆ ---    ┆ ---        │
│ str                     ┆ str        ┆ str    ┆ i64        │
╞═════════════════════════╪════════════╪════════╪════════════╡
│ order_id_type_format    ┆ value      ┆ passed ┆ 0          │
│ order_id__not_null      ┆ row        ┆ passed ┆ 0          │
│ status_type_format      ┆ value      ┆ passed ┆ 0          │
│ status_enum_membership  ┆ value      ┆ failed ┆ 1          │
│ qty_type_format         ┆ value      ┆ passed ┆ 0          │
│ qty_range               ┆ value      ┆ failed ┆ 1          │
│ shipped_qty_type_format ┆ value      ┆ passed ┆ 0          │
│ primary_key_unique      ┆ relation   ┆ passed ┆ 0          │
└─────────────────────────┴────────────┴────────┴────────────┘
```

Each field gets a `<name>_type_format` check, and each declared constraint adds a check named after the field and the constraint. The natural key adds `primary_key_unique`. Check ids are stable, so you can filter on them, alert on them and compare them between runs. The result records a failing check, `passes` turns `False`, and the failing rows land in `result.failure_cases`. [Results, row identity and failure cases](../13-validation/index.md#results-row-identity-and-failure-cases) explains how to read the summaries and failure cases, and what the `value`, `row` and `relation` kinds mean.

Contracts are native to mountainash, independent of Pandera and other validation libraries. Their compiled checks run through the same expression and relation compilation as the rest of the package.

<!-- concept:431 -->
`BaseDataContract` collects every class attribute that holds a `FieldDefinition`, in declaration order, including attributes inherited from a base contract. The definition sets the type. A Python annotation next to it (`qty: int = ma.FieldDefinition(...)`) is optional and leaves the type as defined. An annotation without a definition is an error, and `BaseDataContract` skips `ClassVar` annotations.

The nested `Config` class holds contract-level settings:

| Setting | Default | Effect |
|---|---|---|
| `name` | class name | Contract name, reported as `result.datacontract_name` |
| `natural_key` | `None` | Key columns; gives failure cases keyed row identity and adds `primary_key_unique` |
| `primary_key` | `None` | Primary key written to the schema; `natural_key` is used when it is unset |
| `coerce` | `True` | Apply value transforms while conforming the data to the contract |
| `strict` | `None` | Reserved; currently unused |

`Orders.to_table_schema()` returns the contract as a `TableSchema` and `Orders.to_checks()` returns its compiled checks:

```python
print([check.id for check in Orders.to_checks()])
print(Orders.to_table_schema().primary_key)
```

```text
['order_id_type_format', 'order_id__not_null', 'status_type_format', 'status_enum_membership', 'qty_type_format', 'qty_range', 'shipped_qty_type_format', 'primary_key_unique']
['order_id']
```

A subclass keeps the base members in their original positions, replaces any member it redeclares, and appends new ones:

```python
class LargeOrders(Orders):
    qty = ma.FieldDefinition(dtype=D.I64, minimum=10)
    priority = ma.FieldDefinition(dtype=D.BOOL)

print(list(LargeOrders.to_table_schema().fields))

try:
    class Broken(BaseDataContract):
        note: str
except TypeError as exc:
    print(exc)
```

```text
['order_id', 'status', 'qty', 'shipped_qty', 'priority']
Broken.note is annotated but not declared as a FieldDefinition; contract members are explicit definitions: `note: ... = FieldDefinition(...)`
```

A natural key is a promise about the data, so validation checks it before any rule runs. Null keys or duplicate key tuples raise `IdentityInvalidError` (imported from `mountainash.exceptions`). Pass `allow_imperfect_key=True` to run anyway; `primary_key_unique` then reports the duplicates and `result.identity_diagnostics` counts them:

```python
from mountainash.exceptions import IdentityInvalidError

duplicated = pl.concat([orders, orders.head(1)])
try:
    Orders.validate_datacontract(duplicated)
except IdentityInvalidError as exc:
    print(exc)

imperfect = Orders.validate_datacontract(duplicated, allow_imperfect_key=True)
print(imperfect.check_summaries.filter(pl.col("check_id") == "primary_key_unique")
      .select("check_id", "status", "fail_count"))
```

```text
keyed identity ('order_id',) does not hold: 0 null-key rows, 0 unknown-key rows, 1 duplicate key tuples. Pass allow_imperfect_key=True to proceed with diagnostics recorded.
shape: (1, 3)
┌────────────────────┬────────┬────────────┐
│ check_id           ┆ status ┆ fail_count │
│ ---                ┆ ---    ┆ ---        │
│ str                ┆ str    ┆ i64        │
╞════════════════════╪════════╪════════════╡
│ primary_key_unique ┆ failed ┆ 1          │
└────────────────────┴────────┴────────────┘
```

`validate_datacontract` and `validate_datacontract_quick` also accept `context`, and `head`, `tail` and `sample` (with `random_seed`) to validate a slice; they are shortcuts for a `Validator` built from the contract alone (see [Validator and validation plans](#validator-and-validation-plans)).

<!-- concept:432 -->
`ma.datacontract(source)` builds a contract class from a schema that already exists elsewhere. It accepts a `TableSchema`, a simple `{name: type}` dict, a Frictionless descriptor dict (one with a `"fields"` key), a path or JSON string holding a Frictionless schema, or a Pydantic model class. A `BaseDataContract` subclass comes back unchanged. The generated class takes its name from the schema's `title`, or `CompiledDataContract` when the schema has no title.

```python
Simple = ma.datacontract({"order_id": "integer", "qty": "integer"})
print(Simple.contract_name(), [c.id for c in Simple.to_checks()])

Described = ma.datacontract({
    "fields": [
        {"name": "order_id", "type": "integer", "constraints": {"required": True}},
        {"name": "qty", "type": "integer", "constraints": {"minimum": 1}},
    ],
    "primaryKey": ["order_id"],
})
print([c.id for c in Described.to_checks()])

Titled = ma.datacontract(ma.table_schema({"order_id": "integer"}, title="order_ids"))
print(Titled.contract_name(), ma.datacontract(Orders) is Orders)
```

```text
CompiledDataContract ['order_id_type_format', 'qty_type_format']
['order_id_type_format', 'order_id__not_null', 'qty_type_format', 'qty_range', 'primary_key_unique']
order_ids True
```

A generated contract keeps the source schema, including table-level settings such as `fields_match` and `primary_key`, and can be subclassed like a hand-written one. The same compilation is available as a function: `mountainash.datacontracts.compile_datacontract(schema)` checks the schema's semantics, rejecting an invalid one, and returns the immutable `CompiledValidationPlan` that the validation engine runs (see [Table schema semantic validation](../13-validation/index.md#table-schema-semantic-validation)).

## Rules and guarded rules

<!-- concept:433 -->
Field constraints cover single columns. A comparison between columns, a condition that depends on another column, or a dataset-level statistic is a `Rule`: a named mountainash expression that should hold. The expression can be boolean or ternary. Rules are frozen dataclasses with these fields:

| Field | Meaning |
|---|---|
| `id` | Check id; unique across the contract checks and all rules in a run |
| `expr` | The expression; one value per row, or one value for the dataset if it aggregates |
| `booleanizer` | Which outcomes pass: `"t_is_true"` (default) or another name from the [booleanizer table](../06-ternary-logic/index.md#booleanization) |
| `mostly` | Fraction of rows in (0, 1] that must pass; the default requires every row |
| `severity` | `"blocking"` (default) or `"warning"` |
| `error_message` | Message template for failure cases |
| `fields` | Columns whose values are copied into failure cases |
| `metadata` | Free-form dict carried on the check |

The validation engine evaluates every row to one of three outcomes: pass, fail or unknown. A null in a comparison gives unknown, whether the expression is boolean (`ge`) or ternary (`t_ge`). The booleanizer decides whether unknown rows count as passing. `"t_is_true"` is strict: an unknown row fails the rule. `"t_maybe_true"` makes the rule null-safe, failing only rows that definitely break it. It is the equivalent of an `ignore_na` option in other validation tools, and it works for any rule, including membership tests. The summary reports the three counts separately under either booleanizer.

A rule whose expression reduces the whole dataset to one value (an aggregate with no window) runs once as a dataset-level check. `mostly`, `booleanizer` and `fields` have no meaning for such a rule, and the run rejects them when it starts.

`RuleRegistry` holds a set of rules. Pass it to a `Validator` with the contract:

```python
from mountainash.datacontracts import Rule, RuleRegistry, Validator

rules = RuleRegistry([
    Rule("shipped_le_qty",
         expr=ma.col("shipped_qty").t_le(ma.col("qty")),
         booleanizer="t_maybe_true"),
    Rule("mostly_open_or_shipped",
         expr=ma.col("status").is_in(["open", "shipped"]),
         mostly=0.7),
    Rule("mean_qty_reasonable",
         expr=ma.col("qty").mean().lt(3),
         severity="warning"),
])
validator = Validator(name="orders_daily", contract=Orders, rules=rules)
result = validator.validate(orders)
print(result.check_summaries
      .filter(pl.col("check_id").is_in(["shipped_le_qty", "mostly_open_or_shipped",
                                         "mean_qty_reasonable"]))
      .select("check_id", "status", "severity", "pass_count", "fail_count", "unknown_count"))
```

```text
shape: (3, 6)
┌────────────────────────┬────────┬──────────┬────────────┬────────────┬───────────────┐
│ check_id               ┆ status ┆ severity ┆ pass_count ┆ fail_count ┆ unknown_count │
│ ---                    ┆ ---    ┆ ---      ┆ ---        ┆ ---        ┆ ---           │
│ str                    ┆ str    ┆ str      ┆ i64        ┆ i64        ┆ i64           │
╞════════════════════════╪════════╪══════════╪════════════╪════════════╪═══════════════╡
│ shipped_le_qty         ┆ failed ┆ blocking ┆ 2          ┆ 1          ┆ 1             │
│ mostly_open_or_shipped ┆ passed ┆ blocking ┆ 3          ┆ 1          ┆ 0             │
│ mean_qty_reasonable    ┆ passed ┆ warning  ┆ null       ┆ null       ┆ null          │
└────────────────────────┴────────┴──────────┴────────────┴────────────┴───────────────┘
```

`shipped_le_qty` fails because of order 3 (6 shipped against 5 ordered). The null `shipped_qty` on order 4 is unknown, and `t_maybe_true` counts it in the rule's favour. `mostly_open_or_shipped` passes with 3 of 4 rows. `mean_qty_reasonable` is a dataset-level check, so its row counts are null. A failed `warning` check stays `failed` in the summary and leaves `passes` unchanged (see [Severities](../13-validation/index.md#running-checks)).

Registries compose with `+`. Two different rules under one id raise `CheckDeclarationError`; adding the same rule object twice is fine. A registry also decides which rules apply to a run, from the `context` dict passed to `validate`:

- `registry.only_when(rule_id, when={...})` runs the rule only when every listed context key matches. A missing key makes the rule inapplicable.
- `registry.exclude(rule_id, when={...})` skips the rule when every listed context key matches. A missing key leaves the rule in.

A condition matches by equality for a scalar, by membership for a list, tuple or set, and by calling it for a callable. The registry checks inclusion gates before exclusions. A rule left out appears in the summaries with status `skipped` and the reason in `diagnostic`, and `passes` ignores it.

```python
regional = RuleRegistry([
    Rule("small_qty", expr=ma.col("qty").le(4)),
    Rule("no_zero_shipments", expr=ma.col("shipped_qty").gt(0)),
])
regional.only_when("small_qty", when={"region": ["AU", "NZ"]})
regional.exclude("no_zero_shipments", when={"run": "backfill"})

result = Validator(name="orders_au", contract=Orders, rules=regional).validate(
    orders, context={"region": "US", "run": "backfill"},
)
print(result.check_summaries.filter(pl.col("status") == "skipped")
      .select("check_id", "status", "diagnostic").to_dicts())
```

```text
[{'check_id': 'small_qty', 'status': 'skipped', 'diagnostic': "not applicable: region does not match ['AU', 'NZ'] (got 'US')"}, {'check_id': 'no_zero_shipments', 'status': 'skipped', 'diagnostic': "excluded: run matches 'backfill'"}]
```

A registry with `only_when` gates needs a context: calling `validate` without one raises `CheckDeclarationError`. Pass `context={}` to evaluate the gates against an empty context.

### Writing custom rules

A custom rule is an ordinary expression. Build it from `ma.col`, the expression namespaces and ternary methods; the module `mountainash.datacontracts.expressions` has small combinators for common shapes (`any_not_null`, `all_not_null`, `col_in`, `col_le_col` and others), and `mountainash.datacontracts.constraints` has reusable `FieldConstraints` values (`POSITIVE_INT`, `PERCENTAGE`, `ISO_DATE`) with combinators such as `required` and `with_range`. Keep the applicability decision in the registry (`only_when`, `exclude`) and keep the rule body a pure check. A rule body that returns a constant to "skip" itself is rejected as literal-only.

When a rule needs a value known only at run time, such as a reference date or a version-specific allowed list, declare a `ContextualRule` with a `build` function that receives the context and returns the expression. Import it from `mountainash.datacontracts.rule`; the package-level `mountainash.datacontracts` namespace leaves it out. For time-relative rules, read the reference time with `mountainash.validation.require_as_of(context)`, which requires a timezone-aware `context["as_of"]`, and keep `datetime.now()` out of the rule:

```python
from mountainash.datacontracts.rule import ContextualRule
from mountainash.validation import require_as_of

class Placed(BaseDataContract):
    order_id = ma.FieldDefinition(dtype=D.I64)
    placed_on = ma.FieldDefinition(dtype=D.DATE)

not_future = ContextualRule(
    "placed_not_in_future",
    build=lambda ctx: ma.col("placed_on").le(ma.lit(require_as_of(ctx).date())),
)
placed = pl.DataFrame({"order_id": [1, 2],
                       "placed_on": [dt.date(2026, 3, 1), dt.date(2026, 12, 1)]})
as_of = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
result = Validator(name="placed", contract=Placed,
                   rules=RuleRegistry([not_future])).validate(placed, context={"as_of": as_of})
print(result.check_summaries.filter(pl.col("check_id") == "placed_not_in_future")
      .select("check_id", "status", "fail_count"))
```

```text
shape: (1, 3)
┌──────────────────────┬────────┬────────────┐
│ check_id             ┆ status ┆ fail_count │
│ ---                  ┆ ---    ┆ ---        │
│ str                  ┆ str    ┆ i64        │
╞══════════════════════╪════════╪════════════╡
│ placed_not_in_future ┆ failed ┆ 1          │
└──────────────────────┴────────┴────────────┘
```

A missing or naive `as_of`, a `build` function that raises, or one that returns something other than a mountainash expression raises `CheckDeclarationError` before any data is read. [Check IR and rule kinds](../13-validation/index.md#check-ir-and-rule-kinds) describes the lower-level check types: relation plans that return failing rows, and the closed set of value validators.

<!-- concept:434 -->
`guarded(precondition, test)` builds a conditional rule: rows where the precondition is false pass, and the test applies to the rest. It returns `precondition.not_() | test`, an ordinary expression. Contracts use the same helper internally, so a nullable field's comparison constraints (`eq`, `ne`, `notin` and the string tests) pass on null values.

A null in the precondition makes the guarded expression unknown for that row, as does a null in the test where the precondition holds. Choose the booleanizer accordingly:

```python
from mountainash.datacontracts import guarded

shipped_within_qty = guarded(ma.col("status").eq("shipped"),
                             ma.col("shipped_qty").le(ma.col("qty")))
checks = RuleRegistry([
    Rule("shipped_within_qty", expr=shipped_within_qty),
    Rule("shipped_within_qty_lenient", expr=shipped_within_qty, booleanizer="t_maybe_true"),
])
result = Validator(name="shipping", contract=Orders, rules=checks).validate(orders)
print(result.check_summaries.filter(pl.col("check_id").str.starts_with("shipped_within"))
      .select("check_id", "status", "pass_count", "fail_count", "unknown_count"))
```

```text
shape: (2, 5)
┌────────────────────────────┬────────┬────────────┬────────────┬───────────────┐
│ check_id                   ┆ status ┆ pass_count ┆ fail_count ┆ unknown_count │
│ ---                        ┆ ---    ┆ ---        ┆ ---        ┆ ---           │
│ str                        ┆ str    ┆ i64        ┆ i64        ┆ i64           │
╞════════════════════════════╪════════╪════════════╪════════════╪═══════════════╡
│ shipped_within_qty         ┆ failed ┆ 3          ┆ 0          ┆ 1             │
│ shipped_within_qty_lenient ┆ passed ┆ 3          ┆ 0          ┆ 1             │
└────────────────────────────┴────────┴────────────┴────────────┴───────────────┘
```

Orders 1 and 3 have other statuses and pass by the guard. Order 2 passes the test. Order 4 is shipped with a null `shipped_qty`, so it is unknown: the strict rule fails on it and the lenient rule passes it.

## Validator and validation plans

<!-- concept:435 -->
`Validator(name=..., contract=..., rules=None, natural_key=None, prepare=None)` binds a contract, an optional rule registry and optional data preparation into a reusable validation step. The validator copies the contract's schema, checks, key and settings when you construct it, so editing the contract class afterwards affects only validators built later.

`validator.validate(data, ...)` runs in a fixed order:

1. Declaration phase, before any data is read: resolve row identity, resolve the registry against `context`, materialise contextual rules, and reject duplicate check ids across contract checks and rules.
2. Call `prepare(data)` if given (or `prepare(data, context=...)` when the function accepts `context`).
3. Wrap the data as a relation, take any `head`, `tail` or `sample` slice once on the source backend, and [conform](../11-conforming-data/index.md#relation-conform) it to the contract schema, applying value transforms when `Config.coerce` is true.
4. Run every check through the validation engine's `ValidationRunner`, on the data's own backend.

`validate` also takes `row_identity="row_number"`, `allow_imperfect_key` and `failure_sample` (a cap on failure rows per check); [Results, row identity and failure cases](../13-validation/index.md#results-row-identity-and-failure-cases) describes their effect. `validate_quick` takes the same arguments and stops after the first blocking failure; its result has the same shape.

The validator conforms the data first, so under the default `fields_match="exact"` a column that a rule reads and the contract leaves undeclared is a structural mismatch. Every check shares the conformance step, so its failure turns every check into an `error`:

```python
with_extra = orders.with_columns(discount=pl.lit(0.1))
discount_rules = RuleRegistry([Rule("discount_ok", expr=ma.col("discount").ge(0))])
result = Validator(name="orders", contract=Orders, rules=discount_rules).validate(with_extra)
print(result.passes)
print(result.check_summaries["error"].unique().to_list())
```

```text
False
["ExactFieldsMismatchError: fieldsMatch='exact': count mismatch; expected ('order_id', 'status', 'qty', 'shipped_qty'), actual ('order_id', 'status', 'qty', 'shipped_qty', 'discount')"]
```

Declare the column in the contract, or relax `fields_match` on the contract's schema (the modes are described under [ConformContract dimensions and presets](../11-conforming-data/index.md#conformcontract-dimensions-and-presets)). `"open"` keeps undeclared columns:

```python
from dataclasses import replace

OpenOrders = ma.datacontract(replace(Orders.to_table_schema(), fields_match="open"))
result = Validator(name="orders", contract=OpenOrders, rules=discount_rules).validate(with_extra)
print(result.check_summaries.filter(pl.col("check_id") == "discount_ok")
      .select("check_id", "status", "fail_count"))
```

```text
shape: (1, 3)
┌─────────────┬────────┬────────────┐
│ check_id    ┆ status ┆ fail_count │
│ ---         ┆ ---    ┆ ---        │
│ str         ┆ str    ┆ i64        │
╞═════════════╪════════╪════════════╡
│ discount_ok ┆ passed ┆ 0          │
└─────────────┴────────┴────────────┘
```

A rule that fails on its own (for example, it names a missing column) reports `error` for that rule only, and the other checks still run. To validate several related tables with foreign keys between them, use a `RelationDAG` (see [Validating a DAG](../14-relationdag/index.md#validating-a-dag)).

<!-- concept:436 -->
`ValidationPlan(name=..., steps=[(step_name, validator, data), ...], context=None, fail_fast=False)` runs several validators one after another with a shared context. Step names must be unique and at least one step is required. `execute()` returns a `PlanResult` with `passes` (true only when every step passes), `results` (the `ValidationResult` of each step, by name) and `summary`, a Polars frame with `step`, `passes`, `fail_count` and `elapsed`. With `fail_fast=True` the plan stops after the first failing step.

```python
from mountainash.datacontracts import ValidationPlan

plan = ValidationPlan(
    name="nightly",
    steps=[
        ("orders", Validator(name="orders", contract=Orders), orders),
        ("placed", Validator(name="placed", contract=Placed,
                             rules=RuleRegistry([not_future])), placed),
    ],
    context={"as_of": as_of},
)
outcome = plan.execute()
print(outcome.passes)
print(outcome.summary.select("step", "passes", "fail_count"))
print(outcome.results["placed"].validator_name)
```

```text
False
shape: (2, 3)
┌────────┬────────┬────────────┐
│ step   ┆ passes ┆ fail_count │
│ ---    ┆ ---    ┆ ---        │
│ str    ┆ bool   ┆ i64        │
╞════════╪════════╪════════════╡
│ orders ┆ false  ┆ 2          │
│ placed ┆ false  ┆ 1          │
└────────┴────────┴────────────┘
placed
```

Steps run sequentially. A plan suits independent tables; tables linked by keys belong in a `RelationDAG`.
