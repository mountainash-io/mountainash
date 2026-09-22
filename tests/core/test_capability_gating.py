"""Native storage failures retain their actual operation attribution."""
from __future__ import annotations

import pytest

import mountainash as ma
from mountainash.core.types import BackendCapabilityError
from mountainash.expressions.core.expression_system.function_keys.enums import (
    FKEY_MOUNTAINASH_SCALAR_LIST as FK_LIST,
    FKEY_SUBSTRAIT_SCALAR_STRING as FK_STRING,
)


class TestNativeErrorEnrichment:
    @pytest.mark.parametrize(
        ("first", "operation", "native_issue"),
        [
            ("string", FK_STRING.SPLIT, "narwhals:arrow-string-storage"),
            ("list", FK_LIST.CONTAINS, "narwhals:arrow-list-storage"),
        ],
    )
    def test_native_failure_identifies_the_failing_operation(
        self, backend_factory, first, operation, native_issue,
    ):
        # Both expressions can raise TypeError on object-backed pandas data.
        # Exception class alone must not select the other operation's policy.
        dataframe = backend_factory.create(
            {"text": ["a,b,c"], "tags": [[1, 2, 3]]}, "narwhals-pandas",
        )
        expressions = [
            ma.col("text").str.string_split(",").name.alias("text_parts"),
            ma.col("tags").list.contains(2).name.alias("has_tag"),
        ]
        if first == "list":
            expressions.reverse()
        with pytest.raises(BackendCapabilityError) as raised:
            ma.relation(dataframe).select(*expressions).collect()
        assert raised.value.function_key is operation
        assert raised.value.limitation.native_issue == native_issue
        assert isinstance(raised.value.__cause__, TypeError)
        with ma.capability_policy(ma.CapabilityPolicy.native_debugging()):
            with pytest.raises(TypeError) as native:
                ma.relation(dataframe).select(*expressions).collect()
        assert type(native.value) is TypeError
