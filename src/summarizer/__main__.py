"""Entry point for Summarizer service.

Run with: python -m src.summarizer
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


async def summarize_events(events: List[Event]) -> str:
    """
    Create a summary of events.

    Args:
        events: List of Event objects

    Returns:
        Formatted summary string
    """
    if not events:
        return "No events found for the specified period."

    summary = []
    summary.append(f"Found {len(events)} events:\n")
    summary.append("=" * 80)

    for i, event in enumerate(events, 1):
        summary.append(f"\n{i}. {event.title}")
        if event.event_date:
            summary.append(f"   Date: {event.event_date.strftime('%Y-%m-%d %H:%M')}")
        if event.location:
            summary.append(f"   Location: {event.location}")
        if event.description:
            # Truncate long descriptions
            desc = (
                event.description[:200] + "..."
                if len(event.description) > 200
                else event.description
            )
            summary.append(f"   Description: {desc}")
        summary.append(f"   Source: {event.link}")
        summary.append("")

    summary.append("=" * 80)
    return "\n".join(summary)


async def main():
    """Main entry point for Summarizer service."""
    logger.info("Starting Summarizer service...")

    try:
        # Connect to database
        await db.connect()
        logger.info("Connected to database")

        # Get events from the last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        logger.info(f"Fetching events from {start_date} to {end_date}")
        events = await EventRepository.get_by_date_range(start_date, end_date)

        if not events:
            logger.info("No events found in the specified date range")
            print("No events found in the last 7 days.")
            return

        # Create summary
        summary = await summarize_events(events)
        print(summary)

        logger.info(f"Successfully summarized {len(events)} events")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"Error: {e}")
        import sys

        sys.exit(1)
    finally:
        await db.disconnect()
        logger.info("Disconnected from database")


if __name__ == "__main__":
    asyncio.run(main())
