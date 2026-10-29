import json, os
import pytest
import mountainash as ma
from mountainash.core.location import resolve_resource_location, resource_policy
from mountainash_transport.location import LocationPolicy


def _pkg(root, path):
    p = root / "datapackage.json"
    p.write_text(json.dumps({"name": "p", "resources": [{"name": "r", "path": path}]}))
    return p


def test_default_load_has_no_policy_and_resolves_at_descriptor_dir(tmp_path, monkeypatch):
    # Owner default OFF: loading never manufactures a LocationPolicy, yet descriptor-relative
    # resolution (a base concern, independent of confinement) is unchanged.
    other = tmp_path / "other"; other.mkdir()
    desc = tmp_path / "desc"; desc.mkdir()
    pkg = ma.DataPackage.from_path(_pkg(desc, "a.csv"))
    monkeypatch.chdir(other)
    assert resource_policy(pkg.resources[0]) is None
    assert resolve_resource_location(pkg.resources[0], "a.csv") == os.path.join(os.path.realpath(desc), "a.csv")


def test_explicit_none_policy_is_off(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=None)
    assert resource_policy(pkg.resources[0]) is None


def test_from_path_with_explicit_policy_roots_at_descriptor_dir(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=LocationPolicy())
    assert os.path.realpath(resource_policy(pkg.resources[0]).root) == os.path.realpath(tmp_path)


def test_default_load_reads_outside_descriptor_dir_and_survives_chdir(tmp_path, monkeypatch):
    # Owner default OFF (spec A1): an absolute outside path is readable, and a later chdir
    # does not move a relative resource.
    from mountainash.core.resource_ref import ResourceRef

    desc = tmp_path / "desc"; desc.mkdir()
    elsewhere = tmp_path / "elsewhere"; elsewhere.mkdir()
    outside = tmp_path / "outside.csv"; outside.write_bytes(b"v\n9\n")
    (desc / "a.csv").write_bytes(b"v\n1\n")
    (elsewhere / "a.csv").write_bytes(b"v\n2\n")
    pkg = ma.DataPackage.from_path(_pkg(desc, "a.csv"))
    monkeypatch.chdir(elsewhere)
    assert ResourceRef(pkg.resources[0]).read_bytes() == b"v\n1\n"
    abs_pkg = ma.DataPackage.from_json(json.dumps(
        {"name": "p", "resources": [{"name": "r", "path": str(outside)}]}))
    assert ResourceRef(abs_pkg.resources[0]).read_bytes() == b"v\n9\n"


def test_explicit_policy_rejects_absolute_outside_read_bytes(tmp_path):
    # Retained enabled protection: explicit confinement still denies before reading.
    from mountainash.core.resource_ref import ResourceRef
    from mountainash_transport.location import LocationNotAllowed

    root = tmp_path / "root"; root.mkdir()
    outside = tmp_path / "outside.csv"; outside.write_bytes(b"v\n9\n")
    pkg = ma.DataPackage.from_json(
        json.dumps({"name": "p", "resources": [{"name": "r", "path": str(outside)}]}),
        base_uri=root, policy=LocationPolicy())
    with pytest.raises(LocationNotAllowed):
        ResourceRef(pkg.resources[0]).read_bytes()


def test_explicit_policy_root_does_not_retarget_declared_base(tmp_path):
    # A policy root constrains a resolved location; it never rewrites which file the
    # base-relative path names (spec 3.3).
    from mountainash.core.resource_ref import ResourceRef
    from mountainash_transport.location import LocationNotAllowed

    base = tmp_path / "base"; base.mkdir()
    root = tmp_path / "root"; root.mkdir()
    (base / "x.csv").write_bytes(b"right")
    (root / "x.csv").write_bytes(b"wrong")
    pkg = ma.DataPackage.from_json(
        json.dumps({"name": "p", "resources": [{"name": "r", "path": "x.csv"}]}),
        base_uri=base, policy=LocationPolicy(root=str(root)))
    with pytest.raises(LocationNotAllowed):
        ResourceRef(pkg.resources[0]).read_bytes()
    off = ma.DataPackage.from_json(
        json.dumps({"name": "p", "resources": [{"name": "r", "path": "x.csv"}]}), base_uri=base)
    assert ResourceRef(off.resources[0]).read_bytes() == b"right"


