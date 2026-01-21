"""Entry point for Digest Publisher service.

Run with: python -m src.digest_publisher
"""

import asyncio
import logging
from typing import List
from datetime import datetime, timedelta

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError, NetworkError
from openai import AsyncOpenAI

from common.db.session import db
from common.db.repository import RSSPostRepository
from common.db.models import RSSPost
from .config import digest_publisher_settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def prepare_posts_for_prompt(posts: List[RSSPost]) -> str:
    """
    Prepare posts in a format suitable for OpenAI prompt.

    Args:
        posts: List of RSSPost objects

    Returns:
        Formatted string with all posts
    """
    formatted_posts = []

    for i, post in enumerate(posts, 1):
        post_info = [f"\n--- Post {i} ---"]

        if post.pub_date:
            post_info.append(f"Date: {post.pub_date.strftime('%Y-%m-%d %H:%M')}")

        if post.content:
            # Truncate very long content
            content = post.content[:1000] + "..." if len(post.content) > 1000 else post.content
            post_info.append(f"Content: {content}")

        post_info.append(f"Source: {post.link}")
        formatted_posts.append("\n".join(post_info))

    return "\n".join(formatted_posts)


async def generate_ai_digest(posts: List[RSSPost], client: AsyncOpenAI) -> str:
    """
    Generate an AI-powered digest of RSS posts.

    Args:
        posts: List of RSSPost objects
        client: AsyncOpenAI client instance

    Returns:
        AI-generated digest suitable for Telegram
    """
    if not posts:
        return "No posts found for this period."

    logger.info(f"Generating AI digest for {len(posts)} posts...")

    # Prepare posts for the prompt
    posts_content = prepare_posts_for_prompt(posts)

    # Create the system prompt
    system_prompt = """Developer: # Role and Objective
- Deliver engaging and informative news digests optimized for Telegram channels.

# Checklist (Plan First)
Begin with a concise checklist (3-7 bullets) of what you will do; keep items conceptual, not implementation-level.
- Review all supplied posts to extract key topics.
- Identify the main points for summary inclusion.
- Group related topics for a logical, cohesive flow.
- Plan emoji and formatting usage for engagement.
- Ensure all formatting aligns with Telegram HTML specifications.

# Instructions
1. Analyze every provided post thoroughly.
2. Create a concise, engaging summary that highlights critical information.
3. Structure the summary to be Telegram-friendly, utilizing emojis strategically.
4. Make the digest informative and easy to read.
5. Organize related topics together for improved clarity.

# Format Guidelines
- Start with a catchy, attention-grabbing header.
- Integrate emojis thoughtfully (e.g., 📰 🔥 💡 ⚡ 🏆).
- Limit paragraph length to enhance readability.

# Critical Formatting Rules
- Always use Telegram HTML tags for formatting:
    - <b>text</b> for bold text.
    - <i>text</i> for italics.
    - <a href="URL">text</a> for hyperlinks.
    - <code>text</code> for inline code.
- Never use Markdown syntax (**, *, _, `, etc.).
- Escape &, <, and > only when they appear in text content (never within HTML tags).

# Review Checklist
- Confirm all output formatting complies with Telegram HTML.
- Verify effective use of emojis and sectioning for clarity and engagement.
- Ensure the final summary fulfills the brief and is ready for posting.

# Post-action Validation
After generating the digest, validate in 1-2 lines that formatting adheres to Telegram HTML, emojis are used effectively, and the summary meets all requirements. If any aspect is lacking, revise minimally and re-check.

# Example Formatting
<b>Important Header</b>
This is regular text with an <i>emphasized word</i> and a <a href="https://example.com">link</a>."""

    # Create the user prompt
    user_prompt = f"""Please create an engaging news digest from the following {len(posts)} posts:

{posts_content}

Create a Telegram-friendly digest that readers will find informative and easy to read."""

    try:
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=digest_publisher_settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=digest_publisher_settings.openai_max_tokens,
            temperature=digest_publisher_settings.openai_temperature,
        )

        digest = response.choices[0].message.content
        logger.info("Successfully generated AI digest")
        return digest

    except Exception as e:
        logger.error(f"Failed to generate AI digest: {e}", exc_info=True)
        # Fallback to simple message
        return f"❌ Failed to generate digest: {str(e)}\n\nFound {len(posts)} posts from the last {digest_publisher_settings.days_back} days."


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
        return r"No posts found for this period\."

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
        message: Message to publish (plain text, no markdown)

    Raises:
        ValueError: If bot token or chat ID not configured
        TelegramError: If sending message fails
    """
    bot_token = digest_publisher_settings.telegram_bot_token
    chat_id = digest_publisher_settings.telegram_chat_id

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
                parse_mode=ParseMode.HTML,
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
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
                logger.info(f"Sent part {i}/{len(parts)} to Telegram")
                # Small delay between messages
                if i < len(parts):
                    await asyncio.sleep(0.5)

    except NetworkError as e:
        logger.error(f"Network error connecting to Telegram: {e}")
        logger.error("Check your internet connection, proxy settings, or firewall")
        raise
    except TelegramError as e:
        logger.error(f"Failed to send message to Telegram: {e}")
        raise


async def main():
    """Main entry point for Digest Publisher service."""
    logger.info(f"Using OpenAI model: {digest_publisher_settings.openai_model}")

    try:
        if not db.pool:
            await db.connect()
            logger.info("Connected to database")

        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=digest_publisher_settings.openai_api_key)

        # Get posts from the configured time range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=digest_publisher_settings.days_back)

        logger.info(f"Fetching posts from {start_date} to {end_date}")
        posts = await RSSPostRepository.get_by_date_range(start_date, end_date)

        if not posts:
            logger.info("No recent posts found")
            print(f"No posts found in the last {digest_publisher_settings.days_back} days.")
            return {"published_count": 0}

        # Limit posts if there are too many
        if len(posts) > digest_publisher_settings.max_posts:
            logger.warning(
                f"Found {len(posts)} posts, limiting to {digest_publisher_settings.max_posts}"
            )
            posts = posts[: digest_publisher_settings.max_posts]

        # Generate AI digest
        digest = await generate_ai_digest(posts, client)

        # Publish to Telegram
        await publish_to_telegram(digest)

        logger.info(f"Successfully published AI digest with {len(posts)} posts")

        return {"published_count": len(posts)}

    except ValueError as e:
        # Handle configuration errors
        logger.error(f"Configuration error: {e}")
        print(f"Configuration error: {e}")
        print("Please check OPENAI_API_KEY and Telegram settings.")
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
