"""Entry point for Digest Publisher service.

Run with: python -m src.digest_publisher
"""

import asyncio
import logging
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict

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


def prepare_posts_for_prompt(posts: List[RSSPost], section_title: str = "Posts") -> str:
    """
    Prepare posts in a format suitable for OpenAI prompt, grouped by day.

    Args:
        posts: List of RSSPost objects
        section_title: Title for this section of posts

    Returns:
        Formatted string with all posts grouped by day
    """
    if not posts:
        return ""

    # Group posts by date
    posts_by_date: Dict[str, List[RSSPost]] = defaultdict(list)
    for post in posts:
        if post.pub_date:
            date_key = post.pub_date.strftime("%Y-%m-%d")
            posts_by_date[date_key].append(post)
        else:
            # Posts without date go to "Unknown Date"
            posts_by_date["Unknown Date"].append(post)

    # Sort dates in descending order (newest first)
    sorted_dates = sorted([d for d in posts_by_date.keys() if d != "Unknown Date"], reverse=True)
    if "Unknown Date" in posts_by_date:
        sorted_dates.append("Unknown Date")

    formatted_posts = [f"\n=== {section_title} ==="]

    post_counter = 1
    for date_key in sorted_dates:
        day_posts = posts_by_date[date_key]

        # Add day header
        if date_key == "Unknown Date":
            formatted_posts.append(f"\n## {date_key} ({len(day_posts)} posts)")
        else:
            # Convert to more readable format
            date_obj = datetime.strptime(date_key, "%Y-%m-%d")
            day_name = date_obj.strftime("%A, %B %d, %Y")
            formatted_posts.append(f"\n## {day_name} ({len(day_posts)} posts)")

        # Add posts for this day
        for post in day_posts:
            post_info = [f"\n--- Post {post_counter} ---"]

            if post.pub_date:
                post_info.append(f"Time: {post.pub_date.strftime('%H:%M')}")

            if post.content:
                # Truncate very long content
                content = post.content[:1000] + "..." if len(post.content) > 1000 else post.content
                post_info.append(f"Content: {content}")

            post_info.append(f"Source: {post.link}")
            formatted_posts.append("\n".join(post_info))
            post_counter += 1

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

    # Get links of current posts to exclude from historical lookup
    current_post_links = [post.link for post in posts]

    # Fetch previous posts from last 2 days (excluding current posts)
    logger.info("Fetching previous posts from last 2 days...")
    previous_posts = await RSSPostRepository.get_recent_posts_excluding(
        days=2,
        exclude_links=current_post_links,
        limit=50,  # Limit to avoid overwhelming the context
    )
    logger.info(f"Found {len(previous_posts)} previous posts to include as context")

    # Prepare posts for the prompt
    posts_content = prepare_posts_for_prompt(posts, "CURRENT Posts to Summarize")
    previous_posts_content = prepare_posts_for_prompt(
        previous_posts, "PREVIOUS Posts (Already Published - DO NOT REPEAT)"
    )

    # Create the system prompt
    system_prompt = """Вы — помощник для создания новостных дайджестов в Telegram.

# Задача
Создайте интересный и информативный дайджест новостей на русском языке для публикации в Telegram-канале.

# Инструкции
1. Проанализируйте все ТЕКУЩИЕ посты.
2. Организуйте контент по датам с чёткими заголовками дней (например, "📅 Понедельник, 20 января 2026").
3. Внутри каждого дня группируйте связанные темы для логичного повествования.
4. Используйте эмодзи для улучшения восприятия (📰 🔥 💡 ⚡ 🏆 📅).
5. Пишите кратко и понятно.

# ВАЖНО: Анти-дублирование
- Вам предоставлены ПРЕДЫДУЩИЕ посты — они УЖЕ были опубликованы.
- НЕ включайте и НЕ упоминайте предыдущие посты в дайджесте.
- Создавайте дайджест ТОЛЬКО из раздела "CURRENT Posts to Summarize".
- Если текущий пост похож на предыдущий, можете кратко упомянуть, что это обновление.

# Форматирование
- Используйте только Telegram HTML теги: <b>жирный</b>, <i>курсив</i>, <a href="URL">ссылка</a>
- Никогда не используйте Markdown (**, *, _, `)
- Экранируйте &, <, > только в тексте контента (не внутри HTML-тегов)"""

    # Create the user prompt
    user_prompt_parts = [
        "Создайте увлекательный новостной дайджест на русском языке из ТЕКУЩИХ постов ниже.",
        f"\n{previous_posts_content}" if previous_posts else "",
        f"\n{posts_content}",
        f"\n\n**ВАЖНО**: Создайте дайджест ТОЛЬКО из {len(posts)} ТЕКУЩИХ постов, перечисленных выше.",
        f"НЕ включайте и не упоминайте {len(previous_posts)} предыдущих постов — они даны только для контекста."
        if previous_posts
        else "",
        "\n\n**СТРУКТУРА**: Организуйте дайджест по датам с чёткими заголовками дней (например, '📅 Понедельник, 20 января 2026').",
        "Внутри каждого дня представьте связанные новости вместе в связной форме.",
    ]
    user_prompt = "".join(user_prompt_parts)

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

        # Mark posts as published after successful publication
        post_links = [post.link for post in posts]
        updated_count = await RSSPostRepository.mark_as_published(post_links)
        logger.info(f"Marked {updated_count} posts as published")

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
