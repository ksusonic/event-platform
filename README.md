# Event Platform - Telegram News Aggregator

A production-ready, scalable Python application for aggregating events from Telegram channels via RSS feeds.
The platform fetches, classifies, summarizes, and publishes event announcements through an automated multi-agent pipeline.

## 🏗️ Architecture

The system consists of 4 coordinated agents:

```
┌─────────────────┐
│   RSS Bridge    │ (external: rss-bridge.org)
└────────┬────────┘
         │ RSS/MRSS
         ▼
┌─────────────────┐
│   RSSReader     │ ← Fetches posts from Telegram channels
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│EventClassifier  │ ← Classifies posts as events using OpenAI
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Summarizer    │ ← Creates event summaries
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│DigestPublisher  │ ← Publishes to Telegram
└─────────────────┘
```

## ✨ Features

- 🔄 **Automated Pipeline**: Orchestrated execution of all agents
- 📡 **RSS Feed Processing**: Parse Telegram channels via RSS Bridge
- 🤖 **AI Classification**: OpenAI-powered event detection
- 📊 **Event Summarization**: Generate digestible event summaries
- 📱 **Telegram Publishing**: Automated posting to Telegram channels
- ⏱️ **Scheduling**: Run on schedule or on-demand
- 🛡️ **Error Handling**: Retry logic and graceful failure handling
- 📝 **Comprehensive Logging**: Detailed execution metrics

## 🚀 Quick Start

### Prerequisites

- Python 3.14+
- PostgreSQL 17+
- OpenAI API key
- Telegram Bot token

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd event-platform
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run database migrations:
```bash
alembic upgrade head
```

### Running the Pipeline

**Run once:**
```bash
python -m src.pipeline
```

**Run on schedule:**
```bash
python -m src.pipeline --schedule --interval 60
```

**Run with Docker:**
```bash
docker-compose up -d
```

## 📖 Documentation

- [Pipeline Orchestrator Guide](src/pipeline/README.md)
- [Architecture Details](AGENTS.md)

## 🔧 Configuration

See [`.env.example`](.env.example) for all configuration options.

Key settings:
- `PIPELINE_INTERVAL_MINUTES`: How often to run (default: 60)
- `RSS_READER_TIMEOUT`: RSS Reader timeout in seconds (default: 300)
- `EVENT_CLASSIFIER_TIMEOUT`: Classifier timeout (default: 600)
- `OPENAI_API_KEY`: Your OpenAI API key
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token

## 🧪 Testing

```bash
pytest tests/
```

## 📦 Project Structure

```
event-platform/
├── src/
│   ├── common/           # Shared utilities and database models
│   ├── pipeline/         # Pipeline orchestrator
│   ├── rss_reader/       # RSS feed fetching agent
│   ├── event_classifier/ # Event classification agent
│   ├── summarizer/       # Event summarization agent
│   └── digest_publisher/ # Telegram publishing agent
├── alembic/              # Database migrations
├── tests/                # Test suite
├── docker-compose.yml    # Docker configuration
└── pyproject.toml        # Project dependencies
```

## 🐳 Docker Deployment

Start all services:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f pipeline
```

Stop services:
```bash
docker-compose down
```

## 📝 License

MIT