def test_allow_list_only_policy_keeps_descriptor_root(tmp_path):
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), policy=LocationPolicy(allowed_remote={"https": frozenset()}))
    pol = resource_policy(pkg.resources[0])
    assert os.path.realpath(pol.root) == os.path.realpath(tmp_path) and pol.allowed_remote


def test_from_json_without_base_anchors_at_load_time_cwd(tmp_path, monkeypatch):
    a = tmp_path / "a"; b = tmp_path / "b"; a.mkdir(); b.mkdir()
    monkeypatch.chdir(a)
    doc = json.dumps({"name": "p", "resources": [{"name": "r", "path": "x.csv"}]})
    pkg = ma.DataPackage.from_json(doc)
    confined = ma.DataPackage.from_json(doc, policy=LocationPolicy())
    monkeypatch.chdir(b)  # a later chdir must not move the base, with or without confinement
    assert resource_policy(pkg.resources[0]) is None
    assert resolve_resource_location(pkg.resources[0], "x.csv") == os.path.join(os.path.realpath(a), "x.csv")
    assert os.path.realpath(resource_policy(confined.resources[0]).root) == os.path.realpath(a)
    assert resolve_resource_location(confined.resources[0], "x.csv") == os.path.join(os.path.realpath(a), "x.csv")


@pytest.mark.parametrize("base", ["https://host.example/pkg/", "s3://bucket/pkg/"])
def test_remote_base_grants_no_permission_and_roots_at_cwd_when_confined(tmp_path, monkeypatch, base):
    monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "d/a.csv"}]}),
                                   base_uri=base, policy=LocationPolicy())
    pol = resource_policy(pkg.resources[0])
    assert pol.allowed_remote == {} and os.path.realpath(pol.root) == os.path.realpath(tmp_path)
    assert resolve_resource_location(pkg.resources[0], "d/a.csv") == base + "d/a.csv"


@pytest.mark.parametrize("base", ["https://host.example/pkg/", "s3://bucket/pkg/"])
def test_remote_base_default_is_unconfined(tmp_path, monkeypatch, base):
    monkeypatch.chdir(tmp_path)
    pkg = ma.DataPackage.from_json(json.dumps({"name": "p", "resources": [{"name": "r", "path": "d/a.csv"}]}),
                                   base_uri=base)
    assert resource_policy(pkg.resources[0]) is None
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


@pytest.mark.parametrize("policy", ["default", "explicit"])
@pytest.mark.parametrize("op", ["model_copy", "resource_validate", "package_validate"])
def test_policy_survives_copy_and_revalidation(tmp_path, op, policy):
    kw = {"policy": LocationPolicy()} if policy == "explicit" else {}
    pkg = ma.DataPackage.from_path(_pkg(tmp_path, "a.csv"), **kw)
    original = resource_policy(pkg.resources[0])
    r = pkg.resources[0]
    if op == "model_copy": r = r.model_copy(update={"name": "r2"})
    if op == "resource_validate": r = type(r).model_validate(r)
    if op == "package_validate": r = type(pkg).model_validate(pkg).resources[0]
    assert resource_policy(r) == original
    assert (original is None) == (policy == "default")
    assert resolve_resource_location(r, "a.csv") == os.path.join(os.path.realpath(tmp_path), "a.csv")


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


def test_datacontract_loader_resolves_schema_beside_source_regardless_of_cwd(tmp_path, monkeypatch):
    # Public outcome only: the source-parent base is independent of confinement and cwd.
    schema = tmp_path / "s.json"
    schema.write_text(json.dumps({"fields": [{"name": "a", "type": "integer"}]}))
    elsewhere = tmp_path / "elsewhere"; elsewhere.mkdir()
    (elsewhere / "s.json").write_text(json.dumps({"fields": [{"name": "wrong", "type": "integer"}]}))
    monkeypatch.chdir(elsewhere)
    assert list(ma.datacontract(schema).__table_schema__.fields) == ["a"]


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


