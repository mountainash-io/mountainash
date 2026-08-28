"""Structured transport decoding and action-resolution tests."""
from __future__ import annotations

import math

import pytest

from mountainash.conform.structured_transport import (
    INVALID_STRUCTURED_VALUE,
    StructuredActionConsumer,
    StructuredCarrier,
    StructuredFieldPlan,
    StructuredRoot,
    decode_structured_value,
    resolve_structured_cell,
)


def make_plan(
    *,
    root: StructuredRoot = StructuredRoot.ARRAY,
    carrier: StructuredCarrier = StructuredCarrier.JSON_TEXT,
    action: str = "coerce",
    transforms: bool = True,
    null_fill: object | None = None,
) -> StructuredFieldPlan:
    return StructuredFieldPlan(
        field_name="payload",
        root=root,
        carrier=carrier,
        configured_action=action,
        apply_value_transforms=transforms,
        missing_values=("MISSING",),
        null_fill=null_fill,
        declaration_fingerprint="declaration",
        origin_node_id="node",
    )


@pytest.mark.parametrize(
    ("value", "root", "expected"),
    [
        (None, StructuredRoot.ARRAY, None),
        ("[]", StructuredRoot.ARRAY, []),
        ("{}", StructuredRoot.OBJECT, {}),
        ("[1, {\"nested\": [true, null]}]", StructuredRoot.ARRAY, [1, {"nested": [True, None]}]),
        (' { "\\u006eame" : "caf\\u00e9" } ', StructuredRoot.OBJECT, {"name": "café"}),
        (("item", {"nested": [1, 2]}), StructuredRoot.ARRAY, ["item", {"nested": [1, 2]}]),
        ({"item": (1, 2)}, StructuredRoot.OBJECT, {"item": [1, 2]}),
    ],
)
def test_decode_structured_value_normalizes_accepted_values(value, root, expected):
    """Each accepted physical value becomes its portable logical representation."""
    assert decode_structured_value(value, expected_root=root) == expected


@pytest.mark.parametrize(
    ("value", "root"),
    [
        ('{"a": 1, "a": 2}', StructuredRoot.OBJECT),
        ('{"a": {"b": 1, "b": 2}}', StructuredRoot.OBJECT),
        ("\ufeff[]", StructuredRoot.ARRAY),
        ("[", StructuredRoot.ARRAY),
        ("{}", StructuredRoot.ARRAY),
        ("[]", StructuredRoot.OBJECT),
        ("[NaN]", StructuredRoot.ARRAY),
        ("[Infinity]", StructuredRoot.ARRAY),
        ("[-Infinity]", StructuredRoot.ARRAY),
        ("[1e400]", StructuredRoot.ARRAY),
        ('{"value": 1e400}', StructuredRoot.OBJECT),
        ('{"nested": {"values": [1e400]}}', StructuredRoot.OBJECT),
        ({1: "not-a-string-key"}, StructuredRoot.OBJECT),
        ([math.nan], StructuredRoot.ARRAY),
        ([math.inf], StructuredRoot.ARRAY),
        (object(), StructuredRoot.ARRAY),
    ],
)
def test_decode_structured_value_returns_identity_sentinel_for_invalid_values(value, root):
    """Malformed, ambiguous, and non-finite values are never parsed permissively."""
    assert decode_structured_value(value, expected_root=root) is INVALID_STRUCTURED_VALUE

class _ExplosiveEquality:
    """Opaque carrier that must reach the decoder without sentinel comparison."""

    def __eq__(self, other):
        raise AssertionError("missing-value comparison inspected an opaque carrier")


def test_opaque_value_with_non_scalar_equality_resolves_as_invalid():
    """String missing sentinels must not compare arbitrary opaque physical values."""
    resolution = resolve_structured_cell(
        _ExplosiveEquality(),
        plan=make_plan(),
        consumer=StructuredActionConsumer.VALIDATION,
    )

    assert resolution.logical_value is INVALID_STRUCTURED_VALUE
    assert resolution.keep is True


def test_decode_structured_value_converts_parser_recursion_to_identity_sentinel(monkeypatch):
    """Parser recursion limits become data errors rather than terminal failures."""
    import mountainash.conform.structured_transport as transport

    def raise_recursion(*args, **kwargs):
        raise RecursionError("nested too deeply")

    monkeypatch.setattr(transport.json, "loads", raise_recursion)

    assert (
        decode_structured_value("[]", expected_root=StructuredRoot.ARRAY)
        is INVALID_STRUCTURED_VALUE
    )


