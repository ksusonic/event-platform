"""Repository layer for RSS posts database operations."""

from typing import List, Optional
from datetime import datetime
from .session import db
from .models import RSSPost, TelegramChannel


class TelegramChannelRepository:
    """Repository for Telegram channel operations."""

    @staticmethod
    async def get_all() -> List[TelegramChannel]:
        """Get all Telegram channels."""
        query = """
            SELECT * FROM telegram_channels 
            ORDER BY channel_name ASC
        """
        rows = await db.fetch(query)
        return [TelegramChannel.from_row(row) for row in rows]

    @staticmethod
    async def get_by_id(channel_id: int) -> Optional[TelegramChannel]:
        """Get channel by ID."""
        query = "SELECT * FROM telegram_channels WHERE channel_id = $1"
        row = await db.fetchrow(query, channel_id)
        return TelegramChannel.from_row(row) if row else None

    @staticmethod
    async def get_by_name(channel_name: str) -> Optional[TelegramChannel]:
        """Get channel by name."""
        query = "SELECT * FROM telegram_channels WHERE channel_name = $1"
        row = await db.fetchrow(query, channel_name)
        return TelegramChannel.from_row(row) if row else None

    @staticmethod
    async def create(channel: TelegramChannel) -> int:
        """Create a new Telegram channel.

        Args:
            channel: TelegramChannel dataclass instance

        Returns:
            ID of created channel
        """
        query = """
            INSERT INTO telegram_channels (
                channel_id, channel_name, description, url
            ) VALUES ($1, $2, $3, $4)
            RETURNING channel_id
        """
        channel_id = await db.fetchval(
            query,
            channel.channel_id,
            channel.channel_name,
            channel.description,
            channel.url,
        )
        return channel_id

    @staticmethod
    async def update(channel: TelegramChannel) -> None:
        """Update a Telegram channel."""
        query = """
            UPDATE telegram_channels 
            SET channel_name = $2,
                description = $3,
                url = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE channel_id = $1
        """
        await db.execute(
            query,
            channel.channel_id,
            channel.channel_name,
            channel.description,
            channel.url,
        )

    @staticmethod
    async def delete(channel_id: int) -> None:
        """Delete a Telegram channel."""
        query = "DELETE FROM telegram_channels WHERE channel_id = $1"
        await db.execute(query, channel_id)


class RSSPostRepository:
    """Repository for RSS post operations."""

    @staticmethod
    async def create(post: RSSPost) -> str:
        """Create a new RSS post.

        Args:
            post: RSSPost dataclass instance

        Returns:
            Link of created post
        """
        query = """
            INSERT INTO rss_posts (
                link, content, pub_date, media
            ) VALUES ($1, $2, $3, $4)
            RETURNING link
        """
        link = await db.fetchval(
            query,
            post.link,
            post.content,
            post.pub_date,
            post.media,
        )
        return link

    @staticmethod
    async def get_by_link(link: str) -> Optional[RSSPost]:
        """Get post by link (URL)."""
        query = "SELECT * FROM rss_posts WHERE link = $1"
        row = await db.fetchrow(query, link)
        return RSSPost.from_row(row) if row else None

    @staticmethod
    async def get_all(
        limit: int = 100,
        offset: int = 0,
    ) -> List[RSSPost]:
        """Get posts.

        Args:
            limit: Maximum number of posts to return
            offset: Number of posts to skip

        Returns:
            List of RSSPost instances
        """
        query = """SELECT * FROM rss_posts 
                   ORDER BY created_at DESC 
                   LIMIT $1 OFFSET $2"""
        rows = await db.fetch(query, limit, offset)
        return [RSSPost.from_row(row) for row in rows]

    @staticmethod
    async def get_by_date_range(
        start_date: datetime, end_date: datetime, limit: int = 1000
    ) -> List[RSSPost]:
        """Get posts within a date range.

        Args:
            start_date: Start date
            end_date: End date
            limit: Maximum number of posts to return

        Returns:
            List of RSSPost instances
        """
        query = """
            SELECT * FROM rss_posts 
            WHERE pub_date >= $1 AND pub_date <= $2
            ORDER BY pub_date DESC 
            LIMIT $3
        """
        rows = await db.fetch(query, start_date, end_date, limit)
        return [RSSPost.from_row(row) for row in rows]

    @staticmethod
    async def delete(link: str) -> None:
        """Delete a post."""
        query = "DELETE FROM rss_posts WHERE link = $1"
        await db.execute(query, link)

    @staticmethod
    async def get_stats() -> dict:
        """Get database statistics."""
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN pub_date >= NOW() - INTERVAL '7 days' THEN 1 END) as recent
            FROM rss_posts
        """
        row = await db.fetchrow(query)
        return {
            "total": row["total"] or 0,
            "recent": row["recent"] or 0,
        }

    @staticmethod
    async def exists_by_link(link: str) -> bool:
        """Check if post with given link exists."""
        query = "SELECT 1 FROM rss_posts WHERE link = $1 LIMIT 1"
        result = await db.fetchval(query, link)
        return result is not None
