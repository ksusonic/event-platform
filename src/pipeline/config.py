"""Configuration for the pipeline orchestrator."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineConfig:
    """Pipeline configuration settings."""

    # Scheduling
    run_interval_minutes: int = int(os.getenv("PIPELINE_INTERVAL_MINUTES", "60"))
    schedule_enabled: bool = os.getenv("PIPELINE_SCHEDULE_ENABLED", "false").lower() == "true"

    # Agent timeouts (in seconds)
    rss_reader_timeout: int = int(os.getenv("RSS_READER_TIMEOUT", "300"))
    event_classifier_timeout: int = int(os.getenv("EVENT_CLASSIFIER_TIMEOUT", "600"))
    summarizer_timeout: int = int(os.getenv("SUMMARIZER_TIMEOUT", "180"))
    digest_publisher_timeout: int = int(os.getenv("DIGEST_PUBLISHER_TIMEOUT", "120"))

    # Retry settings
    max_retries: int = int(os.getenv("PIPELINE_MAX_RETRIES", "3"))
    retry_delay_seconds: int = int(os.getenv("PIPELINE_RETRY_DELAY", "30"))

    # Agent control
    skip_rss_reader: bool = os.getenv("SKIP_RSS_READER", "false").lower() == "true"
    skip_event_classifier: bool = os.getenv("SKIP_EVENT_CLASSIFIER", "false").lower() == "true"
    skip_summarizer: bool = os.getenv("SKIP_SUMMARIZER", "false").lower() == "true"
    skip_digest_publisher: bool = os.getenv("SKIP_DIGEST_PUBLISHER", "false").lower() == "true"

    # Logging
    log_level: str = os.getenv("PIPELINE_LOG_LEVEL", "INFO")

    # Database
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))

    def validate(self) -> None:
        """Validate configuration values."""
        if self.run_interval_minutes < 1:
            raise ValueError("run_interval_minutes must be at least 1")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be one of {valid_log_levels}")

    def __post_init__(self):
        """Validate config after initialization."""
        self.validate()
