"""Model layer tests: contract, mock, registry, openai, ollama."""

import socket
import urllib.error

import pytest
from pydantic import ValidationError

from aios_core import __version__
from aios_core.models import (
    ChatMessage,
    ChatResponse,
    MockModel,
    ModelError,
    ModelNotAvailableError,
    ModelRegistry,
    ModelTimeoutError,
    OpenAIModel,
)
from aios_core.models import ollama_provider
from aios_core.models import openai_provider


def msg(role="user", content="hi"):
    return ChatMessage(role=role, content=content)


# -- contract validation ------------------------------------------------------

def test_chat_message_role_literal():
    with pytest.raises(ValidationError):
        ChatMessage(role="assistan", content="x")  # typo


def test_usage_filled_and_negative_rejected():
    resp = ChatResponse(content="x", usage={})
    assert resp.usage == {"prompt_tokens": 0, "completion_tokens": 0}
    with pytest.raises(ValidationError):
        ChatResponse(content="x", usage={"prompt_tokens": -1, "completion_tokens": 0})


def test_chat_input_validation():
    model = MockModel(echo=True)
    with pytest.raises(ValueError, match="empty"):
        model.chat([])
    with pytest.raises(ValueError, match="temperature"):
        model.chat([msg()], temperature=3.0)
    with pytest.raises(ValueError, match="max_tokens"):
        model.chat([msg()], max_tokens=0)


# -- mock ---------------------------------------------------------------------

def test_mock_echo():
    model = MockModel(echo=True)
    resp = model.chat([msg(role="system", content="sys"), msg(content="hello")])
    assert resp.content == "hello"
    assert model.calls == 1
    assert resp.usage["prompt_tokens"] >= 0


def test_mock_fixed_and_sequence():
    fixed = MockModel(responses=["only"])
    assert fixed.chat([msg()]).content == "only"
    assert fixed.chat([msg()]).content == "only"  # fixed: repeats last

    seq = MockModel(responses=["a", "b"])
    assert seq.chat([msg()]).content == "a"
    assert seq.chat([msg()]).content == "b"


def test_mock_exhausted_raises():
    model = MockModel(responses=["a", "b"])
    model.chat([msg()])
    model.chat([msg()])
    with pytest.raises(ModelError, match="exhausted"):
        model.chat([msg()])


def test_mock_loop():
    model = MockModel(responses=["a"], loop=True)
    assert model.chat([msg()]).content == "a"
    assert model.chat([msg()]).content == "a"


def test_mock_none_responses_raises():
    model = MockModel()  # responses=None
    with pytest.raises(ModelError, match="exhausted"):
        model.chat([msg()])


