"""W8: URL secrets never reach descriptor errors or any link of their chains."""
from __future__ import annotations

from pathlib import Path

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
USERINFO_HOST = f"https://user:{SENTINEL}@host.example"


def userinfo_url(path: str) -> str:
    return f"{USERINFO_HOST}{path}"


def query_url(path: str) -> str:
    return f"https://host.example{path}?X-Amz-Signature={SENTINEL}&v=1"


SECRET_URLS = pytest.mark.parametrize("secret_url", [userinfo_url, query_url], ids=["userinfo", "query"])


def _chain(exc: BaseException):
    """Every linked exception, including a suppressed ``__context__``."""
    pending: list[BaseException | None] = [exc]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        pending += [current.__cause__, current.__context__]


def assert_clean(exc: BaseException) -> None:
    for link in _chain(exc):
        for text in (str(link), repr(link), repr(vars(link))):
            assert SENTINEL not in text, f"{type(link).__name__} leaks a URL secret: {text}"


class _Resolver:
    def __init__(self, result):
        self.result = result

    def resolve(self, reference, *, base_uri, expected_kind):
        if isinstance(self.result, Exception):
            raise type(self.result)(f"{base_uri} {reference}")
        return self.result


def _resource(resolver, schema, base_uri):
    return DataPackage.from_descriptor(
        {"resources": [{"name": "r", "path": "r.csv", "schema": schema}]},
        base_uri=base_uri,
        resolver=resolver,
    ).resources[0]


def test_base_uri_errors():
    with pytest.raises(InvalidDescriptorStructure) as caught:
        normalize_base_uri(f"{USERINFO_HOST}:99999/")
    assert_clean(caught.value)


def test_document_uri_errors():
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        normalize_document_uri(f"{USERINFO_HOST}:bad/schema.json", base_uri=None)
    assert_clean(caught.value)


@SECRET_URLS
def test_remote_reference_without_policy(secret_url):
    with pytest.raises(LocationNotAllowed) as caught:
        DefaultDescriptorResolver().resolve(
            secret_url("/schema.json"), base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )
    assert_clean(caught.value)


@SECRET_URLS
@pytest.mark.parametrize(
    ("fetch", "error"),
    [
        (FileNotFoundError, DescriptorReferenceNotFound),
        (lambda url: b"{not json", DescriptorReferenceInvalid),
        (lambda url: b"[]", DescriptorReferenceInvalid),
    ],
)
def test_remote_fetch_errors(monkeypatch, secret_url, fetch, error):
    def fake_read(url, policy):
        result = fetch(url)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(descriptor_context, "facade_read_bytes", fake_read)
    with pytest.raises(error) as caught:
        DefaultDescriptorResolver().resolve(
            secret_url("/schema.json"),
            base_uri=None,
            expected_kind=DescriptorKind.SCHEMA,
            policy=LocationPolicy(),
        )
    assert caught.value.normalized_reference.startswith("https://")
    assert_clean(caught.value)


@SECRET_URLS
@pytest.mark.parametrize("raised", [FileNotFoundError(), PermissionError()])
def test_resolution_rewraps(secret_url, raised):
    with pytest.raises(Exception) as caught:
        _resource(_Resolver(raised), secret_url("/schema.json"), secret_url("/pkg/")).to_table_schema()
    assert_clean(caught.value)


def test_relative_reference_under_credentialed_base():
    with pytest.raises(Exception) as caught:
        _resource(_Resolver(PermissionError()), "schema.json", userinfo_url("/pkg/")).to_table_schema()
    assert_clean(caught.value)


@SECRET_URLS
def test_resolved_schema_with_invalid_structure(secret_url):
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        _resource(
            _Resolver({"fields": [{"name": secret_url("/f"), "type": 1}]}),
            secret_url("/schema.json"),
            secret_url("/pkg/"),
        ).to_table_schema()
    assert_clean(caught.value)


@SECRET_URLS
@pytest.mark.parametrize("as_path", [False, True], ids=["str", "Path"])
def test_package_from_url_path(secret_url, as_path):
    url = secret_url("/datapackage.json")
    with pytest.raises(DescriptorReferenceNotFound) as caught:
        DataPackage.from_path(Path(url) if as_path else url)
    assert_clean(caught.value)


def test_clean_cause_is_kept():
    """Chains without secrets are preserved for debugging."""
    with pytest.raises(DescriptorReferenceNotFound) as caught:
        DataPackage.from_path("/no/such/datapackage.json")
    assert isinstance(caught.value.__cause__, FileNotFoundError)
