import os

# Use the main database for tests
os.environ["DATABASE_HOST"] = os.getenv("TEST_DATABASE_HOST", "localhost")
os.environ["DATABASE_PORT"] = os.getenv("TEST_DATABASE_PORT", "5432")
os.environ["DATABASE_NAME"] = os.getenv("TEST_DATABASE_NAME", "eventdb")
os.environ["DATABASE_USER"] = os.getenv("TEST_DATABASE_USER", "root")
os.environ["DATABASE_PASSWORD"] = os.getenv("TEST_DATABASE_PASSWORD", "password")


# Configure pytest-asyncio to use function scope by default
pytest_plugins = ("pytest_asyncio",)
