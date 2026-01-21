"""Entry point for Digest Publisher service.

Run with: python -m src.digest_publisher
"""

import asyncio
import logging
from typing import List
from datetime import datetime, timedelta

from common.db.session import db
from common.db.repository import RSSPostRepository
from common.db.models import RSSPost

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def format_post_for_telegram(post: RSSPost) -> str:
    """
    Format a post for Telegram message.

    Args:
        post: RSSPost object

    Returns:
        Formatted string for Telegram
    """
    lines = []

    # Extract title from link or use first line of content
    title = post.link.split("/")[-1].replace("-", " ").replace("_", " ")[:100]
    if len(title) < 10 and post.content:
        title = post.content.split("\n")[0][:100]

    lines.append(f"📰 **{title}**")

    if post.pub_date:
        lines.append(f"🕐 {post.pub_date.strftime('%Y-%m-%d %H:%M')}")

    if post.content:
        # Truncate long content for Telegram
        content = post.content[:300] + "..." if len(post.content) > 300 else post.content
        lines.append(f"\n{content}")

    lines.append(f"\n🔗 [Read more]({post.link})")

    return "\n".join(lines)


def create_digest(posts: List[RSSPost]) -> str:
    """
    Create a digest message from posts.

    Args:
        posts: List of RSSPost objects

    Returns:
        Formatted digest string
    """
    if not posts:
        return "No posts found for this period."

    lines = []
    lines.append("📣 **News Digest**")
    lines.append(f"Found {len(posts)} recent posts\n")
    lines.append("=" * 40)
    lines.append("")

    for i, post in enumerate(posts, 1):
        lines.append(format_post_for_telegram(post))
        if i < len(posts):
            lines.append("\n" + "-" * 40 + "\n")

    return "\n".join(lines)


async def publish_to_telegram(message: str):
    """
    Publish message to Telegram.

    Args:
        message: Message to publish
    """
    # TODO: Implement actual Telegram bot integration
    # For now, just print the message
    logger.info("Publishing to Telegram (stub implementation):")
    print("\n" + "=" * 80)
    print("TELEGRAM DIGEST")
    print("=" * 80)
    print(message)
    print("=" * 80)

    # In production, this would use something like:
    # bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    # chat_id = os.getenv("TELEGRAM_CHAT_ID")
    # Send message via Telegram Bot API


async def main():
    """Main entry point for Digest Publisher service."""
    logger.info("Starting Digest Publisher service...")

    try:
        if not db.pool:
            await db.connect()
            logger.info("Connected to database")

        # Get posts from the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        logger.info(f"Fetching posts from {start_date} to {end_date}")
        posts = await RSSPostRepository.get_by_date_range(start_date, end_date)

        if not posts:
            logger.info("No recent posts found")
            print("No posts found in the last 7 days.")
            return {"published_count": 0}

        # Create digest
        digest = create_digest(posts)

        # Publish to Telegram
        await publish_to_telegram(digest)

        logger.info(f"Successfully published digest with {len(posts)} posts")

        return {"published_count": len(posts)}

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
