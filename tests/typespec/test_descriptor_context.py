import importlib
import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from mountainash.exceptions import (
    DescriptorReferenceInvalid,
    DescriptorReferenceNotFound,
    DescriptorReferenceSchemeDenied,
    InvalidDescriptorStructure,
    MissingDescriptorBase,
)
from mountainash.typespec.descriptor_context import (
    DescriptorKind,
    LocalDescriptorResolver,
    StorageDescriptorResolver,
    build_descriptor_context,
    descriptor_cache_key,
    normalize_base_uri,
    normalize_document_uri,
)


def test_normalize_absolute_directory_path(tmp_path: Path) -> None:
    assert normalize_base_uri(tmp_path) == tmp_path.resolve().as_uri() + "/"


def test_normalize_hierarchical_uri_adds_trailing_slash() -> None:
    assert normalize_base_uri("https://EXAMPLE.com/a/../b") == "https://example.com/b/"


@pytest.mark.parametrize("value", ["relative/path", "mailto:test@example.com"])
def test_invalid_explicit_base_is_typed(value: str) -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        normalize_base_uri(value)
    assert caught.value.descriptor_path == "$base_uri"


def test_relative_path_object_base_is_typed() -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        normalize_base_uri(Path("relative/base"))
    assert caught.value.descriptor_path == "$base_uri"


def test_remote_repeated_slashes_are_preserved() -> None:
    assert normalize_document_uri(
        "https://example.com/a//schema.json",
        base_uri=None,
    ) == "https://example.com/a//schema.json"


def test_remote_dot_segments_preserve_repeated_slashes() -> None:
    assert normalize_document_uri(
        "https://example.com/a//b/../schema.json",
        base_uri=None,
    ) == "https://example.com/a//schema.json"


def test_remote_ipv6_literal_stays_bracketed() -> None:
    assert normalize_document_uri(
        "https://[2001:db8::1]/schema.json",
        base_uri=None,
    ) == "https://[2001:db8::1]/schema.json"


def test_malformed_base_uri_is_typed_with_cause() -> None:
    with pytest.raises(InvalidDescriptorStructure) as caught:
        normalize_base_uri("https://[bad")
    assert isinstance(caught.value.__cause__, ValueError)


def test_malformed_document_uri_is_typed_with_cause() -> None:
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        normalize_document_uri("https://[bad", base_uri=None)
    assert isinstance(caught.value.__cause__, ValueError)


