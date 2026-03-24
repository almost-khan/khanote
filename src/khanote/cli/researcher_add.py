"""Researcher add guided flow logic — 9-step guided flow per contracts/researcher-add.md.

NOTE: The guided conversational prompts are designed to be driven by a vibe coding
tool (skill mode). This module provides the underlying logic; the skill SKILL.md
instructs the AI assistant to run the prompts interactively.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from khanote.models.config import Config, EndpointConfig, ResearcherConfig


def add_researcher_to_config(
    config_path: Path | str,
    name: str,
    researcher_config: ResearcherConfig,
) -> None:
    """Merge a new researcher entry into config.yaml.

    Reads the existing config, adds/replaces the researcher under
    `research.researchers.<name>`, and writes the file back.
    """
    config_path = Path(config_path)
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "research" not in data:
        data["research"] = {"default": name, "researchers": {}}
    if "researchers" not in data["research"]:
        data["research"]["researchers"] = {}

    # Build a plain dict for YAML serialisation
    researcher_dict: dict = {
        "enabled": researcher_config.enabled,
        "type": researcher_config.type,
    }
    if researcher_config.api_key:
        researcher_dict["api_key"] = researcher_config.api_key
    if researcher_config.capabilities:
        researcher_dict["capabilities"] = researcher_config.capabilities
    if researcher_config.endpoints:
        researcher_dict["endpoints"] = {
            cap: {
                "url": ep.url,
                "method": ep.method,
                "headers": ep.headers,
                "body_template": ep.body_template,
                "response_mapping": ep.response_mapping,
            }
            for cap, ep in researcher_config.endpoints.items()
        }
    if researcher_config.sop:
        researcher_dict["sop"] = dict(researcher_config.sop)

    data["research"]["researchers"][name] = researcher_dict

    with config_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def add_researcher_to_session(
    session_dir: Path | str,
    name: str,
    researcher_config: ResearcherConfig,
) -> Path:
    """Write researcher config to .khanote/sessions/<slug>/researcher.yaml.

    Returns the path to the written file.
    """
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    researcher_path = session_dir / "researcher.yaml"

    researcher_dict = {
        "name": name,
        "enabled": researcher_config.enabled,
        "type": researcher_config.type,
        "capabilities": researcher_config.capabilities,
    }
    if researcher_config.api_key:
        researcher_dict["api_key"] = researcher_config.api_key
    if researcher_config.endpoints:
        researcher_dict["endpoints"] = {
            cap: {
                "url": ep.url,
                "method": ep.method,
                "headers": ep.headers,
                "body_template": ep.body_template,
                "response_mapping": ep.response_mapping,
            }
            for cap, ep in researcher_config.endpoints.items()
        }
    if researcher_config.sop:
        researcher_dict["sop"] = dict(researcher_config.sop)

    with researcher_path.open("w", encoding="utf-8") as f:
        yaml.dump(researcher_dict, f, default_flow_style=False, allow_unicode=True)
    return researcher_path


def load_session_researcher(session_dir: Path | str) -> tuple[str, ResearcherConfig] | None:
    """Load a session-scoped researcher from .khanote/sessions/<slug>/researcher.yaml.

    Returns (name, ResearcherConfig) or None if not found.
    """
    researcher_path = Path(session_dir) / "researcher.yaml"
    if not researcher_path.exists():
        return None
    with researcher_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    name = data.pop("name", "custom")
    # Re-parse endpoints into EndpointConfig objects if present
    if "endpoints" in data and isinstance(data["endpoints"], dict):
        data["endpoints"] = {
            cap: EndpointConfig(**ep) if isinstance(ep, dict) else ep
            for cap, ep in data["endpoints"].items()
        }
    return name, ResearcherConfig(**data)


def promote_session_researcher(
    session_dir: Path | str,
    config_path: Path | str,
) -> None:
    """Promote a session researcher to permanent config.yaml entry.

    On success, removes the session researcher.yaml.
    """
    result = load_session_researcher(session_dir)
    if result is None:
        raise FileNotFoundError(f"No session researcher found in {session_dir}")
    name, researcher_config = result
    add_researcher_to_config(config_path, name, researcher_config)
    # Clean up session file after promotion
    session_path = Path(session_dir) / "researcher.yaml"
    session_path.unlink(missing_ok=True)


def discard_session_researcher(session_dir: Path | str) -> None:
    """Delete the session researcher config (user declined promotion)."""
    researcher_path = Path(session_dir) / "researcher.yaml"
    researcher_path.unlink(missing_ok=True)
