"""Collect one small relation as dicts, tuples, dataclasses and Pydantic models."""

from dataclasses import dataclass

import mountainash as ma
import polars as pl
import pydantic


@dataclass
class Order:
    order_id: int
    amount: float
    note: str = "none"


class OrderModel(pydantic.BaseModel):
    order_id: str
    amount: float


def main() -> None:
    orders = pl.DataFrame(
        {
            "order_id": [1, 2, 3],
            "customer_id": [10, 11, 10],
            "amount": [120.0, 80.0, 50.0],
        }
    )
    plan = ma.relation(orders).select("order_id", "amount").sort("order_id")

    dicts = plan.to_dicts()
    tuples = plan.to_tuples()
    columns = plan.to_dict()
    dataclasses_ = plan.to_dataclasses(Order)
    plain = plan.to_dataclasses(Order, apply_defaults=True)
    models = plan.to_pydantic(OrderModel)

    print("dicts:", dicts[0])
    print("tuples:", tuples[0])
    print("columns:", columns)
    print("dataclass:", dataclasses_[0])
    print("dataclass with defaults:", plain[0])
    print("pydantic:", models[0])

    assert dicts == [{"order_id": 1, "amount": 120.0}, {"order_id": 2, "amount": 80.0}, {"order_id": 3, "amount": 50.0}]
    assert [tuple(t) for t in tuples][0] == (1, 120.0)
    assert all(isinstance(item, Order) for item in dataclasses_)
    assert [item.order_id for item in models] == ["1", "2", "3"]


if __name__ == "__main__":
    main()
