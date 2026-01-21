"""Configuration for Digest Publisher service."""

import os
from dataclasses import dataclass


@dataclass
class DigestPublisherConfig:
    """Digest Publisher configuration settings."""

    # Telegram Bot settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Digest settings
    digest_days: int = int(os.getenv("DIGEST_DAYS", "7"))
    max_posts_per_digest: int = int(os.getenv("MAX_POSTS_PER_DIGEST", "20"))

    # Formatting
    truncate_content_length: int = int(os.getenv("TRUNCATE_CONTENT_LENGTH", "300"))

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If required configuration is missing
        """
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if not self.telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

        return True
