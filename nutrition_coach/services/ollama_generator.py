from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .image_processing import ProcessedImage


@dataclass(frozen=True)
class GenerationResult:
    text: str | None
    unavailable_reason: str | None = None


class OllamaVisionGenerator:
    """Multimodal vision and text generator backed by local Ollama instance.

    Uses Ollama's HTTP API at http://localhost:11434.
    Supports vision models like minicpm-v, llava, qwen2.5-vl, etc.
    """

    def __init__(self, config: dict) -> None:
        self.host: str = config.get("OLLAMA_HOST", "http://localhost:11434")
        self.model_id: str = config.get("OLLAMA_MODEL", "minicpm-v")

    @property
    def is_configured(self) -> bool:
        return bool(self.host and self.model_id)

    def generate(self, prompt: str, image: ProcessedImage | None) -> GenerationResult:
        if not self.is_configured:
            return GenerationResult(
                None, "Ollama host or model is not configured."
            )

        endpoint = f"{self.host.rstrip('/')}/api/chat"

        message: dict = {
            "role": "user",
            "content": prompt,
        }
        if image:
            message["images"] = [image.base64_data]

        payload = {
            "model": self.model_id,
            "messages": [message],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 900,
            },
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode("utf-8"))
                reply = result.get("message", {}).get("content", "")
                return GenerationResult(reply.strip())
        except urllib.error.URLError as exc:
            return GenerationResult(
                None,
                f"Could not connect to Ollama at {self.host}. Is Ollama running? Error: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            return GenerationResult(None, f"Ollama generation failed: {repr(exc)}")
