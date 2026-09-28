"""Build-time contract for public join execution targets."""

import inspect

import pytest

import mountainash as ma
from mountainash.core.constants import CONST_BACKEND, ExecutionTarget, JoinType
from mountainash.relations.core.relation_protocols.prtcl_relation_api import RelationAPIProtocol
from mountainash.relations.core.relation_protocols.relation_systems.extensions_mountainash.prtcl_relsys_ext_ma_util import MountainashExtensionRelationSystemProtocol
from mountainash.relations.core.relation_protocols.relation_systems.substrait.prtcl_relsys_join import SubstraitJoinRelationSystemProtocol
from mountainash.relations.core.relation_protocols.relsys_base import get_relation_system


@pytest.mark.parametrize("method", ["join", "cross_join", "join_asof"])
@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("left", ExecutionTarget.LEFT),
        ("right", ExecutionTarget.RIGHT),
        (ExecutionTarget.LEFT, ExecutionTarget.LEFT),
        (ExecutionTarget.RIGHT, ExecutionTarget.RIGHT),
    ],
)
def test_target_normalizes_without_compilation(method, value, expected):
    rel = ma.relation({"id": [1]})
    kwargs = {} if method == "cross_join" else {"on": "id"}
    out = getattr(rel, method)({"id": [2]}, execute_on=value, **kwargs)
    assert out._node.execute_on is expected
    assert out._node.left is rel._node
    assert out._node.join_type is {
        "join": JoinType.INNER,
        "cross_join": JoinType.CROSS,
        "join_asof": JoinType.ASOF,
    }[method]
    for owner in (type(rel), RelationAPIProtocol):
        p = inspect.signature(getattr(owner, method)).parameters["execute_on"]
        assert p.kind is inspect.Parameter.KEYWORD_ONLY
        assert p.default is None


@pytest.mark.parametrize("method", ["join", "cross_join", "join_asof"])
@pytest.mark.parametrize("value", ["RIGHT", "duckdb", "", 0, False, [], {}])
def test_invalid_target_is_a_build_error(method, value):
    kwargs = {} if method == "cross_join" else {"on": "id"}
    with pytest.raises(ValueError, match="execute_on"):
        getattr(ma.relation({"id": [1]}), method)({"id": [2]}, execute_on=value, **kwargs)


@pytest.mark.parametrize("owner,method", [
    (SubstraitJoinRelationSystemProtocol, "join"),
    (MountainashExtensionRelationSystemProtocol, "join_asof"),
    *((get_relation_system(family), method) for family in (
        CONST_BACKEND.POLARS, CONST_BACKEND.IBIS, CONST_BACKEND.NARWHALS,
    ) for method in ("join", "join_asof")),
])
def test_native_join_contract_has_no_execution_target(owner, method):
    assert "execute_on" not in inspect.signature(getattr(owner, method)).parameters
