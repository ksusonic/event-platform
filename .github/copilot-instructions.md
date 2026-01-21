# Event Platform - AI Agent Instructions

## Architecture Overview

This is a **multi-agent pipeline** for aggregating and publishing Telegram news events. Four coordinated services run sequentially:

1. **RSSReader** (`src/rss_reader`) - Fetches posts from Telegram channels via RSS Bridge
2. **EventClassifier** (`src/event_classifier`) - Uses OpenAI to classify posts as events
3. **Summarizer** (integrated in digest_publisher) - Generates event summaries
4. **DigestPublisher** (`src/digest_publisher`) - Publishes to Telegram

The **Pipeline Orchestrator** (`src/pipeline`) coordinates execution with retry logic, timeouts, and scheduling.

**Shared code** lives in `src/common/` (database, models, utilities).

## Running the Project

**Primary execution method**: Use `uv run` (UV package manager)

```bash
# Run pipeline once
uv run -m src.pipeline

# Run on schedule
uv run -m src.pipeline --schedule --interval 60

# Run individual agents (for development/debugging)
uv run -m src.rss_reader
uv run -m src.digest_publisher

# Run tests
uv run pytest tests

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

**Docker deployment**: `docker-compose up -d` (includes PostgreSQL + scheduled pipeline)

## Database Patterns

- **PostgreSQL 17+** with `asyncpg` driver (no SQLAlchemy ORM)
- **Manual schema management** via Alembic migrations in `alembic/versions/`
- **Repository pattern** for data access (`src/common/db/repository.py`)
  - Use static methods: `RSSPostRepository.create(post)`, `TelegramChannelRepository.get_all()`
- **Dataclass models** in `src/common/db/models.py` (not SQLAlchemy models)
  - `RSSPost`, `TelegramChannel`, `Event`, `OpenAIRequestLog`
- **Global db instance** imported as `from common.db.session import db`
  - Call `await db.connect()` before operations, `await db.disconnect()` after
  - Connection pooling configured: min=5, max=20, timeout=60s

**Example database operation**:
```python
from common.db.session import db
from common.db.repository import RSSPostRepository
from common.db.models import RSSPost

await db.connect()
post = RSSPost(link="...", content="...", pub_date="2026-01-10T10:00:00Z")
await RSSPostRepository.create(post)
await db.disconnect()
```

## Configuration Management

**Environment-driven** config with dataclass patterns:

- `PipelineConfig` (`src/pipeline/config.py`) - orchestration settings
- `DigestPublisherConfig` (`src/digest_publisher/config.py`) - OpenAI/Telegram settings
- Database config in `src/common/db/config.py`

**All config uses `os.getenv()` with defaults** - never hardcode credentials.

Example pattern from codebase:
```python
@dataclass
class PipelineConfig:
    run_interval_minutes: int = int(os.getenv("PIPELINE_INTERVAL_MINUTES", "60"))
    max_retries: int = int(os.getenv("PIPELINE_MAX_RETRIES", "3"))
    log_level: str = os.getenv("PIPELINE_LOG_LEVEL", "INFO")
```

Required env vars: `DATABASE_DSN`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. See `.env.example`.

## Agent Communication

**Agents are INDEPENDENT** - no direct imports between services. Communication via:
1. **Shared database** (primary): RSSReader writes → DigestPublisher reads
2. **Pipeline orchestrator** invokes agents sequentially with `asyncio.timeout()`
3. Return dicts with metadata: `{"saved_count": 5, "published_count": 1}`

**Import pattern**: Agents import from `common.*` for shared functionality (db, models, utils), never from each other.

## HTML Content Processing

**Critical utility**: `src/common/utils/html.py` for cleaning Telegram HTML:
- Removes unsupported media divs, emoji tags, action links
- Extracts hrefs from links, unescapes HTML entities
- Normalizes whitespace and newlines

**Always use** `clean_content()` when processing RSS feed descriptions:
```python
from common.utils.html import clean_content
cleaned = clean_content(item.description)
```

## Testing Conventions

- **pytest** with `pytest-asyncio` for async tests
- **Database setup**: `conftest.py` sets test database DSN
- **Fixture pattern**: Auto-use `setup_database` fixture truncates tables before each test
- **Event loop handling**: Each test gets fresh db connection to avoid loop issues
- Import from `src.*` paths: `from src.feed.db import db, RSSPost`

See `tests/test_database.py` for patterns.

## Module Execution

**All agents run as modules** with `python -m src.{agent}` pattern:
- Entry points in `__main__.py` files
- Import relative to `src/`: `from common.db import ...` (not `from src.common.db`)
- In orchestrator, imports are local: `from rss_reader.__main__ import main`

## External Dependencies

- **RSS Bridge** (https://rss-bridge.org) for Telegram RSS feeds
  - URL builder: `build_rss_bridge_url(channel_name)` in `src/common/utils/rss_bridge.py`
- **OpenAI API** for event classification and summarization
  - Uses `AsyncOpenAI` client
  - Model configurable: default `gpt-4o-mini`
- **python-telegram-bot** for publishing digests

## Logging & Error Handling

- Standard Python logging: `logging.basicConfig()` with format `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- Pipeline orchestrator includes **retry logic** (default 3 attempts, 30s delay)
- **Timeouts per agent**: RSS Reader (300s), Digest Publisher (120s)
- **Graceful degradation**: Failed agents stop pipeline but log details

## Project Structure Notes

- `src/feed/` is **legacy** - newer code uses split services (rss_reader, event_classifier, digest_publisher)
- `alembic/` migrations reference `src/feed/db/config` for DSN
- `pyproject.toml` defines multiple packages under `src/`
- Python 3.14+ required, uses `uv` for dependency management

## When Adding Features

1. **New agents**: Create under `src/`, follow `__main__.py` pattern, integrate in `src/pipeline/orchestrator.py`
2. **Database changes**: Create Alembic migration, update models in `src/common/db/models.py`, add repository methods
3. **Shared utilities**: Add to `src/common/utils/`, import in agents as needed
4. **Configuration**: Add to appropriate config dataclass with env var + default
5. **Testing**: Add to `tests/`, use async fixtures, truncate tables in setup
