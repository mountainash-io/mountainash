---
title: Table schemas and DataPackage
---

# Table schemas and DataPackage

A table schema declares the columns a table should have: their names and order, their types, the constraints their values must meet, and how raw text should be read into those types. Mountainash represents it as `ma.TableSchema`, a mapping of names to `ma.FieldDefinition` declarations, aligned with the Frictionless Table Schema standard. The same object drives [conforming data](../11-conforming-data/index.md), [data contracts](../12-data-contracts/index.md), [validation](../13-validation/index.md) and the [RelationDAG](../14-relationdag/index.md). `ma.DataPackage` and `ma.DataResource` read and write Frictionless descriptors that bundle several tables, their schemas and their file dialects. Typical work starts from `ma.table_schema({...})` or a `TableSchema` built from field definitions, and from `ma.DataPackage.from_path(...)` for an existing package.

Assumes: [Installation and the package surface](../02-installation-and-package-surface/index.md), [Data types](../03-dtypes/index.md) and [Relations](../07-relations/index.md).

## TableSchema and fields

<!-- concept:400 -->
`TableSchema` holds an ordered `fields` mapping from column name to `FieldDefinition`, plus table-level declarations. The mapping keys supply the names and their order. A definition is unnamed, so one definition can serve under several names.

```python
import mountainash as ma
from mountainash.typespec import UniversalType

Quantity = ma.FieldDefinition(type=UniversalType.INTEGER, minimum=0)

orders = ma.TableSchema(
    fields={
        "order_id": ma.FieldDefinition(type=UniversalType.STRING, required=True, unique=True),
        "quantity": Quantity,
        "returned": Quantity,
        "price": ma.FieldDefinition(dtype=ma.DecimalDtype(10, 2)),
    },
    primary_key=["order_id"],
    title="Orders",
)
print(orders.field_names)
print(orders.fields["price"].type, orders.fields["price"].dtype)
print(orders.fields_match, orders.missing_values)
```

```text
['order_id', 'quantity', 'returned', 'price']
number decimal(10,2)
exact ['']
```

