"""Conform messy input to the orders schema and read the drift report."""

import mountainash as ma
import polars as pl
from mountainash.typespec import UniversalType


def main() -> None:
    schema = ma.TableSchema(
        fields={
            "order_id": ma.FieldDefinition(type=UniversalType.INTEGER),
            "amount": ma.FieldDefinition(type=UniversalType.NUMBER),
            "status": ma.FieldDefinition(type=UniversalType.STRING),
            "ordered_at": ma.FieldDefinition(type=UniversalType.DATE),
        },
        fields_match="partial",
    )
    messy = pl.DataFrame(
        {
            "order_id": ["1", "2", "3"],
            "amount": ["120.0", "n/a", "50"],
            "status": ["shipped", "pending", "shipped"],
            "note": ["gift", "", "rush"],
        }
    )
    contract = {
        "extra_columns": "discard",
        "missing_columns": "null_fill",
        "data_type": "discard_value",
    }

    result = ma.relation(messy).conform(schema, contract=contract).collect_with_drift()
    typed = result.frame
    print(typed)

    drift = result.drift
    for change in drift.extra_columns + drift.missing_columns:
        print(change.name, change.action)
    for mismatch in drift.type_mismatches:
        print(mismatch.name, mismatch.declared, mismatch.actual, mismatch.action)
    print("compatible:", drift.compatible)

    assert typed.columns == ["order_id", "amount", "status", "ordered_at"]
    assert typed["order_id"].to_list() == [1, 2, 3]
    assert typed["amount"].to_list() == [120.0, None, 50.0]
    assert typed["ordered_at"].to_list() == [None, None, None]
    assert [c.name for c in drift.extra_columns] == ["note"]
    assert [c.name for c in drift.missing_columns] == ["ordered_at"]
    assert not drift.compatible


if __name__ == "__main__":
    main()
