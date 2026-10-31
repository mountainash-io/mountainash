"""Start relations from dicts, dataclass instances and Pydantic models."""

import datetime as dt
from dataclasses import dataclass

import mountainash as ma
import pydantic


@dataclass
class OrderRow:
    order_id: int
    customer_id: int
    amount: float
    ordered_at: dt.date


class OrderModel(pydantic.BaseModel):
    order_id: int
    customer_id: int
    amount: float
    ordered_at: dt.date


def main() -> None:
    records = [
        {"order_id": 1, "customer_id": 10, "amount": 120.0, "ordered_at": dt.date(2026, 1, 5)},
        {"order_id": 2, "customer_id": 11, "amount": 80.0, "ordered_at": dt.date(2026, 1, 9)},
        {"order_id": 5, "customer_id": 11, "amount": 50.0, "ordered_at": dt.date(2026, 3, 1)},
    ]
    sources = {
        "dicts": records,
        "dataclasses": [OrderRow(**record) for record in records],
        "pydantic": [OrderModel(**record) for record in records],
    }

    results = {}
    for label, data in sources.items():
        plan = ma.relation(data).filter(ma.col("amount") > 60).sort("order_id")
        results[label] = plan.to_dicts()
        print(label, [row["order_id"] for row in results[label]])

    print(results["dicts"][0])
    assert results["dicts"] == results["dataclasses"] == results["pydantic"]
    assert [row["order_id"] for row in results["dicts"]] == [1, 2]

    # A dict of lists is another shape the same entry point accepts.
    columns = {"customer_id": [10, 11], "region": ["north", "south"]}
    assert ma.relation(columns).to_dict() == columns


if __name__ == "__main__":
    main()
