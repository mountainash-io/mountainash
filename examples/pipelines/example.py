"""Run a three-unit pipeline with a file checkpoint, then run it again and reuse the export."""

import tempfile
from pathlib import Path

import mountainash as ma
import polars as pl
from mountainash.pipelines import FileCheckpoint, ParquetDirectorySink, Pipeline, Runner, WriteMode, unit


@unit(name="orders")
def orders(ctx):
    return pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6],
            "customer_id": [10, 11, 10, 12, 11, 12],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0],
            "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending"],
        }
    )


@unit(name="totals", depends_on=("orders",))
def totals(orders, ctx):
    return (
        ma.relation(orders)
        .filter(ma.col("status") == "shipped")
        .group_by("customer_id")
        .agg(ma.col("amount").sum().alias("total"))
        .sort("customer_id")
        .to_polars()
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "run-state"
        export = ParquetDirectorySink(
            Path(tmp) / "totals", name="export", depends_on=("totals",), mode=WriteMode.REPLACE
        )
        pipeline = Pipeline("daily").add(orders).add(totals).add(export)
        first = Runner(pipeline, checkpoint=FileCheckpoint(state)).run()
        second = Runner(pipeline, checkpoint=FileCheckpoint(state)).run()

    print("first run: ", {name: status.value for name, status in first.statuses.items()})
    print("second run:", {name: status.value for name, status in second.statuses.items()})
    print("rows exported:", second.values["export"].payload.record_count)
    assert second.statuses["export"].value == "reused"
    assert second.statuses["orders"].value == "complete"
    assert second.values["export"].payload.record_count == 2


if __name__ == "__main__":
    main()
