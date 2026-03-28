"""Integration tests for the Narwhals relation backend.

Exercises the full pipeline: relation(df) -> operations -> collect/to_pandas,
parametrized across pandas and PyArrow input types. Both are detected as
NARWHALS backend and wrapped transparently by narwhals.
"""

from __future__ import annotations

import pytest
import pandas as pd
import pyarrow as pa
import narwhals as nw

# Import the relation API
from mountainash.relations import relation

# Trigger backend registration (side-effect imports)
import mountainash.relations.backends.relation_systems.narwhals  # noqa: F401
import mountainash.expressions.backends  # noqa: F401


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_dicts(result) -> list[dict]:
    """Convert a narwhals/pandas/pyarrow result to a list of row dicts."""
    if hasattr(result, "to_pandas"):
        return result.to_pandas().to_dict("records")
    if isinstance(result, pd.DataFrame):
        return result.to_dict("records")
    # PyArrow table
    if hasattr(result, "to_pydict"):
        cols = result.to_pydict()
        n = len(next(iter(cols.values())))
        return [{k: cols[k][i] for k in cols} for i in range(n)]
    raise TypeError(f"Cannot convert {type(result)} to dicts")


def _to_pydict(result) -> dict[str, list]:
    """Convert a narwhals/pandas/pyarrow result to a column-oriented dict."""
    if hasattr(result, "to_pandas"):
        df = result.to_pandas()
        return {c: df[c].tolist() for c in df.columns}
    if isinstance(result, pd.DataFrame):
        return {c: result[c].tolist() for c in result.columns}
    if hasattr(result, "to_pydict"):
        return {k: list(v) for k, v in result.to_pydict().items()}
    raise TypeError(f"Cannot convert {type(result)} to pydict")


def _row_count(result) -> int:
    """Get the row count from any narwhals-compatible result."""
    if hasattr(result, "shape"):
        return result.shape[0]
    if hasattr(result, "num_rows"):
        return result.num_rows
    raise TypeError(f"Cannot get row count from {type(result)}")


def _columns(result) -> list[str]:
    """Get column names from any narwhals-compatible result."""
    if hasattr(result, "columns"):
        cols = result.columns
        return list(cols) if not isinstance(cols, list) else cols
    if hasattr(result, "column_names"):
        return result.column_names
    raise TypeError(f"Cannot get columns from {type(result)}")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_data():
    """Standard test dataset."""
    return {
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 40, 45],
        "score": [85, 90, 75, 95, 80],
        "active": [True, True, False, True, False],
        "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
    }


@pytest.fixture
def join_data():
    """Dataset for join tests."""
    return {
        "name": ["Alice", "Bob", "Charlie", "Frank"],
        "department": ["Engineering", "Marketing", "Engineering", "Sales"],
    }


@pytest.fixture
def null_data():
    """Dataset with null values."""
    return {
        "name": ["Alice", "Bob", None, "David", None],
        "value": [1.0, None, 3.0, None, 5.0],
    }


@pytest.fixture(params=["pandas", "pyarrow"])
def nw_df(request, sample_data):
    """Create a pandas or PyArrow DataFrame from sample_data."""
    if request.param == "pandas":
        return pd.DataFrame(sample_data)
    else:
        return pa.table(sample_data)


@pytest.fixture(params=["pandas", "pyarrow"])
def nw_join_df(request, join_data):
    """Create a pandas or PyArrow DataFrame from join_data."""
    if request.param == "pandas":
        return pd.DataFrame(join_data)
    else:
        return pa.table(join_data)


@pytest.fixture(params=["pandas", "pyarrow"])
def nw_null_df(request, null_data):
    """Create a pandas or PyArrow DataFrame from null_data."""
    if request.param == "pandas":
        return pd.DataFrame(null_data)
    else:
        return pa.table(null_data)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSelect:
    """Select columns, verify output."""

    def test_select_single_column(self, nw_df):
        result = relation(nw_df).select("name").collect()
        cols = _columns(result)
        assert cols == ["name"]
        data = _to_pydict(result)
        assert data["name"] == ["Alice", "Bob", "Charlie", "David", "Eve"]

    def test_select_multiple_columns(self, nw_df):
        result = relation(nw_df).select("name", "age").collect()
        cols = _columns(result)
        assert set(cols) == {"name", "age"}
        assert _row_count(result) == 5


class TestDrop:
    """Drop column."""

    def test_drop_single_column(self, nw_df):
        result = relation(nw_df).drop("salary").collect()
        cols = _columns(result)
        assert "salary" not in cols
        assert "name" in cols
        assert _row_count(result) == 5


class TestRename:
    """Rename columns."""

    def test_rename_columns(self, nw_df):
        result = relation(nw_df).rename({"name": "full_name", "age": "years"}).collect()
        cols = _columns(result)
        assert "full_name" in cols
        assert "years" in cols
        assert "name" not in cols
        assert "age" not in cols


class TestFilter:
    """Filter with narwhals expressions."""

    def test_filter_with_narwhals_expression(self, nw_df):
        result = relation(nw_df).filter(nw.col("score") > 85).collect()
        data = _to_pydict(result)
        # score > 85 -> Bob (90), David (95)
        assert sorted(data["name"]) == ["Bob", "David"]

    def test_filter_multiple_predicates(self, nw_df):
        result = (
            relation(nw_df)
            .filter(nw.col("score") > 75, nw.col("active") == True)  # noqa: E712
            .collect()
        )
        data = _to_pydict(result)
        # score > 75 AND active == True -> Alice (85, True), Bob (90, True), David (95, True)
        assert sorted(data["name"]) == ["Alice", "Bob", "David"]


