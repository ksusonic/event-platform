"""Data models for RSS posts (dataclass representations)."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Union
from email.utils import parsedate_to_datetime
import json


@dataclass
class RSSPost:
    """Dataclass representation of an RSS post."""

    link: str
    content: str
    pub_date: Optional[datetime] = None
    media: Optional[str] = None
    is_processed: bool = False
    is_event: Optional[bool] = None
    classification_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    classified_at: Optional[datetime] = None

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
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
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
        """Create RSSPost from database row.

        Note: asyncpg returns JSONB fields as already-parsed dictionaries/lists,
        but if they come as strings, we parse them.
        """

        # Helper to parse JSON if it's a string, otherwise return as-is
        def parse_json(value):
            if value is None:
                return None
            if isinstance(value, str):
                return json.loads(value)
            return value

        return RSSPost(
            link=row["link"],
            content=row["content"],
            pub_date=row.get("pub_date"),
            media=row.get("media"),
            is_processed=row.get("is_processed", False),
            is_event=row.get("is_event"),
            classification_data=parse_json(row.get("classification_data")),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            classified_at=row.get("classified_at"),
        )
