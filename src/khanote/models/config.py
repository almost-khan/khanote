"""Pydantic v2 models for config.yaml."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, model_validator


def _expand_env(value: str) -> str:
    """Expand ${VAR} and $VAR environment variables in a string."""
    return re.sub(
        r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)",
        lambda m: os.environ.get(m.group(1) or m.group(2), m.group(0)),
        value,
    )


class ResearcherConfig(BaseModel):
    enabled: bool = True
    status: str = "stable"
    api_key: str | None = None
    semantic_scholar_api_key: str | None = None

    @field_validator("api_key", "semantic_scholar_api_key", mode="before")
    @classmethod
    def expand_env_vars(cls, v: Any) -> Any:
        if isinstance(v, str):
            return _expand_env(v)
        return v


class ResearchConfig(BaseModel):
    default: str = "perplexity"
    researchers: dict[str, ResearcherConfig] = {}

    @model_validator(mode="after")
    def at_least_one_enabled(self) -> "ResearchConfig":
        enabled = [r for r in self.researchers.values() if r.enabled]
        if not enabled:
            raise ValueError("At least one researcher must be enabled")
        return self


class DomainConfig(BaseModel):
    name: str
    keywords: list[str] = []
    start_my_day_researcher: str | None = None


class Config(BaseModel):
    version: str = "0.1.0"
    vault_path: Path
    initialized_tools: list[str] = []
    research: ResearchConfig
    domains: list[DomainConfig] = []

    @field_validator("vault_path", mode="before")
    @classmethod
    def resolve_vault_path(cls, v: Any) -> Path:
        if isinstance(v, str):
            v = _expand_env(v)
            v = os.path.expanduser(v)
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"vault_path does not exist: {path}")
        return path

    @classmethod
    def from_yaml(cls, path: Path | str) -> "Config":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: Path | str) -> None:
        path = Path(path)
        data = self.model_dump(mode="json")
        data["vault_path"] = str(self.vault_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
