"""Main OpenAI worker for event classification."""

import asyncio
from typing import Optional
from datetime import datetime

from .batch_processor import BatchProcessor
from .config import openai_settings
from common.db.repository import RSSPostRepository
from common.db.session import db


class OpenAIWorker:
    """Worker that processes unclassified posts using OpenAI Batch API."""

    def __init__(self):
        """Initialize the OpenAI worker."""
        self.processor = BatchProcessor()

    async def process_unprocessed_posts(
        self, batch_size: Optional[int] = None, wait_for_completion: bool = True
    ) -> dict:
        """Get all unprocessed posts and submit them for classification.

        Args:
            batch_size: Maximum number of posts to process (default from config)
            wait_for_completion: Whether to wait for batch completion

        Returns:
            Dictionary with processing information
        """
        if batch_size is None:
            batch_size = openai_settings.batch_size

        print(f"Fetching up to {batch_size} unprocessed posts...")

        # Get unprocessed posts from database
        posts = await RSSPostRepository.get_unprocessed(limit=batch_size)

        if not posts:
            print("No unprocessed posts found.")
            return {"status": "no_posts", "posts_count": 0, "batch_id": None}

        print(f"Found {len(posts)} unprocessed posts")
        print("Submitting batch to OpenAI...")

        # Submit batch
        batch_id = await self.processor.submit_batch(posts)

        result = {
            "status": "submitted",
            "posts_count": len(posts),
            "batch_id": batch_id,
            "submitted_at": datetime.now().isoformat(),
        }

        if wait_for_completion:
            print("\nWaiting for batch to complete...")
            success = await self.processor.wait_for_completion(batch_id)

            if success:
                # Download and process results
                results_file = self.processor.download_results(batch_id)
                if results_file:
                    print("\nProcessing results and updating database...")
                    stats = await self.processor.process_results(results_file, posts)
                    result["status"] = "completed"
                    result["stats"] = stats
                else:
                    result["status"] = "download_failed"
            else:
                result["status"] = "failed"

        return result

    async def check_batch(self, batch_id: str) -> dict:
        """Check the status of a previously submitted batch.

        Args:
            batch_id: OpenAI batch ID

        Returns:
            Dictionary with batch status
        """
        return self.processor.check_batch_status(batch_id)

    async def complete_batch(self, batch_id: str, posts_links: list[str]) -> dict:
        """Download and process results for a completed batch.

        Args:
            batch_id: OpenAI batch ID
            posts_links: List of post links that were in the batch

        Returns:
            Dictionary with processing statistics
        """
        # Download results
        results_file = self.processor.download_results(batch_id)
        if not results_file:
            return {"status": "not_ready"}

        # Get posts from database
        posts = []
        for link in posts_links:
            post = await RSSPostRepository.get_by_link(link)
            if post:
                posts.append(post)

        # Process results
        stats = await self.processor.process_results(results_file, posts)
        return {"status": "completed", "stats": stats}

    async def run(self):
        """Main worker loop - process posts and wait for completion."""
        print("=" * 80)
        print("OpenAI Event Classification Worker")
        print("=" * 80)
        print(f"Model: {openai_settings.model}")
        print(f"Batch size: {openai_settings.batch_size}")
        print(f"Temperature: {openai_settings.temperature}")
        print("=" * 80)
        print()

        if not db.pool:
            await db.connect()

        result = await self.process_unprocessed_posts(wait_for_completion=True)

        print("\n" + "=" * 80)
        print("Processing Summary")
        print("=" * 80)
        print(f"Status: {result['status']}")
        print(f"Posts processed: {result['posts_count']}")
        if result.get("batch_id"):
            print(f"Batch ID: {result['batch_id']}")
        if result.get("stats"):
            stats = result["stats"]
            print("\nResults:")
            print(f"  Total responses: {stats['total']}")
            print(f"  Successful: {stats['success']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Events found: {stats['events_found']}")
        print("=" * 80)

        return result


async def main():
    """Entry point for running the worker."""
    worker = OpenAIWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
