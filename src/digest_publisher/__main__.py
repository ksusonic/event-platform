"""Entry point for Digest Publisher service.

Run with: python -m src.digest_publisher
"""

import asyncio
import logging
from typing import List
from datetime import datetime, timedelta

from common.db.session import db
from common.db.repository import EventRepository
from common.db.models import Event

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def format_event_for_telegram(event: Event) -> str:
    """
    Format an event for Telegram message.

    Args:
        event: Event object

    Returns:
        Formatted string for Telegram
    """
    lines = []
    lines.append(f"📅 **{event.title}**")

    if event.event_date:
        lines.append(f"🕐 {event.event_date.strftime('%Y-%m-%d %H:%M')}")

    if event.location:
        lines.append(f"📍 {event.location}")

    if event.description:
        # Truncate long descriptions for Telegram
        desc = (
            event.description[:300] + "..." if len(event.description) > 300 else event.description
        )
        lines.append(f"\n{desc}")

    lines.append(f"\n🔗 [Source]({event.link})")

    return "\n".join(lines)


def create_digest(events: List[Event]) -> str:
    """
    Create a digest message from events.

    Args:
        events: List of Event objects

    Returns:
        Formatted digest string
    """
    if not events:
        return "No events found for this period."

    lines = []
    lines.append("🎉 **Event Digest**")
    lines.append(f"Found {len(events)} upcoming events\n")
    lines.append("=" * 40)
    lines.append("")

    for i, event in enumerate(events, 1):
        lines.append(format_event_for_telegram(event))
        if i < len(events):
            lines.append("\n" + "-" * 40 + "\n")

    return "\n".join(lines)


async def publish_to_telegram(message: str):
    """
    Publish message to Telegram.

    Args:
        message: Message to publish
    """
    # TODO: Implement actual Telegram bot integration
    # For now, just print the message
    logger.info("Publishing to Telegram (stub implementation):")
    print("\n" + "=" * 80)
    print("TELEGRAM DIGEST")
    print("=" * 80)
    print(message)
    print("=" * 80)

    # In production, this would use something like:
    # bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    # chat_id = os.getenv("TELEGRAM_CHAT_ID")
    # Send message via Telegram Bot API


async def main():
    """Main entry point for Digest Publisher service."""
    logger.info("Starting Digest Publisher service...")

    try:
        if not db.pool:
            await db.connect()
            logger.info("Connected to database")

        # Get events from the next 7 days
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        logger.info(f"Fetching events from {start_date} to {end_date}")
        events = await EventRepository.get_by_date_range(start_date, end_date)

        if not events:
            logger.info("No upcoming events found")
            print("No upcoming events in the next 7 days.")
            return

        # Create digest
        digest = create_digest(events)

        # Publish to Telegram
        await publish_to_telegram(digest)

        logger.info(f"Successfully published digest with {len(events)} events")

        return {"published_count": len(events)}

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
