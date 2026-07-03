"""Tests for the shared KeyedRegistry plumbing."""
from __future__ import annotations

import pytest

from mountainash.core.registries import KeyedRegistry


class TestKeyedRegistryBasics:
    def test_register_and_get(self):
        reg = KeyedRegistry("widget")
        reg.register("a", 1)
        assert reg.get("a") == 1

    def test_register_returns_value(self):
        reg = KeyedRegistry("widget")
        assert reg.register("a", 1) == 1

    def test_decorator_registration(self):
        reg = KeyedRegistry("system")

        @reg.decorator("polars")
        class Thing:
            pass

        assert reg.get("polars") is Thing

    def test_get_missing_raises_keyerror_listing_available(self):
        reg = KeyedRegistry("widget")
        reg.register("a", 1)
        with pytest.raises(KeyError) as exc:
            reg.get("zzz")
        assert "widget" in str(exc.value)
        assert "'a'" in str(exc.value)

    def test_get_optional_returns_none_on_miss(self):
        reg = KeyedRegistry("widget")
        assert reg.get_optional("nope") is None

    def test_duplicate_key_raises(self):
        reg = KeyedRegistry("widget")
        reg.register("a", 1)
        with pytest.raises(ValueError, match="already registered"):
            reg.register("a", 2)

    def test_unregister_is_idempotent(self):
        reg = KeyedRegistry("widget")
        reg.register("a", 1)
        reg.unregister("a")
        reg.unregister("a")  # no error
        assert reg.get_optional("a") is None

    def test_list_keys_and_reset(self):
        reg = KeyedRegistry("widget")
        reg.register("a", 1)
        reg.register("b", 2)
        assert reg.list_keys() == ["a", "b"]
        reg.reset()
        assert reg.list_keys() == []


class TestKeyedRegistryHooks:
    def test_lazy_initializer_runs_once_on_first_read(self):
        calls = []
        reg = KeyedRegistry("widget", initializer=lambda: calls.append(1))
        assert calls == []          # not run at construction
        reg.get_optional("x")
        reg.get_optional("y")
        assert calls == [1]         # ran exactly once

    def test_initializer_can_register(self):
        holder = {}

        def init():
            holder["reg"].register("seeded", 42)

        reg = KeyedRegistry("widget", initializer=init)
        holder["reg"] = reg
        assert reg.get("seeded") == 42

    def test_validator_blocks_registration(self):
        def no_ints(key, value):
            if isinstance(value, int):
                raise TypeError("ints not allowed")

        reg = KeyedRegistry("widget", validator=no_ints)
        with pytest.raises(TypeError, match="ints not allowed"):
            reg.register("a", 1)
        reg.register("b", "fine")

    def test_reset_rearms_initializer(self):
        calls = []
        reg = KeyedRegistry("widget", initializer=lambda: calls.append(1))
        reg.get_optional("x")
        reg.reset()
        reg.get_optional("x")
        assert calls == [1, 1]


class TestKeyedRegistryMulti:
    def test_multi_accumulates_per_key(self):
        reg = KeyedRegistry("pass", multi=True)
        reg.register("t", "f1")
        reg.register("t", "f2")
        assert reg.get("t") == ["f1", "f2"]

    def test_multi_entries_preserve_global_insertion_order(self):
        reg = KeyedRegistry("pass", multi=True)
        reg.register("a", 1)
        reg.register("b", 2)
        reg.register("a", 3)
        assert reg.entries() == [("a", 1), ("b", 2), ("a", 3)]

    def test_single_mode_entries(self):
        reg = KeyedRegistry("widget")
        reg.register("a", 1)
        assert reg.entries() == [("a", 1)]
