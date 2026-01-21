"""Entry point for Pipeline Orchestrator.

Run with:
    python -m src.pipeline                    # Run pipeline once
    python -m src.pipeline --schedule         # Run on schedule
    python -m src.pipeline --help             # Show help
"""

import asyncio
import argparse
import sys
import logging

from .orchestrator import PipelineOrchestrator
from .config import PipelineConfig


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Telegram News Aggregator Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pipeline once
  python -m src.pipeline

  # Run on schedule (reads PIPELINE_INTERVAL_MINUTES from env)
  python -m src.pipeline --schedule

  # Run with custom interval
  python -m src.pipeline --schedule --interval 30

  # Skip specific agents
  python -m src.pipeline --skip-rss-reader --skip-summarizer

  # Set log level
  python -m src.pipeline --log-level DEBUG
  
  # With all options
  python -m src.pipeline --schedule --interval 30 --max-retries 5 --log-level DEBUG

Environment Variables:
  # Pipeline Control
  PIPELINE_INTERVAL_MINUTES     Interval between runs (default: 60)
  PIPELINE_SCHEDULE_ENABLED     Enable scheduled runs (default: false)
  PIPELINE_MAX_RETRIES         Max retry attempts (default: 3)
  PIPELINE_RETRY_DELAY         Delay between retries in seconds (default: 30)
  PIPELINE_LOG_LEVEL           Log level (default: INFO)
  
  # Agent Timeouts (seconds)
  RSS_READER_TIMEOUT           RSS Reader timeout (default: 300)
  SUMMARIZER_TIMEOUT           Summarizer timeout (default: 180)
  DIGEST_PUBLISHER_TIMEOUT     Digest Publisher timeout (default: 120)
  
  # Agent Control
  SKIP_RSS_READER              Skip RSS Reader (default: false)
  SKIP_SUMMARIZER              Skip Summarizer (default: false)
  SKIP_DIGEST_PUBLISHER        Skip Digest Publisher (default: false)
  
  # Database
  DB_POOL_SIZE                 Database connection pool size (default: 10)
  DB_MAX_OVERFLOW              Max database overflow connections (default: 20)
  
  # Telegram (for Digest Publisher)
  TELEGRAM_BOT_TOKEN           Telegram bot token (required for publishing)
  TELEGRAM_CHAT_ID             Telegram chat/channel ID (required for publishing)
  DIGEST_DAYS                  Number of days for digest (default: 7)
  MAX_POSTS_PER_DIGEST         Max posts per digest (default: 20)
  TRUNCATE_CONTENT_LENGTH      Content truncation length (default: 300)
        """,
    )

    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run pipeline on a schedule (continuously)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        metavar="MINUTES",
        help="Interval between runs in minutes (default: from env or 60)",
    )

    parser.add_argument(
        "--skip-rss-reader",
        action="store_true",
        help="Skip RSS Reader agent",
    )

    parser.add_argument(
        "--skip-summarizer",
        action="store_true",
        help="Skip Summarizer agent",
    )

    parser.add_argument(
        "--skip-digest-publisher",
        action="store_true",
        help="Skip Digest Publisher agent",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set log level (default: from env or INFO)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        metavar="N",
        help="Maximum retry attempts (default: from env or 3)",
    )

    parser.add_argument(
        "--retry-delay",
        type=int,
        metavar="SECONDS",
        help="Delay between retries in seconds (default: from env or 30)",
    )

    return parser.parse_args()


def create_config(args) -> PipelineConfig:
    """Create config from command line arguments."""
    config = PipelineConfig()

    # Override with command line args if provided
    if args.interval is not None:
        config.run_interval_minutes = args.interval

    if args.schedule:
        config.schedule_enabled = True

    if args.skip_rss_reader:
        config.skip_rss_reader = True

    if args.skip_summarizer:
        config.skip_summarizer = True

    if args.skip_digest_publisher:
        config.skip_digest_publisher = True

    if args.log_level:
        config.log_level = args.log_level

    if args.max_retries is not None:
        config.max_retries = args.max_retries

    if args.retry_delay is not None:
        config.retry_delay_seconds = args.retry_delay

    return config


async def main():
    """Main entry point."""
    args = parse_args()
    config = create_config(args)

    # Validate config
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create orchestrator
    orchestrator = PipelineOrchestrator(config)

    # Run pipeline
    try:
        if config.schedule_enabled or args.schedule:
            await orchestrator.run_scheduled()
        else:
            results = await orchestrator.run_pipeline()

            # Exit with error code if any agent failed
            failed = any(r.status.value == "failed" for r in results)
            if failed:
                sys.exit(1)

    except KeyboardInterrupt:
        orchestrator.logger.info("\n⏹️  Pipeline stopped by user")
        sys.exit(0)

    except Exception as e:
        logging.error(f"💥 Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
