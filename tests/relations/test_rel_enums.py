"""Tests for relational AST enums and supporting types."""
import pytest
from enum import StrEnum
from mountainash.core.constants import (
    ProjectOperation, JoinType, ExecutionTarget, SetType,
    ExtensionRelOperation, SortField,
)

class TestProjectOperation:
    def test_members(self):
        assert ProjectOperation.SELECT is not None
        assert ProjectOperation.WITH_COLUMNS is not None
        assert ProjectOperation.DROP is not None
        assert ProjectOperation.RENAME is not None
    def test_member_count(self):
        assert len(ProjectOperation) == 4

class TestJoinType:
    def test_is_strenum(self):
        assert issubclass(JoinType, StrEnum)
    def test_string_values(self):
        assert JoinType.INNER == "inner"
        assert JoinType.LEFT == "left"
        assert JoinType.RIGHT == "right"
        assert JoinType.OUTER == "outer"
        assert JoinType.SEMI == "semi"
        assert JoinType.ANTI == "anti"
        assert JoinType.CROSS == "cross"
        assert JoinType.ASOF == "asof"
    def test_member_count(self):
        assert len(JoinType) == 8

class TestExecutionTarget:
    def test_members(self):
        assert ExecutionTarget.LEFT is not None
        assert ExecutionTarget.RIGHT is not None
    def test_member_count(self):
        assert len(ExecutionTarget) == 2

class TestSetType:
    def test_members(self):
        assert SetType.UNION_ALL is not None
        assert SetType.UNION_DISTINCT is not None

class TestExtensionRelOperation:
    def test_members(self):
        assert ExtensionRelOperation.DROP_NULLS is not None
        assert ExtensionRelOperation.WITH_ROW_INDEX is not None
        assert ExtensionRelOperation.EXPLODE is not None
        assert ExtensionRelOperation.SAMPLE is not None
        assert ExtensionRelOperation.UNPIVOT is not None
        assert ExtensionRelOperation.PIVOT is not None
        assert ExtensionRelOperation.TOP_K is not None
    def test_member_count(self):
        assert len(ExtensionRelOperation) == 7

class TestSortField:
    def test_creation(self):
        sf = SortField(column="age")
        assert sf.column == "age"
        assert sf.descending is False
        assert sf.nulls_last is True
    def test_descending(self):
        sf = SortField(column="age", descending=True)
        assert sf.descending is True
    def test_frozen(self):
        sf = SortField(column="age")
        with pytest.raises(AttributeError):
            sf.column = "name"
