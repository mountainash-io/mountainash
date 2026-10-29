"""Cross-backend regression coverage for ``Relation.with_row_index``.

Narwhals lazy requires an explicit ``order_by`` and remains a strict native failure.
"""

from __future__ import annotations

import pytest

from fixtures.backend_registry import ALL_BACKENDS
from fixtures.call_expectations import expect_call_failure
from mountainash.relations import relation


@pytest.mark.cross_backend
@pytest.mark.parametrize("backend_name", ALL_BACKENDS)
class TestWithRowIndex:
    def test_with_row_index_adds_zero_based_sequence(self, backend_name, backend_factory):
        """Each supported backend adds a zero-based index; known failures
        exercise their exact public/native boundary."""
        data = {"name": ["a", "b", "c", "d"]}
        df = backend_factory.create(data, backend_name)

        with expect_call_failure(
            when=backend_name == "narwhals-lazy",
            reason="Narwhals LazyFrame.with_row_index() requires an explicit order_by.",
            errors=(TypeError,),
        ):
            result = relation(df).with_row_index(name="idx").collect()

            # Result type varies by backend; extract the idx column to a plain list.
            if hasattr(result, "execute"):
                idx_values = result.execute()["idx"].tolist()
            else:
                idx_values = list(result["idx"])

            assert idx_values == [0, 1, 2, 3], (
                f"[{backend_name}] Expected [0, 1, 2, 3], got {idx_values}"
            )