def test_mock_raise_error():
    model = MockModel(raise_error=RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        model.chat([msg()])


def test_mock_available_and_metadata():
    model = MockModel(echo=True)
    assert model.is_available() is True
    meta = model.metadata()
    assert meta.id == "models.mock"
    assert meta.version == __version__
    assert "1.1.0" in meta.version


# -- registry -----------------------------------------------------------------

def test_registry_register_get_list():
    reg = ModelRegistry()
    reg.register("mock", MockModel(echo=True))
    assert reg.get("mock").name == "mock"
    assert reg.list() == ["mock"]


def test_registry_unknown_raises():
    reg = ModelRegistry()
    with pytest.raises(ModelError, match="Unknown model"):
        reg.get("nope")


def test_registry_default():
    reg = ModelRegistry(default_name="mock")
    reg.register("mock", MockModel(echo=True))
    assert reg.default().name == "mock"
    with pytest.raises(ModelError):
        reg.default("missing")


def test_registry_overwrite():
    reg = ModelRegistry()
    reg.register("mock", MockModel(echo=True))
    reg.register("mock", MockModel(responses=["x"]))
    assert reg.get("mock").responses == ["x"]


# -- openai -------------------------------------------------------------------

def test_openai_unavailable(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setattr(openai_provider, "_is_openai_installed", lambda: True)
    model = OpenAIModel(api_key=None, base_url=None)
    assert model.is_available() is False
    with pytest.raises(ModelNotAvailableError):
        model.chat([msg()])


def test_openai_not_installed(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai_provider, "_is_openai_installed", lambda: False)
    model = OpenAIModel(api_key="sk-test")
    assert model.is_available() is False


def test_openai_fake_client_seam():
    class FakeMessage:
        content = "hello from fake"

    class FakeChoice:
        message = FakeMessage()
        finish_reason = "stop"

    class FakeUsage:
        prompt_tokens = 5
        completion_tokens = 7

    class FakeCompletion:
        model = "gpt-fake"
        choices = [FakeChoice()]
        usage = FakeUsage()

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeCompletion()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    model = OpenAIModel(client=FakeClient(), api_key=None, base_url=None)
    resp = model.chat([msg()])  # explicit client bypasses is_available
    assert resp.content == "hello from fake"
    assert resp.usage == {"prompt_tokens": 5, "completion_tokens": 7}
    assert resp.finish_reason == "stop"


# -- ollama -------------------------------------------------------------------

class FakeResp:
    def __init__(self, status=200, body=None):
        self.status = status
        self._body = body or b"{}"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def test_ollama_is_available_false(monkeypatch):
    def fake_urlopen(*args, **kwargs):
        raise ConnectionRefusedError("refused")

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    assert model.is_available() is False


def test_ollama_mapping(monkeypatch):
    body = b'{"model":"llama3.2","message":{"content":"hi there"},"prompt_eval_count":11,"eval_count":9,"done_reason":"stop"}'

    def fake_urlopen(req, timeout=30.0):
        assert req.method == "POST"
        return FakeResp(status=200, body=body)

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    resp = model.chat([msg()])
    assert resp.content == "hi there"
    assert resp.usage == {"prompt_tokens": 11, "completion_tokens": 9}
    assert resp.finish_reason == "stop"


def test_ollama_http_error(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        raise urllib.error.HTTPError(req.full_url, 500, "Internal", {}, None)

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    with pytest.raises(ModelError):
        model.chat([msg()])


def test_ollama_timeout(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        raise socket.timeout("timed out")

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    with pytest.raises(ModelTimeoutError):
        model.chat([msg()])


def test_ollama_connection_refused(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        raise urllib.error.URLError(ConnectionRefusedError("refused"))

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    with pytest.raises(ModelNotAvailableError):
        model.chat([msg()])


def test_ollama_invalid_json(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        return FakeResp(status=200, body=b"not-json")

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    with pytest.raises(ModelError, match="JSON"):
        model.chat([msg()])


def test_ollama_metadata():
    model = ollama_provider.OllamaModel(model="llama3.2")
    meta = model.metadata()
    assert meta.id == "models.ollama"
    assert meta.name == "llama3.2"
    assert meta.version == __version__


def test_ollama_is_available_true(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        return FakeResp(status=200, body=b'{"models": []}')

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    assert model.is_available() is True


def test_ollama_generic_urlerror(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        raise urllib.error.URLError(RuntimeError("boom"))

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    with pytest.raises(ModelError, match="request failed"):
        model.chat([msg()])


def test_ollama_missing_message(monkeypatch):
    def fake_urlopen(req, timeout=30.0):
        return FakeResp(status=200, body=b'{"model": "llama3.2"}')

    monkeypatch.setattr(ollama_provider, "urlopen", fake_urlopen)
    model = ollama_provider.OllamaModel()
    with pytest.raises(ModelError, match="message"):
        model.chat([msg()])


def test_openai_metadata():
    model = OpenAIModel(model="gpt-4o-mini", client=object())
    meta = model.metadata()
    assert meta.id == "models.openai"
    assert meta.name == "gpt-4o-mini"
    assert meta.version == __version__


def test_openai_available_with_key(monkeypatch):
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setattr(openai_provider, "_is_openai_installed", lambda: True)
    model = OpenAIModel(api_key="sk-test")
    assert model.is_available() is True
