from __future__ import annotations

from datetime import date

import pytest

from mountainash.pipelines.core.capabilities import ParamSpec


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
