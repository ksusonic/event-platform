"""Main pipeline orchestrator that coordinates all agents."""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from .config import PipelineConfig


class AgentStatus(Enum):
    """Status of agent execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentResult:
    """Result from an agent execution."""

    def __init__(
        self,
        agent_name: str,
        status: AgentStatus,
        duration: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.agent_name = agent_name
        self.status = status
        self.duration = duration
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def __repr__(self):
        return f"AgentResult({self.agent_name}, {self.status.value}, duration={self.duration}s)"


class PipelineOrchestrator:
    """Orchestrates the execution of all agents in the pipeline."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the pipeline orchestrator.

        Args:
            config: Pipeline configuration. If None, uses default config.
        """
        self.config = config or PipelineConfig()
        self.logger = self._setup_logger()
        self.results: List[AgentResult] = []

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with configured log level."""
        logger = logging.getLogger("pipeline")
        logger.setLevel(self.config.log_level.upper())

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def _run_agent_with_retry(
        self, agent_name: str, agent_func: callable, skip: bool = False
    ) -> AgentResult:
        """Run an agent with retry logic.

        Args:
            agent_name: Name of the agent
            agent_func: Async function to execute
            skip: Whether to skip this agent

        Returns:
            AgentResult with execution details
        """
        if skip:
            self.logger.info(f"⏭️  Skipping {agent_name}")
            return AgentResult(agent_name, AgentStatus.SKIPPED)

        self.logger.info(f"🚀 Starting {agent_name}")
        start_time = asyncio.get_event_loop().time()

        for attempt in range(self.config.max_retries + 1):
            try:
                result = await agent_func()
                duration = asyncio.get_event_loop().time() - start_time

                self.logger.info(f"✅ {agent_name} completed in {duration:.2f}s")
                return AgentResult(
                    agent_name, AgentStatus.SUCCESS, duration=duration, metadata=result
                )

            except asyncio.TimeoutError:
                error_msg = f"{agent_name} timed out"
                self.logger.error(f"⏱️  {error_msg}")

                if attempt < self.config.max_retries:
                    self.logger.info(
                        f"🔄 Retrying {agent_name} (attempt {attempt + 2}/{self.config.max_retries + 1})"
                    )
                    await asyncio.sleep(self.config.retry_delay_seconds)
                else:
                    duration = asyncio.get_event_loop().time() - start_time
                    return AgentResult(
                        agent_name, AgentStatus.FAILED, duration=duration, error=error_msg
                    )

            except Exception as e:
                error_msg = f"{agent_name} failed: {str(e)}"
                self.logger.error(f"❌ {error_msg}", exc_info=True)

                if attempt < self.config.max_retries:
                    self.logger.info(
                        f"🔄 Retrying {agent_name} (attempt {attempt + 2}/{self.config.max_retries + 1})"
                    )
                    await asyncio.sleep(self.config.retry_delay_seconds)
                else:
                    duration = asyncio.get_event_loop().time() - start_time
                    return AgentResult(
                        agent_name, AgentStatus.FAILED, duration=duration, error=error_msg
                    )

    async def _run_rss_reader(self) -> Dict[str, Any]:
        """Run the RSS Reader agent."""
        from rss_reader.__main__ import main as rss_reader_main

        async with asyncio.timeout(self.config.rss_reader_timeout):
            result = await rss_reader_main()
            return {"posts_saved": result.get("saved_count", 0)} if result else {}

    async def _run_event_classifier(self) -> Dict[str, Any]:
        """Run the Event Classifier agent."""
        from event_classifier.worker import main as classifier_main

        async with asyncio.timeout(self.config.event_classifier_timeout):
            result = await classifier_main()
            return {"posts_classified": result.get("classified_count", 0)} if result else {}

    async def _run_summarizer(self) -> Dict[str, Any]:
        """Run the Summarizer agent."""
        from summarizer.__main__ import main as summarizer_main

        async with asyncio.timeout(self.config.summarizer_timeout):
            result = await summarizer_main()
            return {"events_summarized": result.get("event_count", 0)} if result else {}

    async def _run_digest_publisher(self) -> Dict[str, Any]:
        """Run the Digest Publisher agent."""
        from digest_publisher.__main__ import main as publisher_main

        async with asyncio.timeout(self.config.digest_publisher_timeout):
            result = await publisher_main()
            return {"digests_published": result.get("published_count", 0)} if result else {}

    async def run_pipeline(self) -> List[AgentResult]:
        """Execute the full pipeline.

        Returns:
            List of AgentResult objects for each agent
        """
        self.logger.info("=" * 80)
        self.logger.info("🎬 Starting Pipeline Execution")
        self.logger.info("=" * 80)

        # Import db here to avoid circular imports
        from common.db.session import db

        # Connect to database once for all agents
        await db.connect()
        self.logger.info("📊 Connected to database")

        pipeline_start = asyncio.get_event_loop().time()
        self.results = []

        # Agent 1: RSS Reader
        result = await self._run_agent_with_retry(
            "RSSReader", self._run_rss_reader, self.config.skip_rss_reader
        )
        self.results.append(result)

        # Stop pipeline if critical agent failed
        if result.status == AgentStatus.FAILED:
            self.logger.error("⛔ RSSReader failed - stopping pipeline")
            return self.results

        # Agent 2: Event Classifier
        result = await self._run_agent_with_retry(
            "EventClassifier", self._run_event_classifier, self.config.skip_event_classifier
        )
        self.results.append(result)

        if result.status == AgentStatus.FAILED:
            self.logger.warning("⚠️  EventClassifier failed - continuing with remaining agents")

        # Agent 3: Summarizer
        result = await self._run_agent_with_retry(
            "Summarizer", self._run_summarizer, self.config.skip_summarizer
        )
        self.results.append(result)

        if result.status == AgentStatus.FAILED:
            self.logger.warning("⚠️  Summarizer failed - continuing with remaining agents")

        # Agent 4: Digest Publisher
        result = await self._run_agent_with_retry(
            "DigestPublisher", self._run_digest_publisher, self.config.skip_digest_publisher
        )
        self.results.append(result)

        # Summary
        pipeline_duration = asyncio.get_event_loop().time() - pipeline_start
        self._print_summary(pipeline_duration)

        # Disconnect from database
        from common.db.session import db

        await db.disconnect()
        self.logger.info("📊 Disconnected from database")

        return self.results

    def _print_summary(self, duration: float):
        """Print execution summary."""
        self.logger.info("=" * 80)
        self.logger.info("📊 Pipeline Execution Summary")
        self.logger.info("=" * 80)

        for result in self.results:
            status_icon = {
                AgentStatus.SUCCESS: "✅",
                AgentStatus.FAILED: "❌",
                AgentStatus.SKIPPED: "⏭️",
            }.get(result.status, "❓")

            duration_str = f"{result.duration:.2f}s" if result.duration else "N/A"
            self.logger.info(f"{status_icon} {result.agent_name:20} | {duration_str:>10}")

            if result.error:
                self.logger.info(f"   Error: {result.error}")

            if result.metadata:
                for key, value in result.metadata.items():
                    self.logger.info(f"   {key}: {value}")

        self.logger.info("-" * 80)
        self.logger.info(f"Total Duration: {duration:.2f}s")

        success_count = sum(1 for r in self.results if r.status == AgentStatus.SUCCESS)
        failed_count = sum(1 for r in self.results if r.status == AgentStatus.FAILED)
        skipped_count = sum(1 for r in self.results if r.status == AgentStatus.SKIPPED)

        self.logger.info(
            f"Results: {success_count} succeeded, {failed_count} failed, {skipped_count} skipped"
        )
        self.logger.info("=" * 80)

    async def run_scheduled(self):
        """Run the pipeline on a schedule."""
        self.logger.info(
            f"📅 Starting scheduled pipeline (interval: {self.config.run_interval_minutes}m)"
        )

        while True:
            try:
                await self.run_pipeline()
                self.logger.info(f"⏰ Next run in {self.config.run_interval_minutes} minutes")
                await asyncio.sleep(self.config.run_interval_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("⏹️  Stopping scheduled pipeline")
                break

            except Exception as e:
                self.logger.error(f"💥 Unexpected error in scheduled pipeline: {e}", exc_info=True)
                self.logger.info(f"⏰ Retrying in {self.config.run_interval_minutes} minutes")
                await asyncio.sleep(self.config.run_interval_minutes * 60)