class TestSort:
    """Sort by column."""

    def test_sort_ascending(self, nw_df):
        result = relation(nw_df).sort("score").collect()
        data = _to_pydict(result)
        assert data["score"] == [75, 80, 85, 90, 95]

    def test_sort_descending(self, nw_df):
        result = relation(nw_df).sort("score", descending=True).collect()
        data = _to_pydict(result)
        assert data["score"] == [95, 90, 85, 80, 75]


class TestHeadTail:
    """Verify row counts for head/tail."""

    def test_head(self, nw_df):
        result = relation(nw_df).head(3).collect()
        assert _row_count(result) == 3

    def test_tail(self, nw_df):
        result = relation(nw_df).tail(2).collect()
        assert _row_count(result) == 2


class TestJoin:
    """Join two DataFrames."""

    def test_inner_join(self, sample_data, join_data, request):
        """Test inner join — uses same input type for both sides."""
        # Use pandas for both sides to avoid cross-type issues
        left = pd.DataFrame(sample_data)
        right = pd.DataFrame(join_data)

        result = relation(left).join(relation(right), on="name").collect()
        data = _to_pydict(result)
        # Inner join: Alice, Bob, Charlie (common names)
        assert sorted(data["name"]) == ["Alice", "Bob", "Charlie"]
        assert "department" in _columns(result)

    def test_inner_join_pyarrow(self, sample_data, join_data):
        """Test inner join with PyArrow tables."""
        left = pa.table(sample_data)
        right = pa.table(join_data)

        result = relation(left).join(relation(right), on="name").collect()
        data = _to_pydict(result)
        assert sorted(data["name"]) == ["Alice", "Bob", "Charlie"]
        assert "department" in _columns(result)


class TestGroupByAgg:
    """Group and aggregate."""

    def test_group_by_with_narwhals_agg(self, nw_df):
        result = (
            relation(nw_df)
            .group_by("active")
            .agg(nw.col("salary").sum())
            .collect()
        )
        data = _to_dicts(result)
        # active=True: Alice(50k) + Bob(60k) + David(80k) = 190k
        # active=False: Charlie(70k) + Eve(90k) = 160k
        result_map = {row["active"]: row["salary"] for row in data}
        assert result_map[True] == pytest.approx(190000.0)
        assert result_map[False] == pytest.approx(160000.0)


class TestUnique:
    """Deduplicate rows."""

    def test_unique_on_column(self):
        data = {
            "category": ["A", "B", "A", "C", "B"],
            "value": [1, 2, 3, 4, 5],
        }
        df = pd.DataFrame(data)
        result = relation(df).unique("category").collect()
        data_out = _to_pydict(result)
        # Should have 3 unique categories
        assert sorted(data_out["category"]) == ["A", "B", "C"]

    def test_unique_on_column_pyarrow(self):
        data = {
            "category": ["A", "B", "A", "C", "B"],
            "value": [1, 2, 3, 4, 5],
        }
        df = pa.table(data)
        result = relation(df).unique("category").collect()
        data_out = _to_pydict(result)
        assert sorted(data_out["category"]) == ["A", "B", "C"]


class TestDropNulls:
    """Filter nulls."""

    def test_drop_nulls_all_columns(self, nw_null_df):
        result = relation(nw_null_df).drop_nulls().collect()
        data = _to_pydict(result)
        # Only rows where BOTH name and value are non-null:
        # Alice (1.0), row index 0 — both non-null
        # That's the only row with no nulls in either column
        assert _row_count(result) >= 1
        # All values should be non-null
        assert None not in data["name"]
        assert None not in data["value"]

    def test_drop_nulls_subset(self, nw_null_df):
        result = relation(nw_null_df).drop_nulls(subset=["value"]).collect()
        data = _to_pydict(result)
        # Drops rows where value is null: keeps rows 0 (1.0), 2 (3.0), 4 (5.0)
        assert None not in data["value"]
        assert _row_count(result) == 3


class TestPipeline:
    """Chain multiple operations."""

    def test_filter_sort_head(self, nw_df):
        result = (
            relation(nw_df)
            .filter(nw.col("score") >= 80)
            .sort("score", descending=True)
            .head(3)
            .collect()
        )
        data = _to_pydict(result)
        # score >= 80: Alice(85), Bob(90), David(95), Eve(80)
        # sorted desc: David(95), Bob(90), Alice(85), Eve(80)
        # head 3: David(95), Bob(90), Alice(85)
        assert data["score"] == [95, 90, 85]
        assert data["name"] == ["David", "Bob", "Alice"]

    def test_select_rename_sort(self, nw_df):
        result = (
            relation(nw_df)
            .select("name", "salary")
            .rename({"salary": "pay"})
            .sort("pay")
            .collect()
        )
        data = _to_pydict(result)
        assert "pay" in _columns(result)
        assert "salary" not in _columns(result)
        assert data["pay"] == [50000.0, 60000.0, 70000.0, 80000.0, 90000.0]

    def test_filter_drop_sort_pipeline(self, nw_df):
        result = (
            relation(nw_df)
            .filter(nw.col("active") == True)  # noqa: E712
            .drop("active")
            .sort("age")
            .collect()
        )
        data = _to_pydict(result)
        assert "active" not in _columns(result)
        assert data["age"] == [25, 30, 40]
        assert data["name"] == ["Alice", "Bob", "David"]
