from __future__ import annotations

import json
from socket import timeout as SocketTimeout
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.analysis.schema import RcaDraft
from app.core.config import get_settings


class LlmUnavailableError(RuntimeError):
    pass


class InvalidLlmResponseError(RuntimeError):
    pass


class OllamaRcaGenerator:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.ollama_model
        self.url = settings.ollama_url.rstrip("/") + "/api/chat"
        self.timeout = settings.ollama_timeout_seconds

    def generate_with_trace(self, system_prompt: str, user_prompt: str) -> tuple[RcaDraft, str]:
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": RcaDraft.model_json_schema(),
            "stream": False,
            "think": False,
            "options": {"temperature": 0},
        }).encode("utf-8")
        request = Request(self.url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw_response = json.load(response)
        except (SocketTimeout, TimeoutError) as exc:
            raise LlmUnavailableError(f"Ollama timed out after {self.timeout} seconds") from exc
        except (HTTPError, URLError, OSError) as exc:
            raise LlmUnavailableError("Ollama is unavailable or the model could not run") from exc
        except json.JSONDecodeError as exc:
            raise InvalidLlmResponseError("Ollama returned invalid JSON") from exc
        try:
            content = raw_response["message"]["content"]
            return RcaDraft.model_validate_json(content), content
        except (KeyError, TypeError, ValidationError, ValueError) as exc:
            raise InvalidLlmResponseError("Ollama returned an invalid RCA JSON response") from exc

    def generate(self, system_prompt: str, user_prompt: str) -> RcaDraft:
        draft, _ = self.generate_with_trace(system_prompt, user_prompt)
        return draft
