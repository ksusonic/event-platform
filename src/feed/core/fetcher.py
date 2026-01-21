import requests
import logging

logger = logging.getLogger(__name__)


class FeedFetcher:
    """Handles HTTP requests for RSS feeds."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RSS-Parser/1.0"})

    def fetch(self, url: str) -> str:
        if not url:
            raise ValueError("URL cannot be empty")

        logger.info(f"Fetching RSS feed from {url}")

        try:
            return self._fetch_direct(url)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            raise

    def _fetch_direct(self, url: str) -> str:
        """Direct HTTP fetch."""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text
