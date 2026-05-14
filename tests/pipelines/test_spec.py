import pytest
from mountainash.pipelines.core.spec import PipelineSpec
from mountainash.pipelines.core.step import StepDefinition


def _make_defn(name: str, depends_on: list[str] | None = None) -> StepDefinition:
    return StepDefinition(name=name, fn=lambda ctx: [], depends_on=depends_on or [])


def test_pipeline_spec_creation():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "a": _make_defn("a"),
            "b": _make_defn("b", depends_on=["a"]),
        },
    )
    assert spec.name == "test"
    assert spec.version == "1.0.0"
    assert len(spec.steps) == 2


def test_topological_order_linear():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "a": _make_defn("a"),
            "b": _make_defn("b", depends_on=["a"]),
            "c": _make_defn("c", depends_on=["b"]),
        },
    )
    order = spec.topological_order()
    assert order.index("a") < order.index("b") < order.index("c")


def test_topological_order_diamond():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "source": _make_defn("source"),
            "left": _make_defn("left", depends_on=["source"]),
            "right": _make_defn("right", depends_on=["source"]),
            "sink": _make_defn("sink", depends_on=["left", "right"]),
        },
    )
    order = spec.topological_order()
    assert order.index("source") < order.index("left")
    assert order.index("source") < order.index("right")
    assert order.index("left") < order.index("sink")
    assert order.index("right") < order.index("sink")


def test_topological_order_with_target():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "a": _make_defn("a"),
            "b": _make_defn("b", depends_on=["a"]),
            "c": _make_defn("c", depends_on=["a"]),
        },
    )
    order = spec.topological_order(target="b")
    assert "a" in order
    assert "b" in order
    assert "c" not in order


def test_parallel_layers_diamond():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "source": _make_defn("source"),
            "left": _make_defn("left", depends_on=["source"]),
            "right": _make_defn("right", depends_on=["source"]),
            "sink": _make_defn("sink", depends_on=["left", "right"]),
        },
    )
    order = spec.topological_order()
    layers = spec.parallel_layers(order)
    assert layers[0] == ["source"]
    assert set(layers[1]) == {"left", "right"}
    assert layers[2] == ["sink"]


def test_parallel_layers_independent():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "a": _make_defn("a"),
            "b": _make_defn("b"),
            "c": _make_defn("c"),
        },
    )
    order = spec.topological_order()
    layers = spec.parallel_layers(order)
    assert len(layers) == 1
    assert set(layers[0]) == {"a", "b", "c"}


def test_ancestors():
    spec = PipelineSpec(
        name="test",
        version="1.0.0",
        steps={
            "a": _make_defn("a"),
            "b": _make_defn("b", depends_on=["a"]),
            "c": _make_defn("c", depends_on=["b"]),
            "d": _make_defn("d"),
        },
    )
    assert spec.ancestors("c") == {"a", "b"}
    assert spec.ancestors("b") == {"a"}
    assert spec.ancestors("a") == set()


def test_cycle_detection():
    with pytest.raises(ValueError, match="[Cc]ycle"):
        spec = PipelineSpec(
            name="test",
            version="1.0.0",
            steps={
                "a": _make_defn("a", depends_on=["b"]),
                "b": _make_defn("b", depends_on=["a"]),
            },
        )
        spec.topological_order()


def test_missing_dependency():
    with pytest.raises(ValueError, match="missing"):
        PipelineSpec(
            name="test",
            version="1.0.0",
            steps={
                "b": _make_defn("b", depends_on=["a"]),
            },
        )
