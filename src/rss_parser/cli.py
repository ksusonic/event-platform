"""Command-line interface for RSS parser."""

import sys
import logging
from rss_parser.core.parser import RSSParser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Main CLI entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: python -m rss_parser <RSS_URL>")
        sys.exit(1)

    url = sys.argv[1]
    parser = RSSParser()

    try:
        feed = parser.parse_url(url)
        print(f"✓ Feed: {feed.title}")
        print(f"✓ Items: {len(feed.items)}")
        print(f"✓ Link: {feed.link}\n")

        for i, item in enumerate(feed.items[:5], 1):
            print(f"Item {i}: {item.title}")
            print(f"  Date: {item.pub_date}")
            print(f"  Link: {item.link}")
            desc = (
                item.description[:100] + "..." if len(item.description) > 100 else item.description
            )
            print(f"  Desc: {desc}\n")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
