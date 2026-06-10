# tests/core/dtypes/test_casts.py
from mountainash.core.dtypes.canonical import MountainashDtype as D
from mountainash.core.dtypes.casts import is_safe_cast


class TestIsSafeCast:
    def test_same_type_safe(self):
        assert is_safe_cast(D.I64, D.I64)

    def test_widening_int_safe(self):
        assert is_safe_cast(D.I8, D.I64)
        assert is_safe_cast(D.U8, D.U64)
        assert is_safe_cast(D.I32, D.FP64)

    def test_narrowing_unsafe(self):
        assert not is_safe_cast(D.I64, D.I8)
        assert not is_safe_cast(D.FP64, D.I64)

    def test_to_string_safe(self):
        assert is_safe_cast(D.I64, D.STRING)
        assert is_safe_cast(D.TIMESTAMP, D.STRING)

    def test_string_parsing_unsafe(self):
        assert not is_safe_cast(D.STRING, D.I64)
        assert not is_safe_cast(D.STRING, D.TIMESTAMP)

    def test_unlisted_pair_defaults_unsafe(self):
        assert not is_safe_cast(D.BINARY, D.I64)
        assert not is_safe_cast(D.LIST, D.STRUCT)
