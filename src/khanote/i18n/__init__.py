"""Lightweight i18n loader for wizard, status, and post-init messages."""
from __future__ import annotations

from khanote.i18n.messages import MESSAGES


def get_message(key: str, lang: str = "en") -> str:
    """Return localized message for *key* in *lang*.

    Fallback chain: exact match → language prefix (e.g. 'zh-CN' → 'zh') → English.
    Returns the key itself if not found in any language.
    """
    translations = MESSAGES.get(key)
    if translations is None:
        return key

    # Exact match
    if lang in translations:
        return translations[lang]

    # Language prefix fallback (e.g. 'zh-CN' → 'zh')
    prefix = lang.split("-")[0].split("_")[0].lower()
    if prefix in translations:
        return translations[prefix]

    # English fallback
    return translations.get("en", key)
