"""W8 design section 5 (test 2): no sentinel reaches any mountainash error surface.

Userinfo, query and fragment sentinels go through each public operation that can
fail with a location, with and without a location policy. Absent from ``str``,
``repr``, ``args``, ``vars``, every ``__cause__``/``__context__`` (recursively), the
formatted traceback and every log record emitted at DEBUG.
"""
from __future__ import annotations

import http.server
import json
import logging
import threading
import traceback
from pathlib import Path
from typing import Any, Callable

import pytest
from mountainash_transport.location import LocationPolicy

from mountainash.core.resource_ref import ResourceRef
from mountainash.exceptions import (
    DescriptorReferenceInvalid,
    InvalidDescriptorSyntax,
    InvalidDescriptorStructure,
)
from mountainash.typespec import FieldConstraints, FieldDefinition, TableSchema, UniversalType
from mountainash.typespec.datapackage import DataPackage, DataResource
from mountainash.typespec.descriptor_context import (
    DefaultDescriptorResolver,
    DescriptorKind,
    normalize_base_uri,
    normalize_document_uri,
)
from mountainash.validation import require_valid_table_schema
from mountainash.validation.jsonschema import compile_json_schema

SENTINELS = ("SENTU", "SENTP", "SENTQ", "SENTF")


def surfaces(exc: BaseException) -> list[str]:
    """Every text a caller can reach from *exc*, including hidden chain members."""
    out: list[str] = []
    seen: set[int] = set()
    stack: list[BaseException | None] = [exc]
    while stack:
        current = stack.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        out += [str(current), repr(current), repr(current.args), repr(vars(current))]
        for name in ("filename", "filename2"):
            out.append(repr(getattr(current, name, None)))
        stack += [current.__cause__, current.__context__]
    out.append("".join(traceback.format_exception(exc)))
    return out


def log_texts(caplog: pytest.LogCaptureFixture) -> list[str]:
    texts = []
    for record in caplog.records:
        texts += [record.getMessage(), repr(record.args), str(record.exc_text)]
        if record.exc_info:
            texts.append("".join(traceback.format_exception(*record.exc_info)))
    return texts


def assert_no_sentinel(exc: BaseException, logs: list[str] = ()) -> None:
    leaked = [text for text in [*surfaces(exc), *logs] if any(s in text for s in SENTINELS)]
    assert not leaked, leaked


def walk(operation: Callable[[], Any], caplog: pytest.LogCaptureFixture) -> BaseException:
    """Run *operation* with DEBUG logging captured; it must fail, cleanly."""
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(Exception) as caught:
            operation()
    assert_no_sentinel(caught.value, log_texts(caplog))
    return caught.value


LOCATIONS = {
    "userinfo": "https://SENTU:SENTP@host.example/d/x.json",
    "at-in-password": "https://SENTU:pa@SENTP@host.example/x.json",
    "query-and-fragment": "https://SENTU:SENTP@host.example/x.json?token=SENTQ#SENTF",
    "query-only": "https://host.example/x.json?X-Amz-Signature=SENTQ",
    "bare-query": "https://host.example/x.json?SENTQ",
    "fragment-token": "https://host.example/x.json#access_token=SENTF",
    "network-path": "//SENTU:SENTP@host.example/x.json?token=SENTQ#SENTF",
    "single-slash": "https:/SENTU:SENTP@host.example/x.json",
    "scheme-less": "SENTU:SENTP@host.example/x.json?token=SENTQ",
    "leading-whitespace": " \thttps://SENTU:SENTP@host.example/x.json",
    "unknown-scheme": "htps://SENTU:SENTP@host.example/x.json?token=SENTQ#SENTF",
    "malformed-port": "https://SENTU:SENTP@host.example:99999/x.json?token=SENTQ",
    "malformed-ipv6": "https://SENTU:SENTP@[host.example/x.json?token=SENTQ",
}

