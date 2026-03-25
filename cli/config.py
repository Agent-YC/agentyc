"""Configuration management for Agent YC CLI.

Handles global config (``~/.agentyc/config.yml``) and project-local
settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


GLOBAL_CONFIG_DIR = Path.home() / ".agentyc"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.yml"


@dataclass
class Config:
    """Agent YC configuration."""

    # Ollama settings
    ollama_url: str = "http://localhost:11434"
    default_model: str = "llama3.2"

    # Cloud settings (Phase 3)
    api_key: str = ""
    cloud_url: str = "https://api.agentyc.com"

    # Preferences
    output_format: str = "rich"  # rich | json | plain

    def save(self, path: Path | None = None) -> None:
        """Save config to YAML file."""
        target = path or GLOBAL_CONFIG_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ollama_url": self.ollama_url,
            "default_model": self.default_model,
            "api_key": self.api_key,
            "cloud_url": self.cloud_url,
            "output_format": self.output_format,
        }
        target.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        """Load config from YAML file. Returns defaults if file doesn't exist."""
        target = path or GLOBAL_CONFIG_FILE
        if not target.exists():
            return cls()
        try:
            data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
            return cls(
                ollama_url=data.get("ollama_url", "http://localhost:11434"),
                default_model=data.get("default_model", "llama3.2"),
                api_key=data.get("api_key", ""),
                cloud_url=data.get("cloud_url", "https://api.agentyc.com"),
                output_format=data.get("output_format", "rich"),
            )
        except Exception:
            return cls()


def get_config() -> Config:
    """Load the global configuration."""
    return Config.load()


def save_config(config: Config) -> None:
    """Save the global configuration."""
    config.save()
