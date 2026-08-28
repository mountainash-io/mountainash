"""Declaration fingerprint compatibility tests."""
from __future__ import annotations

from mountainash.typespec._fingerprint import declaration_fingerprint
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation.plan import build_compiled_plan, freeze_typespec


def test_shared_fingerprint_matches_compiled_validation_plan():
    """A frozen TypeSpec has one canonical fingerprint at every consumer boundary."""
    spec = TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.OBJECT)])

    plan = build_compiled_plan(spec, ())

    assert declaration_fingerprint(freeze_typespec(spec)) == plan.declaration_fingerprint


def test_equivalent_typespec_declarations_have_matching_fingerprints():
    """Reconstructed equivalent declarations retain their stable identity."""
    first = TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])
    second = TypeSpec(fields=[FieldSpec(name="payload", type=UniversalType.ARRAY)])

    assert declaration_fingerprint(freeze_typespec(first)) == declaration_fingerprint(
        freeze_typespec(second)
    )
