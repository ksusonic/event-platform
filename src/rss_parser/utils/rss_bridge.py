"""RSS Bridge utilities for building Telegram channel RSS feeds."""

from urllib.parse import urlencode


def build_rss_bridge_url(
    channel_name: str,
    base_url: str = "https://rss-bridge.org/bridge01/",
    bridge: str = "TelegramBridge",
    format: str = "Mrss",
) -> str:
    """
    Build an RSS bridge URL for a Telegram channel.

    Args:
        channel_name: The Telegram channel name
        base_url: The base RSS bridge URL (default: 'https://rss-bridge.org/bridge01/')
        bridge: The bridge to use (default: 'TelegramBridge')
        format: The output format (default: 'Mrss')

    Returns:
        Complete RSS bridge URL
    """
    params = {
        "action": "display",
        "username": channel_name,
        "bridge": bridge,
        "format": format,
    }
    return f"{base_url}?{urlencode(params)}"
