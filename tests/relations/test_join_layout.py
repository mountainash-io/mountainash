"""Join output naming rule (backlog 245): pure layout decisions."""

from mountainash.core.constants import JoinType
from mountainash.relations.core.join_layout import join_layout


def _layout(left, right, **kw):
    base = dict(join_type=JoinType.INNER, on=None, left_on=None, right_on=None,
                suffix="_right", coalesce=None)
    base.update(kw)
    return join_layout(left, right, **base)


def test_left_on_right_on_default_keeps_both_keys():
    lay = _layout(["k", "v", "w"], ["kk", "w"], left_on=["k"], right_on=["kk"])
    assert lay.right_rename == {"w": "w_right"}
    assert lay.right_keys == ["kk"]
    assert lay.drop == [] and lay.merge == []


def test_on_default_merges_by_dropping_for_inner_and_left():
    for jt in (JoinType.INNER, JoinType.LEFT):
        lay = _layout(["k", "v"], ["k", "w"], join_type=jt, on=["k"])
        assert lay.right_keys == ["k_right"]
        assert lay.drop == ["k_right"] and lay.merge == []


def test_on_default_coalesces_for_right_and_outer():
    for jt in (JoinType.RIGHT, JoinType.OUTER):
        lay = _layout(["k", "v"], ["k", "w"], join_type=jt, on=["k"])
        assert lay.merge == [("k", "k_right")]
        assert lay.drop == ["k_right"]


def test_explicit_coalesce_overrides_key_form():
    kept = _layout(["k"], ["k"], on=["k"], coalesce=False)
    assert kept.drop == [] and kept.right_keys == ["k_right"]
    merged = _layout(["k"], ["kk"], join_type=JoinType.OUTER,
                     left_on=["k"], right_on=["kk"], coalesce=True)
    assert merged.merge == [("k", "kk")] and merged.drop == ["kk"]


def test_clash_increments_and_records_collision():
    lay = _layout(["k", "w", "w_right"], ["k", "w"], on=["k"])
    assert lay.right_rename["w"] == "w_right_1"
    assert ("w", "w_right_1") in lay.collisions


def test_clash_with_original_right_column_increments():
    lay = _layout(["k", "w"], ["k", "w", "w_right"], on=["k"])
    assert lay.right_rename["w"] == "w_right_1"
    assert "w_right" not in lay.right_rename


def test_increments_follow_right_column_order():
    lay = _layout(["id", "a", "a_1"], ["id", "a_1", "a"], on=["id"], suffix="_1")
    assert lay.right_rename == {"id": "id_1", "a_1": "a_1_1", "a": "a_1_2"}


def test_unknown_right_schema_never_targets_a_left_column():
    # Left already owns k_right; right schema unknown. The right key must get a
    # fresh name so dropping it can never remove the left payload.
    lay = _layout(["k", "k_right"], [], on=["k"])
    assert lay.right_keys == ["k_right_1"]
    assert lay.drop == ["k_right_1"]


def test_right_key_clashes_with_left_payload():
    lay = _layout(["k", "w"], ["w", "x"], left_on=["k"], right_on=["w"])
    assert lay.right_keys == ["w_right"]


def test_layout_with_empty_right_names():
    # Unknown right schema: the key still follows the clash rule execution will apply.
    lay = _layout(["k", "v"], [], on=["k"])
    assert lay.right_rename == {"k": "k_right"} and lay.right_keys == ["k_right"]
