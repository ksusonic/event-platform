FROM python:3.14-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Run migrations on startup
CMD ["sh", "-c", "alembic upgrade head && python -m src.pipeline --schedule"]
