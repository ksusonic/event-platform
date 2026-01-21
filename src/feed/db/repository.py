"""Repository layer for RSS posts database operations."""

from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import json
from .session import db
from .models import RSSPost, TelegramChannel, OpenAIRequestLog, Event


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


class OpenAIRequestLogRepository:
    """Repository for OpenAI request log operations."""

    @staticmethod
    async def create(log: OpenAIRequestLog) -> int:
        """Create a new OpenAI request log.

        Args:
            log: OpenAIRequestLog dataclass instance

        Returns:
            ID of created log entry
        """
        query = """
            INSERT INTO openai_request_logs (
                batch_id, custom_id, request_type, model, endpoint,
                request_data, response_data, status, status_code,
                tokens_used, cost_estimate, error_message, post_link
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            RETURNING id
        """
        log_id = await db.fetchval(
            query,
            log.batch_id,
            log.custom_id,
            log.request_type,
            log.model,
            log.endpoint,
            json.dumps(log.request_data) if log.request_data else None,
            json.dumps(log.response_data) if log.response_data else None,
            log.status,
            log.status_code,
            log.tokens_used,
            log.cost_estimate,
            log.error_message,
            log.post_link,
        )
        return log_id

    @staticmethod
    async def update_status(
        log_id: int,
        status: str,
        response_data: Optional[dict] = None,
        status_code: Optional[int] = None,
        tokens_used: Optional[int] = None,
        cost_estimate: Optional[Decimal] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update log entry status.

        Args:
            log_id: ID of the log entry
            status: New status ('completed', 'failed', etc.)
            response_data: Response data from OpenAI
            status_code: HTTP status code
            tokens_used: Number of tokens used
            cost_estimate: Estimated cost
            error_message: Error message if failed
        """
        query = """
            UPDATE openai_request_logs 
            SET status = $2,
                response_data = $3,
                status_code = $4,
                tokens_used = $5,
                cost_estimate = $6,
                error_message = $7,
                completed_at = $8,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        completed_at = datetime.now() if status in ["completed", "failed"] else None
        await db.execute(
            query,
            log_id,
            status,
            json.dumps(response_data) if response_data else None,
            status_code,
            tokens_used,
            cost_estimate,
            error_message,
            completed_at,
        )

    @staticmethod
    async def get_by_id(log_id: int) -> Optional[OpenAIRequestLog]:
        """Get log entry by ID."""
        query = "SELECT * FROM openai_request_logs WHERE id = $1"
        row = await db.fetchrow(query, log_id)
        return OpenAIRequestLog.from_row(row) if row else None

    @staticmethod
    async def get_by_batch_id(batch_id: str) -> List[OpenAIRequestLog]:
        """Get all log entries for a batch."""
        query = """
            SELECT * FROM openai_request_logs 
            WHERE batch_id = $1 
            ORDER BY created_at DESC
        """
        rows = await db.fetch(query, batch_id)
        return [OpenAIRequestLog.from_row(row) for row in rows]

    @staticmethod
    async def get_by_custom_id(custom_id: str) -> Optional[OpenAIRequestLog]:
        """Get log entry by custom_id."""
        query = """
            SELECT * FROM openai_request_logs 
            WHERE custom_id = $1 
            ORDER BY created_at DESC 
            LIMIT 1
        """
        row = await db.fetchrow(query, custom_id)
        return OpenAIRequestLog.from_row(row) if row else None

    @staticmethod
    async def get_all(
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        request_type: Optional[str] = None,
    ) -> List[OpenAIRequestLog]:
        """Get log entries with optional filters.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            status: Filter by status
            request_type: Filter by request type

        Returns:
            List of OpenAIRequestLog instances
        """
        query = "SELECT * FROM openai_request_logs WHERE 1=1"
        params = []
        param_count = 1

        if status is not None:
            query += f" AND status = ${param_count}"
            params.append(status)
            param_count += 1

        if request_type is not None:
            query += f" AND request_type = ${param_count}"
            params.append(request_type)
            param_count += 1

        query += f" ORDER BY created_at DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
        params.extend([limit, offset])

        rows = await db.fetch(query, *params)
        return [OpenAIRequestLog.from_row(row) for row in rows]

    @staticmethod
    async def get_stats() -> dict:
        """Get OpenAI request statistics."""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(tokens_used) as total_tokens,
                SUM(cost_estimate) as total_cost
            FROM openai_request_logs
        """
        row = await db.fetchrow(query)
        return {
            "total": row["total"] or 0,
            "completed": row["completed"] or 0,
            "failed": row["failed"] or 0,
            "pending": row["pending"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "total_cost": float(row["total_cost"]) if row["total_cost"] else 0.0,
        }

    @staticmethod
    async def delete_old_logs(days: int = 30) -> int:
        """Delete logs older than specified days.

        Args:
            days: Number of days to keep logs

        Returns:
            Number of deleted rows
        """
        query = (
            """
            DELETE FROM openai_request_logs 
            WHERE created_at < NOW() - INTERVAL '%s days'
        """
            % days
        )
        result = await db.execute(query)
        # Parse result like "DELETE 5" to get count
        return int(result.split()[-1]) if result else 0


class EventRepository:
    """Repository for event operations."""

    @staticmethod
    async def create(event: Event) -> int:
        """Create a new event.

        Args:
            event: Event dataclass instance

        Returns:
            ID of created event
        """
        query = """
            INSERT INTO events (
                post_link, title, summary, event_date, event_date_is_approximate,
                location, event_type, confidence, additional_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """
        event_id = await db.fetchval(
            query,
            event.post_link,
            event.title,
            event.summary,
            event.event_date,
            event.event_date_is_approximate,
            event.location,
            event.event_type,
            event.confidence,
            json.dumps(event.additional_data) if event.additional_data else None,
        )
        return event_id

    @staticmethod
    async def get_by_id(event_id: int) -> Optional[Event]:
        """Get event by ID."""
        query = "SELECT * FROM events WHERE id = $1"
        row = await db.fetchrow(query, event_id)
        return Event.from_row(row) if row else None

    @staticmethod
    async def get_by_post_link(post_link: str) -> Optional[Event]:
        """Get event by post link."""
        query = "SELECT * FROM events WHERE post_link = $1"
        row = await db.fetchrow(query, post_link)
        return Event.from_row(row) if row else None

    @staticmethod
    async def get_all(
        limit: int = 100, offset: int = 0, order_by: str = "event_date"
    ) -> List[Event]:
        """Get all events with pagination.

        Args:
            limit: Maximum number of events to return
            offset: Number of events to skip
            order_by: Field to order by (event_date, created_at, confidence)

        Returns:
            List of Event instances
        """
        # Validate order_by to prevent SQL injection
        valid_order_fields = ["event_date", "created_at", "confidence", "id"]
        if order_by not in valid_order_fields:
            order_by = "event_date"

        query = f"""
            SELECT * FROM events 
            ORDER BY {order_by} DESC NULLS LAST
            LIMIT $1 OFFSET $2
        """
        rows = await db.fetch(query, limit, offset)
        return [Event.from_row(row) for row in rows]

    @staticmethod
    async def get_upcoming_events(limit: int = 50) -> List[Event]:
        """Get upcoming events (events with future dates).

        Args:
            limit: Maximum number of events to return

        Returns:
            List of Event instances
        """
        query = """
            SELECT * FROM events 
            WHERE event_date >= CURRENT_TIMESTAMP
            ORDER BY event_date ASC
            LIMIT $1
        """
        rows = await db.fetch(query, limit)
        return [Event.from_row(row) for row in rows]

    @staticmethod
    async def get_by_type(event_type: str, limit: int = 100) -> List[Event]:
        """Get events by type.

        Args:
            event_type: Type of event (e.g., 'conference', 'meetup')
            limit: Maximum number of events to return

        Returns:
            List of Event instances
        """
        query = """
            SELECT * FROM events 
            WHERE event_type = $1
            ORDER BY event_date DESC NULLS LAST
            LIMIT $2
        """
        rows = await db.fetch(query, event_type, limit)
        return [Event.from_row(row) for row in rows]

    @staticmethod
    async def update(event: Event) -> None:
        """Update an event.

        Args:
            event: Event dataclass instance with id set
        """
        if not event.id:
            raise ValueError("Event ID must be set to update")

        query = """
            UPDATE events 
            SET post_link = $2,
                title = $3,
                summary = $4,
                event_date = $5,
                event_date_is_approximate = $6,
                location = $7,
                event_type = $8,
                confidence = $9,
                additional_data = $10,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        await db.execute(
            query,
            event.id,
            event.post_link,
            event.title,
            event.summary,
            event.event_date,
            event.event_date_is_approximate,
            event.location,
            event.event_type,
            event.confidence,
            json.dumps(event.additional_data) if event.additional_data else None,
        )

    @staticmethod
    async def delete(event_id: int) -> None:
        """Delete an event.

        Args:
            event_id: ID of the event to delete
        """
        query = "DELETE FROM events WHERE id = $1"
        await db.execute(query, event_id)

    @staticmethod
    async def count() -> int:
        """Get total count of events."""
        query = "SELECT COUNT(*) FROM events"
        return await db.fetchval(query)

    @staticmethod
    async def search(
        query_text: Optional[str] = None,
        event_type: Optional[str] = None,
        location: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Search events with multiple filters.

        Args:
            query_text: Text to search in title and summary
            event_type: Filter by event type
            location: Filter by location
            date_from: Filter events from this date
            date_to: Filter events until this date
            limit: Maximum number of results

        Returns:
            List of Event instances
        """
        conditions = []
        params = []
        param_count = 0

        if query_text:
            param_count += 1
            conditions.append(f"(title ILIKE ${param_count} OR summary ILIKE ${param_count})")
            params.append(f"%{query_text}%")

        if event_type:
            param_count += 1
            conditions.append(f"event_type = ${param_count}")
            params.append(event_type)

        if location:
            param_count += 1
            conditions.append(f"location ILIKE ${param_count}")
            params.append(f"%{location}%")

        if date_from:
            param_count += 1
            conditions.append(f"event_date >= ${param_count}")
            params.append(date_from)

        if date_to:
            param_count += 1
            conditions.append(f"event_date <= ${param_count}")
            params.append(date_to)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        param_count += 1
        params.append(limit)

        query = f"""
            SELECT * FROM events 
            WHERE {where_clause}
            ORDER BY event_date DESC NULLS LAST
            LIMIT ${param_count}
        """
        rows = await db.fetch(query, *params)
        return [Event.from_row(row) for row in rows]
