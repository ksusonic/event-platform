# Event Platform - RSS Parser

A production-ready, scalable Python application for parsing RSS and Atom feeds.

## Features

- ✅ Parse RSS 2.0 and Atom feeds
- ✅ Clean, modular architecture with separation of concerns
- ✅ Type hints and comprehensive error handling
- ✅ CLI interface for quick testing
- ✅ Library interface for programmatic use
- ✅ CORS proxy support for cross-origin requests
- ✅ HTML tag stripping from content
- ✅ JSON export functionality
- ✅ Comprehensive test suite

## Project Structure

```
event-platform/
├── src/
│   └── rss_parser/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # CLI entry point
│       ├── cli.py               # Command-line interface
│       ├── manager.py           # Feed manager for multiple feeds
│       ├── core/
│       │   ├── __init__.py
│       │   ├── parser.py        # Core RSS/Atom parsing logic
│       │   └── fetcher.py       # HTTP fetching with proxy support
│       ├── models/
│       │   ├── __init__.py
│       │   └── feed.py          # Data models (RSSChannel, RSSItem)
│       └── utils/
│           ├── __init__.py
│           └── html.py          # HTML utilities
├── tests/
│   ├── __init__.py
│   └── test_parser.py           # Unit tests
├── pyproject.toml               # Project configuration
├── uv.lock                      # Dependency lock file
└── README.md

```

## Installation

```bash
# Install the package in editable mode
uv pip install -e .

# Or install from the directory
uv pip install .
```

## Usage

### Command Line Interface

```bash
# Parse an RSS feed
python -m rss_parser https://example.com/feed.xml

# Example with real feed
python -m rss_parser https://news.ycombinator.com/rss
```

### Library Usage

```python
from rss_parser import RSSParser, RSSChannel, RSSItem

# Basic parsing
parser = RSSParser()
feed = parser.parse_url('https://example.com/feed.xml')

print(f"Feed: {feed.title}")
print(f"Items: {len(feed.items)}")

for item in feed.items:
    print(f"- {item.title}")
    print(f"  {item.link}")
    print(f"  {item.pub_date}")
```

### Using with CORS Proxy

```python
# For cross-origin requests
parser = RSSParser()
feed = parser.parse_url('https://example.com/feed.xml')
```

### Managing Multiple Feeds

```python
from rss_parser.manager import RSSFeedManager

manager = RSSFeedManager()

# Add multiple feeds
manager.add_feed('hn', 'https://news.ycombinator.com/rss')
manager.add_feed('blog', 'https://example.com/feed.xml')

# Get a specific feed
feed = manager.get_feed('hn')
print(f"HN has {len(feed.items)} items")

# Export to JSON
json_data = manager.export_json('hn')
print(json_data)
```

### Working with Feed Data

```python
# Convert to dictionary
feed_dict = feed.to_dict()
print(feed_dict['item_count'])

# Convert to JSON
json_str = feed.to_json()

# Access items
for item in feed.items:
    item_dict = item.to_dict()
    item_json = item.to_json()
```

## Development

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=rss_parser --cov-report=html
```

### Code Quality

```bash
# Format and lint with ruff
ruff check src/
ruff format src/
```

## Architecture

### Core Components

- **`core/parser.py`**: Main parsing logic for RSS and Atom feeds
- **`core/fetcher.py`**: HTTP client with proxy support
- **`models/feed.py`**: Data models using dataclasses
- **`utils/html.py`**: Utility functions for HTML processing
- **`manager.py`**: High-level API for managing multiple feeds
- **`cli.py`**: Command-line interface

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Type Safety**: Comprehensive type hints throughout
3. **Error Handling**: Proper exception handling and logging
4. **Testability**: Modular design makes testing easy
5. **Extensibility**: Easy to add new feed formats or features

## Dependencies

- `requests>=2.32.5` - HTTP library

### Dev Dependencies

- `pytest>=7.4.0` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `ruff>=0.1.0` - Linting and formatting

## License

MIT

