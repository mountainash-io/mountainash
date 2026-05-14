import threading
import pytest

from mountainash.pipelines.orchestration.resolver import ResolverRegistry


def test_register_and_resolve():
    registry = ResolverRegistry()
    registry.register("pipeline_a", "user_1", spec="my_spec", storage="my_storage")
    resolved = registry.resolve("pipeline_a", "user_1")
    assert resolved["spec"] == "my_spec"
    assert resolved["storage"] == "my_storage"


def test_resolve_missing_raises():
    registry = ResolverRegistry()
    with pytest.raises(KeyError):
        registry.resolve("nonexistent", "user_1")


def test_different_users_isolated():
    registry = ResolverRegistry()
    registry.register("p", "user_1", storage="storage_1")
    registry.register("p", "user_2", storage="storage_2")
    assert registry.resolve("p", "user_1")["storage"] == "storage_1"
    assert registry.resolve("p", "user_2")["storage"] == "storage_2"


def test_thread_safety():
    registry = ResolverRegistry()
    errors = []

    def writer(user_id: str):
        try:
            for i in range(100):
                registry.register("p", user_id, value=i)
        except Exception as e:
            errors.append(e)

    def reader(user_id: str):
        try:
            for _ in range(100):
                try:
                    registry.resolve("p", user_id)
                except KeyError:
                    pass
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=writer, args=("u1",)),
        threading.Thread(target=writer, args=("u2",)),
        threading.Thread(target=reader, args=("u1",)),
        threading.Thread(target=reader, args=("u2",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0


def test_unregister():
    registry = ResolverRegistry()
    registry.register("p", "u", spec="s")
    registry.unregister("p", "u")
    with pytest.raises(KeyError):
        registry.resolve("p", "u")
