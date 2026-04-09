import pytest
from mountainash.typespec.datapackage import DataPackage, DataResource


def _r(name: str, **kw) -> DataResource:
    return DataResource(name=name, path=f"{name}.csv", **kw)


def test_minimal_package():
    pkg = DataPackage(resources=[_r("orders")])
    assert len(pkg.resources) == 1


def test_must_have_at_least_one_resource():
    with pytest.raises(ValueError, match="at least one resource"):
        DataPackage(resources=[])


def test_resource_names_must_be_unique():
    with pytest.raises(ValueError, match="duplicate resource name"):
        DataPackage(resources=[_r("orders"), _r("orders")])


def test_extras_preserved():
    raw = {
        "name": "demo",
        "resources": [{"name": "orders", "path": "orders.csv"}],
        "futureProp": "x",
    }
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.extras == {"futureProp": "x"}
    assert pkg.to_descriptor() == raw


def test_dollar_schema_preserved():
    raw = {
        "$schema": "https://datapackage.org/profiles/2.0/datapackage.json",
        "resources": [{"name": "orders", "path": "orders.csv"}],
    }
    pkg = DataPackage.from_descriptor(raw)
    assert pkg.dollar_schema == "https://datapackage.org/profiles/2.0/datapackage.json"
    assert pkg.to_descriptor()["$schema"] == raw["$schema"]