def test_local_resolver_normalizes_path_and_file_uri(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text(json.dumps({"fields": []}), encoding="utf-8")
    resolver = LocalDescriptorResolver()
    from_path = resolver.resolve(
        str(path), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    )
    from_uri = resolver.resolve(
        path.as_uri(), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    )
    assert from_path == from_uri == {"fields": []}


def test_relative_reference_requires_base() -> None:
    with pytest.raises(MissingDescriptorBase):
        LocalDescriptorResolver().resolve(
            "schema.json", base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )


@pytest.mark.parametrize("reference", ["https://example.com/schema.json", "s3://bucket/schema.json"])
def test_default_resolver_denies_remote_scheme(reference: str) -> None:
    with pytest.raises(DescriptorReferenceSchemeDenied):
        LocalDescriptorResolver().resolve(
            reference, base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )


def test_local_resolver_missing_file_preserves_cause(tmp_path: Path) -> None:
    reference = tmp_path / "missing.json"
    with pytest.raises(DescriptorReferenceNotFound) as caught:
        LocalDescriptorResolver().resolve(
            str(reference), base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )
    assert isinstance(caught.value.__cause__, FileNotFoundError)


def test_local_resolver_malformed_json_preserves_cause(tmp_path: Path) -> None:
    reference = tmp_path / "malformed.json"
    reference.write_text("{not json", encoding="utf-8")
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        LocalDescriptorResolver().resolve(
            str(reference), base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )
    assert isinstance(caught.value.__cause__, json.JSONDecodeError)


@pytest.mark.parametrize("suffix", ["?version=1", "#schema"])
def test_local_resolver_rejects_query_or_fragment(suffix: str, tmp_path: Path) -> None:
    reference = f"{(tmp_path / 'schema.json').as_uri()}{suffix}"
    with pytest.raises(DescriptorReferenceInvalid):
        LocalDescriptorResolver().resolve(
            reference, base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )


def test_local_resolver_rejects_non_mapping_root(tmp_path: Path) -> None:
    reference = tmp_path / "list.json"
    reference.write_text("[]", encoding="utf-8")
    with pytest.raises(DescriptorReferenceInvalid) as caught:
        LocalDescriptorResolver().resolve(
            str(reference), base_uri=None, expected_kind=DescriptorKind.SCHEMA
        )
    assert caught.value.__cause__ is None


def test_storage_resolver_reads_allowed_scheme(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def read_bytes(reference: str) -> bytes:
        calls.append(reference)
        return b'{"fields": []}'

    module = importlib.import_module("mountainash.typespec.descriptor_context")
    monkeypatch.setattr(module, "facade_read_bytes", read_bytes)
    result = StorageDescriptorResolver(allowed_schemes={"HTTPS"}).resolve(
        "https://EXAMPLE.com:443/a/../schema.json?profile=v2",
        base_uri=None,
        expected_kind=DescriptorKind.SCHEMA,
    )
    assert result == {"fields": []}
    assert calls == ["https://example.com/schema.json?profile=v2"]

def test_storage_resolver_denies_unlisted_scheme() -> None:
    with pytest.raises(DescriptorReferenceSchemeDenied):
        StorageDescriptorResolver(allowed_schemes={"https"}).resolve(
            "s3://bucket/schema.json",
            base_uri=None,
            expected_kind=DescriptorKind.SCHEMA,
        )


def test_equivalent_local_forms_share_cache_key(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    assert descriptor_cache_key(
        str(path), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    ) == descriptor_cache_key(
        path.as_uri(), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    )


def test_storage_resolver_translates_transport_missing_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport_errors = pytest.importorskip("mountainash_transport._core.exceptions")

    def read_bytes(reference: str) -> bytes:
        raise transport_errors.PathNotFoundError(reference)

    module = importlib.import_module("mountainash.typespec.descriptor_context")
    monkeypatch.setattr(module, "facade_read_bytes", read_bytes)
    with pytest.raises(DescriptorReferenceNotFound) as caught:
        StorageDescriptorResolver(allowed_schemes={"https"}).resolve(
            "https://example.com/missing.json",
            base_uri=None,
            expected_kind=DescriptorKind.SCHEMA,
        )
    assert isinstance(caught.value.__cause__, transport_errors.PathNotFoundError)


def test_expected_kind_is_part_of_cache_key(tmp_path: Path) -> None:
    path = tmp_path / "descriptor.json"
    schema_key = descriptor_cache_key(
        str(path), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    )
    dialect_key = descriptor_cache_key(
        str(path), base_uri=None, expected_kind=DescriptorKind.DIALECT
    )
    assert schema_key != dialect_key


def test_caching_resolver_delegates_equivalent_references_once(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text('{"fields": []}', encoding="utf-8")

    class CachingResolver:
        def __init__(self) -> None:
            self.inner = LocalDescriptorResolver()
            self.cache: dict[tuple[str, DescriptorKind], Mapping[str, Any]] = {}
            self.reads = 0

        def resolve(
            self,
            reference: str,
            *,
            base_uri: str | None,
            expected_kind: DescriptorKind,
        ) -> Mapping[str, Any]:
            key = descriptor_cache_key(
                reference, base_uri=base_uri, expected_kind=expected_kind
            )
            if key not in self.cache:
                self.reads += 1
                self.cache[key] = self.inner.resolve(
                    reference, base_uri=base_uri, expected_kind=expected_kind
                )
            return self.cache[key]

    resolver = CachingResolver()
    assert resolver.resolve(
        str(path), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    ) == resolver.resolve(
        path.as_uri(), base_uri=None, expected_kind=DescriptorKind.SCHEMA
    )
    assert resolver.reads == 1


def test_build_descriptor_context_defaults_and_freezes_sources() -> None:
    sources = [{"name": "catalog"}]
    context = build_descriptor_context(
        base_uri=None, resolver=None, package_sources=sources
    )
    sources.append({"name": "later"})
    assert isinstance(context.resolver, LocalDescriptorResolver)
    assert context.package_sources == ({"name": "catalog"},)
