"""Personalization block builder — render user preferences as SOP injection text."""
from __future__ import annotations

from khanote.preferences.models import Preferences

# Depth guidelines
_DEPTH_GUIDELINES: dict[str, str] = {
    "headlines": (
        "- Depth: Headlines only. Provide very brief, concise summaries (1-2 sentences max per item). "
        "Focus on the most critical information only."
    ),
    "summary": (
        "- Depth: Summary level. Provide balanced summaries (3-5 sentences per item). "
        "Cover key points without exhaustive detail."
    ),
    "detailed": (
        "- Depth: Detailed analysis. Provide thorough explanations with supporting context, "
        "examples, and implications for each item."
    ),
    "deep_dive": (
        "- Depth: Deep dive. Provide comprehensive, thorough analysis. Include methodology, "
        "nuances, counterarguments, and extended implications. Prioritize depth over brevity."
    ),
}

# Expertise guidelines
_EXPERTISE_GUIDELINES: dict[str, str] = {
    "beginner": (
        "- Expertise level: Beginner. Use simple language, avoid technical jargon, "
        "explain concepts clearly, and provide analogies where helpful."
    ),
    "intermediate": (
        "- Expertise level: Intermediate. Assume familiarity with core concepts. "
        "Use standard domain terminology but explain specialized or niche terms."
    ),
    "expert": (
        "- Expertise level: Expert. Use advanced technical terminology freely. "
        "Skip basic explanations and focus on nuance, edge cases, and sophisticated analysis."
    ),
}

# Tone guidelines
_TONE_GUIDELINES: dict[str, str] = {
    "formal_report": (
        "- Tone: Formal report. Write in third person, use structured headings, "
        "objective language, and professional register suitable for executive consumption."
    ),
    "professional_briefing": (
        "- Tone: Professional briefing. Use clear, direct language in second person where appropriate. "
        "Balance professionalism with readability."
    ),
    "casual_notes": (
        "- Tone: Casual notes. Use conversational language, first person where natural, "
        "and a relaxed informal register. Bullet points and fragments are acceptable."
    ),
}


def build_personalization_block(prefs: Preferences) -> str:
    """Build a personalization instructions block from user preferences.

    This block is injected as {personalization_instructions} into every SOP template.
    The LLM receives only the applicable guidelines, not conditional branches.

    Returns:
        A multi-line string with personalization guidelines.
    """
    lines = [
        "## Personalization Instructions",
        "",
        f"- Output language: {prefs.language}. Write all output in this language.",
        _DEPTH_GUIDELINES[prefs.depth],
        _EXPERTISE_GUIDELINES[prefs.expertise],
        _TONE_GUIDELINES[prefs.tone],
    ]

    if prefs.interests:
        interest_list = ", ".join(prefs.interests)
        lines.append(f"- User interests: {interest_list}. Prioritize content related to these areas.")

    if prefs.role and prefs.role != "mixed":
        lines.append(f"- User role: {prefs.role}. Frame insights and recommendations accordingly.")

    return "\n".join(lines)
