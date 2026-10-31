"""Compare a plain filter with a ternary filter that keeps unknown amounts."""

from datetime import date

import mountainash as ma
import polars as pl


def orders_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "order_id": [1, 2, 3, 4, 5, 6],
            "customer_id": [10, 11, 10, 12, 11, 12],
            "amount": [120.0, 80.0, None, 200.0, 50.0, 95.0],
            "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending"],
            "ordered_at": [
                date(2026, 1, 5), date(2026, 1, 9), date(2026, 2, 2),
                date(2026, 2, 14), date(2026, 3, 1), date(2026, 3, 20),
            ],
        }
    )



def main() -> None:
    plan = ma.relation(orders_frame())

    plain = plan.filter(ma.col("amount") > 90).sort("order_id").to_dicts()
    amount = ma.t_col("amount", unknown={None}).t_gt(90)
    explicit = plan.filter(amount.t_maybe_true()).sort("order_id").to_dicts()
    flagged = (
        plan.with_columns(amount.t_is_unknown().alias("unknown"))
        .filter(ma.col("unknown"))
        .select("order_id")
        .to_dicts()
    )

    plain_ids = {row["order_id"] for row in plain}
    explicit_ids = {row["order_id"] for row in explicit}
    assert explicit_ids - plain_ids == {3}
    assert plain_ids < explicit_ids
    assert [row["order_id"] for row in flagged] == [3]
    print("plain filter   ", sorted(plain_ids))
    print("keep unknowns  ", sorted(explicit_ids))
    print("flagged unknown", [row["order_id"] for row in flagged])


if __name__ == "__main__":
    main()
