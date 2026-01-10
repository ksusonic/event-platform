"""Data models for RSS feeds."""

from dataclasses import dataclass, asdict
from typing import List, Optional
import json


@dataclass
class RSSItem:
    """Represents a single RSS feed item."""

    link: str
    description: str
    pub_date: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class RSSChannel:
    """Represents RSS feed metadata."""

    title: str
    link: str
    description: str
    language: Optional[str] = None
    last_build_date: Optional[str] = None
    items: List[RSSItem] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["items"] = [item.to_dict() for item in self.items]
        data["item_count"] = len(self.items)
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
