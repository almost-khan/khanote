"""ResearcherRegistryEntry — metadata for one researcher in the registry."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ResearcherRegistryEntry(BaseModel):
    """Metadata for one researcher entry in the registry.

    Built-in researchers come from registry.yaml.
    Custom HTTP researchers are derived from config.yaml.
    """

    name: str
    type: Literal["builtin", "http"]
    domains: list[str] = []
    capabilities: list[str] = []
    description: str = ""
    priority: Literal["fallback", "specialized"] = "specialized"
    requires_key: bool = False
    env_var: str | None = None
    available: bool = False


__all__ = ["ResearcherRegistryEntry"]
