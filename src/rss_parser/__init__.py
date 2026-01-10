"""RSS Parser - Production-ready RSS/Atom feed parser."""

from .core.parser import RSSParser
from .models.feed import RSSChannel, RSSItem

__version__ = "1.0.0"
__all__ = ["RSSParser", "RSSChannel", "RSSItem"]
