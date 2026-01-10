"""HTML utilities."""

import html
import re


# Compiled regex patterns for better performance
# Remove unsupported media message div
UNSUPPORTED_MEDIA_REGEX = re.compile(
    r'<div class="message_media_not_supported"[^>]*>.*?</div>', re.DOTALL
)

# Remove "message_media_not_supported_label" spans
MEDIA_LABEL_REGEX = re.compile(
    r'<span class="message_media_not_supported_label"[^>]*>.*?</span>', re.DOTALL
)

# Remove action links like "VIEW IN TELEGRAM" (both <a> and <span> tags)
ACTION_LINK_REGEX = re.compile(
    r'<(?:a|span)[^>]*class="message_media_view_in_telegram"[^>]*>.*?</(?:a|span)>', re.DOTALL
)

# Remove img tags
IMG_TAG_REGEX = re.compile(r"<img[^>]*/?>", re.IGNORECASE)

# Remove link tags but extract href
LINK_HREF_REGEX = re.compile(r'<a[^>]*href="([^"]*)"[^>]*>', re.IGNORECASE)

# Remove emoji tags and keep the emoji
EMOJI_REGEX = re.compile(
    r"<tg-emoji[^>]*>.*?<b>([^<]*)</b>.*?</tg-emoji>", re.DOTALL | re.IGNORECASE
)

# Remove HTML tags
HTML_TAG_REGEX = re.compile(r"<[^>]+>")

# Normalize multiple spaces (but not newlines)
SPACE_REGEX = re.compile(r"[ \t]+")


def clean_content(html_content: str) -> str:
    """
    Clean up HTML content by:
    - Unescaping HTML entities (handles double-encoded HTML)
    - Removing unsupported media message divs
    - Removing action links (like "VIEW IN TELEGRAM")
    - Removing HTML tags
    - Normalizing whitespace

    Args:
        html_content: Raw HTML content string

    Returns:
        Cleaned text content
    """
    if not html_content:
        return ""

    # First, unescape HTML entities to handle double-encoded content
    # (e.g., &lt;div&gt; becomes <div>)
    content = html.unescape(html_content)

    # Remove unsupported media messages
    content = UNSUPPORTED_MEDIA_REGEX.sub("", content)

    # Remove media not supported labels
    content = MEDIA_LABEL_REGEX.sub("", content)

    # Remove action links like "VIEW IN TELEGRAM"
    content = ACTION_LINK_REGEX.sub("", content)

    # Replace line breaks with newlines
    content = content.replace("<br/>", "\n")
    content = content.replace("<br>", "\n")

    # Remove img tags (they've been extracted)
    content = IMG_TAG_REGEX.sub("", content)

    # Remove link tags but keep the text content
    content = LINK_HREF_REGEX.sub("", content)
    content = content.replace("</a>", "")

    # Remove emoji tags and keep the emoji
    content = EMOJI_REGEX.sub(r"\1", content)

    # Remove all remaining HTML tags
    content = HTML_TAG_REGEX.sub("", content)

    # Unescape HTML entities again (for any remaining entities in text content)
    content = html.unescape(content)

    # Normalize spaces and tabs (but preserve newlines)
    content = SPACE_REGEX.sub(" ", content)

    # Trim leading/trailing whitespace
    content = content.strip()

    return content


def strip_html(text: str) -> str:
    """
    Remove HTML tags from text (simple version).

    Deprecated: Use clean_content() for more comprehensive cleaning.

    Args:
        text: Text with HTML tags

    Returns:
        Text without HTML tags
    """
    if not text:
        return ""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text).strip()


def extract_media_urls(html_content: str) -> list[str]:
    """
    Extract media URLs (images and video posters) from HTML content.

    Extracts:
    - Image src from <img> tags
    - Video poster URLs from <video> tags

    Args:
        html_content: Raw HTML content string

    Returns:
        List of media URLs found in the content
    """
    if not html_content:
        return []

    media_urls = []

    # Unescape HTML entities first
    content = html.unescape(html_content)

    # Extract image URLs from <img src="...">
    img_pattern = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)
    img_matches = img_pattern.findall(content)
    media_urls.extend(img_matches)

    # Extract video poster URLs from <video poster="...">
    video_pattern = re.compile(r'<video[^>]+poster="([^"]+)"', re.IGNORECASE)
    video_matches = video_pattern.findall(content)
    media_urls.extend(video_matches)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in media_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls
