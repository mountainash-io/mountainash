# tests/core/dtypes/test_cast_safety.py
from mountainash.core.dtypes import CastSafety, MountainashDtype as D, classify_cast


class TestClassifyCast:
    def test_identity_is_safe(self):
        assert classify_cast(D.I64, D.I64) is CastSafety.SAFE

    def test_widening_is_safe(self):
        assert classify_cast(D.I32, D.I64) is CastSafety.SAFE

    def test_narrowing_is_unsafe(self):
        assert classify_cast(D.I64, D.I32) is CastSafety.UNSAFE

    def test_string_to_int_is_unsafe(self):
        assert classify_cast(D.STRING, D.I64) is CastSafety.UNSAFE

    def test_enum_values_are_strings(self):
        assert CastSafety.SAFE.value == "safe"
        assert CastSafety.UNSAFE.value == "unsafe"

    def test_exhaustive_consistency_with_is_safe_cast(self):
        from mountainash.core.dtypes import is_safe_cast

        for a in D:
            for b in D:
                expected = CastSafety.SAFE if is_safe_cast(a, b) else CastSafety.UNSAFE
                assert classify_cast(a, b) is expected
