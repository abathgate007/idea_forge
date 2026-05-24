import json
from urllib.error import URLError

import pytest

from idea_forge.ollama_client import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    OLLAMA_BASE_URL_ENV,
    OLLAMA_MODEL_ENV,
    OllamaClient,
    OllamaHTTPError,
    OllamaResponseError,
    OllamaUnavailableError,
)


class FakeResponse:
    def __init__(self, status: int, body: str) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body.encode("utf-8")


def test_client_uses_defaults() -> None:
    client = OllamaClient()

    assert client.base_url == DEFAULT_OLLAMA_BASE_URL
    assert client.model == DEFAULT_OLLAMA_MODEL


def test_client_can_be_configured_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(OLLAMA_BASE_URL_ENV, "http://ollama.local:11434")
    monkeypatch.setenv(OLLAMA_MODEL_ENV, "custom-model:latest")

    client = OllamaClient.from_environment()

    assert client.base_url == "http://ollama.local:11434"
    assert client.model == "custom-model:latest"


def test_generate_posts_prompt_to_ollama_and_returns_text() -> None:
    calls = []

    def fake_transport(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(200, json.dumps({"response": "  generated idea  "}))

    client = OllamaClient(
        base_url="http://example.test:11434/",
        model="test-model",
        timeout_seconds=7,
        transport=fake_transport,
    )

    result = client.generate("make something useful")

    assert result == "generated idea"
    request, timeout = calls[0]
    assert request.full_url == "http://example.test:11434/api/generate"
    assert request.get_method() == "POST"
    assert request.get_header("Content-type") == "application/json"
    assert timeout == 7
    assert json.loads(request.data.decode("utf-8")) == {
        "model": "test-model",
        "prompt": "make something useful",
        "stream": False,
    }


def test_generate_raises_for_ollama_unavailable() -> None:
    def fake_transport(_request, _timeout):
        raise URLError("connection refused")

    client = OllamaClient(transport=fake_transport)

    with pytest.raises(OllamaUnavailableError):
        client.generate("prompt")


def test_generate_raises_for_non_200_response() -> None:
    client = OllamaClient(
        transport=lambda _request, _timeout: FakeResponse(500, "server failed")
    )

    with pytest.raises(OllamaHTTPError) as error:
        client.generate("prompt")

    assert error.value.status_code == 500
    assert error.value.response_body == "server failed"


@pytest.mark.parametrize(
    "body",
    [
        "not json",
        json.dumps(["not", "an", "object"]),
        json.dumps({"done": True}),
        json.dumps({"response": ""}),
        json.dumps({"response": "   "}),
    ],
)
def test_generate_raises_for_malformed_or_empty_response(body: str) -> None:
    client = OllamaClient(transport=lambda _request, _timeout: FakeResponse(200, body))

    with pytest.raises(OllamaResponseError):
        client.generate("prompt")
