"""Entry point for RSS Reader service.

Run with: python -m src.rss_reader
"""

import asyncio
import logging
import json
import sys
from typing import Tuple

from common.db.session import db
from common.db.repository import RSSPostRepository, TelegramChannelRepository
from common.db.models import RSSPost, TelegramChannel
from common.utils.rss_bridge import build_rss_bridge_url
from .core.parser import RSSParser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def process_channel(
    channel: TelegramChannel, parser: RSSParser
) -> Tuple[str, int, int, int, int]:
    """
    Process a single Telegram channel.

    Args:
        channel: TelegramChannel instance
        parser: RSSParser instance

    Returns:
        Tuple of (channel_name, saved_count, skipped_count, empty_count, error_count)
    """
    saved_count = 0
    skipped_count = 0
    error_count = 0
    empty_count = 0

    try:
        # Build RSS bridge URL for the channel
        rss_url = build_rss_bridge_url(channel.channel_name)
        logger.info(f"Processing channel: {channel.channel_name} ({rss_url})")

        # Parse the RSS feed
        feed = parser.parse_url(rss_url)
        logger.info(
            f"✓ Channel: {channel.channel_name} - Feed: {feed.title} - Items: {len(feed.items)}"
        )

        # Save items to database
        for item in feed.items:
            try:
                # Skip if content is empty
                if not item.description or not item.description.strip():
                    logger.debug(f"Skipping item with empty content: {item.link}")
                    empty_count += 1
                    continue

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
                logger.debug(f"Saved: {item.link}")

            except Exception as e:
                logger.error(f"Failed to save item {item.link}: {e}")
                error_count += 1

    except Exception as e:
        logger.error(f"Failed to process channel {channel.channel_name}: {e}", exc_info=True)
        error_count += 1

    return (channel.channel_name, saved_count, skipped_count, empty_count, error_count)


async def main():
    """Main entry point for RSS Reader service."""
    logger.info("Starting RSS Reader service...")

    try:
        if not db.pool:
            await db.connect()
            logger.info("Connected to database")

        # Fetch all Telegram channels
        channels = await TelegramChannelRepository.get_all()

        if not channels:
            logger.warning("No Telegram channels found in database")
            print("No Telegram channels found in database. Please add channels first.")
            return

        logger.info(f"Found {len(channels)} Telegram channels to process")
        print(f"Processing {len(channels)} Telegram channels...\n")

        # Create parser instance
        parser = RSSParser()

        # Process all channels in parallel
        tasks = [process_channel(channel, parser) for channel in channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate totals and display summary
        total_saved = 0
        total_skipped = 0
        total_empty = 0
        total_errors = 0

        print("\n" + "=" * 80)
        print("SUMMARY BY CHANNEL")
        print("=" * 80)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Channel processing failed with exception: {result}")
                total_errors += 1
                continue

            channel_name, saved, skipped, empty, errors = result
            total_saved += saved
            total_skipped += skipped
            total_empty += empty
            total_errors += errors

            print(f"\n{channel_name}:")
            print(f"  ✓ Saved: {saved}")
            print(f"  ⊘ Skipped (already exists): {skipped}")
            if empty > 0:
                print(f"  ⊘ Skipped (empty content): {empty}")
            if errors > 0:
                print(f"  ✗ Errors: {errors}")

        print("\n" + "=" * 80)
        print("OVERALL TOTALS")
        print("=" * 80)
        print(f"✓ Total Saved: {total_saved}")
        print(f"⊘ Total Skipped (already exists): {total_skipped}")
        if total_empty > 0:
            print(f"⊘ Total Skipped (empty content): {total_empty}")
        if total_errors > 0:
            print(f"✗ Total Errors: {total_errors}")
        print(f"📡 Channels Processed: {len(channels)}")
        print("=" * 80)

        logger.info("RSS Reader service completed successfully")

        return {"saved_count": total_saved}

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
