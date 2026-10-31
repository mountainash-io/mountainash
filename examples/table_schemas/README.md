# Table schemas

How do I declare a schema, extract one from data and write it as a Frictionless descriptor?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
python examples/table_schemas/example.py
```

Expected output:

```text
declared: ['order_id', 'customer_id', 'amount', 'status', 'ordered_at'] ['order_id']
from frame: {'order_id': 'integer', 'customer_id': 'integer', 'amount': 'number', 'status': 'string', 'ordered_at': 'date'}
from dataclass: {'order_id': 'integer', 'customer_id': 'integer', 'amount': 'number', 'status': 'string', 'ordered_at': 'date'}
round trip equal: True
descriptor keys: ['fields', 'primaryKey', 'title']
```

`ma.TableSchema` declares the orders fields with their types, constraints and primary key. `extract_from_dataframe` and `extract_from_dataclass` build schemas from a Polars frame and from a dataclass, and the script asserts that both have the declared field names and types. `to_frictionless()` produces a descriptor, the script writes it as JSON in a temporary directory, and `TableSchema.from_frictionless` reads it back to an equal schema.

Book: [Extracting and converting schemas](https://docs.mountainash.io/mountainash/chapters/10-table-schemas-and-datapackage/#extracting-and-converting-schemas) and [Frictionless descriptors](https://docs.mountainash.io/mountainash/chapters/10-table-schemas-and-datapackage/#frictionless-descriptors). Next: [conform_and_drift](../conform_and_drift/).
