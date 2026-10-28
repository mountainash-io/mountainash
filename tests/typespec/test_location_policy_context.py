import json, os
import pytest
import mountainash as ma
from mountainash.core.location import resolve_resource_location, resource_policy
from mountainash_transport.location import LocationPolicy


def _pkg(root, path):
    p = root / "datapackage.json"
    p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": path}]}))
    return p


def test_from_path_roots_at_descriptor_dir(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"))
    assert os.path.realpath(resource_policy(pkg.resources[0]).root) == os.path.realpath(tmp_path)


def test_allow_list_only_policy_keeps_descriptor_root(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=LocationPolicy(allowed_remote={"https": frozenset()}))
    pol = resource_policy(pkg.resources[0])
    assert os.path.realpath(pol.root) == os.path.realpath(tmp_path) and pol.allowed_remote


def test_from_json_without_base_roots_at_load_time_cwd(tmp_path, monkeypatch):
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    monkeypatch.chdir(a)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "x.csv"}]}))
    monkeypatch.chdir(b)  # a later chdir must not move the root or base
    assert os.path.realpath(resource_policy(pkg.resources[0]).root) == os.path.realpath(a)
    assert resolve_resource_location(pkg.resources[0], "x.csv") == os.path.join(os.path.realpath(a), "x.csv")


@pytest.mark.parametrize("base", ["https://host.example/pkg/", "s3://bucket/pkg/"])
def test_remote_base_grants_no_permission_and_roots_at_cwd(tmp_path, monkeypatch, base):
    monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "d/a.csv"}]}),
                                   base_uri=base)
    pol = resource_policy(pkg.resources[0])
    assert pol.allowed_remote == {} and os.path.realpath(pol.root) == os.path.realpath(tmp_path)
    assert resolve_resource_location(pkg.resources[0], "d/a.csv") == base + "d/a.csv"


def test_bare_path_joined_literally(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "report%20a.csv"))
    assert resolve_resource_location(pkg.resources[0], "report%20a.csv").endswith("report%20a.csv")


def test_programmatic_package_has_no_policy():
    pkg = ma.DataPackage(name="p", resources=[{"name": "r", "path": "/abs/a.csv"}])
    assert resource_policy(pkg.resources[0]) is None
    assert resolve_resource_location(pkg.resources[0], "rel.csv") == "rel.csv"


def test_opt_out_is_inactive(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=LocationPolicy(allow_unconfined=True))
    assert resource_policy(pkg.resources[0]) is None


@pytest.mark.parametrize("op", ["model_copy", "resource_validate", "package_validate"])
def test_policy_survives_copy_and_revalidation(tmp_path, op):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"))
    original = resource_policy(pkg.resources[0])
    r = pkg.resources[0]
    if op == "model_copy": r = r.model_copy(update={"name": "r2"})
    if op == "resource_validate": r = type(r).model_validate(r)
    if op == "package_validate": r = type(pkg).model_validate(pkg).resources[0]
    assert resource_policy(r) == original and resource_policy(r).root is not None


def test_opt_out_still_resolves_relative_to_descriptor(tmp_path, monkeypatch):
    d = tmp_path / "desc"; d.mkdir(); monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_path(_pkg(d, "a.csv"), policy=LocationPolicy(allow_unconfined=True))
    assert resolve_resource_location(pkg.resources[0], "a.csv") == os.path.join(os.path.realpath(d), "a.csv")


def test_opt_out_without_base_resolves_against_cwd_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "x.csv"}]}),
                                   policy=LocationPolicy(allow_unconfined=True))
    assert resolve_resource_location(pkg.resources[0], "x.csv") == os.path.join(os.path.realpath(tmp_path), "x.csv")


def test_descriptor_round_trip_unchanged(tmp_path):
    p = _pkg(tmp_path, "report%20a.csv")
    assert ma.DataPackage.from_path(p).to_descriptor()["resources"][0]["path"] == "report%20a.csv"


def test_datacontract_loader_roots_at_source_parent(tmp_path, monkeypatch):
    from mountainash.typespec.datapackage import DataPackage
    seen = []
    orig = DataPackage.from_descriptor.__func__

    def spy(cls, raw, **kw):
        pkg = orig(cls, raw, **kw)
        seen.append(pkg.resources[0])
        return pkg

    monkeypatch.setattr(DataPackage, "from_descriptor", classmethod(spy))
    schema = tmp_path / "s.json"
    schema.write_text(json.dumps({"fields": [{"name": "a", "type": "integer"}]}))
    ma.datacontract(schema)
    assert os.path.realpath(resource_policy(seen[0]).root) == os.path.realpath(tmp_path)


@pytest.mark.parametrize("base", ["https://[bad", "file://evilhost/tmp/"])
@pytest.mark.parametrize("loader", ["from_descriptor", "from_json"])
def test_malformed_base_keeps_descriptor_error(base, loader):
    from mountainash.typespec.errors import InvalidDescriptorStructure
    doc = {"name": "p", "resources": [{"name": "r", "path": "a.csv"}]}
    arg = doc if loader == "from_descriptor" else json.dumps(doc)
    with pytest.raises(InvalidDescriptorStructure):
        getattr(ma.DataPackage, loader)(arg, base_uri=base)


def test_relative_explicit_root_without_base_anchored_once(tmp_path, monkeypatch):
    from mountainash.core.resource_ref import ResourceRef

    (tmp_path / "data" / "data").mkdir(parents=True)
    (tmp_path / "data" / "a.csv").write_bytes(b"right")
    (tmp_path / "data" / "data" / "a.csv").write_bytes(b"wrong")
    monkeypatch.chdir(tmp_path)
    descriptor = {"name": "p", "resources": [{"name": "r", "path": "a.csv"}]}
    pkg = ma.DataPackage.from_json(json.dumps(descriptor), policy=LocationPolicy(root="data"))
    assert ResourceRef(pkg.resources[0]).read_bytes() == b"right"
