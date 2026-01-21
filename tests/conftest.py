import os

# Use the main database for tests
os.environ["DATABASE_DSN"] = os.getenv(
    "TEST_DATABASE_DSN", "postgresql://root:password@localhost:5432/eventdb"
)


# Configure pytest-asyncio to use function scope by default
pytest_plugins = ("pytest_asyncio",)