POLICIES = {
    "no-policy": None,
    "policy": LocationPolicy(allowed_remote={"https": frozenset({"host.example"})}),
    "empty-allow-list": LocationPolicy(allowed_remote={"https": frozenset()}),
}


def _package(entry: dict[str, Any], policy: LocationPolicy | None, **kwargs: Any) -> DataPackage:
    resource = {"name": "r", "path": "r.csv", **entry}
    if policy is None:
        return DataPackage.from_descriptor({"resources": [resource]}, **kwargs)
    return DataPackage.from_descriptor({"resources": [resource]}, policy=policy, **kwargs)


def _resolve(location, policy):
    return DefaultDescriptorResolver().resolve(
        location, base_uri=None, expected_kind=DescriptorKind.SCHEMA, policy=policy
    )


def _schema_reference(location, policy):
    return _package({"schema": location}, policy).resources[0].to_table_schema()


def _dialect_reference(location, policy):
    return _package({"dialect": location}, policy).resources[0].to_dialect()


def _relative_reference_under_base(location, policy):
    package = _package({"schema": "schema.json"}, policy, base_uri=location)
    return package.resources[0].to_table_schema()


def _resource_read_bytes(location, policy):
    return ResourceRef(_package({"path": location}, policy).resources[0]).read_bytes()


def _relation_collect(location, policy):
    package = _package({"path": location, "format": "csv"}, policy)
    return package.to_relation_dag().collect("r")


def _package_from_path(location, policy):
    return DataPackage.from_path(location, policy=policy)


def _package_from_path_object(location, policy):
    return DataPackage.from_path(Path(location), policy=policy)


def _package_write(location, policy):
    return DataPackage.from_descriptor({"resources": [{"name": "r", "path": "r.csv"}]}).write(location)


def _json_schema_reference(location, policy):
    return compile_json_schema({"$ref": location})


def _semantic_json_schema_reference(location, policy):
    schema = TableSchema(
        fields={
            "payload": FieldDefinition(
                type=UniversalType.OBJECT,
                constraints=FieldConstraints(json_schema={"$ref": location}),
            )
        }
    )
    return require_valid_table_schema(schema)


OPERATIONS = {
    "resolve": _resolve,
    "schema-reference": _schema_reference,
    "dialect-reference": _dialect_reference,
    "relative-reference-under-base": _relative_reference_under_base,
    "resource-read-bytes": _resource_read_bytes,
    "relation-collect": _relation_collect,
    "package-from-path": _package_from_path,
    "package-from-path-object": _package_from_path_object,
    "package-write": _package_write,
    "json-schema-reference": _json_schema_reference,
    "semantic-json-schema-reference": _semantic_json_schema_reference,
}

@pytest.mark.parametrize("policy", POLICIES.values(), ids=POLICIES.keys())
@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
@pytest.mark.parametrize("operation", OPERATIONS.values(), ids=OPERATIONS.keys())
def test_sentinels_stay_out_of_every_error_surface(operation, location, policy, caplog):
    walk(lambda: operation(location, policy), caplog)


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_normalisation_errors_stay_clean(location, caplog):
    """Canonical URIs may keep their userinfo internally; errors never show it."""
    for operation in (
        lambda: normalize_base_uri(location),
        lambda: normalize_document_uri(location, base_uri=None),
        lambda: normalize_document_uri("x.json", base_uri=location),
    ):
        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            try:
                operation()
            except Exception as exc:  # noqa: BLE001 - success is allowed for well-formed URLs
                assert_no_sentinel(exc, log_texts(caplog))
        assert not any(s in text for text in log_texts(caplog) for s in SENTINELS)


def test_canonical_uri_keeps_userinfo_for_resolution_and_caching_only() -> None:
    canonical = normalize_document_uri("https://SENTU:SENTP@host.example/a/x.json", base_uri=None)
    assert canonical == "https://SENTU:SENTP@host.example/a/x.json"


