import logging
from xml.etree import ElementTree as ET
from typing import Optional

from ..models.feed import RSSChannel, RSSItem
from ..utils.html import clean_content
from .fetcher import FeedFetcher

logger = logging.getLogger(__name__)


class RSSParser:
    """Production-grade RSS parser with error handling."""

    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "media": "http://search.yahoo.com/mrss/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    def __init__(self, timeout: int = 10):
        """
        Initialize RSS parser.

        Args:
            timeout: Request timeout in seconds
        """
        self.fetcher = FeedFetcher(timeout=timeout)

    def parse_url(self, url: str) -> RSSChannel:
        """
        Parse RSS feed from URL.

        Args:
            url: RSS feed URL

        Returns:
            RSSChannel with parsed feed data

        Raises:
            ValueError: If URL is invalid or feed parsing fails
            requests.RequestException: If HTTP request fails
        """
        try:
            content = self.fetcher.fetch(url)
            return self.parse_content(content)
        except Exception as e:
            logger.error(f"Failed to parse feed from {url}: {e}")
            raise ValueError(f"Failed to parse RSS feed: {e}")

    def parse_content(self, xml_content: str) -> RSSChannel:
        """
        Parse RSS feed from XML string.

        Args:
            xml_content: XML content as string

        Returns:
            RSSChannel with parsed feed data
        """
        try:
            root = ET.fromstring(xml_content)
            logger.info("Successfully parsed XML content")

            if root.tag.endswith("rss"):
                return self._parse_rss(root)
            elif root.tag.endswith("feed"):
                return self._parse_atom(root)
            else:
                raise ValueError(f"Unknown feed format: {root.tag}")

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Invalid XML format: {e}")

    def _parse_rss(self, root: ET.Element) -> RSSChannel:
        """Parse RSS 2.0 format."""
        channel = root.find("channel")
        if channel is None:
            raise ValueError("Invalid RSS: no channel element found")

        feed = RSSChannel(
            title=self._get_text(channel, "title", "Unknown Feed"),
            link=self._get_text(channel, "link", ""),
            description=self._get_text(channel, "description", ""),
            language=self._get_text(channel, "language"),
            last_build_date=self._get_text(channel, "lastBuildDate"),
        )

        for item_elem in channel.findall("item"):
            item = self._parse_rss_item(item_elem)
            feed.items.append(item)

        logger.info(f"Parsed RSS feed: {feed.title} with {len(feed.items)} items")
        return feed

    def _parse_atom(self, root: ET.Element) -> RSSChannel:
        """Parse Atom format."""
        ns = self.NAMESPACES["atom"]

        feed = RSSChannel(
            title=self._get_text(root, f"{{{ns}}}title", "Unknown Feed"),
            link=self._get_attr(root.find(f"{{{ns}}}link"), "href", ""),
            description=self._get_text(root, f"{{{ns}}}subtitle", ""),
            last_build_date=self._get_text(root, f"{{{ns}}}updated"),
        )

        for entry in root.findall(f"{{{ns}}}entry"):
            item = self._parse_atom_entry(entry)
            feed.items.append(item)

        logger.info(f"Parsed Atom feed: {feed.title} with {len(feed.items)} items")
        return feed

    def _parse_rss_item(self, item_elem: ET.Element) -> RSSItem:
        """Parse individual RSS item."""
        description = self._get_text(item_elem, "description", "")
        content_encoded = self._get_text_with_ns(item_elem, "content", "encoded")
        if content_encoded:
            description = content_encoded

        return RSSItem(
            title=self._get_text(item_elem, "title", "No Title"),
            link=self._get_text(item_elem, "link", ""),
            description=clean_content(description),
            pub_date=self._get_text(item_elem, "pubDate"),
            guid=self._get_text(item_elem, "guid"),
            author=self._get_text(item_elem, "author"),
            category=self._get_text(item_elem, "category"),
        )

    def _parse_atom_entry(self, entry: ET.Element) -> RSSItem:
        """Parse individual Atom entry."""
        ns = self.NAMESPACES["atom"]

        link_elem = entry.find(f"{{{ns}}}link")
        link = self._get_attr(link_elem, "href", "") if link_elem is not None else ""

        content = self._get_text(entry, f"{{{ns}}}content", "")
        if not content:
            content = self._get_text(entry, f"{{{ns}}}summary", "")

        return RSSItem(
            title=self._get_text(entry, f"{{{ns}}}title", "No Title"),
            link=link,
            description=clean_content(content),
            pub_date=self._get_text(entry, f"{{{ns}}}published"),
            guid=self._get_text(entry, f"{{{ns}}}id"),
            author=self._get_text(entry, f"{{{ns}}}author/{{{ns}}}name"),
        )

    @staticmethod
    def _get_text(elem: Optional[ET.Element], tag: str, default: str = "") -> str:
        """Safely get text content from element."""
        if elem is None:
            return default
        child = elem.find(tag)
        return child.text or default if child is not None else default

    def _get_text_with_ns(
        self, elem: Optional[ET.Element], ns_key: str, tag: str, default: str = ""
    ) -> str:
        """Get text with namespace support."""
        if elem is None:
            return default
        ns = self.NAMESPACES.get(ns_key, "")
        child = elem.find(f"{{{ns}}}{tag}") if ns else elem.find(tag)
        return child.text or default if child is not None else default

    @staticmethod
    def _get_attr(elem: Optional[ET.Element], attr: str, default: str = "") -> str:
        """Safely get attribute from element."""
        if elem is None:
            return default
        return elem.get(attr, default)
