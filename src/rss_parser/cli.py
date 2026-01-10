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

        for i, item in enumerate(feed.items[:10], 1):
            print(f"  Date: {item.pub_date}")
            print(f"  Link: {item.link}")
            print(f"  Desc: {item.description}")
            if item.media_urls:
                print(f"  Media: {len(item.media_urls)} URL(s)")
                for media_url in item.media_urls[:3]:  # Show first 3 media URLs
                    print(f"    - {media_url}")
                if len(item.media_urls) > 3:
                    print(f"    ... and {len(item.media_urls) - 3} more")
            print()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
