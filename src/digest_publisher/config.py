"""Configuration for Digest Publisher service."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


@dataclass
class DigestPublisherConfig:
    """Digest Publisher configuration settings."""

    # OpenAI settings for summarization
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("DIGEST_PUBLISHER_MODEL", "gpt-4o-mini")
    openai_max_tokens: int = int(os.getenv("DIGEST_PUBLISHER_MAX_TOKENS", "2000"))
    openai_temperature: float = float(os.getenv("DIGEST_PUBLISHER_TEMPERATURE", "0.5"))

    # Telegram Bot settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Digest settings
    days_back: int = int(os.getenv("DIGEST_PUBLISHER_DAYS_BACK", "7"))
    max_posts: int = int(os.getenv("DIGEST_PUBLISHER_MAX_POSTS", "50"))

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If required configuration is missing
        """
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        if not self.telegram_chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")

        return True


digest_publisher_settings = DigestPublisherConfig()
