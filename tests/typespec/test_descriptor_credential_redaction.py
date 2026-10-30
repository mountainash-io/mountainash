"""W8: URL userinfo never reaches descriptor errors or their displayed chains."""
from __future__ import annotations

import pytest
from mountainash_transport.location import LocationNotAllowed, LocationPolicy

import mountainash.typespec.descriptor_context as descriptor_context
from mountainash.typespec.datapackage import DataPackage
from mountainash.typespec.descriptor_context import (
    DefaultDescriptorResolver,
    DescriptorKind,
    normalize_base_uri,
    normalize_document_uri,
)
from mountainash.typespec.errors import (
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    InvalidDescriptorStructure,
)

SENTINEL = "SENTINEL0w8"
CREDENTIALED = f"https://user:{SENTINEL}@host.example"


def _displayed_chain(exc: BaseException):
    current: BaseException | None = exc
    while current is not None:
        yield current
        current = current.__cause__ or (None if current.__suppress_context__ else current.__context__)


def assert_clean(exc: BaseException) -> None:
    for link in _displayed_chain(exc):
        for text in (str(link), repr(link), repr(vars(link))):
            assert SENTINEL not in text, f"{type(link).__name__} leaks userinfo: {text}"


class _Resolver:
    def __init__(self, result):
        self.result = result

    def resolve(self, reference, *, base_uri, expected_kind):
        if isinstance(self.result, Exception):
            raise type(self.result)(f"{base_uri}{reference}")
        return self.result


def _resource(resolver, schema=f"{CREDENTIALED}/schema.json"):
    return DataPackage.from_descriptor(
        {"resources": [{"name": "r", "path": "r.csv", "schema": schema}]},
        base_uri=f"{CREDENTIALED}/pkg/",
        resolver=resolver,
    ).resources[0]


def test_base_uri_errors():
    with pytest.raises(InvalidDescriptorStructure) as caught:
        normalize_base_uri(f"{CREDENTIALED}:99999/")
    assert_clean(caught.value)


def test_document_uri_errors():
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        normalize_document_uri(f"{CREDENTIALED}:bad/schema.json", base_uri=None)
    assert_clean(caught.value)


def test_remote_reference_without_policy():
    with pytest.raises(LocationNotAllowed) as caught:
        DefaultDescriptorResolver().resolve(
            f"{CREDENTIALED}/schema.json", base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )
    assert_clean(caught.value)


@pytest.mark.parametrize(
    ("fetch", "error"),
    [
        (FileNotFoundError, DescriptorReferenceNotFound),
        (lambda url: b"{not json", DescriptorReferenceInvalid),
        (lambda url: b"[]", DescriptorReferenceInvalid),
    ],
)
def test_remote_fetch_errors(monkeypatch, fetch, error):
    def fake_read(url, policy):
        result = fetch(url)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(descriptor_context, "facade_read_bytes", fake_read)
    with pytest.raises(error) as caught:
        DefaultDescriptorResolver().resolve(
            f"{CREDENTIALED}/schema.json",
            base_uri=None,
            expected_kind=DescriptorKind.SCHEMA,
            policy=LocationPolicy(),
        )
    assert caught.value.normalized_reference == "https://***@host.example/schema.json"
    assert_clean(caught.value)


@pytest.mark.parametrize("raised", [FileNotFoundError(), PermissionError()])
def test_resolution_rewraps(raised):
    with pytest.raises(Exception) as caught:
        _resource(_Resolver(raised)).to_table_schema()
    assert_clean(caught.value)


def test_relative_reference_under_credentialed_base():
    with pytest.raises(Exception) as caught:
        _resource(_Resolver(PermissionError()), schema="schema.json").to_table_schema()
    assert_clean(caught.value)


def test_resolved_schema_with_invalid_structure():
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        _resource(_Resolver({"fields": [{"name": CREDENTIALED, "type": 1}]})).to_table_schema()
    assert_clean(caught.value)


def test_package_from_url_path():
    with pytest.raises(DescriptorReferenceNotFound) as caught:
        DataPackage.from_path(f"{CREDENTIALED}/datapackage.json")
    assert_clean(caught.value)
