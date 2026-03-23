"""Distribution registry — re-exports TOOL_CONFIG for use in distribution layer."""
from khanote.models.tool import TOOL_CONFIG, ToolConfig

__all__ = ["TOOL_CONFIG", "ToolConfig"]
