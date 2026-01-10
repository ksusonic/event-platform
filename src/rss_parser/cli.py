"""Command-line interface for RSS parser."""

import sys
import asyncio
import logging
import json
from rss_parser.core.parser import RSSParser
from rss_parser.db.session import db
from rss_parser.db.repository import RSSPostRepository
from rss_parser.db.models import RSSPost

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def async_main():
    """Async main CLI entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: python -m rss_parser <RSS_URL>")
        sys.exit(1)

    url = sys.argv[1]
    parser = RSSParser()

    try:
        # Parse the RSS feed
        feed = parser.parse_url(url)
        print(f"✓ Feed: {feed.title}")
        print(f"✓ Items: {len(feed.items)}")
        print(f"✓ Link: {feed.link}\n")

        # Connect to database
        await db.connect()
        logger.info("Connected to database")

        saved_count = 0
        skipped_count = 0
        error_count = 0

        # Save items to database
        for i, item in enumerate(feed.items, 1):
            try:
                # Check if item already exists
                existing = await RSSPostRepository.get_by_link(item.link)
                if existing:
                    logger.debug(f"Skipping existing item: {item.link}")
                    skipped_count += 1
                    continue

                # Convert RSSItem to RSSPost
                media_json = json.dumps(item.media_urls) if item.media_urls else None
                post = RSSPost(
                    link=item.link,
                    content=item.description,
                    pub_date=item.pub_date,
                    media=media_json,
                )

                # Save to database
                await RSSPostRepository.create(post)
                saved_count += 1
                print(f"  {i}. Saved: {item.link}")

            except Exception as e:
                logger.error(f"Failed to save item {item.link}: {e}")
                error_count += 1

        # Summary
        print(f"\n✓ Saved: {saved_count}")
        print(f"✓ Skipped (already exists): {skipped_count}")
        if error_count > 0:
            print(f"✗ Errors: {error_count}")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await db.disconnect()
        logger.info("Disconnected from database")


def main():
    """Main CLI entrypoint (sync wrapper)."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
