"""Repository layer for RSS posts database operations."""

from typing import List, Optional
import json
from .session import db
from .models import RSSPost


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
                link, content, pub_date, media,
                is_processed, is_event, classification_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING link
        """
        link = await db.fetchval(
            query,
            post.link,
            post.content,
            post.pub_date,
            post.media,
            post.is_processed,
            post.is_event,
            json.dumps(post.classification_data) if post.classification_data else None,
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
        is_processed: Optional[bool] = None,
        is_event: Optional[bool] = None,
    ) -> List[RSSPost]:
        """Get posts with optional filters.

        Args:
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            is_processed: Filter by processed status (None = no filter)
            is_event: Filter by event status (None = no filter)

        Returns:
            List of RSSPost instances
        """
        query = "SELECT * FROM rss_posts WHERE 1=1"
        params = []
        param_count = 1

        if is_processed is not None:
            query += f" AND is_processed = ${param_count}"
            params.append(is_processed)
            param_count += 1

        if is_event is not None:
            query += f" AND is_event = ${param_count}"
            params.append(is_event)
            param_count += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [RSSPost.from_row(row) for row in rows]

    @staticmethod
    async def get_unprocessed(limit: int = 100) -> List[RSSPost]:
        """Get unprocessed posts."""
        query = """
            SELECT * FROM rss_posts 
            WHERE is_processed = FALSE 
            ORDER BY created_at ASC 
            LIMIT $1
        """
        rows = await db.fetch(query, limit)
        return [RSSPost.from_row(row) for row in rows]

    @staticmethod
    async def mark_as_processed(
        link: str,
        is_event: bool,
        classification_data: Optional[dict] = None,
    ) -> None:
        """Mark a post as processed and set classification.

        Args:
            link: Link of the post
            is_event: Whether the post is an event
            classification_data: Optional classification metadata
        """
        query = """
            UPDATE rss_posts 
            SET is_processed = TRUE, 
                is_event = $2, 
                classification_data = $3,
                classified_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE link = $1
        """
        await db.execute(
            query,
            link,
            is_event,
            json.dumps(classification_data) if classification_data else None,
        )

    @staticmethod
    async def mark_as_unprocessed(link: str) -> None:
        """Mark a post as unprocessed."""
        query = """
            UPDATE rss_posts 
            SET is_processed = FALSE, 
                updated_at = CURRENT_TIMESTAMP
            WHERE link = $1
        """
        await db.execute(query, link)

    @staticmethod
    async def update_classification(
        link: str,
        is_event: bool,
        classification_data: Optional[dict] = None,
    ) -> None:
        """Update classification for a post."""
        query = """
            UPDATE rss_posts 
            SET is_event = $2, 
                classification_data = $3,
                updated_at = CURRENT_TIMESTAMP
            WHERE link = $1
        """
        await db.execute(
            query,
            link,
            is_event,
            json.dumps(classification_data) if classification_data else None,
        )

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
                SUM(CASE WHEN is_processed = TRUE THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN is_event = TRUE THEN 1 ELSE 0 END) as events,
                SUM(CASE WHEN is_processed = FALSE THEN 1 ELSE 0 END) as unprocessed
            FROM rss_posts
        """
        row = await db.fetchrow(query)
        return {
            "total": row["total"] or 0,
            "processed": row["processed"] or 0,
            "events": row["events"] or 0,
            "unprocessed": row["unprocessed"] or 0,
        }

    @staticmethod
    async def exists_by_link(link: str) -> bool:
        """Check if post with given link exists."""
        query = "SELECT 1 FROM rss_posts WHERE link = $1 LIMIT 1"
        result = await db.fetchval(query, link)
        return result is not None