@pytest.mark.parametrize(
    ("consumer", "transforms", "action", "valid_expected", "invalid_expected", "invalid_keep"),
    [
        (StructuredActionConsumer.LOGICAL_EGRESS, False, "coerce", "[1]", "bad", True),
        (StructuredActionConsumer.LOGICAL_EGRESS, False, "discard_value", "[1]", "bad", True),
        (StructuredActionConsumer.LOGICAL_EGRESS, False, "discard_row", "[1]", "bad", True),
        (StructuredActionConsumer.LOGICAL_EGRESS, False, "evolve", "[1]", "bad", True),
        (StructuredActionConsumer.LOGICAL_EGRESS, False, "freeze", "[1]", "bad", True),
        (StructuredActionConsumer.LOGICAL_EGRESS, True, "coerce", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.LOGICAL_EGRESS, True, "discard_value", [1], None, True),
        (StructuredActionConsumer.LOGICAL_EGRESS, True, "discard_row", [1], INVALID_STRUCTURED_VALUE, False),
        (StructuredActionConsumer.LOGICAL_EGRESS, True, "evolve", "[1]", "bad", True),
        (StructuredActionConsumer.LOGICAL_EGRESS, True, "freeze", "[1]", "bad", True),
        (StructuredActionConsumer.VALIDATION, False, "coerce", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, False, "discard_value", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, False, "discard_row", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, False, "evolve", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, False, "freeze", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, True, "coerce", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, True, "discard_value", [1], None, True),
        (StructuredActionConsumer.VALIDATION, True, "discard_row", [1], INVALID_STRUCTURED_VALUE, False),
        (StructuredActionConsumer.VALIDATION, True, "evolve", [1], INVALID_STRUCTURED_VALUE, True),
        (StructuredActionConsumer.VALIDATION, True, "freeze", [1], INVALID_STRUCTURED_VALUE, True),
    ],
)
def test_resolve_structured_cell_applies_consumer_action_matrix(
    consumer,
    transforms,
    action,
    valid_expected,
    invalid_expected,
    invalid_keep,
):
    """A wrong consumer/action branch changes a visible logical or row outcome."""
    plan = make_plan(action=action, transforms=transforms)

    valid = resolve_structured_cell("[1]", plan=plan, consumer=consumer)
    invalid = resolve_structured_cell("bad", plan=plan, consumer=consumer)

    assert valid.logical_value == valid_expected
    assert valid.keep is True
    assert invalid.logical_value is invalid_expected or invalid.logical_value == invalid_expected
    assert invalid.keep is invalid_keep


@pytest.mark.parametrize("missing", [None, "MISSING"])
def test_resolve_structured_cell_applies_valid_null_fill_after_missing_detection(missing):
    """Physical nulls and sentinels share the documented fill ordering."""
    resolution = resolve_structured_cell(
        missing,
        plan=make_plan(null_fill="[1]"),
        consumer=StructuredActionConsumer.VALIDATION,
    )

    assert resolution.post_missing_is_null is True
    assert resolution.logical_value == [1]
    assert resolution.keep is True


def test_discard_row_keeps_missing_value_with_invalid_null_fill_as_logical_null():
    """An invalid fill does not delete a row whose original value was missing."""
    resolution = resolve_structured_cell(
        "MISSING",
        plan=make_plan(action="discard_row", null_fill="not-json"),
        consumer=StructuredActionConsumer.VALIDATION,
    )

    assert resolution.post_missing_is_null is True
    assert resolution.logical_value is None
    assert resolution.keep is True


@pytest.mark.parametrize("backend_name", ["pandas", "narwhals-pandas"])
@pytest.mark.parametrize("missing_kind", ["pandas_na", "numpy_nan"])
def test_opaque_backend_null_scalars_use_structured_null_fill(
    backend_name, missing_kind, backend_factory
):
    """Opaque pandas cells carrying backend null scalars follow missing semantics."""
    import numpy as np
    import pandas as pd

    missing = pd.NA if missing_kind == "pandas_na" else np.nan
    frame = backend_factory.create({"payload": [[1], missing]}, backend_name)
    physical_value = frame["payload"].to_list()[1]
    plan = make_plan(
        carrier=StructuredCarrier.OPAQUE,
        null_fill=[99],
    )

    resolution = resolve_structured_cell(
        physical_value,
        plan=plan,
        consumer=StructuredActionConsumer.VALIDATION,
    )

    assert resolution.post_missing_is_null is True
    assert resolution.logical_value == [99]
