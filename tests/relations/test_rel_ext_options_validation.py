"""Build-time extension-options validation (spec §3.5): malformed extension
ops fail at node construction, not deep in backend compilation."""
from __future__ import annotations

import polars as pl
import pytest
from pydantic import ValidationError

from mountainash.relations.core.relation_nodes import ReadRelNode
from mountainash.relations.core.relation_nodes.extensions_mountainash import (
    ExtensionRelNode,
)
from mountainash.relations.core.relation_system.relation_keys.enums import (
    RKEY_MOUNTAINASH_REL,
)


def _read():
    return ReadRelNode(dataframe=pl.DataFrame({"a": [1]}))


def test_pivot_without_on_fails_at_construction():
    with pytest.raises(ValidationError, match="on"):
        ExtensionRelNode(
            input=_read(), operation=RKEY_MOUNTAINASH_REL.PIVOT, options={}
        )


def test_unknown_option_fails_at_construction():
    with pytest.raises(ValidationError, match="no_such_option"):
        ExtensionRelNode(
            input=_read(),
            operation=RKEY_MOUNTAINASH_REL.DROP_NULLS,
            options={"no_such_option": 1},
        )


def test_valid_options_pass():
    n = ExtensionRelNode(
        input=_read(),
        operation=RKEY_MOUNTAINASH_REL.PIVOT,
        options={"on": "k", "index": ["a"]},
    )
    assert n.options["on"] == "k"


def test_optional_params_may_be_omitted():
    n = ExtensionRelNode(
        input=_read(), operation=RKEY_MOUNTAINASH_REL.DROP_NULLS, options={}
    )
    assert n.options == {}
