"""Round-trip integration tests: Python → relation transforms → Python."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

import mountainash as ma


@dataclass
class Product:
    name: str
    price: float


class TestRoundTripDicts:
    """Python dicts → relation → Python dicts."""

    def test_dicts_filter_to_dicts(self):
        data = [
            {"name": "Widget", "price": 9.99},
            {"name": "Gadget", "price": 24.99},
            {"name": "Doohickey", "price": 4.99},
        ]
        result = ma.relation(data).filter(
            ma.col("price").gt(5.0)
        ).sort("price").to_dicts()

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Widget"
        assert result[1]["name"] == "Gadget"

    def test_dicts_select_to_dicts(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        result = ma.relation(data).select("a", "c").to_dicts()
        assert result == [{"a": 1, "c": 3}]


class TestRoundTripDataclasses:
    """Python dicts → relation → dataclass instances."""

    def test_dicts_to_dataclasses(self):
        data = [
            {"name": "Widget", "price": 9.99},
            {"name": "Gadget", "price": 24.99},
        ]
        result = ma.relation(data).sort("name").to_dataclasses(Product)

        assert len(result) == 2
        assert isinstance(result[0], Product)
        assert result[0].name == "Gadget"
        assert result[1].name == "Widget"

    def test_filter_to_dataclasses(self):
        data = [
            {"name": "Cheap", "price": 1.0},
            {"name": "Expensive", "price": 100.0},
        ]
        result = ma.relation(data).filter(
            ma.col("price").gt(50.0)
        ).to_dataclasses(Product)

        assert len(result) == 1
        assert result[0].name == "Expensive"
        assert result[0].price == 100.0


class TestRoundTripPydantic:
    """Python dicts → relation → Pydantic model instances."""

    def test_dicts_to_pydantic(self):
        try:
            from pydantic import BaseModel
        except ImportError:
            pytest.skip("pydantic not installed")

        class Item(BaseModel):
            name: str
            price: float

        data = [{"name": "Thing", "price": 5.0}]
        result = ma.relation(data).to_pydantic(Item)

        assert len(result) == 1
        assert isinstance(result[0], Item)
        assert result[0].name == "Thing"


class TestRoundTripWithSchema:
    """Python data → schema transform → relation → Python data."""

    def test_schema_apply_then_relation(self):
        import polars as pl

        # Raw data with string ages
        df = pl.DataFrame({"age": ["30", "25"], "name": ["Alice", "Bob"]})

        # Apply conform to cast types, then filter
        from mountainash.typespec.spec import FieldSpec, TypeSpec
        from mountainash.typespec.universal_types import UniversalType

        spec = TypeSpec(
            fields=[
                FieldSpec(name="age", type=UniversalType.INTEGER),
                FieldSpec(name="name", type=UniversalType.STRING),
            ],
        )
        result = (
            ma.relation(df)
            .conform(spec)
            .filter(ma.col("age").gt(28))
            .to_dicts()
        )

        assert len(result) == 1
        assert result[0]["name"] == "Alice"
