"""Entry point for Digest Publisher service.

Run with: python -m src.digest_publisher
"""

import asyncio
import logging
import os
from typing import List
from datetime import datetime, timedelta

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from common.db.session import db
from common.db.repository import RSSPostRepository
from common.db.models import RSSPost

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def escape_markdown_v2(text: str) -> str:
    """
    Escape special characters for Telegram MarkdownV2.

    Args:
        text: Text to escape

    Returns:
        Escaped text
    """
    # Characters that need to be escaped in MarkdownV2
    special_chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def format_post_for_telegram(post: RSSPost) -> str:
    """
    Format a post for Telegram message with MarkdownV2.

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

    title = escape_markdown_v2(title)
    lines.append(f"📰 *{title}*")

    if post.pub_date:
        date_str = escape_markdown_v2(post.pub_date.strftime("%Y-%m-%d %H:%M"))
        lines.append(f"🕐 {date_str}")

    if post.content:
        # Truncate long content for Telegram
        content = post.content[:300] + "..." if len(post.content) > 300 else post.content
        content = escape_markdown_v2(content)
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
        return "No posts found for this period\."

    lines = []
    lines.append("📣 *News Digest*")
    lines.append(f"Found {len(posts)} recent posts\n")
    lines.append(escape_markdown_v2("=" * 40))
    lines.append("")

    for i, post in enumerate(posts, 1):
        lines.append(format_post_for_telegram(post))
        if i < len(posts):
            lines.append("\n" + escape_markdown_v2("-" * 40) + "\n")

    return "\n".join(lines)


async def publish_to_telegram(message: str):
    """
    Publish message to Telegram.

    Args:
        message: Message to publish

    Raises:
        ValueError: If bot token or chat ID not configured
        TelegramError: If sending message fails
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, printing to console instead")
        print("\n" + "=" * 80)
        print("TELEGRAM DIGEST (BOT TOKEN NOT CONFIGURED)")
        print("=" * 80)
        print(message)
        print("=" * 80)
        return

    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

    try:
        bot = Bot(token=bot_token)

        # Split message if it exceeds Telegram's limit (4096 characters)
        max_length = 4000  # Leave some margin
        if len(message) <= max_length:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2,
                disable_web_page_preview=True,
            )
            logger.info(f"Successfully sent digest to Telegram chat {chat_id}")
        else:
            # Split into multiple messages
            parts = [message[i : i + max_length] for i in range(0, len(message), max_length)]
            for i, part in enumerate(parts, 1):
                await bot.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True,
                )
                logger.info(f"Sent part {i}/{len(parts)} to Telegram")

    except TelegramError as e:
        logger.error(f"Failed to send message to Telegram: {e}")
        raise


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
