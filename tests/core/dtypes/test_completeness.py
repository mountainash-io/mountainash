# tests/core/dtypes/test_completeness.py
"""Closed-by-default gates: every (dtype, target, use) must be mapped or
explicitly declared unsupported. Adding a new enum member fails these tests
until every target maps it or declares it unsupported."""
import pytest

from mountainash.core.dtypes.canonical import MountainashDtype as D
from mountainash.core.dtypes.errors import DtypeMappingError
from mountainash.core.dtypes.registry import registry
from mountainash.core.dtypes.targets import TypeTarget

ALL_TARGETS = list(TypeTarget)


@pytest.mark.parametrize("target", ALL_TARGETS)
@pytest.mark.parametrize("dtype", [dtype for dtype in D if dtype is not D.DECIMAL])
def test_schema_mapping_complete(dtype, target):
    """Schema use is complete over all members for every target."""
    native = registry.to_native_schema(dtype, target)
    assert native is not None


@pytest.mark.parametrize("target", ALL_TARGETS)
@pytest.mark.parametrize("dtype", [dtype for dtype in D if dtype is not D.DECIMAL])
def test_cast_mapping_resolves_or_declares(dtype, target):
    """Cast use either resolves or raises DtypeMappingError via the module's
    explicit CAST_UNSUPPORTED set — never KeyError or silence."""
    mod = registry._target(target)
    if dtype in mod.CAST_UNSUPPORTED:
        with pytest.raises(DtypeMappingError):
            registry.to_native_cast(dtype, target)
    else:
        assert registry.to_native_cast(dtype, target) is not None


@pytest.mark.parametrize("target", ALL_TARGETS)
def test_bare_decimal_is_rejected_as_incomplete_target(target):
    with pytest.raises(DtypeMappingError, match="Bare DECIMAL is incomplete"):
        registry.to_native_schema(D.DECIMAL, target)
    with pytest.raises(DtypeMappingError, match="Bare DECIMAL is incomplete"):
        registry.to_native_cast(D.DECIMAL, target)


@pytest.mark.parametrize("target", ALL_TARGETS)
def test_target_module_contract(target):
    mod = registry._target(target)
    for name in ("SCHEMA_TYPES", "CAST_UNSUPPORTED", "from_native", "parse_type_string"):
        assert hasattr(mod, name), f"{target.value} module missing {name}"
