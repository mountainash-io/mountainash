from __future__ import annotations

from datetime import date

import pytest

from mountainash.pipelines.core.capabilities import ParamAxis, ParamSpec, expand_axes


class TestParamSpec:
    def test_required_param(self):
        spec = ParamSpec(name="start", type=date, required=True)
        assert spec.name == "start"
        assert spec.type is date
        assert spec.required is True
        assert spec.default is None

    def test_optional_param_with_default(self):
        spec = ParamSpec(name="limit", type=int, required=False, default=100)
        assert spec.required is False
        assert spec.default == 100

    def test_frozen(self):
        spec = ParamSpec(name="start", type=date)
        with pytest.raises(AttributeError):
            spec.name = "end"


class TestParamAxis:
    def test_single_param_axis(self):
        axis = ParamAxis(names="user_id", values=[1, 2, 3])
        assert axis.names == "user_id"
        assert axis.values == [1, 2, 3]

    def test_tuple_param_axis(self):
        axis = ParamAxis(names=("start", "end"), values=[("2024-01-01", "2024-01-31")])
        assert axis.names == ("start", "end")
        assert axis.values == [("2024-01-01", "2024-01-31")]

    def test_tuple_axis_empty_names_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ParamAxis(names=(), values=[])

    def test_tuple_axis_arity_mismatch_rejected(self):
        with pytest.raises(ValueError, match="tuple of length 2"):
            ParamAxis(names=("a", "b"), values=[(1, 2, 3)])

    def test_tuple_axis_non_tuple_value_rejected(self):
        with pytest.raises(ValueError, match="tuple of length 2"):
            ParamAxis(names=("a", "b"), values=["not_a_tuple"])

    def test_frozen(self):
        axis = ParamAxis(names="x", values=[1])
        with pytest.raises(AttributeError):
            axis.names = "y"


class TestExpandAxes:
    def test_no_axes_yields_one_empty_dict(self):
        result = list(expand_axes())
        assert result == [{}]

    def test_single_axis(self):
        axis = ParamAxis(names="user_id", values=[10, 20, 30])
        result = list(expand_axes(axis))
        assert result == [{"user_id": 10}, {"user_id": 20}, {"user_id": 30}]

    def test_empty_axis_yields_nothing(self):
        axis = ParamAxis(names="user_id", values=[])
        result = list(expand_axes(axis))
        assert result == []

    def test_two_axes_cartesian_product(self):
        axis_a = ParamAxis(names="a", values=[1, 2])
        axis_b = ParamAxis(names="b", values=["x", "y"])
        result = list(expand_axes(axis_a, axis_b))
        assert len(result) == 4
        assert {"a": 1, "b": "x"} in result
        assert {"a": 1, "b": "y"} in result
        assert {"a": 2, "b": "x"} in result
        assert {"a": 2, "b": "y"} in result

    def test_tuple_axis_explodes(self):
        axis = ParamAxis(names=("start", "end"), values=[("2024-01-01", "2024-01-31"), ("2024-02-01", "2024-02-29")])
        result = list(expand_axes(axis))
        assert result == [
            {"start": "2024-01-01", "end": "2024-01-31"},
            {"start": "2024-02-01", "end": "2024-02-29"},
        ]

    def test_mixed_tuple_and_single_axes(self):
        axis_range = ParamAxis(names=("start", "end"), values=[("2024-01-01", "2024-01-31")])
        axis_user = ParamAxis(names="user_id", values=[1, 2])
        result = list(expand_axes(axis_range, axis_user))
        assert len(result) == 2
        assert {"start": "2024-01-01", "end": "2024-01-31", "user_id": 1} in result
        assert {"start": "2024-01-01", "end": "2024-01-31", "user_id": 2} in result

    def test_duplicate_param_names_across_axes_rejected(self):
        axis_a = ParamAxis(names="x", values=[1, 2])
        axis_b = ParamAxis(names="x", values=[3, 4])
        with pytest.raises(ValueError, match="duplicate"):
            list(expand_axes(axis_a, axis_b))

    def test_duplicate_param_names_tuple_vs_single_rejected(self):
        axis_a = ParamAxis(names=("x", "y"), values=[(1, 2)])
        axis_b = ParamAxis(names="x", values=[3])
        with pytest.raises(ValueError, match="duplicate"):
            list(expand_axes(axis_a, axis_b))
