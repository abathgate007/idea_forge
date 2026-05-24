"""Small Ollama HTTP client for local model calls."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import socket
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_TIMEOUT_SECONDS = 30.0

OLLAMA_BASE_URL_ENV = "IDEA_FORGE_OLLAMA_BASE_URL"
OLLAMA_MODEL_ENV = "IDEA_FORGE_OLLAMA_MODEL"


class OllamaClientError(RuntimeError):
    """Base exception for Ollama client failures."""


class OllamaUnavailableError(OllamaClientError):
    """Raised when the local Ollama service cannot be reached."""


class OllamaHTTPError(OllamaClientError):
    """Raised when Ollama returns a non-success HTTP response."""

    def __init__(self, status_code: int, response_body: str = "") -> None:
        self.status_code = status_code
        self.response_body = response_body
        message = f"Ollama returned HTTP {status_code}"
        if response_body:
            message = f"{message}: {response_body}"
        super().__init__(message)


class OllamaResponseError(OllamaClientError):
    """Raised when Ollama returns unusable response data."""


class _HTTPResponse(Protocol):
    status: int

    def read(self) -> bytes:
        """Read the response body."""


Transport = Callable[[Request, float], _HTTPResponse]


def _default_transport(request: Request, timeout_seconds: float) -> _HTTPResponse:
    return urlopen(request, timeout=timeout_seconds)


@dataclass(frozen=True)
class OllamaClient:
    """Client abstraction for Ollama's local generate API."""

    base_url: str = DEFAULT_OLLAMA_BASE_URL
    model: str = DEFAULT_OLLAMA_MODEL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    transport: Transport = _default_transport

    @classmethod
    def from_environment(cls) -> "OllamaClient":
        """Create a client using environment variables when present."""
        return cls(
            base_url=os.getenv(OLLAMA_BASE_URL_ENV, DEFAULT_OLLAMA_BASE_URL),
            model=os.getenv(OLLAMA_MODEL_ENV, DEFAULT_OLLAMA_MODEL),
        )

    def generate(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated text."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        request = Request(
            urljoin(self._normalized_base_url, "/api/generate"),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            response = self.transport(request, self.timeout_seconds)
            status_code = getattr(response, "status", 200)
            body = response.read().decode("utf-8")
        except HTTPError as error:
            raise OllamaHTTPError(error.code, _read_error_body(error)) from error
        except (TimeoutError, socket.timeout, URLError, OSError) as error:
            raise OllamaUnavailableError("Ollama is unavailable") from error

        if status_code != 200:
            raise OllamaHTTPError(status_code, body)

        return _parse_generated_text(body)

    @property
    def _normalized_base_url(self) -> str:
        return self.base_url.rstrip("/") + "/"


def _parse_generated_text(body: str) -> str:
    try:
        data: Any = json.loads(body)
    except json.JSONDecodeError as error:
        raise OllamaResponseError("Ollama returned malformed JSON") from error

    if not isinstance(data, dict):
        raise OllamaResponseError("Ollama returned malformed response data")

    response_text = data.get("response")
    if not isinstance(response_text, str):
        raise OllamaResponseError("Ollama response is missing generated text")

    generated_text = response_text.strip()
    if not generated_text:
        raise OllamaResponseError("Ollama returned empty generated output")

    return generated_text


def _read_error_body(error: HTTPError) -> str:
    try:
        return error.read().decode("utf-8")
    except OSError:
        return ""
