"""Entry point for Summarizer service.

Run with: python -m src.summarizer
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


async def summarize_posts(posts: List[RSSPost]) -> str:
    """
    Create a summary of RSS posts.

    Args:
        posts: List of RSSPost objects

    Returns:
        Formatted summary string
    """
    if not posts:
        return "No posts found for the specified period."

    summary = []
    summary.append(f"📰 News Summary - {len(posts)} posts\n")
    summary.append("=" * 80)

    for i, post in enumerate(posts, 1):
        # Extract title from link or use first line of content
        title = post.link.split("/")[-1].replace("-", " ").replace("_", " ")[:100]
        if len(title) < 10 and post.content:
            title = post.content.split("\n")[0][:100]

        summary.append(f"\n{i}. {title}")
        if post.pub_date:
            summary.append(f"   📅 {post.pub_date.strftime('%Y-%m-%d %H:%M')}")

        if post.content:
            # Truncate long content
            content = post.content[:300] + "..." if len(post.content) > 300 else post.content
            summary.append(f"   {content}")

        summary.append(f"   🔗 {post.link}")
        summary.append("")

    summary.append("=" * 80)
    return "\n".join(summary)


async def main():
    """Main entry point for Summarizer service."""
    logger.info("Starting Summarizer service...")

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
            logger.info("No posts found in the specified date range")
            print("No posts found in the last 7 days.")
            return {"post_count": 0}

        # Create summary
        summary = await summarize_posts(posts)
        print(summary)

        logger.info(f"Successfully summarized {len(posts)} posts")

        return {"post_count": len(posts)}

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
