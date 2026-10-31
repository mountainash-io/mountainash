# DataPackage as a DAG

How do I load a multi-table package, derive a relation, check its foreign key and export it again?

[example.py](example.py): run from the repository root, after the [shared setup](../README.md#setup):

```bash
hatch run test:python examples/datapackage_dag/example.py
```

Expected output:

```text
resources: ['customers', 'orders']
constraint edges: {('customers', 'orders')}
{'customer_id': 10, 'total': 120.0}
{'customer_id': 11, 'total': 130.0}
{'customer_id': 12, 'total': 295.0}
{'customer_id': 99, 'total': 30.0}
foreign keys pass: False
fk__orders__customer_id__customers 99
exported: ['customers', 'order_totals', 'orders']
round trip: ['customers', 'order_totals', 'orders']
```

`DataPackage.from_path` reads `datapackage.json` and the CSV files beside it, and `to_relation_dag()` turns each resource into a named relation, with the declared foreign key recorded as a constraint edge from `customers` to `orders`. The recipe adds a derived relation, `order_totals`, collects it, and runs `validate` with each resource's table schema. The foreign-key check reports one failure case: customer 99, the customer on the synthetic order 7 that has no row in `customers`. `to_package()` returns the resources plus the derived one, `write` saves the descriptor to a temporary directory, and reading it back lists the same three names.

Book: [Resources and DataPackage](https://docs.mountainash.io/mountainash/chapters/14-relationdag/#resources-and-datapackage). Next: [pipelines](../pipelines/).
