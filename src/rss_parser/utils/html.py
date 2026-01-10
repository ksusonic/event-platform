"""HTML utilities."""

import re


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text).strip()
