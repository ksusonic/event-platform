"""Entry point for OpenAI worker module."""

import asyncio
from .worker import main

if __name__ == "__main__":
    asyncio.run(main())
