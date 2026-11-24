"""Write a reusable relation rule as a function and run it on Polars and DuckDB."""

import ibis
import mountainash as ma
import polars as pl
from mountainash.validation import RelationRule, ValidationRunner


def at_most_per_key(key, limit):
    """No value of `key` may appear in more than `limit` rows."""
    return RelationRule(
        id=f"{key}_at_most_{limit}",
        plan=lambda rel: rel.group_by(key)
        .agg(ma.count_records().alias("n"))
        .filter(ma.col("n").gt(limit)),
    )


def summarise(source, rules):
    result = ValidationRunner().validate_relation(ma.relation(source), rules)
    return [
        (row["check_id"], row["status"], row["fail_count"])
        for row in result.check_summaries.sort("check_id").to_dicts()
    ]


def main() -> None:
    data = {
        "order_id": [1, 2, 3, 4, 5, 6],
        "status": ["shipped", "pending", "shipped", "cancelled", "shipped", "pending"],
    }
    rules = [at_most_per_key("status", 2), at_most_per_key("status", 3)]

    polars_summary = summarise(pl.DataFrame(data), rules)
    duckdb_summary = summarise(ibis.duckdb.connect().create_table("orders", data), rules)

    print("polars:", polars_summary)
    print("duckdb:", duckdb_summary)

    assert polars_summary == duckdb_summary
    assert polars_summary == [
        ("status_at_most_2", "failed", 1),
        ("status_at_most_3", "passed", 0),
    ]


if __name__ == "__main__":
    main()