def test_relative_root_with_symlink_dotdot_not_collapsed(tmp_path, monkeypatch):
    from mountainash.core.resource_ref import ResourceRef

    safe = tmp_path / "safe"; (safe / "sub").mkdir(parents=True)
    cwd = tmp_path / "cwd"; cwd.mkdir()
    (cwd / "link").symlink_to(safe / "sub")
    (safe / "a.csv").write_bytes(b"ok")
    (cwd / "x.csv").write_bytes(b"no")
    monkeypatch.chdir(cwd)

    def load(base, path):
        d = {"name": "p", "resources": [{"name": "r", "path": path}]}
        pkg = ma.DataPackage.from_json(json.dumps(d), base_uri=base, policy=LocationPolicy(root="link/.."))
        return ResourceRef(pkg.resources[0]).read_bytes()

    assert load(safe.as_uri() + "/", "a.csv") == b"ok"
    with pytest.raises(Exception):
        load(cwd.as_uri() + "/", "x.csv")


_BAD_SECRET = "https://user:secret@exam\uff0fple.com/x"


def _bad_resource(**kw):
    d = {"name": "p", "resources": [{"name": "r", "path": _BAD_SECRET, "format": "csv"}]}
    return ma.DataPackage.from_json(json.dumps(d), **kw).resources[0]


def _assert_sanitized(e):
    from mountainash_transport.location import LocationNotAllowed
    from traceback import format_exception
    assert isinstance(e.value, LocationNotAllowed)
    assert "secret" not in str(e.value)
    assert "secret" not in "".join(format_exception(e.value))


def test_loaded_malformed_credential_path_read_bytes_sanitized():
    from mountainash.core.resource_ref import ResourceRef
    from mountainash_transport.location import LocationNotAllowed
    with pytest.raises(LocationNotAllowed) as e:
        ResourceRef(_bad_resource(policy=LocationPolicy())).read_bytes()
    _assert_sanitized(e)


@pytest.mark.parametrize("target", ["polars", "ibis"])
def test_loaded_malformed_credential_path_collect_sanitized(target):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    from mountainash_transport.location import LocationNotAllowed
    rel = Relation(ResourceReadRelNode(resource=_bad_resource(policy=LocationPolicy())))
    with pytest.raises(LocationNotAllowed) as e:
        rel.collect(target=target)
    _assert_sanitized(e)


@pytest.mark.parametrize("loaded", [False, True], ids=["programmatic", "loaded-default-off"])
def test_unconfined_malformed_path_keeps_value_error(loaded):
    from mountainash.core.resource_ref import ResourceRef
    from mountainash.typespec.datapackage import DataResource
    from mountainash_transport.location import LocationNotAllowed
    res = _bad_resource() if loaded else DataResource(name="r", path=_BAD_SECRET, format="csv")
    with pytest.raises(ValueError) as e:
        ResourceRef(res).read_bytes()
    assert not isinstance(e.value, LocationNotAllowed)


@pytest.mark.parametrize("target", ["polars", "ibis"])
def test_joined_location_malformed_credential_sanitized(target):
    from mountainash.relations.core.relation_api.relation import Relation
    from mountainash.relations.core.relation_nodes.extensions_mountainash import ResourceReadRelNode
    from mountainash_transport.location import LocationNotAllowed
    d = {"name": "p", "resources": [{"name": "r", "path": "0user:secret@exam\uff0fple.com/x", "format": "csv"}]}
    res = ma.DataPackage.from_json(json.dumps(d), base_uri="/", policy=LocationPolicy()).resources[0]
    with pytest.raises(LocationNotAllowed) as e:
        Relation(ResourceReadRelNode(resource=res)).collect(target=target)
    _assert_sanitized(e)
