import pytest
from mountainash.typespec.datapackage import DataResource, TableDialect


def test_minimal_resource_with_path():
    r = DataResource(name="orders", path="orders.csv")
    assert r.name == "orders"
    assert r.path == "orders.csv"
    assert r.data is None


def test_resource_with_inline_data():
    r = DataResource(name="orders", data=[{"id": 1}, {"id": 2}])
    assert r.data == [{"id": 1}, {"id": 2}]
    assert r.path is None


def test_must_have_exactly_one_of_path_or_data():
    with pytest.raises(ValueError, match="exactly one of path or data"):
        DataResource(name="orders")
    with pytest.raises(ValueError, match="exactly one of path or data"):
        DataResource(name="orders", path="x.csv", data=[{"id": 1}])


def test_multi_file_path_array():
    r = DataResource(name="orders", path=["a.csv", "b.csv"])
    assert r.path == ["a.csv", "b.csv"]


def test_extras_preserved():
    raw = {"name": "orders", "path": "orders.csv", "futurePropX": 42}
    r = DataResource.from_descriptor(raw)
    assert r.extras == {"futurePropX": 42}
    assert r.to_descriptor() == raw


def test_dialect_round_trip():
    raw = {
        "name": "orders",
        "path": "orders.csv",
        "type": "table",
        "dialect": {"delimiter": ";"},
    }
    r = DataResource.from_descriptor(raw)
    assert isinstance(r.dialect, TableDialect)
    assert r.to_descriptor() == raw
