import asyncio
from pathlib import Path

import pytest

import agents.projector_agent as projector


@pytest.mark.parametrize(
    "content,exists,expected",
    [("hello", True, "hello"), ("", False, "")],
)
def test__load_text(tmp_path: Path, content, exists, expected):
    target = tmp_path / "file.txt"
    if exists:
        target.write_text(content, encoding="utf-8")
    assert projector._load_text(target) == expected


def test_node_classify_sets_mode_and_trace(monkeypatch):
    state = projector.GraphState(message="hi")

    def fake_classify(message, image_url):
        assert message == "hi"
        assert image_url is None
        return "CASUAL"

    monkeypatch.setattr(projector, "classify_message", fake_classify)
    result = asyncio.run(projector.node_classify(state))

    assert result["mode"] == "CASUAL"
    assert result["trace"][-1]["step"] == "classified"
    assert result["trace"][-1]["data"] == {"mode": "CASUAL"}


class DummySettings:
    def __init__(self, model="gpt-test"):
        self.openai_model_gpt = model


def test__projector_call_without_image(monkeypatch):
    calls = {}

    async def fake_chat(messages, model, temperature):
        calls["messages"] = messages
        calls["model"] = model
        calls["temperature"] = temperature
        return "result"

    monkeypatch.setattr(projector, "chat", fake_chat)
    monkeypatch.setattr(projector, "settings", DummySettings("demo-model"))
    monkeypatch.setattr(projector, "SYSTEM_PROMPT", "system base ")
    monkeypatch.setattr(projector, "PROJECT_PROMPT", "foundation")

    result = asyncio.run(projector._projector_call("user question"))

    assert result == "result"
    assert calls["model"] == "demo-model"
    assert calls["temperature"] == 0.7
    assert calls["messages"][0] == {
        "role": "system",
        "content": "system base\n\n[Foundation]\nfoundation",
    }
    assert calls["messages"][1] == {"role": "user", "content": "user question"}


def test__projector_call_with_image(monkeypatch):
    recorded = {}

    async def fake_chat(messages, model, temperature):
        recorded["messages"] = messages
        return "call"

    monkeypatch.setattr(projector, "chat", fake_chat)
    monkeypatch.setattr(projector, "settings", DummySettings("model-x"))
    monkeypatch.setattr(projector, "SYSTEM_PROMPT", "sys")
    monkeypatch.setattr(projector, "PROJECT_PROMPT", "")

    result = asyncio.run(projector._projector_call("describe", image_url="http://img"))

    assert result == "call"
    message = recorded["messages"][1]
    assert message["role"] == "user"
    assert message["content"][0] == {"type": "text", "text": "describe"}
    assert message["content"][1]["type"] == "image_url"
    assert message["content"][1]["image_url"]["url"] == "http://img"


def test_node_handle_photo_without_image(monkeypatch):
    state = projector.GraphState(message="hi")

    def fail(*args, **kwargs):  # pragma: no cover - safety
        raise AssertionError("should not be called")

    monkeypatch.setattr(projector, "image_has_person", fail)

    result = asyncio.run(projector.node_handle_photo(state))

    assert result["next_action"] == "need_better_photo"
    assert "trace" in result and result["trace"][0]["step"] == "photo_validated"


def test_node_handle_photo_rejects_when_no_person(monkeypatch):
    state = projector.GraphState(message="text", image_url="img")

    monkeypatch.setattr(projector, "image_has_person", lambda url: False)

    async def fail(*args, **kwargs):  # pragma: no cover - safety
        raise AssertionError("projector call should not run")

    monkeypatch.setattr(projector, "_projector_call", fail)

    result = asyncio.run(projector.node_handle_photo(state))

    assert result["next_action"] == "need_better_photo"
    assert "couldn’t confidently detect" in result["output"]
    steps = [step["step"] for step in result["trace"]]
    assert steps == ["photo_validated"]


def test_node_handle_photo_success(monkeypatch):
    state = projector.GraphState(message="text", image_url="img")
    monkeypatch.setattr(projector, "image_has_person", lambda url: True)

    async def fake_projector_call(*_, **__):
        return "done"

    monkeypatch.setattr(projector, "_projector_call", fake_projector_call)

    result = asyncio.run(projector.node_handle_photo(state))

    assert result["output"] == "done"
    assert result["next_action"] == "none"
    steps = [step["step"] for step in result["trace"]]
    assert steps == ["photo_validated", "projector_photo_start", "projector_photo_done"]


def test_node_handle_meta(monkeypatch):
    state = projector.GraphState(message="meta info")

    async def fake_projector_call(*_):
        return "meta"

    monkeypatch.setattr(projector, "_projector_call", fake_projector_call)

    result = asyncio.run(projector.node_handle_meta(state))

    assert result["output"] == "meta"
    steps = [step["step"] for step in result["trace"]]
    assert steps == ["projector_meta_start", "projector_meta_done"]


def test_node_handle_casual(monkeypatch):
    state = projector.GraphState(message="hi")

    def fake_answer(message):
        assert message == "hi"
        return "casual"

    monkeypatch.setattr("tools.local_simple.answer_casual", fake_answer)

    result = asyncio.run(projector.node_handle_casual(state))

    assert result["output"] == "casual"
    steps = [step["step"] for step in result["trace"]]
    assert steps == ["casual_start", "casual_done"]


def test_node_handle_oos():
    state = projector.GraphState()

    result = asyncio.run(projector.node_handle_oos(state))

    assert "outside my scope" in result["output"].lower()
    steps = [step["step"] for step in result["trace"]]
    assert steps == ["oos_start", "oos_done"]


def test__projector_call_ignores_empty_image_and_strips_prompts(monkeypatch):
    recorded = {}

    async def fake_chat(messages, model, temperature):
        recorded["messages"] = messages
        recorded["model"] = model
        recorded["temperature"] = temperature
        return "ok"

    monkeypatch.setattr(projector, "chat", fake_chat)
    monkeypatch.setattr(projector, "settings", DummySettings("trim-model"))
    monkeypatch.setattr(projector, "SYSTEM_PROMPT", "  sys text  ")
    monkeypatch.setattr(projector, "PROJECT_PROMPT", "   ")

    result = asyncio.run(projector._projector_call("ask something", image_url=""))

    assert result == "ok"
    assert recorded["messages"][0] == {"role": "system", "content": "sys text"}
    assert recorded["messages"][1] == {"role": "user", "content": "ask something"}
    assert recorded["temperature"] == 0.7
