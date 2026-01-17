"""Database configuration for asyncpg."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    def __init__(self):
        self.dsn = os.getenv("DATABASE_DSN")
        if self.dsn is None:
            raise EnvironmentError("DATABASE_DSN not set")

    def get_dsn(self) -> str:
        return self.dsn


settings = Settings()
