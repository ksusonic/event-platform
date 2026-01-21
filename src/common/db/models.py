"""Data models for RSS posts (dataclass representations)."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
from email.utils import parsedate_to_datetime


@dataclass
class TelegramChannel:
    """Dataclass representation of a Telegram channel."""

    channel_id: int
    channel_name: str
    description: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_row(row: dict) -> "TelegramChannel":
        """Create TelegramChannel from database row."""
        return TelegramChannel(
            channel_id=row["channel_id"],
            channel_name=row["channel_name"],
            description=row.get("description"),
            url=row.get("url"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )


@dataclass
class RSSPost:
    """Dataclass representation of an RSS post."""

    link: str
    content: str
    pub_date: Optional[datetime] = None
    media: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Parse pub_date string into datetime if needed."""
        if self.pub_date and isinstance(self.pub_date, str):
            self.pub_date = self._parse_datetime(self.pub_date)

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """Parse datetime from string.

        Supports:
        - ISO 8601: '2026-01-10T10:00:00Z'
        - RFC 2822: 'Thu, 08 Jan 2026 06:42:01 +0000'

        Returns timezone-naive datetime for PostgreSQL TIMESTAMP compatibility.
        """
        dt = None

        # Try RFC 2822 format first (common in RSS feeds)
        try:
            dt = parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            pass

        # Try ISO 8601 format
        if dt is None:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # If all fail, raise error
        if dt is None:
            raise ValueError(f"Unable to parse datetime from: {date_str}")

        # Convert to timezone-naive (PostgreSQL TIMESTAMP expects naive datetimes)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        return dt

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_row(row: dict) -> "RSSPost":
        """Create RSSPost from database row."""
        return RSSPost(
            link=row["link"],
            content=row["content"],
            pub_date=row.get("pub_date"),
            media=row.get("media"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )
