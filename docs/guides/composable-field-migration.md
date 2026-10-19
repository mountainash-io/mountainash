# Migrating to composable field declarations

`FieldSpec` is now an immutable, unnamed field definition. Names are supplied where a definition is attached: a key in `TypeSpec.fields`, a member of an object, or an attribute of a data contract. One definition can be reused under many names, and `.variant(...)` creates a specialised copy.

This is a breaking change with no compatibility mode. Old calls fail immediately with a message that names the replacement.

## Schemas

Before:

```python
TypeSpec(fields=[
    FieldSpec(name="id", type=UniversalType.INTEGER),
    FieldSpec(name="email", type=UniversalType.STRING, rename_from="EmailAddress"),
])
```

After:

```python
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

schema = TypeSpec(fields={
    "id": FieldSpec(type=UniversalType.INTEGER),
    "email": FieldSpec(type=UniversalType.STRING, rename_from="EmailAddress"),
})
assert schema.field_names == ["id", "email"]
```

`TypeSpec.fields` is an ordered mapping; insertion order is field order. `FieldSpec` no longer has `name` or `source_name`. The source column is `rename_from` if set, otherwise the mapping key.

## Reuse and variants

```python
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

quantity = FieldSpec(type=UniversalType.INTEGER, minimum=0, maximum=100)
orders = TypeSpec(fields={"quantity": quantity})
shipments = TypeSpec(fields={"shipped_quantity": quantity})
bulk = quantity.variant(minimum=10)

assert orders.fields["quantity"] is shipments.fields["shipped_quantity"]
assert (bulk.constraints.minimum, bulk.constraints.maximum) == (10, 100)
assert quantity.constraints.minimum == 0
```

Constraint keywords (`minimum`, `pattern`, `enum`, `eq`, `notin`, `str_contains`, …) can be passed directly, or as `constraints=FieldConstraints(...)` with keywords overlaid. A variant replaces only the properties it names. There is no removal syntax: author a new definition when the meaning differs.

`severity` is field-local. A child without its own severity uses the system default (`blocking`); it does not inherit its parent's.

## Nested objects, collections and fixed arrays

| Before | After |
|---|---|
| `FieldSpec(name="p", type=OBJECT, object_fields=[FieldSpec(name="id", ...)])` | `FieldSpec(fields={"id": FieldSpec(...)})` |
| `FieldSpec(name="rows", type=ARRAY, item_object_fields=[...])` | `FieldSpec(element=FieldSpec(fields={...}))` |
| scalar array items via a dtype tree | `FieldSpec(element=FieldSpec(type=UniversalType.INTEGER))` |
| fixed-size array | `FieldSpec(element=..., dimensions=(2, 2))` |

```python
from mountainash.typespec import FieldSpec, TypeSpec, UniversalType

line = FieldSpec(fields={
    "sku": FieldSpec(type=UniversalType.STRING),
    "qty": FieldSpec(type=UniversalType.INTEGER, minimum=0, null_fill=0),
})
schema = TypeSpec(fields={
    "lines": FieldSpec(element=line, min_length=1),
    "grid": FieldSpec(element=FieldSpec(type=UniversalType.INTEGER), dimensions=(2, 2)),
})
assert schema.fields["lines"].element.fields["qty"].constraints.minimum == 0
```

Container requirements (`min_length` on `lines`) apply to the collection; element requirements apply to each item, recursively. `fields={}` declares a known empty object. A bare structured `dtype=` (for example `ListDtype(MountainashDtype.I32)`) is still valid for type-only casts.

## Data contracts

The separate `mountainash.datacontracts.Field` class is removed. Contract members are `FieldSpec` definitions, discovered in inherited member order:

| `Field(...)` keyword | `FieldSpec(...)` keyword |
|---|---|
| `nullable=False` | `required=True` |
| `ge`, `le` | `minimum`, `maximum` |
| `gt`, `lt` | `exclusive_minimum`, `exclusive_maximum` |
| `isin` | `enum` |
| `str_matches` | `pattern` |
| `str_length={"min_value": a, "max_value": b}` | `min_length=a, max_length=b` |
| `eq`, `ne`, `notin`, `str_contains`, `str_startswith`, `str_endswith`, `unique`, `severity` | unchanged |

```python
import polars as pl

from mountainash.datacontracts.contract import BaseDataContract
from mountainash.typespec import FieldSpec, UniversalType


class Orders(BaseDataContract):
    id = FieldSpec(type=UniversalType.INTEGER, minimum=1, required=True)
    status = FieldSpec(type=UniversalType.STRING, enum=["open", "closed"])


result = Orders.validate_datacontract(pl.DataFrame({"id": [1, 0], "status": ["open", "x"]}))
assert not result.passes
```

Annotation-only members (`name: str`) are no longer declarations; give each member an explicit `FieldSpec`. A standalone definition compiles its checks with `definition.to_checks("column_name")`.

## Struct and list expressions

`ma.col(...).struct.cast(fields=...)` takes a name-to-`FieldSpec` mapping, and `ma.col(...).list.cast_items(element=FieldSpec(...))` replaces `item_object_fields=`. The lexical `item_type=` form is unchanged.

## Persisted descriptors

Typed reading accepts the new canonical form: `x-mountainash.fields` for object members and `x-mountainash.element` (plus optional `dimensions`) for collections. Descriptors that still use `object_fields` or `item_object_fields` are rejected with an error naming the migration function. Convert them explicitly; nothing is migrated automatically:

```python
from mountainash.typespec.frictionless import migrate_nested_field_declarations, typespec_from_frictionless

legacy = {"fields": [{"name": "record", "type": "object", "x-mountainash": {
    "object_fields": [{"name": "quantity", "type": "integer", "constraints": {"minimum": 0}}],
}}]}
migrated = migrate_nested_field_declarations(legacy)
schema = typespec_from_frictionless(migrated)
assert schema.fields["record"].fields["quantity"].constraints.minimum == 0
assert "object_fields" in legacy["fields"][0]["x-mountainash"]  # input is not modified
```

The function is pure and idempotent. It keeps the existing precedence: a native override stays authoritative; otherwise the canonical parent shape, order and known child types win; compatible legacy declarations fill unknown types; matching metadata stays attached by name. Unknown custom properties are copied unchanged.

Typed export normalises to one canonical recursive form. Date, time and datetime bounds are written as text in the field's format, and decimals as exact decimal text. In-memory native objects that cannot be written losslessly (for example a native `backend_type` object) raise a property-specific error at export time. Raw `DataPackage` storage is unchanged: `DataPackage.from_descriptor(...).write(...)` preserves the original document, including legacy keys, and never migrates it implicitly.

## Downstream packages

Packages that build `FieldSpec` values or read `.name` from them must migrate together with this release. Mountainash StructureMap's codec `fields` change from tuples of named `FieldSpec` to `Mapping[str, FieldSpec]`; custom codec implementers must make the same change, and must pin a Mountainash version that includes this cutover.
