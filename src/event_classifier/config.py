"""Configuration for OpenAI integration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class OpenAISettings:
    """OpenAI configuration settings."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.batch_size = int(os.getenv("OPENAI_BATCH_SIZE", 100))
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", 500))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.3))


openai_settings = OpenAISettings()
