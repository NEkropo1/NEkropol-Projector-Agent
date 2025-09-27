import pytest

import agents.base as base


class FakeGraph:
    last_instance: "FakeGraph | None" = None

    def __init__(self, _state_type):
        self.nodes = []
        self.entry = None
        self.conditional_branch = None
        self.edges = []
        self.compile_called = False
        FakeGraph.last_instance = self

    def add_node(self, name, fn):
        self.nodes.append((name, fn))

    def set_entry_point(self, name):
        self.entry = name

    def add_conditional_edges(self, name, fn):
        self.conditional_branch = (name, fn)

    def add_edge(self, src, dst):
        self.edges.append((src, dst))

    def compile(self):
        self.compile_called = True
        return {"compiled": True, "edges": self.edges}


def test_add_trace_appends_and_initializes_trace():
    state: base.GraphState = {}

    base.add_trace(state, "step-one", {"foo": "bar"})
    base.add_trace(state, "step-two")

    assert state["trace"][0]["step"] == "step-one"
    assert state["trace"][0]["data"] == {"foo": "bar"}
    assert state["trace"][1]["step"] == "step-two"
    assert state["trace"][1]["data"] == {}


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("PERSON_PHOTO", "handle_photo"),
        ("PERSON_METADATA", "handle_meta"),
        ("CASUAL", "handle_casual"),
        ("OUT_OF_SCOPE", "handle_oos"),
        (None, "handle_oos"),
    ],
)
def test_compile_graph_branching(monkeypatch, mode, expected):
    fake_end = object()
    monkeypatch.setattr(base, "StateGraph", FakeGraph)
    monkeypatch.setattr(base, "END", fake_end)

    def stub(*args, **kwargs):  # pragma: no cover - safety
        raise AssertionError("stub should not be called")

    compiled = base.compile_graph(*(stub,) * 5)

    assert compiled["compiled"] is True
    assert ("classify", fake_end) not in compiled["edges"]

    assert FakeGraph.last_instance is not None
    branch_name, branch_fn = FakeGraph.last_instance.conditional_branch
    assert branch_name == "classify"
    state = base.GraphState(mode=mode) if mode is not None else base.GraphState()
    assert branch_fn(state) == expected
