"""OpenAI Batch API processor for event classification."""

import json
import time
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from openai import OpenAI

from .config import openai_settings
from ..db.models import RSSPost, OpenAIRequestLog, Event
from ..db.repository import RSSPostRepository, OpenAIRequestLogRepository, EventRepository


class BatchProcessor:
    """Handles OpenAI Batch API requests for event classification."""

    SYSTEM_PROMPT = """Classify if posts describe events (conferences, meetups, launches, workshops, etc.). Events have specific dates/times and activities.

JSON response format:
{
    "is_event": true/false,
    "confidence": 0.0-1.0,
    "event_details": {
        "date": "date if found",
        "location": "location if found",
        "type": "event type"
    }
}"""

    USER_PROMPT_TEMPLATE = """Link: {link}
Content: {content}
Date: {pub_date}

Is this an event?"""

    def __init__(self):
        """Initialize the batch processor."""
        self.client = OpenAI(api_key=openai_settings.api_key)
        self.batch_dir = Path(__file__).parent.parent.parent.parent / "batch_data"
        self.batch_dir.mkdir(exist_ok=True)

    async def create_batch_request_file(
        self, posts: List[RSSPost], batch_id: Optional[str] = None
    ) -> Path:
        """Create a JSONL file with batch requests and log them to database.

        Args:
            posts: List of RSSPost instances to process
            batch_id: Optional batch ID to associate with logs (for pre-logging)

        Returns:
            Path to the created JSONL file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.batch_dir / f"batch_request_{timestamp}.jsonl"

        with open(filepath, "w") as f:
            for i, post in enumerate(posts):
                # Truncate content if too long (to stay within token limits)
                content = post.content[:2000] if len(post.content) > 2000 else post.content

                user_prompt = self.USER_PROMPT_TEMPLATE.format(
                    link=post.link,
                    content=content,
                    pub_date=post.pub_date.isoformat() if post.pub_date else "Unknown",
                )

                # Create a unique custom_id using hash of the link
                link_hash = hashlib.md5(post.link.encode()).hexdigest()[:16]
                custom_id = f"post_{i}_{link_hash}"

                request_body = {
                    "model": openai_settings.model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": openai_settings.max_tokens,
                    "temperature": openai_settings.temperature,
                    "response_format": {"type": "json_object"},
                }

                request = {
                    "custom_id": custom_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": request_body,
                }
                f.write(json.dumps(request) + "\n")

                # Log the request to database
                log_entry = OpenAIRequestLog(
                    batch_id=batch_id,
                    custom_id=custom_id,
                    request_type="batch",
                    model=openai_settings.model,
                    endpoint="/v1/chat/completions",
                    request_data={
                        "messages": request_body["messages"],
                        "max_tokens": request_body["max_tokens"],
                        "temperature": request_body["temperature"],
                    },
                    status="pending",
                    post_link=post.link,
                )
                await OpenAIRequestLogRepository.create(log_entry)

        return filepath

    async def submit_batch(self, posts: List[RSSPost]) -> str:
        """Submit a batch of posts for processing.

        Args:
            posts: List of RSSPost instances to process

        Returns:
            Batch ID from OpenAI
        """
        if not posts:
            raise ValueError("No posts provided for batch processing")

        # Create batch request file (this will log individual requests with batch_id=None initially)
        request_file_path = await self.create_batch_request_file(posts)

        # Upload file to OpenAI
        with open(request_file_path, "rb") as f:
            batch_input_file = self.client.files.create(file=f, purpose="batch")

        # Create batch
        batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": f"Event classification for {len(posts)} posts",
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Update all pending logs with the batch_id
        for post in posts:
            link_hash = hashlib.md5(post.link.encode()).hexdigest()[:16]
            # Find log entries by custom_id pattern
            for i in range(len(posts)):
                custom_id = f"post_{i}_{link_hash}"
                log = await OpenAIRequestLogRepository.get_by_custom_id(custom_id)
                if log and log.batch_id is None:
                    # Update with batch_id
                    query = "UPDATE openai_request_logs SET batch_id = $1 WHERE id = $2"
                    from ..db.session import db

                    await db.execute(query, batch.id, log.id)
                    break

        print(f"Batch submitted: {batch.id}")
        print(f"Status: {batch.status}")
        print(f"Request file saved: {request_file_path}")
        print(f"Logged {len(posts)} requests to database")

        return batch.id

    def check_batch_status(self, batch_id: str) -> Dict:
        """Check the status of a batch.

        Args:
            batch_id: OpenAI batch ID

        Returns:
            Dictionary with batch status information
        """
        batch = self.client.batches.retrieve(batch_id)

        return {
            "id": batch.id,
            "status": batch.status,
            "created_at": batch.created_at,
            "completed_at": batch.completed_at,
            "failed_at": batch.failed_at,
            "error_file_id": batch.error_file_id,
            "output_file_id": batch.output_file_id,
            "request_counts": {
                "total": batch.request_counts.total,
                "completed": batch.request_counts.completed,
                "failed": batch.request_counts.failed,
            },
        }

    def download_results(self, batch_id: str) -> Optional[Path]:
        """Download batch results.

        Args:
            batch_id: OpenAI batch ID

        Returns:
            Path to downloaded results file, or None if not ready
        """
        batch = self.client.batches.retrieve(batch_id)

        if batch.status != "completed":
            print(f"Batch {batch_id} not completed yet. Status: {batch.status}")
            return None

        if not batch.output_file_id:
            print(f"No output file for batch {batch_id}")
            return None

        # Download results
        file_content = self.client.files.content(batch.output_file_id)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.batch_dir / f"batch_results_{batch_id}_{timestamp}.jsonl"

        with open(output_path, "wb") as f:
            f.write(file_content.content)

        print(f"Results downloaded: {output_path}")
        return output_path

    async def process_results(self, results_file: Path, posts: List[RSSPost]) -> Dict:
        """Process batch results and update database.

        Args:
            results_file: Path to the results JSONL file
            posts: Original list of posts (for reference)

        Returns:
            Dictionary with processing statistics
        """
        stats = {"total": 0, "success": 0, "failed": 0, "events_found": 0}

        # Create a mapping of posts by their link hash for quick lookup
        posts_by_hash = {}
        for post in posts:
            link_hash = hashlib.md5(post.link.encode()).hexdigest()[:16]
            posts_by_hash[link_hash] = post

        with open(results_file, "r") as f:
            for line in f:
                stats["total"] += 1
                result = json.loads(line)

                try:
                    # Extract custom_id to find the corresponding post
                    custom_id = result["custom_id"]
                    # custom_id format: "post_{i}_{link_hash}"

                    # Extract the hash from custom_id
                    parts = custom_id.split("_")
                    if len(parts) < 3:
                        print(f"Invalid custom_id format: {custom_id}")
                        stats["failed"] += 1
                        continue

                    link_hash = parts[2]

                    # Get the response
                    response = result["response"]
                    status_code = response["status_code"]

                    if status_code != 200:
                        stats["failed"] += 1
                        print(f"Failed response for {custom_id}: {response}")

                        # Log the failure
                        log = await OpenAIRequestLogRepository.get_by_custom_id(custom_id)
                        if log:
                            await OpenAIRequestLogRepository.update_status(
                                log_id=log.id,
                                status="failed",
                                status_code=status_code,
                                response_data=response,
                                error_message=response.get("body", {})
                                .get("error", {})
                                .get("message", "Unknown error"),
                            )
                        continue

                    # Parse the classification result
                    message_content = response["body"]["choices"][0]["message"]["content"]
                    classification = json.loads(message_content)

                    # Calculate tokens used
                    usage = response["body"].get("usage", {})
                    tokens_used = usage.get("total_tokens", 0)

                    # Estimate cost (gpt-4o-mini pricing: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens)
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    cost_estimate = Decimal(
                        (prompt_tokens * 0.15 / 1_000_000) + (completion_tokens * 0.60 / 1_000_000)
                    )

                    # Find the matching post using the hash
                    matching_post = posts_by_hash.get(link_hash)

                    if not matching_post:
                        print(
                            f"Could not find matching post for hash {link_hash} (custom_id: {custom_id})"
                        )
                        stats["failed"] += 1

                        # Still log the response
                        log = await OpenAIRequestLogRepository.get_by_custom_id(custom_id)
                        if log:
                            await OpenAIRequestLogRepository.update_status(
                                log_id=log.id,
                                status="completed",
                                status_code=status_code,
                                response_data=response["body"],
                                tokens_used=tokens_used,
                                cost_estimate=cost_estimate,
                                error_message="Post not found in current batch",
                            )
                        continue

                    # Update the database
                    is_event = classification.get("is_event", False)
                    classification_data = {
                        "confidence": classification.get("confidence", 0.0),
                        "event_details": classification.get("event_details", {}),
                        "model": openai_settings.model,
                        "classified_at": datetime.now().isoformat(),
                    }

                    await RSSPostRepository.mark_as_processed(
                        link=matching_post.link,
                        is_event=is_event,
                        classification_data=classification_data,
                    )

                    # If it's an event, create an entry in the events table
                    if is_event:
                        event_details = classification.get("event_details", {})

                        # Extract and parse event date if available
                        event_date = None
                        event_date_str = event_details.get("date")
                        if event_date_str:
                            try:
                                # Try to parse the date
                                event_date = datetime.fromisoformat(
                                    event_date_str.replace("Z", "+00:00")
                                )
                                if event_date.tzinfo is not None:
                                    event_date = event_date.replace(tzinfo=None)
                            except (ValueError, AttributeError):
                                # If parsing fails, leave it as None
                                pass

                        # Extract title from link (simple extraction)
                        title = (
                            matching_post.link.split("/")[-1][:500] if matching_post.link else None
                        )

                        # Create event
                        event = Event(
                            post_link=matching_post.link,
                            title=title,
                            summary=matching_post.content[:1000] if matching_post.content else None,
                            event_date=event_date,
                            event_date_is_approximate=event_date is None or not event_date_str,
                            location=event_details.get("location"),
                            event_type=event_details.get("type"),
                            confidence=Decimal(str(classification.get("confidence", 0.0))),
                            additional_data={
                                "classification_model": openai_settings.model,
                                "original_content_length": len(matching_post.content),
                                "pub_date": matching_post.pub_date.isoformat()
                                if matching_post.pub_date
                                else None,
                            },
                        )

                        try:
                            event_id = await EventRepository.create(event)
                            print(f"  → Created event #{event_id} in events table")
                        except Exception as e:
                            print(f"  ⚠ Failed to create event: {e}")

                    # Log the successful response
                    log = await OpenAIRequestLogRepository.get_by_custom_id(custom_id)
                    if log:
                        await OpenAIRequestLogRepository.update_status(
                            log_id=log.id,
                            status="completed",
                            status_code=status_code,
                            response_data=response["body"],
                            tokens_used=tokens_used,
                            cost_estimate=cost_estimate,
                        )

                    stats["success"] += 1
                    if is_event:
                        stats["events_found"] += 1
                        print(f"✓ Event found: {matching_post.link[:80]}")
                    else:
                        print(f"○ Not an event: {matching_post.link[:80]}")

                except Exception as e:
                    stats["failed"] += 1
                    print(f"Error processing result: {e}")

                    # Try to log the error
                    try:
                        custom_id = result.get("custom_id")
                        if custom_id:
                            log = await OpenAIRequestLogRepository.get_by_custom_id(custom_id)
                            if log:
                                await OpenAIRequestLogRepository.update_status(
                                    log_id=log.id, status="failed", error_message=str(e)
                                )
                    except Exception:
                        pass
                    continue

        return stats

    async def wait_for_completion(
        self, batch_id: str, poll_interval: int = 30, max_wait: int = 3600
    ) -> bool:
        """Wait for batch to complete.

        Args:
            batch_id: OpenAI batch ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait

        Returns:
            True if completed successfully, False otherwise
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_info = self.check_batch_status(batch_id)
            status = status_info["status"]

            print(f"Batch {batch_id} status: {status}")
            print(
                f"  Completed: {status_info['request_counts']['completed']}/{status_info['request_counts']['total']}"
            )

            if status == "completed":
                print("✓ Batch completed successfully")
                return True
            elif status in ["failed", "expired", "cancelled"]:
                print(f"✗ Batch ended with status: {status}")
                return False

            # Still processing
            time.sleep(poll_interval)

        print("✗ Timeout waiting for batch completion")
        return False
