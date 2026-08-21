import json
from pathlib import Path

from mountainash.typespec.datapackage import DataPackage


def test_v2_descriptor_path_smoke(tmp_path: Path) -> None:
    schema = {
        "$schema": "https://datapackage.org/profiles/2.0/tableschema.json",
        "fields": [{"name": "id", "type": "integer"}],
    }
    dialect = {
        "$schema": "https://datapackage.org/profiles/2.0/tabledialect.json",
        "delimiter": ";",
    }
    descriptor = {
        "name": "smoke",
        "sources": [{"title": "catalog"}],
        "resources": [{
            "name": "orders",
            "path": "orders.csv",
            "type": "table",
            "schema": "schema.json",
            "dialect": "dialect.json",
        }],
    }
    (tmp_path / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
    (tmp_path / "dialect.json").write_text(json.dumps(dialect), encoding="utf-8")
    (tmp_path / "orders.csv").write_text("id\n1\n", encoding="utf-8")
    path = tmp_path / "datapackage.json"
    path.write_text(json.dumps(descriptor), encoding="utf-8")

    package = DataPackage.from_path(path)
    resource = package.resources[0]
    assert package._descriptor_context.base_uri == tmp_path.resolve().as_uri() + "/"
    assert resource.table_schema == "schema.json"
    assert resource.to_typespec().field_names == ["id"]
    assert resource.dialect == "dialect.json"
    assert resource.to_dialect().delimiter == ";"
    assert resource.effective_sources == [{"title": "catalog"}]

    preserve = package.to_descriptor()
    canonical = package.to_canonical_descriptor()
    preserve["resources"][0]["schema"] = "changed"
    canonical["sources"][0]["title"] = "changed"
    assert package.to_descriptor() == descriptor
    assert package.to_canonical_descriptor()["resources"][0]["schema"] == "schema.json"
