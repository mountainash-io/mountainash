"""Unit tests for mountainash.core.dtypes — canonical type resolution."""

import pytest


class TestMountainashDtypeEnum:
    """Test that the enum has all tier-1 types and behaves as str."""

    def test_enum_is_str(self):
        from mountainash.core.dtypes import MountainashDtype
        assert isinstance(MountainashDtype.I64, str)
        assert MountainashDtype.I64 == "i64"

    def test_all_tier1_types_present(self):
        from mountainash.core.dtypes import MountainashDtype
        expected = {
            "bool", "i8", "i16", "i32", "i64",
            "u8", "u16", "u32", "u64",
            "fp32", "fp64", "string", "binary",
            "date", "time", "timestamp",
        }
        actual = {m.value for m in MountainashDtype}
        assert actual == expected

    def test_enum_usable_as_dict_key(self):
        from mountainash.core.dtypes import MountainashDtype
        d = {MountainashDtype.I64: "works"}
        assert d["i64"] == "works"


class TestResolveDtype:
    """Test resolve_dtype() normalizes all input forms to canonical strings."""

    def test_canonical_strings_pass_through(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("i64") == "i64"
        assert resolve_dtype("string") == "string"
        assert resolve_dtype("fp64") == "fp64"
        assert resolve_dtype("bool") == "bool"
        assert resolve_dtype("u32") == "u32"

    def test_polars_capitalized_aliases(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("Int64") == "i64"
        assert resolve_dtype("Float64") == "fp64"
        assert resolve_dtype("Utf8") == "string"
        assert resolve_dtype("String") == "string"
        assert resolve_dtype("Boolean") == "bool"
        assert resolve_dtype("UInt32") == "u32"

    def test_common_lowercase_aliases(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("int64") == "i64"
        assert resolve_dtype("float64") == "fp64"
        assert resolve_dtype("boolean") == "bool"
        assert resolve_dtype("uint8") == "u8"
        assert resolve_dtype("f64") == "fp64"
        assert resolve_dtype("f32") == "fp32"

    def test_python_builtin_types(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(int) == "i64"
        assert resolve_dtype(float) == "fp64"
        assert resolve_dtype(str) == "string"
        assert resolve_dtype(bool) == "bool"

    def test_enum_members(self):
        from mountainash.core.dtypes import MountainashDtype, resolve_dtype
        assert resolve_dtype(MountainashDtype.I64) == "i64"
        assert resolve_dtype(MountainashDtype.STRING) == "string"
        assert resolve_dtype(MountainashDtype.TIMESTAMP) == "timestamp"

    def test_polars_native_types_via_str(self):
        import polars as pl
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(pl.Int64) == "i64"
        assert resolve_dtype(pl.Utf8) == "string"
        assert resolve_dtype(pl.Float64) == "fp64"
        assert resolve_dtype(pl.Boolean) == "bool"
        assert resolve_dtype(pl.UInt16) == "u16"

    def test_narwhals_native_types_via_str(self):
        import narwhals as nw
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(nw.Int64) == "i64"
        assert resolve_dtype(nw.String) == "string"
        assert resolve_dtype(nw.Float64) == "fp64"
        assert resolve_dtype(nw.UInt32) == "u32"

    def test_ibis_native_types_via_str(self):
        import ibis.expr.datatypes as dt
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype(dt.int64) == "i64"
        assert resolve_dtype(dt.string) == "string"
        assert resolve_dtype(dt.float64) == "fp64"
        assert resolve_dtype(dt.uint8) == "u8"

    def test_datetime_alias_maps_to_timestamp(self):
        from mountainash.core.dtypes import resolve_dtype
        assert resolve_dtype("Datetime") == "timestamp"
        assert resolve_dtype("timestamp") == "timestamp"

    def test_invalid_string_raises_valueerror(self):
        from mountainash.core.dtypes import resolve_dtype
        with pytest.raises(ValueError, match="Unknown dtype"):
            resolve_dtype("foobar")

    def test_empty_string_raises_valueerror(self):
        from mountainash.core.dtypes import resolve_dtype
        with pytest.raises(ValueError, match="Unknown dtype"):
            resolve_dtype("")

    def test_none_raises_valueerror(self):
        from mountainash.core.dtypes import resolve_dtype
        with pytest.raises(ValueError, match="Unknown dtype"):
            resolve_dtype(None)


class TestDtypeAliases:
    """Test that DTYPE_ALIASES covers all expected variations."""

    def test_every_canonical_name_is_in_aliases(self):
        from mountainash.core.dtypes import MountainashDtype, DTYPE_ALIASES
        for member in MountainashDtype:
            assert member.value in DTYPE_ALIASES, f"Canonical name {member.value!r} missing from DTYPE_ALIASES"

    def test_aliases_all_resolve_to_valid_enum(self):
        from mountainash.core.dtypes import MountainashDtype, DTYPE_ALIASES
        for alias, target in DTYPE_ALIASES.items():
            assert isinstance(target, MountainashDtype), f"Alias {alias!r} maps to {target!r}, not a MountainashDtype"
