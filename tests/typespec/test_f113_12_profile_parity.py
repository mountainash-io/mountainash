import pytest

from mountainash.typespec.datapackage import DataPackage, TableDialect
from mountainash.typespec.errors import UnsupportedDescriptorVersion
from mountainash.typespec.frictionless_invariants import is_recognized_v1_profile
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from tests.fixtures.f113_12_profile_cases import V1_DIALECT_MARKERS, V1_PROFILE_URIS


def _package(schema_url: str) -> dict[str, object]:
    return {"$schema": schema_url, "resources": [{"name": "orders", "path": "orders.csv"}]}


@pytest.mark.parametrize("profile_uri", V1_PROFILE_URIS)
def test_full_v1_uri_matrix_is_classified(profile_uri: str) -> None:
    assert is_recognized_v1_profile(profile_uri)
    with pytest.raises(UnsupportedDescriptorVersion):
        DataPackage.from_descriptor(_package(profile_uri))


@pytest.mark.parametrize("profile_uri", V1_PROFILE_URIS[:8])
def test_query_and_fragment_do_not_change_profile_identity(profile_uri: str) -> None:
    for suffix in ("?x=1", "#fragment", "?x=1#fragment"):
        assert is_recognized_v1_profile(profile_uri + suffix)


@pytest.mark.parametrize("marker,required_form", V1_DIALECT_MARKERS)
def test_raw_dialect_markers_have_shared_public_error(marker, required_form) -> None:
    with pytest.raises(UnsupportedDescriptorVersion) as caught:
        DataPackage.from_descriptor(
            {"resources": [{"name": "orders", "path": "orders.csv", "dialect": marker}]}
        )
    assert caught.value.required_form == required_form


@pytest.mark.parametrize("profile_uri", V1_PROFILE_URIS[:4])
def test_typed_schema_profile_boundary_matches_raw(profile_uri: str) -> None:
    with pytest.raises(UnsupportedDescriptorVersion):
        TypeSpec(
            fields=[FieldSpec(name="id", type=UniversalType.INTEGER)],
            schema_url=profile_uri,
        )


@pytest.mark.parametrize("profile_uri", V1_PROFILE_URIS[:4])
def test_typed_dialect_profile_boundary_matches_raw(profile_uri: str) -> None:
    with pytest.raises(UnsupportedDescriptorVersion):
        TableDialect(schema_url=profile_uri)
