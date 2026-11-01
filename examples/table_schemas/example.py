"""Declare a table schema, extract one from data, and round-trip a Frictionless descriptor."""

import json
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import mountainash as ma
import polars as pl
from mountainash.typespec import UniversalType, extract_from_dataclass, extract_from_dataframe


@dataclass
class Order:
    order_id: int
    customer_id: int
    amount: float
    status: str
    ordered_at: date


def main() -> None:
    orders_schema = ma.TableSchema(
        title="Orders",
        fields={
            "order_id": ma.FieldDefinition(type=UniversalType.INTEGER, required=True, unique=True),
            "customer_id": ma.FieldDefinition(type=UniversalType.INTEGER, required=True),
            "amount": ma.FieldDefinition(type=UniversalType.NUMBER, minimum=0),
            "status": ma.FieldDefinition(
                type=UniversalType.STRING, enum=["shipped", "pending", "cancelled"]
            ),
            "ordered_at": ma.FieldDefinition(type=UniversalType.DATE),
        },
        primary_key=["order_id"],
    )
    print("declared:", orders_schema.field_names, orders_schema.primary_key)

    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3],
            "customer_id": [10, 11, 10],
            "amount": [120.0, 80.0, None],
            "status": ["shipped", "pending", "shipped"],
            "ordered_at": [date(2026, 1, 5), date(2026, 1, 9), date(2026, 2, 2)],
        }
    )
    from_frame = extract_from_dataframe(orders)
    from_class = extract_from_dataclass(Order)
    print("from frame:", {name: str(f.type) for name, f in from_frame.fields.items()})
    print("from dataclass:", {name: str(f.type) for name, f in from_class.fields.items()})
    for extracted in (from_frame, from_class):
        assert extracted.field_names == orders_schema.field_names
        assert {n: f.type for n, f in extracted.fields.items()} == {
            n: f.type for n, f in orders_schema.fields.items()
        }

    descriptor = orders_schema.to_frictionless()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "orders.schema.json"
        path.write_text(json.dumps(descriptor, indent=2, sort_keys=True))
        loaded = ma.TableSchema.from_frictionless(json.loads(path.read_text()))
    assert loaded == orders_schema
    print("round trip equal:", loaded == orders_schema)
    print("descriptor keys:", sorted(descriptor))


if __name__ == "__main__":
    main()
