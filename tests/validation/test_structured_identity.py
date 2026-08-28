"""Structured identity and uniqueness: the canonical logical-key algebra
over JSON-transported ARRAY/OBJECT fields (spec section 15, Task 7 step 3).

Cross-backend keyed-identity mechanics (validate_keyed_identity against real
data across all backends, scalar keys only) live in
cross_backend/test_identity_keyed.py. This file covers the structured-value
specific contract: object-name order and JSON whitespace never affect
identity, boolean never equals number, an invalid component yields an
unknown outcome rather than a false duplicate, a discard-row value never
enters identity or uniqueness, and a composite key can mix scalar, ARRAY,
and OBJECT fields.
"""
from __future__ import annotations

import polars as pl
import pytest

import mountainash as ma
from mountainash.typespec.spec import FieldSpec, TypeSpec
from mountainash.typespec.universal_types import UniversalType
from mountainash.validation import ValidationRunner
from mountainash.validation.checks import ValueRule, ValueValidatorKey
from mountainash.validation.errors import IdentityInvalidError
from mountainash.validation.identity import RowIdentity
from mountainash.validation.value import INVALID_VALUE, canonical_value_key


# ---------------------------------------------------------------------------
# canonical_value_key(): pure-function equality contract (spec §15).
# ---------------------------------------------------------------------------


class TestCanonicalValueKeyStructuredEquality:
    def test_object_name_order_does_not_change_identity(self):
        first = canonical_value_key({"a": 1, "b": 2})
        second = canonical_value_key({"b": 2, "a": 1})
        assert first == second

    def test_json_whitespace_does_not_change_identity(self):
        from mountainash.conform.structured_transport import (
            StructuredRoot,
            decode_structured_value,
        )

        compact = decode_structured_value('{"a":1,"b":2}', expected_root=StructuredRoot.OBJECT)
        spaced = decode_structured_value(
            '{ "a" : 1 , "b" : 2 }', expected_root=StructuredRoot.OBJECT
        )
        assert canonical_value_key(compact) == canonical_value_key(spaced)

    def test_boolean_never_equals_number(self):
        assert canonical_value_key(True) != canonical_value_key(1)
        assert canonical_value_key(False) != canonical_value_key(0)

    def test_array_element_order_is_significant(self):
        """Unlike object names, array order IS part of array identity."""
        assert canonical_value_key([1, 2]) != canonical_value_key([2, 1])

    def test_invalid_value_is_its_own_distinct_key(self):
        assert canonical_value_key(INVALID_VALUE) == ("invalid",)
        assert canonical_value_key(INVALID_VALUE) != canonical_value_key(None)


# ---------------------------------------------------------------------------
# Integration: prepared-snapshot-backed identity and uniqueness.
# ---------------------------------------------------------------------------


def _structured_relation(rows: dict, *, action: str = "coerce"):
    df = pl.DataFrame(rows)
    fields = []
    if "tags" in rows:
        fields.append(FieldSpec(name="tags", type=UniversalType.ARRAY))
    if "meta" in rows:
        fields.append(FieldSpec(name="meta", type=UniversalType.OBJECT))
    for name in rows:
        if name not in {"tags", "meta"}:
            fields.append(FieldSpec(name=name, type=UniversalType.INTEGER))
    spec = TypeSpec(fields_match="open", fields=fields)
    return ma.relation(df).conform(spec, contract={"data_type": action})


class TestInvalidComponentUniqueness:
    def test_invalid_component_produces_unknown_not_a_duplicate(self):
        """An invalid decode is unknown, not a false positive duplicate:
        two independently-unparseable rows are never proven equal."""
        rel = _structured_relation({"meta": ['{"a":1}', "{broken", "{broken"]})
        result = ValidationRunner().validate_relation(
            rel,
            checks=[
                ValueRule(
                    id="meta_unique", fields=["meta"], validator=ValueValidatorKey.UNIQUE,
                    options={},
                )
            ],
        )
        summary = result.check_summaries.filter(pl.col("check_id") == "meta_unique")
        assert summary["unknown_count"].item() == 2
        assert summary["fail_count"].item() == 0


class TestDiscardRowExclusion:
    def test_discard_row_values_never_enter_identity_or_uniqueness(self):
        """A row removed by `discard_row` is gone before identity and
        uniqueness ever see it -- it cannot cause a spurious null-key or
        duplicate-key diagnostic (spec 12.5)."""
        rel = _structured_relation(
            {"id": [1, 2, 3], "meta": ['{"a":1}', "{broken", '{"a":1}']},
            action="discard_row",
        )
        result = ValidationRunner().validate_relation(
            rel, identity=RowIdentity("keyed", ("id",)), allow_imperfect_key=True,
        )
        # Row 2 (the malformed `meta` cell) is discarded before identity
        # runs; the remaining ids (1, 3) are both unique and non-null.
        assert result.identity_diagnostics["null_key_rows"] == 0
        assert result.identity_diagnostics["unknown_key_rows"] == 0
        assert result.identity_diagnostics["duplicate_key_tuples"] == 0


class TestCompositeStructuredKey:
    def test_composite_key_mixes_scalar_array_and_object_fields(self):
        rel = _structured_relation(
            {
                "id": [1, 1],
                "tags": ["[1,2]", "[1,2]"],
                "meta": ['{"a":1}', '{"a": 1}'],
            }
        )
        with pytest.raises(IdentityInvalidError):
            ValidationRunner().validate_relation(
                rel, identity=RowIdentity("keyed", ("id", "tags", "meta")),
            )
        # Same composite key on every row (JSON whitespace in `meta` does
        # not change identity) -- both rows collapse to one duplicate key.
        result = ValidationRunner().validate_relation(
            rel,
            identity=RowIdentity("keyed", ("id", "tags", "meta")),
            allow_imperfect_key=True,
        )
        assert result.identity_diagnostics["duplicate_key_tuples"] == 1

    def test_composite_key_distinguishes_structurally_different_values(self):
        rel = _structured_relation(
            {
                "id": [1, 1],
                "tags": ["[1,2]", "[2,1]"],
                "meta": ['{"a":1}', '{"a":1}'],
            }
        )
        result = ValidationRunner().validate_relation(
            rel,
            identity=RowIdentity("keyed", ("id", "tags", "meta")),
        )
        assert result.identity_diagnostics == {
            "null_key_rows": 0,
            "unknown_key_rows": 0,
            "duplicate_key_tuples": 0,
        }