A field states its type in one of two vocabularies. `type=` takes a `UniversalType`, the Frictionless type list (`integer`, `number`, `date`, `year` and so on). `dtype=` takes a [canonical dtype](../03-dtypes/index.md#canonical-dtypes), which is more precise: the `price` field above declares a decimal with precision 10 and scale 2, and its Frictionless `type` is derived as `number`. When both are given they must agree. Pass `type=` as a `UniversalType` member. `FieldDefinition(type="array")` accepts the string and stores it as a plain string, and parts of conform that test the type by identity then misread the field (a JSON-text array source fails with `ConformTransformError`, while `type=UniversalType.ARRAY` decodes it). `ma.table_schema` parses strings for you.

The table-level declarations are:

| Property | Meaning |
|---|---|
| `fields` | Ordered `{name: FieldDefinition}` mapping; copied on assignment |
| `primary_key` | List of field names that identify a row |
| `unique_keys` | List of composite unique keys, each a list of field names |
| `foreign_keys` | List of `ForeignKey` declarations (see [Foreign keys](#foreign-keys)) |
| `missing_values` | Text values read as null, default `[""]` (see [Missing values and temporals](#missing-values-and-temporals)) |
| `fields_match` | How conform treats columns that differ from the declared fields, default `"exact"` |
| `contract` | Optional reconciliation policy layered over `fields_match` |
| `title`, `description` | Descriptive metadata |
| `schema_url` | The `$schema` profile URL, fixed after construction |

Construction checks the key properties: `primary_key`, each unique key and each foreign key must be a list of strings, and a malformed one raises `InvalidKeyShapeError`. `fields_match` and `contract` belong to conformance; [ConformContract dimensions and presets](../11-conforming-data/index.md#conformcontract-dimensions-and-presets) explains them.

A schema is a declaration. Data and backend come in only when a consumer uses it, and each consumer interprets it in its own way: `relation.conform(schema)` reshapes and converts data to match it, `schema.to_contract()` compiles its constraints into a [data contract](../12-data-contracts/index.md#declaring-a-contract), and a DataPackage resource supplies it to the RelationDAG. Type comparisons use the canonical dtype vocabulary, so the same schema applies to a Polars frame, a pandas frame or an Ibis table.

<!-- concept:401 -->
`FieldDefinition` is an immutable, unnamed declaration. Its properties fall into five groups:

| Group | Properties |
|---|---|
| Type | `type`, `format`, `dtype`, `backend_type` (a native dtype override) |
| Constraints | `required`, `unique`, `minimum`, `maximum`, `exclusive_minimum`, `exclusive_maximum`, `min_length`, `max_length`, `pattern`, `enum`, `json_schema`, plus the extensions `eq`, `ne`, `notin`, `str_contains`, `str_startswith`, `str_endswith`, `enum_weights` |
| Lexical reading | `missing_values`, `true_values`, `false_values`, `decimal_char`, `group_char`, `bare_number`, `categories`, `categories_ordered`, `item_type`, `delimiter` |
| Conversion instructions | `rename_from`, `null_fill`, `rounding`, `custom_cast` |
| Nested shape and metadata | `fields`, `element`, `dimensions`; `title`, `description`, `example`, `rdf_type`, `severity` |

A definition stores constraint keywords such as `minimum=0` in a `FieldConstraints` object (`definition.constraints`) and also exposes them as flat attributes (`definition.minimum`). `variant(...)` returns a copy with changes applied; every other property keeps its value:

```python
Shipped = Quantity.variant(required=True, maximum=500)
print(Quantity.minimum, Quantity.required)
print(Shipped.minimum, Shipped.required, Shipped.maximum)
try:
    Quantity.minimum = 1
except AttributeError as exc:
    print(type(exc).__name__, exc)
```

```text
0 False
0 True 500
FrozenInstanceError cannot assign to field 'minimum'
```

Construction checks properties that belong to a single type. `delimiter` and `item_type` apply to `list` fields, `element` and `dimensions` to `array` fields, `fields` to `object` fields, and `rounding` to decimal dtypes:

```python
from mountainash.exceptions import TypeSpecError

try:
    ma.FieldDefinition(type=UniversalType.STRING, delimiter=";")
except TypeSpecError as exc:
    print(type(exc).__name__, exc)
```

```text
IncompatibleFieldPropertiesError field None: 'delimiter' requires type in (list), got 'string'
```

Nested columns are declared by composition. An `object` field takes `fields={name: FieldDefinition}` for its members, and an `array` field takes `element=FieldDefinition` and, for fixed-size arrays, `dimensions`. The field then derives its `dtype` (a `StructDtype`, `ListDtype` or `ArrayDtype`), so `dtype` cannot also be passed. Constraints describe valid data, and [validation](../13-validation/index.md) checks them; conform leaves them alone. Conversion instructions tell conform how to reach the declared state.

<!-- concept:402 -->
`ma.table_schema(columns, **metadata)` builds a schema from a `{name: type_string}` dictionary. The strings are Frictionless type names, and `title`, `description` and `primary_key` pass through as metadata. It currently ignores any other keyword silently, `fields_match` included; set it on the result (`schema.fields_match = "open"`) or build a `TableSchema` directly:

```python
customers = ma.table_schema(
    {"customer_id": "integer", "name": "string", "joined": "date"},
    primary_key=["customer_id"],
)
print(customers.fields["joined"].type, customers.primary_key)
```

```text
date ['customer_id']
```

It is equivalent to `ma.TableSchema.from_simple_dict(...)`. It parses type names strictly, so `"int"` raises `UnknownDtypeError` (shown in [Errors](../02-installation-and-package-surface/index.md#errors)). Use `TableSchema` directly when a field needs constraints, a canonical dtype or conversion instructions.

## Missing values and temporals

<!-- concept:413 -->
Missing values are text sentinels that stand for null in lexical data such as CSV. The schema-level `missing_values` list applies to every field and defaults to `[""]`; a field-level `missing_values` replaces it for that field. Following Frictionless, sentinels are always strings, and the comparison happens before any type conversion. A sentinel may carry a label with `LabeledValue`, which records why the value is missing and round-trips through the descriptor:

```python
import polars as pl
from mountainash.typespec import LabeledValue

survey = pl.DataFrame({
    "respondent": ["r1", "r2", "r3", "r4"],
    "score": ["7.5", "NA", "-99", ""],
})
spec = ma.TableSchema(fields={
    "respondent": ma.FieldDefinition(type=UniversalType.STRING),
    "score": ma.FieldDefinition(
        type=UniversalType.NUMBER,
        missing_values=["", "NA", LabeledValue("-99", label="refused")],
    ),
})
print(ma.relation(survey).conform(spec).to_polars())
```

```text
shape: (4, 2)
┌────────────┬───────┐
│ respondent ┆ score │
│ ---        ┆ ---   │
│ str        ┆ f64   │
╞════════════╪═══════╡
│ r1         ┆ 7.5   │
│ r2         ┆ null  │
│ r3         ┆ null  │
│ r4         ┆ null  │
└────────────┴───────┘
```

Sentinels apply only to text sources; a column that already arrives as numbers skips the comparison. `LabeledValue` is also the labelled form of `categories`, where its `value` takes the field's own type. Boolean fields read text through `true_values` and `false_values` (by default `true`, `True`, `TRUE`, `1` and their false counterparts), and a sentinel that overlaps those tokens produces a warning. To replace nulls with a value after reading, declare `null_fill` on the field; conform applies it to source nulls and to sentinel matches.

<!-- concept:415 -->
Temporal fields are read from text according to their `format`:

- `date`, `time` and `datetime` with `format="default"` expect ISO 8601 text. A default `datetime` value with a timezone offset or `Z` becomes naive UTC.
- A format pattern such as `"%d/%m/%Y"` parses with that pattern.
- `format="any"` parses with one fixed, deterministic rule set (year-first, two-digit years pivoting at 68, `UTC` and `GMT` recognised).
- `year`, `yearmonth` and `duration` values must match the XSD lexical forms (`2024`, `2024-01`, `PT1H30M`) and stay as strings. Their canonical dtypes are `xsd_year`, `xsd_yearmonth` and `xsd_duration`, as described in [Canonical dtypes](../03-dtypes/index.md#canonical-dtypes).

```python
events = pl.DataFrame({
    "visited": ["03/02/2024", "15/12/2023"],
    "seen_at": ["2024-02-03T10:00:00Z", "2024-02-04T11:30:00"],
    "loose": ["3 Feb 2024", "2024/02/04"],
    "period": ["2024-01", "2023-12"],
    "wait": ["PT1H30M", "P2D"],
})
temporal = ma.TableSchema(fields={
    "visited": ma.FieldDefinition(type=UniversalType.DATE, format="%d/%m/%Y"),
    "seen_at": ma.FieldDefinition(type=UniversalType.DATETIME),
    "loose": ma.FieldDefinition(type=UniversalType.DATE, format="any"),
    "period": ma.FieldDefinition(type=UniversalType.YEARMONTH),
    "wait": ma.FieldDefinition(type=UniversalType.DURATION),
})
print(ma.relation(events).conform(temporal).to_polars())
```

```text
shape: (2, 5)
┌────────────┬─────────────────────┬────────────┬─────────┬─────────┐
│ visited    ┆ seen_at             ┆ loose      ┆ period  ┆ wait    │
│ ---        ┆ ---                 ┆ ---        ┆ ---     ┆ ---     │
│ date       ┆ datetime[μs]        ┆ date       ┆ str     ┆ str     │
╞════════════╪═════════════════════╪════════════╪═════════╪═════════╡
│ 2024-02-03 ┆ 2024-02-03 10:00:00 ┆ 2024-02-03 ┆ 2024-01 ┆ PT1H30M │
│ 2023-12-15 ┆ 2024-02-04 11:30:00 ┆ 2024-02-04 ┆ 2023-12 ┆ P2D     │
└────────────┴─────────────────────┴────────────┴─────────┴─────────┘
```

The same parsers are available for single Python values in `mountainash.typespec` (`parse_temporal_any`, `parse_default_datetime`, `parse_xsd_duration`, `parse_xsd_partial_date`). The conform contract's `data_type` policy decides what happens to a value that fails to parse; see [Conform errors](../11-conforming-data/index.md#conform-errors).

## Frictionless descriptors

<!-- concept:403 -->
`schema.to_frictionless()` writes a Frictionless Table Schema descriptor as a dictionary, and `ma.TableSchema.from_frictionless(descriptor)` reads one. Standard properties keep their standard names and locations in camelCase (`primaryKey`, `missingValues`, `decimalChar`); the Python attributes use snake_case. The codec writes mountainash-only declarations, such as `rename_from`, `null_fill`, a precise `dtype`, the `open` fields-match mode and a reconciliation `contract`, under an `x-mountainash` key, following the Frictionless convention for custom properties. It omits defaults.

```python
import json

staged = ma.TableSchema(
    fields={
        "user_id": ma.FieldDefinition(type=UniversalType.INTEGER, rename_from="uid", null_fill=0),
        "score": ma.FieldDefinition(type=UniversalType.NUMBER, decimal_char=","),
    },
    primary_key=["user_id"],
    fields_match="open",
)
descriptor = staged.to_frictionless()
print(json.dumps(descriptor, indent=2))
print(ma.TableSchema.from_frictionless(descriptor) == staged)
```

```text
{
  "primaryKey": [
    "user_id"
  ],
  "x-mountainash": {
    "fields_match": "open"
  },
  "fields": [
    {
      "name": "user_id",
      "type": "integer",
      "x-mountainash": {
        "rename_from": "uid",
        "null_fill": 0
      }
    },
    {
      "name": "score",
      "type": "number",
      "decimalChar": ","
    }
  ]
}
True
```

Another Frictionless tool reads this descriptor as a plain integer and number table and ignores the extension keys. The reverse direction is strict: the standard `fieldsMatch` key accepts only the five standard modes, so `from_frictionless` rejects a descriptor that puts the mountainash `open` mode there, with no silent reinterpretation:

```python
from mountainash.exceptions import InvalidFieldMatchDeclaration

try:
    ma.TableSchema.from_frictionless(
        {"fields": [{"name": "id", "type": "integer"}], "fieldsMatch": "open"}
    )
except InvalidFieldMatchDeclaration as exc:
    print(exc)
```

```text
invalid fieldsMatch declaration (fieldsMatch is not one of the five standard modes): standard='open', x-mountainash=None
```

The codec targets Frictionless v2. It keeps the meaning of every supported v2 property (schema `fields`, `title`, `description`, `fieldsMatch`, `missingValues`, `primaryKey`, `uniqueKeys`, `foreignKeys`, `$schema`, and the field properties from `type` and `format` through `itemType` and `delimiter`); byte-for-byte preservation of the input is outside its guarantee. The codec rejects recognised v1 profiles with typed `DescriptorError` subclasses.

<!-- concept:404 -->
The Frictionless type list and the [canonical dtypes](../03-dtypes/index.md#canonical-dtypes) are two vocabularies joined at this boundary. `to_canonical` maps a `UniversalType` to its canonical dtype (`integer` to `i64`, `year` to `xsd_year`, `any` to `None`, meaning unconstrained). `from_canonical` maps the other way and is deliberately broad: every integer width becomes `integer`, and `binary` becomes `string` with format `binary`.

```python
from mountainash.typespec import to_canonical, from_canonical

D = ma.MountainashDtype
print(to_canonical(UniversalType.INTEGER), to_canonical(UniversalType.YEAR))
print(from_canonical(D.I16), from_canonical(D.BINARY))
narrow = ma.TableSchema(fields={"small": ma.FieldDefinition(dtype=D.I16)})
print(narrow.to_frictionless())
```

```text
MountainashDtype.I64 MountainashDtype.XSD_YEAR
(<UniversalType.INTEGER: 'integer'>, None) (<UniversalType.STRING: 'string'>, 'binary')
{'fields': [{'name': 'small', 'type': 'integer', 'x-mountainash': {'dtype': {'kind': 'canonical', 'name': 'i16'}}}]}
```

`x-mountainash.dtype` keeps the precision that the standard type loses, so a schema round-trips through a descriptor with its exact dtypes. The canonical dtype of a `geopoint` depends on the field's `format`, so `to_canonical(UniversalType.GEOPOINT)` raises `AmbiguousGeospatialTypeError`.

## DataPackage, resources and dialects

<!-- concept:405 -->
A Frictionless Data Package is a JSON descriptor listing named resources. Each resource points at its data (`path` or inline `data`) and may carry a table schema and a dialect, inline or as a reference to another JSON file. The examples in this section use this package, with a semicolon-separated `customers.csv` and an `orders.csv`:

```json
{
  "name": "shop",
  "resources": [
    {
      "name": "customers",
      "path": "customers.csv",
      "format": "csv",
      "dialect": {"delimiter": ";"},
      "schema": {
        "fields": [
          {"name": "customer_id", "type": "integer"},
          {"name": "name", "type": "string"}
        ],
        "primaryKey": ["customer_id"]
      }
    },
    {
      "name": "orders",
      "path": "orders.csv",
      "format": "csv",
      "schema": "schemas/orders.json"
    }
  ]
}
```

`schemas/orders.json` declares `order_id`, `customer_id` and `amount`, a primary key, `"missingValues": ["", "NA"]` and a foreign key to `customers`.

`ma.DataPackage` holds an ordered tuple of `ma.DataResource` objects plus package metadata (`name`, `title`, `version`, `licenses`, `contributors`, `sources` and the rest of the v2 package properties). A resource stores its schema and dialect exactly as the descriptor gave them, a mapping or a reference string. `to_table_schema()` and `to_dialect()` resolve and convert them on demand:

```python
package = ma.DataPackage.from_path("pkg/datapackage.json")
print([resource.name for resource in package.resources])
orders_resource = package.resources[1]
print(orders_resource.table_schema)
orders_schema = orders_resource.to_table_schema()
print(orders_schema.field_names, orders_schema.primary_key, orders_schema.missing_values)
```

```text
['customers', 'orders']
schemas/orders.json
['order_id', 'customer_id', 'amount'] ['order_id'] ['', 'NA']
```

Keeping the raw form means a package written back out still says `"schema": "schemas/orders.json"` and keeps the file as a reference, and a schema problem surfaces where the schema is used, after the package has opened. Loading checks package-level structure (resource names, unique names, required properties).

A package can also be built in code. A resource accepts a `TableSchema` object directly:

```python
inline = ma.DataPackage(
    name="inline",
    resources=[ma.DataResource(name="customers", path="customers.csv", table_schema=customers)],
)
print(inline.to_descriptor())
```

```text
{'name': 'inline', 'resources': [{'name': 'customers', 'path': 'customers.csv', 'schema': {'primaryKey': ['customer_id'], 'fields': [{'name': 'customer_id', 'type': 'integer'}, {'name': 'name', 'type': 'string'}, {'name': 'joined', 'type': 'date'}]}}]}
```

`package.to_relation_dag()` turns the tabular resources into named relations of a [RelationDAG](../14-relationdag/index.md#resources-and-datapackage), and `resource.to_contract()` compiles a resource's schema into a data contract. `mountainash-files` reads a resource's file, and `mountainash-transport` handles remote paths; see [Where mountainash sits](../02-installation-and-package-surface/index.md#where-mountainash-sits) for the extras that provide them.

<!-- concept:406 -->
`ma.TableDialect` is the Frictionless Table Dialect: how a delimited, structured, spreadsheet or database source is laid out. It covers `delimiter`, `line_terminator`, `quote_char`, `double_quote`, `escape_char`, `null_sequence`, `skip_initial_space`, `header`, `header_rows`, `header_join`, `comment_char`, `comment_rows`, `item_type`, `item_keys`, `property`, `sheet_name`, `sheet_number` and `table`, with camelCase aliases for the descriptor. A resource's dialect draws its properties from one family, and that family must suit the resource's `format`.

```python
customers_resource = package.resources[0]
dialect = customers_resource.to_dialect()
print(dialect.delimiter, dialect.to_polars_read_csv_kwargs())
print(ma.ResourceRef(customers_resource).relation().to_polars())
```

```text
; {'separator': ';'}
shape: (2, 2)
┌─────────────┬───────┐
│ customer_id ┆ name  │
│ ---         ┆ ---   │
│ i64         ┆ str   │
╞═════════════╪═══════╡
│ 1           ┆ Ada   │
│ 2           ┆ Grace │
└─────────────┴───────┘
```

`ResourceRef(resource).relation()` reads the file with its dialect and conforms it to the resource schema. `to_polars_read_csv_kwargs()` translates the subset that `polars.read_csv` understands and drops the rest.

<!-- concept:407 -->
`DataPackage.from_path(path)`, `from_json(text)` and `from_descriptor(mapping)` read a package. `to_descriptor()` returns a fresh dictionary, and `write(path, mode=...)` writes JSON. `ma.DescriptorWriteMode` selects the form:

- `PRESERVE` (the default, also used by `to_descriptor()`) writes the descriptor as authored: references stay references and profile URLs appear only where the author wrote them.
- `CANONICAL` (also `to_canonical_descriptor()`) writes the normalised v2 form, adding the `$schema` profile URL at package, resource, schema and dialect level.

```python
package.write("pkg/out-preserve.json")
package.write("pkg/out-canonical.json", mode=ma.DescriptorWriteMode.CANONICAL)
canonical = json.load(open("pkg/out-canonical.json"))
print(canonical["$schema"])
print(canonical["resources"][1])
```

```text
https://datapackage.org/profiles/2.0/datapackage.json
{'name': 'orders', 'path': 'orders.csv', 'format': 'csv', 'schema': 'schemas/orders.json', '$schema': 'https://datapackage.org/profiles/2.0/dataresource.json'}
```

Both modes keep relative paths and references as written, so write a package next to the files it refers to.

<!-- concept:408 -->
A schema or dialect given as a string is a reference to a JSON document, which `to_table_schema()` or `to_dialect()` resolves when it runs. Relative references resolve against a base URI: the package file's directory for `from_path`, or the absolute `base_uri=` passed to `from_descriptor` and `from_json`. With no base, a relative reference raises `MissingDescriptorBase`, and a missing file raises `DescriptorReferenceNotFound`.

```python
from pathlib import Path
from mountainash.exceptions import DescriptorReferenceNotFound, MissingDescriptorBase

raw = {"resources": [{"name": "customers", "path": "customers.csv", "schema": "schemas/customers.json"}]}
found = ma.DataPackage.from_descriptor(raw, base_uri=Path("pkg").resolve())
print(found.resources[0].to_table_schema().field_names)
try:
    ma.DataPackage.from_descriptor(raw).resources[0].to_table_schema()
except MissingDescriptorBase as exc:
    print(type(exc).__name__, exc)
remote = {"resources": [{"name": "customers", "path": "customers.csv", "schema": "https://example.com/customers.json"}]}
try:
    ma.DataPackage.from_descriptor(remote, base_uri=Path("pkg").resolve()).resources[0].to_table_schema()
except Exception as exc:
    print(type(exc).__name__, exc)
```

```text
['customer_id', 'name']
MissingDescriptorBase relative descriptor reference requires a base URI
LocationNotAllowed location not allowed: https://example.com (remote not allowed)
```

Resolution is confined: local references must stay under the package root, and remote references need explicit permission. `mountainash-transport` raises the denial as `LocationNotAllowed`, which sits outside the `MountainashError` hierarchy. To read remote descriptors, pass a location policy from `mountainash-transport` that allows the scheme (`policy=`), or inject your own `DescriptorResolver` (`resolver=`), an object with a `resolve(reference, *, base_uri, expected_kind, policy)` method returning the parsed mapping. [Where mountainash sits](../02-installation-and-package-surface/index.md#where-mountainash-sits) covers transport and its policies.

## Foreign keys

<!-- concept:414 -->
A foreign key declares that the values of some fields in this table must appear in fields of a referenced table. `ForeignKey(fields=[...], reference=ForeignKeyReference(resource=..., fields=[...]))` is the typed form; `resource=None` references the same table. Both field lists must be lists of strings.

```python
from mountainash.typespec import ForeignKey, ForeignKeyReference
from mountainash.exceptions import InvalidDescriptorRelationship

employees = ma.TableSchema(
    fields={
        "id": ma.FieldDefinition(type=UniversalType.INTEGER),
        "manager_id": ma.FieldDefinition(type=UniversalType.INTEGER),
        "dept": ma.FieldDefinition(type=UniversalType.STRING),
    },
    primary_key=["id"],
    foreign_keys=[
        ForeignKey(fields=["manager_id"], reference=ForeignKeyReference(resource=None, fields=["id"])),
        ForeignKey(fields=["dept"], reference=ForeignKeyReference(resource="departments", fields=["code"])),
    ],
)
print(employees.to_frictionless()["foreignKeys"])
try:
    ma.DataPackage(resources=[ma.DataResource(name="employees", path="employees.csv", table_schema=employees)])
except InvalidDescriptorRelationship as exc:
    print(type(exc).__name__, exc)
print(orders_schema.foreign_keys)
print(package.to_relation_dag().constraint_edges)
```

```text
[{'fields': ['manager_id'], 'reference': {'fields': ['id']}}, {'fields': ['dept'], 'reference': {'fields': ['code'], 'resource': 'departments'}}]
InvalidDescriptorRelationship foreign key references an unknown resource
[ForeignKey(fields=['customer_id'], reference=ForeignKeyReference(resource='customers', fields=['customer_id']))]
{('customers', 'orders')}
```

Inside a package, a foreign key's target resource must exist; the check runs when the package is built and again when a referenced schema is resolved. A schema is a declaration, so declaring a key leaves the data unchecked. `to_relation_dag()` records each key as a constraint edge between resources, separate from data dependencies. [Validation](../13-validation/index.md#foreign-keys) checks the values, and conform reports keys that a conform step dropped or broke as key drift (see [Drift reporting](../11-conforming-data/index.md#drift-reporting)).

## Extracting and converting schemas

<!-- concept:409 -->
Extraction builds a `TableSchema` from something that already has a shape. `extract_from_dataframe(df)` reads any supported dataframe (Polars, pandas, PyArrow, Ibis, Narwhals) and records the canonical dtype and, by default, the native dtype of each column. `extract_from_dataclass(cls)` and `extract_from_pydantic(model)` read type annotations; Pydantic field constraints such as `ge=0` become field constraints, and a non-optional Pydantic field is `required`.

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from mountainash.typespec import extract_from_dataframe, extract_from_dataclass, extract_from_pydantic

frame = pl.DataFrame({"id": pl.Series([1, 2], dtype=pl.Int32), "name": ["Ada", "Grace"]})
for name, field in extract_from_dataframe(frame).fields.items():
    print(name, field.type, field.dtype)

@dataclass
class Customer:
    id: int
    joined: Optional[date] = None

class Order(BaseModel):
    order_id: int
    amount: float = Field(ge=0)

print(extract_from_dataclass(Customer).fields["joined"].type)
amount = extract_from_pydantic(Order).fields["amount"]
print(amount.type, amount.required, amount.minimum)
```

```text
id integer MountainashDtype.I32
name string MountainashDtype.STRING
date
number True 0
```

`from_dataframe`, `from_dataclass` and `from_pydantic` are aliases. The `extract_schema_from_*` variants cache the result per class.

<!-- concept:410 -->
Conversion goes the other way, from a schema to a library's own schema object, through the dtype registry described in [Native type targets](../03-dtypes/index.md#native-type-targets):

```python
from mountainash.typespec import to_polars_schema, to_pandas_dtypes, to_ibis_schema, convert_to_backend

print(to_polars_schema(customers))
print(to_pandas_dtypes(customers))
print(to_ibis_schema(customers))
print(convert_to_backend(customers, "pyarrow"))
```

```text
{'customer_id': Int64, 'name': String, 'joined': Date}
{'customer_id': 'Int64', 'name': 'string', 'joined': 'datetime64[ns]'}
{'customer_id': 'int64', 'name': 'string', 'joined': 'date'}
customer_id: int64
name: string
joined: date32[day]
```

Each field resolves to the most specific type it declares: `backend_type` for its own library, then `dtype`, then the canonical mapping of `type`. `convert_to_backend` accepts any registered target name (`"arrow"` is accepted for `"pyarrow"`). Adding a target is an extension task; [Type and schema adapters](../22-extending-mountainash/index.md#type-and-schema-adapters) covers it.

<!-- concept:411 -->
`compare_specs(source, target)` compares two schemas and returns a `SpecDiff`: fields missing from the source, extra fields in the source, and type changes for shared fields. `is_compatible` is false when anything is missing or a type changed. `validate_match(df, schema)` checks a dataframe against a schema and returns `(is_valid, messages)`; `assert_match` raises `SchemaValidationError` instead. Pass `strict=False` to allow extra columns.

```python
from mountainash.typespec import compare_specs, validate_match

v2 = ma.table_schema({"customer_id": "integer", "name": "string", "email": "string", "joined": "datetime"})
diff = compare_specs(customers, v2)
print(diff.missing_columns, diff.extra_columns, diff.type_mismatches, diff.is_compatible)
print(validate_match(frame, ma.table_schema({"id": "integer", "email": "string"})))
```

```text
['email'] [] [('joined', <UniversalType.DATE: 'date'>, <UniversalType.DATETIME: 'datetime'>)] False
(False, ["Missing required columns: ['email']", "Unexpected columns: ['name']"])
```

`compare_specs` compares declared identities, both `type` and `dtype`, so an extracted schema (which records exact dtypes such as `i32`) differs from a hand-written `integer` field. `validate_match` accepts any data type that satisfies the declaration. To reconcile data, use [conform](../11-conforming-data/index.md); for value-level checks, use [validation](../13-validation/index.md).

## Custom semantic types

<!-- concept:412 -->
A custom semantic type is a named converter for values that need logic beyond a type cast: NaN handling, token parsing, normalisation. `CustomTypeRegistry` holds them process-wide, and a field opts in with `custom_cast="name"`. Four are registered by default: `safe_float`, `safe_int`, `xml_string` and `rich_boolean`. Register your own with a Python converter (called per value as `converter(value, field_name=...)`), a Narwhals converter (a function of the column name returning an expression builder, which runs vectorised), or both:

```python
from mountainash.typespec import CustomTypeRegistry

def country_code(value, *, field_name=None):
    return None if value is None else str(value).strip().upper()

CustomTypeRegistry.register(
    name="country_code",
    target_universal_type="string",
    python_converter=country_code,
    description="Trimmed upper-case ISO country code",
)
print(sorted(CustomTypeRegistry.list_converters()))
addresses = ma.TableSchema(fields={
    "country": ma.FieldDefinition(type=UniversalType.STRING, custom_cast="country_code"),
    "flag": ma.FieldDefinition(type=UniversalType.BOOLEAN, custom_cast="rich_boolean"),
})
print(ma.PydataIngress.convert([{"country": " au ", "flag": "yes"}, {"country": "nz", "flag": "no"}], addresses))
```

```text
['country_code', 'rich_boolean', 'safe_float', 'safe_int', 'xml_string']
shape: (2, 2)
┌─────────┬───────┐
│ country ┆ flag  │
│ ---     ┆ ---   │
│ str     ┆ bool  │
╞═════════╪═══════╡
│ AU      ┆ true  │
│ NZ      ┆ false │
└─────────┴───────┘
```

Custom converters run at the Python boundary, when Python data is converted with a target schema, as [Typed Python data ingress](#typed-python-data-ingress) describes. `relation.conform(schema)` does not apply `custom_cast`. Registering a name twice raises `ValueError`; call `unregister(name)` first to replace a converter. Descriptors carry `custom_cast` under `x-mountainash`, so a consumer reading the descriptor needs the same converter registered. [Extending mountainash](../22-extending-mountainash/index.md) lists this registry among the package's extension points.

## Typed Python data ingress

<!-- concept:482 -->
`ma.PydataIngress.convert(data, table_schema, *, source_table_schema=None)` converts Python data into a Polars frame (see [Relations from Python data](../07-relations/index.md#relations-from-python-data)) and takes two schemas with different jobs. The source schema states what the input columns are, and `convert` builds the frame with those dtypes. The target schema states what they should become, and its conversions (type casts, `null_fill`, `rename_from`, custom converters) run after construction. Only the source schema informs how the input is typed.

```python
rows = [{"id": 1, "code": None}, {"id": 2, "code": None}]
print(ma.PydataIngress.convert(rows).schema)
source = ma.TableSchema(fields={
    "id": ma.FieldDefinition(dtype=D.I32),
    "code": ma.FieldDefinition(dtype=D.STRING),
})
target = ma.TableSchema(fields={
    "code": ma.FieldDefinition(dtype=D.STRING, null_fill="NONE"),
})
print(ma.PydataIngress.convert(rows, source_table_schema=source).schema)
print(ma.PydataIngress.convert(rows, target, source_table_schema=source))
```

```text
Schema({'id': Int64, 'code': Null})
Schema({'id': Int32, 'code': String})
shape: (2, 2)
┌─────┬──────┐
│ id  ┆ code │
│ --- ┆ ---  │
│ i32 ┆ str  │
╞═════╪══════╡
│ 1   ┆ NONE │
│ 2   ┆ NONE │
└─────┴──────┘
```

With no source schema, an all-null column gets the Polars `Null` type. `convert` resolves source dtypes per column: the source schema first, then dataclass or Pydantic annotations, then inference from the values. A source field left as `type="any"` with no `dtype` declares nothing. Target conversion adds and replaces columns but keeps the others: a field with `rename_from` adds the renamed column next to its source. Use `ma.relation(data).conform(schema)` when the output must have exactly the declared columns. Pass `inline_conform=False` to apply only the source typing.
