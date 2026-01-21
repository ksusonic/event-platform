"""Entry point for Event Classifier service.

Run with: python -m src.event_classifier
"""

import asyncio
from .worker import main

if __name__ == "__main__":
    asyncio.run(main())