# --- shapes the descriptor layer builds from the caller's input ---------------------------


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_descriptor_error_attributes_hold_display_forms(location, caplog):
    error = walk(lambda: _resolve(location, None), caplog)
    for name in ("reference", "normalized_reference", "rejected_value", "descriptor_path"):
        assert not any(s in repr(getattr(error, name, None)) for s in SENTINELS)


def test_reference_attribute_is_the_display_form() -> None:
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        _package(
            {"schema": "https://SENTU:SENTP@host.example/s.json?token=SENTQ"},
            LocationPolicy(allowed_remote={"https": frozenset({"host.example"})}),
            resolver=_Resolver(RuntimeError("SENTQ")),
        ).resources[0].to_table_schema()
    assert caught.value.reference == "https://host.example/s.json"
    assert caught.value.rejected_value == "https://host.example/s.json"


class _Resolver:
    """Resolver whose native failure text and attributes carry the sentinels."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    def resolve(self, reference, *, base_uri, expected_kind):
        raise self.error


_NATIVE_FAILURES = {
    "free-text": lambda url: RuntimeError(f"cannot read {url}"),
    "oserror-with-filename": lambda url: FileNotFoundError(2, "No such file or directory", url),
    "permission-with-filename": lambda url: PermissionError(13, "Permission denied", url),
    "oserror-without-errno": lambda url: OSError(url),
    "value-error": lambda url: ValueError(url),
}


@pytest.mark.parametrize("failure", _NATIVE_FAILURES.values(), ids=_NATIVE_FAILURES.keys())
@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_resolver_native_failures_are_rewrapped_safely(failure, location, caplog):
    resolver = _Resolver(failure(location))
    walk(lambda: _package({"schema": location}, None, resolver=resolver, base_uri=None)
         .resources[0].to_table_schema(), caplog)


@pytest.mark.parametrize("failure", _NATIVE_FAILURES.values(), ids=_NATIVE_FAILURES.keys())
def test_ambient_context_is_not_reachable(failure, caplog):
    """An exception being handled when the error is raised must not stay in its context."""
    location = LOCATIONS["query-and-fragment"]
    resolver = _Resolver(failure(location))
    package = _package({"schema": location}, None, resolver=resolver)

    def operation():
        try:
            raise RuntimeError(f"ambient {location}")
        except RuntimeError:
            package.resources[0].to_table_schema()

    error = walk(operation, caplog)
    assert error.__context__ is None


def test_chained_oserror_has_no_filename() -> None:
    resolver = _Resolver(FileNotFoundError(2, "No such file or directory", LOCATIONS["userinfo"]))
    resource = _package({"schema": "schema.json"}, None, resolver=resolver).resources[0]
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        resource.to_table_schema()
    cause = caught.value.__cause__
    assert isinstance(cause, FileNotFoundError)
    assert (cause.errno, cause.filename) == (2, None)


def test_non_listed_native_exception_is_unreachable_through_either_chain() -> None:
    resolver = _Resolver(RuntimeError(LOCATIONS["query-and-fragment"]))
    resource = _package({"schema": "schema.json"}, None, resolver=resolver).resources[0]
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        resource.to_table_schema()
    assert caught.value.__cause__ is None and caught.value.__context__ is None
    assert "RuntimeError" not in str(caught.value)


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_resolved_schema_with_invalid_structure_and_nested_rejected_values(location, caplog):
    nested = {"fields": [{"name": location, "type": 1, "x": [{"deep": location}, (location,)]}]}
    resolver = _Resolver(RuntimeError("unused"))
    resolver.resolve = lambda reference, *, base_uri, expected_kind: nested
    error = walk(
        lambda: _package({"schema": location}, None, resolver=resolver).resources[0].to_table_schema(),
        caplog,
    )
    assert isinstance(error, (DescriptorReferenceInvalid, InvalidDescriptorStructure))


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_inline_descriptor_rejected_values_in_containers(location, caplog):
    def operation():
        DataPackage.from_descriptor({
            "resources": [{"name": "r", "path": "r.csv", "schema": {"fields": [
                {"name": {"nested": [location, {"k": location}]}, "type": "string"}
            ]}}]
        }).resources[0].to_table_schema()

    walk(operation, caplog)


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_pydantic_validation_failures(location, caplog):
    walk(lambda: DataResource(name="r", path="r.csv", bytes=location), caplog)
    walk(lambda: DataPackage.from_descriptor({"resources": [], "created": location}), caplog)
    walk(lambda: DataPackage.from_descriptor({"resources": [{"name": "r", "path": "r.csv", "bytes": location}]}), caplog)
    walk(lambda: DataPackage.model_validate({"resources": [], "created": location}), caplog)
    walk(lambda: DataPackage.model_validate_json(json.dumps({"resources": [], "created": location})), caplog)


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_malformed_descriptor_text_is_not_stored(location, tmp_path, caplog):
    """A location inside malformed JSON text is document content; the text is never kept."""
    text = '{"resources": [{"name": "r", "path": "' + location + '"}], '  # truncated: invalid JSON
    for operation in (
        lambda: DataPackage.from_json(text),
        lambda: DataPackage.model_validate_json(text),
        lambda: DataPackage.model_validate_json(text.encode()),
        lambda: DataPackage.model_validate_json(location.encode() + b"\xff"),
        lambda: DataPackage.from_json(location),
    ):
        error = walk(operation, caplog)
        assert isinstance(error, InvalidDescriptorSyntax)
    path = tmp_path / "datapackage.json"
    path.write_text(text, encoding="utf-8")
    error = walk(lambda: DataPackage.from_path(path), caplog)
    assert error.rejected_value is None


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_package_constructor_pydantic_rewrap(location, caplog):
    walk(lambda: DataPackage(resources=[], created=location), caplog)
    walk(lambda: DataPackage(resources=[], keywords=location), caplog)
    walk(lambda: DataPackage(resources=[{"name": "r", "path": "r.csv", "bytes": location}]), caplog)


@pytest.mark.parametrize("keyword", ["$ref", "$dynamicRef", "$recursiveRef"])
@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_json_schema_reference_keywords(keyword, location, caplog):
    walk(lambda: compile_json_schema({"properties": {"a": {keyword: location}}}), caplog)


@pytest.mark.parametrize("location", LOCATIONS.values(), ids=LOCATIONS.keys())
def test_invalid_json_schema_declaration_shows_only_the_error_class(location, caplog):
    error = walk(lambda: compile_json_schema({"$id": location, "type": location}), caplog)
    assert error.__cause__ is None and error.__context__ is None
    assert "SchemaError" in str(error)


def test_local_write_failure_keeps_its_type_and_path(tmp_path) -> None:
    target = tmp_path / "missing" / "datapackage.json"
    package = DataPackage.from_descriptor({"resources": [{"name": "r", "path": "r.csv"}]})
    with pytest.raises(FileNotFoundError) as caught:
        package.write(target)
    assert caught.value.filename == str(target) and caught.value.errno == 2
    assert caught.value.__cause__ is None


def test_upath_input_is_not_shown(caplog) -> None:
    upath = pytest.importorskip("upath")
    value = upath.UPath("s3://SENTU:SENTP@bucket/x.json?token=SENTQ")
    walk(lambda: DataPackage.from_path(value), caplog)


# --- transport-originated errors pass through; none carries a sentinel -------------------


class _NotFound(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib handler name
        self.send_response(404)
        self.end_headers()

    def log_message(self, *args):  # silence the stdlib access log
        pass


@pytest.fixture
def local_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _NotFound)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address[1]
    server.shutdown()
    server.server_close()
    thread.join()


def _remote(port: int, name: str = "x.json") -> str:
    return f"http://SENTU:SENTP@127.0.0.1:{port}/{name}?sig=SENTQ#SENTF"


HTTP_POLICY = LocationPolicy(allowed_remote={"http": frozenset({"127.0.0.1"})})
TRANSPORT_OPERATIONS = {
    "resolve": lambda url, policy: _resolve(url, policy),
    "schema-reference": lambda url, policy: _schema_reference(url, policy),
    "resource-read-bytes": lambda url, policy: _resource_read_bytes(url, policy),
    "relation-collect": lambda url, policy: _relation_collect(url, policy),
    "package-from-path": lambda url, policy: _package_from_path(url, policy),
}


@pytest.mark.parametrize("policy", [None, HTTP_POLICY], ids=["no-policy", "policy"])
@pytest.mark.parametrize("operation", TRANSPORT_OPERATIONS.values(), ids=TRANSPORT_OPERATIONS.keys())
def test_transport_not_found_errors(operation, policy, local_server, caplog):
    walk(lambda: operation(_remote(local_server), policy), caplog)


@pytest.mark.parametrize("policy", [None, HTTP_POLICY], ids=["no-policy", "policy"])
@pytest.mark.parametrize("operation", TRANSPORT_OPERATIONS.values(), ids=TRANSPORT_OPERATIONS.keys())
def test_transport_connection_errors(operation, policy, caplog):
    walk(lambda: operation(_remote(1), policy), caplog)


@pytest.mark.parametrize("operation", TRANSPORT_OPERATIONS.values(), ids=TRANSPORT_OPERATIONS.keys())
def test_transport_policy_errors(operation, caplog):
    other = LocationPolicy(allowed_remote={"http": frozenset({"other.example"})})
    walk(lambda: operation(_remote(80), other), caplog)


# --- end-to-end: a refusing policy never reaches the network ----------------------------


class _Counting(_NotFound):
    requests: list[str]

    def do_GET(self):  # noqa: N802 - stdlib handler name
        self.server.requests.append(self.path)
        body = b'{"fields": []}' if self.path.endswith(".json") else b"a\n1\n"
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture
def counting_server():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Counting)
    server.requests = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


REFUSE_HTTP = LocationPolicy(allowed_remote={"https": frozenset()})
ALLOW_LOCALHOST = LocationPolicy(allowed_remote={"http": frozenset({"127.0.0.1"})})
E2E_OPERATIONS = {
    "resolve": _resolve,
    "package-from-path": _package_from_path,
    "resource-read-bytes": _resource_read_bytes,
    "relation-collect": _relation_collect,
}


@pytest.mark.parametrize("operation", E2E_OPERATIONS.values(), ids=E2E_OPERATIONS.keys())
@pytest.mark.parametrize("scheme", ["http", "ftp", "gopher"])
def test_refusing_policy_makes_no_request(operation, scheme, counting_server):
    port = counting_server.server_address[1]
    with pytest.raises(Exception) as caught:
        operation(f"{scheme}://127.0.0.1:{port}/x.json", REFUSE_HTTP)
    assert counting_server.requests == []
    allowed_types = {"LocationNotAllowed", "DescriptorReferenceNotFound", "BackendNotImplementedError"}
    assert caught.type.__name__ in allowed_types, caught.type


@pytest.mark.parametrize("operation", E2E_OPERATIONS.values(), ids=E2E_OPERATIONS.keys())
def test_policy_on_other_host_makes_no_request(operation, counting_server):
    port = counting_server.server_address[1]
    other = LocationPolicy(allowed_remote={"http": frozenset({"other.example"})})
    with pytest.raises(Exception):
        operation(f"http://127.0.0.1:{port}/x.json", other)
    assert counting_server.requests == []


def test_allowed_host_succeeds(counting_server):
    port = counting_server.server_address[1]
    assert _resolve(f"http://127.0.0.1:{port}/s.json", ALLOW_LOCALHOST) == {"fields": []}
    assert _resource_read_bytes(f"http://127.0.0.1:{port}/r.csv", ALLOW_LOCALHOST) == b"a\n1\n"
    assert counting_server.requests == ["/s.json", "/r.csv"]
