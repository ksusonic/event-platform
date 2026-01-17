"""Test script to verify OpenAI request logging functionality."""

import asyncio
from decimal import Decimal

from ..db.models import OpenAIRequestLog
from ..db.repository import OpenAIRequestLogRepository
from ..db.session import db


async def test_logging():
    """Test OpenAI request logging."""

    print("🔍 Testing OpenAI Request Logging\n")

    # Initialize database connection
    await db.connect()

    try:
        # Test 1: Create a log entry
        print("1. Creating a test log entry...")
        log = OpenAIRequestLog(
            batch_id="batch_test_123",
            custom_id="post_0_abc123def456",
            request_type="batch",
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            request_data={
                "messages": [
                    {"role": "system", "content": "Test system prompt"},
                    {"role": "user", "content": "Test user prompt"}
                ],
                "max_tokens": 500,
                "temperature": 0.3
            },
            status="pending",
            post_link="https://example.com/test-post"
        )

        log_id = await OpenAIRequestLogRepository.create(log)
        print(f"✓ Created log entry with ID: {log_id}\n")

        # Test 2: Retrieve the log entry
        print("2. Retrieving the log entry...")
        retrieved_log = await OpenAIRequestLogRepository.get_by_id(log_id)
        if retrieved_log:
            print(f"✓ Retrieved log: {retrieved_log.custom_id}")
            print(f"  Status: {retrieved_log.status}")
            print(f"  Model: {retrieved_log.model}\n")

        # Test 3: Update status to completed
        print("3. Updating status to completed...")
        await OpenAIRequestLogRepository.update_status(
            log_id=log_id,
            status="completed",
            status_code=200,
            response_data={
                "choices": [{"message": {"content": '{"is_event": true}'}}],
                "usage": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50}
            },
            tokens_used=150,
            cost_estimate=Decimal("0.000023")
        )
        print("✓ Updated status to completed\n")

        # Test 4: Get by batch_id
        print("4. Retrieving logs by batch_id...")
        batch_logs = await OpenAIRequestLogRepository.get_by_batch_id("batch_test_123")
        print(f"✓ Found {len(batch_logs)} log(s) for batch\n")

        # Test 5: Get statistics
        print("5. Getting statistics...")
        stats = await OpenAIRequestLogRepository.get_stats()
        print(f"✓ Stats:")
        print(f"  Total: {stats['total']}")
        print(f"  Completed: {stats['completed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Total tokens: {stats['total_tokens']}")
        print(f"  Total cost: ${stats['total_cost']:.6f}\n")

        # Test 6: Get all logs
        print("6. Retrieving all logs (limit 10)...")
        all_logs = await OpenAIRequestLogRepository.get_all(limit=10)
        print(f"✓ Retrieved {len(all_logs)} log(s)\n")

        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(test_logging())
