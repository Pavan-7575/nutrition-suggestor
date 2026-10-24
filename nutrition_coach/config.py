from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    secret_key: str
    max_upload_bytes: int
    ollama_host: str
    ollama_model: str
    debug: bool

    @classmethod
    def from_environment(cls) -> Settings:
        load_dotenv()
        return cls(
            secret_key=os.getenv("FLASK_SECRET_KEY", "development-only-change-me"),
            max_upload_bytes=int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024,
            ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "minicpm-v"),
            debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        )

    def as_flask_config(self) -> dict:
        return {
            "SECRET_KEY": self.secret_key,
            "MAX_CONTENT_LENGTH": self.max_upload_bytes,
            "MAX_UPLOAD_BYTES": self.max_upload_bytes,
            "OLLAMA_HOST": self.ollama_host,
            "OLLAMA_MODEL": self.ollama_model,
            "DEBUG": self.debug,
        }
