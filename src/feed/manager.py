"""Feed manager for handling multiple RSS feeds."""

import logging
from typing import List, Optional

from .core.parser import RSSParser
from .models.feed import RSSChannel

logger = logging.getLogger(__name__)


class RSSFeedManager:
    """Manage multiple RSS feeds."""

    def __init__(self):
        self.parser = RSSParser()
        self.feeds: dict[str, RSSChannel] = {}

    def add_feed(self, name: str, url: str) -> RSSChannel:
        """Add and parse a new feed."""
        try:
            feed = self.parser.parse_url(url)
            self.feeds[name] = feed
            logger.info(f"Added feed '{name}' with {len(feed.items)} items")
            return feed
        except Exception as e:
            logger.error(f"Failed to add feed '{name}': {e}")
            raise

    def get_feed(self, name: str) -> Optional[RSSChannel]:
        """Get a previously parsed feed."""
        return self.feeds.get(name)

    def list_feeds(self) -> List[str]:
        """List all feed names."""
        return list(self.feeds.keys())

    def export_json(self, name: str) -> str:
        """Export feed as JSON."""
        feed = self.get_feed(name)
        if feed is None:
            raise ValueError(f"Feed '{name}' not found")
        return feed.to_json()
