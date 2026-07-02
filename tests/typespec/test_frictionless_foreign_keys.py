"""Round-trip tests for the reusable ForeignKey dict<->object helpers."""
from __future__ import annotations

from mountainash.typespec.frictionless import (
    foreign_key_from_dict,
    foreign_key_to_dict,
)
from mountainash.typespec.spec import ForeignKey, ForeignKeyReference


RAW = {
    "fields": ["customer_id"],
    "reference": {"resource": "customers", "fields": ["id"]},
}


def test_foreign_key_from_dict():
    fk = foreign_key_from_dict(RAW)
    assert fk.fields == ["customer_id"]
    assert fk.reference.resource == "customers"
    assert fk.reference.fields == ["id"]


def test_foreign_key_to_dict():
    fk = ForeignKey(
        fields=["customer_id"],
        reference=ForeignKeyReference(resource="customers", fields=["id"]),
    )
    assert foreign_key_to_dict(fk) == RAW


def test_round_trip_is_identity():
    assert foreign_key_to_dict(foreign_key_from_dict(RAW)) == RAW


def test_self_reference_empty_resource():
    raw = {"fields": ["parent_id"], "reference": {"resource": "", "fields": ["id"]}}
    fk = foreign_key_from_dict(raw)
    assert fk.reference.resource == ""
    assert foreign_key_to_dict(fk) == raw
