"""Database configuration for asyncpg."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    """Application settings."""

    def __init__(self):
        self.database_host = os.getenv("DATABASE_HOST", "localhost")
        self.database_port = int(os.getenv("DATABASE_PORT", 5432))
        self.database_name = os.getenv("DATABASE_NAME", "eventdb")
        self.database_user = os.getenv("DATABASE_USER", "root")
        self.database_password = os.getenv("DATABASE_PASSWORD", "password")

    def get_dsn(self) -> str:
        """Get database connection string (DSN) for asyncpg."""
        return (
            f"postgresql://{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )


settings = Settings()
